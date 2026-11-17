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

import copy
import json

from unittest import mock

from pollinate import secrets
from pollinate.tests.unit import base
from pollinate.tests.unit import fakes


LOGGER = 'pollinate.providers.windows'
TRAIT = 'trait:CUSTOM_NECTAR_WINDOWS'


@mock.patch.object(secrets.PollinateSecrets, 'get')
@mock.patch('pollinate.clients.get_cinder_client')
@mock.patch('pollinate.clients.get_glance_client')
@mock.patch('pollinate.clients.get_nova_client')
class TestWindowsProductKeyProvider(base.TestCase):
    def setUp(self):
        self.override_config('providers', 'windows_product_key')
        self.override_config('path', 'k8s/nova-pollinate/secrets', 'vault')
        super().setUp()

    def _post(self, context=None):
        with self.app.test_client() as client:
            return client.post(
                '/',
                content_type='application/json',
                data=json.dumps(context or fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

    def _windows_image(self, **props):
        image = fakes.FakeImage()
        image.set(TRAIT, 'required')
        for k, v in props.items():
            image.set(k, v)
        return image

    def test_from_image(self, mock_nova, mock_glance, mock_cinder, mock_get):
        mock_get.return_value = 'foo'
        mock_glance.return_value.images.get.return_value = self._windows_image(
            os_version='2025'
        )
        mock_nova.return_value.servers.get.return_value = fakes.FakeInstance(
            availability_zone='ardc-syd-1'
        )

        with self.assertLogs(logger=LOGGER, level='INFO') as cm:
            response = self._post()

        mock_get.assert_called_once_with(
            'ardc-syd-1', path='k8s/nova-pollinate/windows/2025'
        )
        self.assertEqual(
            cm.output,
            [
                f'INFO:{LOGGER}:Instance fake-instance-id requested '
                'Windows 2025 product key for zone ardc-syd-1'
            ],
        )
        self.assertEqual(
            response.json,
            {
                'windows_product_key': {
                    'product_key': 'foo',
                    'os_version': '2025',
                }
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_from_volume(self, mock_nova, mock_glance, mock_cinder, mock_get):
        mock_get.return_value = 'foo'
        context = copy.deepcopy(fakes.NOVA_VENDORDATA_CONTEXT)
        context['image-id'] = ''  # Boot from volume

        volume = fakes.FakeVolume()
        volume.set('bootable', True)
        volume.set(
            'volume_image_metadata', {TRAIT: 'required', 'os_version': '2022'}
        )
        mock_cinder.return_value.volumes.get.return_value = volume

        instance = fakes.FakeInstance(availability_zone='QRIScloud')
        instance.set('os-extended-volumes:volumes_attached', [{'id': 'v'}])
        mock_nova.return_value.servers.get.return_value = instance

        response = self._post(context)

        mock_get.assert_called_once_with(
            'QRIScloud', path='k8s/nova-pollinate/windows/2022'
        )
        self.assertEqual(
            response.json,
            {
                'windows_product_key': {
                    'product_key': 'foo',
                    'os_version': '2022',
                }
            },
        )

    def test_no_trait(self, mock_nova, mock_glance, mock_cinder, mock_get):
        mock_glance.return_value.images.get.return_value = fakes.FakeImage()
        mock_nova.return_value.servers.get.return_value = fakes.FakeInstance()

        with self.assertLogs(logger=LOGGER, level='INFO') as cm:
            response = self._post()

        self.assertEqual(
            cm.output,
            [f'INFO:{LOGGER}:Trait not found for instance fake-instance-id'],
        )
        mock_get.assert_not_called()
        self.assertEqual(response.json, {})

    def test_missing_os_version(
        self, mock_nova, mock_glance, mock_cinder, mock_get
    ):
        mock_glance.return_value.images.get.return_value = (
            self._windows_image()
        )
        mock_nova.return_value.servers.get.return_value = fakes.FakeInstance()

        with self.assertLogs(logger=LOGGER, level='WARNING'):
            response = self._post()

        mock_get.assert_not_called()
        self.assertEqual(response.json, {})

    def test_invalid_os_version(
        self, mock_nova, mock_glance, mock_cinder, mock_get
    ):
        mock_glance.return_value.images.get.return_value = self._windows_image(
            os_version='../secrets'
        )
        mock_nova.return_value.servers.get.return_value = fakes.FakeInstance()

        with self.assertLogs(logger=LOGGER, level='WARNING'):
            response = self._post()

        mock_get.assert_not_called()
        self.assertEqual(response.json, {})

    def test_no_key_for_zone(
        self, mock_nova, mock_glance, mock_cinder, mock_get
    ):
        mock_get.side_effect = KeyError('monash-01')
        mock_glance.return_value.images.get.return_value = self._windows_image(
            os_version='2022'
        )
        mock_nova.return_value.servers.get.return_value = fakes.FakeInstance(
            availability_zone='monash-01'
        )

        with self.assertLogs(logger=LOGGER, level='INFO') as cm:
            response = self._post()

        self.assertEqual(
            cm.output,
            [
                f'INFO:{LOGGER}:No Windows 2022 product key for zone '
                'monash-01 (instance fake-instance-id)'
            ],
        )
        self.assertEqual(response.json, {})
        self.assertEqual(response.status_code, 200)
