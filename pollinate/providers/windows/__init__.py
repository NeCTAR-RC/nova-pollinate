# Copyright 2022 Australian Research Data Commons
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

import posixpath

from flask import current_app
import glanceclient.exc as glance_exc
from oslo_config import cfg
from oslo_log import log as logging

from pollinate import clients
from pollinate.providers import PollinateProvider


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

TRAIT = 'trait:CUSTOM_NECTAR_WINDOWS'


def _vault_path(os_version):
    # e.g. k8s/nova-pollinate/secrets -> k8s/nova-pollinate/windows/2022
    base = posixpath.dirname(CONF.vault.path)
    return posixpath.join(base, 'windows', os_version)


class WindowsProductKeyProvider(PollinateProvider):
    """Serve the Windows product key for the instance's zone and version.

    Keys live in Vault at windows/<os_version> alongside the [vault] path,
    one field per availability zone. Only images (or boot volumes) carrying the
    Windows trait are served; the trait also confines scheduling to
    licensed hosts.
    """

    name = 'windows_product_key'

    def _image_metadata(self, context, instance):
        """Return the boot image's properties, or None if not Windows."""
        image_id = context['image-id']
        if image_id:
            glance_client = clients.get_glance_client(current_app.ks_session)
            try:
                image = glance_client.images.get(image_id)
            except glance_exc.HTTPNotFound:
                LOG.warning('Image %s not found', image_id)
                return None
            if hasattr(image, TRAIT):
                return {'os_version': getattr(image, 'os_version', None)}
            return None

        cinder_client = clients.get_cinder_client(current_app.ks_session)
        for volume in getattr(
            instance, 'os-extended-volumes:volumes_attached'
        ):
            v = cinder_client.volumes.get(volume['id'])
            metadata = getattr(v, 'volume_image_metadata', None) or {}
            if v.bootable and TRAIT in metadata:
                return {'os_version': metadata.get('os_version')}
        return None

    def run(self, context):
        instance_id = context['instance-id']
        instance = self.get_instance(context)

        metadata = self._image_metadata(context, instance)
        if metadata is None:
            LOG.info('Trait not found for instance %s', instance_id)
            return

        os_version = metadata['os_version']
        # User-settable and used in a Vault path, so digits only
        if not str(os_version).isdigit():
            LOG.warning(
                'Instance %s has invalid or missing os_version %r',
                instance_id,
                os_version,
            )
            return

        zone = getattr(instance, 'OS-EXT-AZ:availability_zone')
        try:
            product_key = current_app.secrets.get(
                zone, path=_vault_path(os_version)
            )
        except KeyError:
            # Expected at sites that license Windows themselves
            LOG.info(
                'No Windows %s product key for zone %s (instance %s)',
                os_version,
                zone,
                instance_id,
            )
            return

        LOG.info(
            'Instance %s requested Windows %s product key for zone %s',
            instance_id,
            os_version,
            zone,
        )
        return {'product_key': product_key, 'os_version': os_version}
