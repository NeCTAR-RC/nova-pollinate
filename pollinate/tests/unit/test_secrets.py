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

from unittest import mock

from hvac import exceptions as hvac_exc

from pollinate import secrets
from pollinate.tests.unit import base


def _kv(data):
    return {'data': {'data': data}}


@mock.patch.object(secrets.PollinateSecrets, '_get_vault_client')
class TestSecrets(base.TestCase):
    def setUp(self):
        super().setUp()
        self.override_config('path', 'k8s/nova-pollinate/secrets', 'vault')
        self.secrets = secrets.PollinateSecrets()

    def _read(self, mock_client):
        return mock_client.return_value.secrets.kv.read_secret_version

    def test_get_default_path(self, mock_client):
        self._read(mock_client).return_value = _kv({'FOO': 'bar'})

        self.assertEqual(self.secrets.get('FOO'), 'bar')
        self._read(mock_client).assert_called_once_with(
            path='k8s/nova-pollinate/secrets', raise_on_deleted_version=True
        )

    def test_get_missing_key(self, mock_client):
        self._read(mock_client).return_value = _kv({})

        self.assertRaises(KeyError, self.secrets.get, 'FOO')

    def test_paths_cached_separately(self, mock_client):
        self._read(mock_client).side_effect = [
            _kv({'FOO': 'bar'}),
            _kv({'QRIScloud': 'key'}),
        ]

        self.assertEqual(self.secrets.get('FOO'), 'bar')
        self.assertEqual(
            self.secrets.get('QRIScloud', path='windows/2022'), 'key'
        )
        # Both served from cache
        self.assertEqual(self.secrets.get('FOO'), 'bar')
        self.assertEqual(
            self.secrets.get('QRIScloud', path='windows/2022'), 'key'
        )
        self.assertEqual(self._read(mock_client).call_count, 2)

    def test_missing_path(self, mock_client):
        self._read(mock_client).side_effect = hvac_exc.InvalidPath()

        self.assertRaises(
            KeyError, self.secrets.get, 'QRIScloud', path='windows/2025'
        )
