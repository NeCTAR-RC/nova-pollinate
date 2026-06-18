# Copyright 2026 Australian Research Data Commons
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""CrowdStrike Falcon Sensor Provider

This provider generates vendor data for the CrowdStrike cloud-init module. It
retrieves the CID (Customer ID) and installer URLs from Vault based on the
instance's availability zone.

**Availability zone lookup:**

Nova does not pass the availability zone in the vendordata context (only
``project-id``, ``instance-id``, ``image-id``, ``user-data``, ``hostname`` and
``metadata``). The provider therefore looks the instance up via the Nova API
and reads ``OS-EXT-AZ:availability_zone`` from the server object.

**Vault Secrets Structure:**

All secrets are AZ-specific. The AZ name is normalised by upper-casing it,
preserving hyphens (e.g. ``melbourne-qh2`` -> ``MELBOURNE-QH2``).

- ``CROWDSTRIKE_<AZ>_CID``: CID for the availability zone
- ``CROWDSTRIKE_<AZ>_INSTALLER_URL_DEB``: URL for the Debian/Ubuntu package
- ``CROWDSTRIKE_<AZ>_INSTALLER_URL_RPM``: URL for the RHEL/SUSE package
- ``CROWDSTRIKE_<AZ>_ENABLED``: optional per-AZ opt-out (default ``true``)
- ``CROWDSTRIKE_<AZ>_FAIL_IF_MISSING``: optional fail-closed
  (default ``false``)

**Behaviour:**

- Returns configuration only if a CID is found for the AZ.
- If no CID is found for the AZ, returns an empty dict (silent skip). This
  gives per-AZ opt-in: AZs without Vault config never attempt installation.
- If ``CROWDSTRIKE_<AZ>_ENABLED`` is set to a false value, the provider skips
  the AZ entirely so no CID or URLs are injected (per-AZ opt-out).
- The cloud-init module handles the actual installation and configuration, and
  selects the deb or rpm URL based on the guest OS family.

**Output:**

The provider returns the bare configuration dict. ``service.py`` keys it under
the provider name (``crowdstrike``) and Nova nests the whole response under the
dynamic target name (``nectar``), so the guest sees it at
``vendor_data2.nectar.crowdstrike``:

.. code-block:: json

    {
      "cid": "XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XX",
      "installer_url": "https://example.com/falcon-sensor.deb",
      "installer_url_deb": "https://example.com/falcon-sensor.deb",
      "installer_url_rpm": "https://example.com/falcon-sensor.rpm",
      "enabled": true,
      "fail_if_missing": false
    }
"""

import logging

from flask import current_app

from pollinate import clients
from pollinate.providers import PollinateProvider

LOG = logging.getLogger(__name__)


def _as_bool(value, default):
    """Coerce a Vault value to a boolean.

    Vault kv values are stored as strings, so accept the common truthy
    spellings. Returns ``default`` when the value is missing.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class CrowdStrikeProvider(PollinateProvider):
    """Provider for CrowdStrike Falcon sensor configuration."""

    name = 'crowdstrike'

    def _normalize_az_name(self, az):
        """Normalise an availability zone name for Vault key construction.

        Upper-cases the name while preserving hyphens, keeping the full AZ
        identity for granular per-AZ configuration.

        Examples:
            melbourne-qh2 -> MELBOURNE-QH2
            melbourne-qh2-uom -> MELBOURNE-QH2-UOM
            monash-01 -> MONASH-01
            tasmania -> TASMANIA
        """
        if not az:
            return None
        return az.upper()

    def _get_secret(self, key):
        """Return a Vault secret, or None if it is not present."""
        try:
            return current_app.secrets.get(key)
        except KeyError:
            LOG.debug('%s not found in Vault', key)
            return None

    def run(self, context):
        """Generate vendor data for CrowdStrike installation.

        Args:
            context: Nova metadata context containing instance details

        Returns:
            Dict with the CrowdStrike config, or an empty dict to skip
        """
        ks_session = current_app.ks_session
        nova_client = clients.get_nova_client(ks_session)

        instance_id = context['instance-id']
        instance = nova_client.servers.get(instance_id)
        az = getattr(instance, 'OS-EXT-AZ:availability_zone', None)

        if not az:
            LOG.warning(
                'No availability zone for instance %s, skipping CrowdStrike',
                instance_id,
            )
            return {}

        site = self._normalize_az_name(az)

        # Get the CID for this site. Absence means this AZ has not opted in.
        cid = self._get_secret(f'CROWDSTRIKE_{site}_CID')
        if not cid:
            LOG.info(
                'No CrowdStrike CID found for AZ %s (site: %s), '
                'skipping installation',
                az,
                site,
            )
            return {}

        # Per-AZ opt-out: skip entirely so no CID or URLs are injected.
        enabled = _as_bool(
            self._get_secret(f'CROWDSTRIKE_{site}_ENABLED'), default=True
        )
        if not enabled:
            LOG.info(
                'CrowdStrike disabled for AZ %s (site: %s), skipping', az, site
            )
            return {}

        deb_url = self._get_secret(f'CROWDSTRIKE_{site}_INSTALLER_URL_DEB')
        rpm_url = self._get_secret(f'CROWDSTRIKE_{site}_INSTALLER_URL_RPM')

        if not deb_url and not rpm_url:
            LOG.error(
                'No CrowdStrike installer URLs found in Vault for site %s, '
                'cannot generate configuration',
                site,
            )
            return {}

        fail_if_missing = _as_bool(
            self._get_secret(f'CROWDSTRIKE_{site}_FAIL_IF_MISSING'),
            default=False,
        )

        # Provide both package-type variants so the cloud-init module can pick
        # the right one for the guest OS family. installer_url is kept as a
        # generic fallback for backwards compatibility.
        config = {
            'cid': cid,
            'installer_url': deb_url or rpm_url,
            'enabled': True,
            'fail_if_missing': fail_if_missing,
        }
        if deb_url:
            config['installer_url_deb'] = deb_url
        if rpm_url:
            config['installer_url_rpm'] = rpm_url

        LOG.info(
            'Generated CrowdStrike config for instance %s in AZ %s',
            instance_id,
            az,
        )

        return config
