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
@mock.patch('pollinate.clients.get_cinder_client')
@mock.patch('pollinate.clients.get_glance_client')
@mock.patch('pollinate.clients.get_nova_client')
class TestWindowsProductKeyProvider(base.TestCase):

    def setUp(self):
        self.override_config('providers', 'windows_product_key')
        super(TestWindowsProductKeyProvider, self).setUp()

    def test_windows_product_key_fromimage(
            self, mock_nova_client, mock_glance_client, mock_cinder_client,
            mock_secrets_get):
        with self.app.test_client() as client:
            mock_secrets_get.return_value = 'foo'
            gc = mock_glance_client.return_value
            nc = mock_nova_client.return_value
            image = fakes.FakeImage()
            # Set our required trait
            image.set('trait:CUSTOM_NECTAR_WINDOWS', 'required')
            gc.images.get.return_value = image
            nc.servers.get.return_value = fakes.FakeInstance()

            logger = 'pollinate.providers.windows'
            level = 'INFO'
            with self.assertLogs(logger=logger, level=level) as cm:
                response = client.post('/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'})

            log_message = (f"{level}:{logger}:Instance fake-instance-id "
                "requested product key for FOO")
            self.assertEqual(cm.output, [log_message])

            resp_data = {'windows_product_key': {'product_key': 'foo'}}
            self.assertEqual(response.json, resp_data)
            self.assertEqual(response.status_code, 200)

    def test_windows_product_key_volume(
            self, mock_nova_client, mock_glance_client, mock_cinder_client,
            mock_secrets_get):
        with self.app.test_client() as client:
            mock_secrets_get.return_value = 'foo'
            cc = mock_cinder_client.return_value
            nc = mock_nova_client.return_value

            # Unset image id from context
            context = fakes.NOVA_VENDORDATA_CONTEXT
            context['image-id'] = ''  # No image

            # Set volume
            volume = fakes.FakeVolume()
            volume_image_metadata = {}
            volume_image_metadata['trait:CUSTOM_NECTAR_WINDOWS'] = 'required'
            volume.set('volume_image_metadata', volume_image_metadata)
            volume.set('bootable', True)
            cc.volumes.get.return_value = volume

            # Set up instance
            instance = fakes.FakeInstance()
            instance.set('os-extended-volumes:volumes_attached',
                         [{'id': 'dummy'}])
            nc.servers.get.return_value = instance

            logger = 'pollinate.providers.windows'
            level = 'INFO'
            with self.assertLogs(logger=logger, level=level) as cm:
                response = client.post('/',
                    content_type='application/json',
                    data=json.dumps(context),
                    headers={'X-Identity-Status': 'Confirmed'})

            log_message = (f"{level}:{logger}:Instance fake-instance-id "
                "requested product key for FOO")
            self.assertEqual(cm.output, [log_message])

            resp_data = {'windows_product_key': {'product_key': 'foo'}}
            self.assertEqual(response.json, resp_data)
            self.assertEqual(response.status_code, 200)

    def test_windows_product_key_not_found(
            self, mock_nova_client, mock_glance_client, mock_cinder_client,
            mock_secrets_get):
        with self.app.test_client() as client:
            mock_secrets_get.return_value = 'foo'
            gc = mock_glance_client.return_value
            nc = mock_nova_client.return_value
            # No trait set on image
            gc.images.get.return_value = fakes.FakeImage()
            nc.servers.get.return_value = fakes.FakeInstance()

            logger = 'pollinate.providers.windows'
            level = 'INFO'
            with self.assertLogs(logger=logger, level=level) as cm:
                response = client.post('/',
                    content_type='application/json',
                    data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                    headers={'X-Identity-Status': 'Confirmed'})

            log_message = (f"{level}:{logger}:Trait not found for instance "
                "fake-instance-id")
            self.assertEqual(cm.output, [log_message])

            resp_data = {}  # Empty
            self.assertEqual(response.json, resp_data)
            self.assertEqual(response.status_code, 200)
