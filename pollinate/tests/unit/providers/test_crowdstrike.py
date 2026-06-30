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

import json

from unittest import mock

from pollinate import secrets
from pollinate.tests.unit import base
from pollinate.tests.unit import fakes


@mock.patch.object(secrets.PollinateSecrets, 'get')
@mock.patch('pollinate.clients.get_nova_client')
class TestCrowdStrikeProvider(base.TestCase):
    def setUp(self):
        self.override_config('providers', 'crowdstrike')
        super().setUp()

    def _set_az(self, mock_nova_client, az):
        """Make the mocked Nova client return an instance in the given AZ."""
        nc = mock_nova_client.return_value
        nc.servers.get.return_value = fakes.FakeInstance(availability_zone=az)

    def test_crowdstrike_with_az_specific_cid(
        self, mock_nova_client, mock_secrets_get
    ):
        """AZ-specific CID and both installer URLs present in Vault."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'melbourne-qh2')

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MELBOURNE-QH2_CID': 'MELBOURNE-CID-123',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_RPM': 'https://example.com/falcon.rpm',
                }
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

            self.assertEqual(response.status_code, 200)
            resp_data = {
                'crowdstrike': {
                    'cid': 'MELBOURNE-CID-123',
                    'installer_url': 'https://example.com/falcon.deb',
                    'installer_url_deb': 'https://example.com/falcon.deb',
                    'installer_url_rpm': 'https://example.com/falcon.rpm',
                    'enabled': True,
                    'fail_if_missing': False,
                }
            }
            self.assertEqual(response.json, resp_data)

    def test_crowdstrike_with_provisioning_token_and_tags(
        self, mock_nova_client, mock_secrets_get
    ):
        """Optional provisioning token and tags are passed through."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'melbourne-qh2')

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MELBOURNE-QH2_CID': 'MELBOURNE-CID-123',
                    'CROWDSTRIKE_MELBOURNE-QH2_PROVISIONING_TOKEN': 'TOKEN-789',
                    'CROWDSTRIKE_MELBOURNE-QH2_TAGS': 'nectar,melbourne',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                }
                if key not in vault_secrets:
                    raise KeyError('Not found')
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

            self.assertEqual(response.status_code, 200)
            cs_data = response.json['crowdstrike']
            self.assertEqual(cs_data['provisioning_token'], 'TOKEN-789')
            self.assertEqual(cs_data['tags'], 'nectar,melbourne')

    def test_crowdstrike_token_and_tags_omitted_when_absent(
        self, mock_nova_client, mock_secrets_get
    ):
        """No provisioning token or tags keys: omit them from the config."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'melbourne-qh2')

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MELBOURNE-QH2_CID': 'MELBOURNE-CID-123',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                }
                if key not in vault_secrets:
                    raise KeyError('Not found')
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

            self.assertEqual(response.status_code, 200)
            cs_data = response.json['crowdstrike']
            self.assertNotIn('provisioning_token', cs_data)
            self.assertNotIn('tags', cs_data)

    def test_crowdstrike_no_config_for_az(
        self, mock_nova_client, mock_secrets_get
    ):
        """AZ has no Vault config: silent skip."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'tasmania')
            mock_secrets_get.side_effect = KeyError('Not found')

            logger = 'pollinate.providers.crowdstrike'
            with self.assertLogs(logger=logger, level='INFO') as cm:
                response = client.post(
                    '/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'},
                )

            self.assertIn(
                'No CrowdStrike CID found for AZ tasmania (site: TASMANIA)',
                cm.output[0],
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_crowdstrike_no_availability_zone(
        self, mock_nova_client, mock_secrets_get
    ):
        """Instance has no availability zone: skip with a warning."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, '')

            logger = 'pollinate.providers.crowdstrike'
            with self.assertLogs(logger=logger, level='WARNING') as cm:
                response = client.post(
                    '/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'},
                )

            self.assertIn('No availability zone for instance', cm.output[0])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_crowdstrike_per_az_opt_out(
        self, mock_nova_client, mock_secrets_get
    ):
        """ENABLED set false for the AZ: skip entirely, inject nothing."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'melbourne-qh2')

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MELBOURNE-QH2_CID': 'MELBOURNE-CID-123',
                    'CROWDSTRIKE_MELBOURNE-QH2_ENABLED': 'false',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                }
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            logger = 'pollinate.providers.crowdstrike'
            with self.assertLogs(logger=logger, level='INFO') as cm:
                response = client.post(
                    '/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'},
                )

            self.assertIn(
                'CrowdStrike disabled for AZ melbourne-qh2', cm.output[0]
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_crowdstrike_no_installer_urls(
        self, mock_nova_client, mock_secrets_get
    ):
        """CID present but no installer URLs: error and skip."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'melbourne-qh2')

            def vault_get(key):
                if key == 'CROWDSTRIKE_MELBOURNE-QH2_CID':
                    return 'MELBOURNE-CID-123'
                raise KeyError('Not found')

            mock_secrets_get.side_effect = vault_get

            logger = 'pollinate.providers.crowdstrike'
            with self.assertLogs(logger=logger, level='ERROR') as cm:
                response = client.post(
                    '/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'},
                )

            self.assertIn(
                'No CrowdStrike installer URLs found in Vault', cm.output[0]
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_crowdstrike_only_rpm_url(
        self, mock_nova_client, mock_secrets_get
    ):
        """Only an RPM URL is present: use it as the generic installer_url."""
        with self.app.test_client() as client:
            self._set_az(mock_nova_client, 'monash-01')

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MONASH-01_CID': 'MONASH-CID-456',
                    'CROWDSTRIKE_MONASH-01_INSTALLER_URL_RPM': 'https://example.com/falcon.rpm',
                }
                if key not in vault_secrets:
                    raise KeyError('Not found')
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

            self.assertEqual(response.status_code, 200)
            cs_data = response.json['crowdstrike']
            self.assertEqual(cs_data['cid'], 'MONASH-CID-456')
            self.assertEqual(
                cs_data['installer_url'], 'https://example.com/falcon.rpm'
            )
            self.assertEqual(
                cs_data['installer_url_rpm'], 'https://example.com/falcon.rpm'
            )
            self.assertNotIn('installer_url_deb', cs_data)

    def test_crowdstrike_az_normalization(
        self, mock_nova_client, mock_secrets_get
    ):
        """AZ names normalise to per-AZ Vault keys."""
        with self.app.test_client() as client:

            def vault_get(key):
                vault_secrets = {
                    'CROWDSTRIKE_MONASH-01_CID': 'MONASH-01-CID',
                    'CROWDSTRIKE_MONASH-01_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                    'CROWDSTRIKE_MONASH-02_CID': 'MONASH-02-CID',
                    'CROWDSTRIKE_MONASH-02_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                    'CROWDSTRIKE_MELBOURNE-QH2_CID': 'MELBOURNE-QH2-CID',
                    'CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                    'CROWDSTRIKE_MELBOURNE-QH2-UOM_CID': 'MELBOURNE-UOM-CID',
                    'CROWDSTRIKE_MELBOURNE-QH2-UOM_INSTALLER_URL_DEB': 'https://example.com/falcon.deb',
                }
                return vault_secrets[key]

            mock_secrets_get.side_effect = vault_get

            test_cases = [
                ('monash-01', 'MONASH-01-CID'),
                ('monash-02', 'MONASH-02-CID'),
                ('melbourne-qh2', 'MELBOURNE-QH2-CID'),
                ('melbourne-qh2-uom', 'MELBOURNE-UOM-CID'),
            ]

            for az_name, expected_cid in test_cases:
                self._set_az(mock_nova_client, az_name)
                response = client.post(
                    '/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'},
                )

                self.assertEqual(
                    response.status_code, 200, f'Failed for AZ: {az_name}'
                )
                cs_data = response.json['crowdstrike']
                self.assertEqual(
                    cs_data['cid'],
                    expected_cid,
                    f'Wrong CID for AZ: {az_name}',
                )
