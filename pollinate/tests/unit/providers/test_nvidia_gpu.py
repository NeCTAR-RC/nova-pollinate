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
import os

from unittest import mock

from pollinate.tests.unit import base
from pollinate.tests.unit import fakes


@mock.patch('pollinate.clients.get_keystone_client')
class TestNvidiaGPUProvider(base.TestCase):

    def setUp(self):
        super(TestNvidiaGPUProvider, self).setUp()
        self.override_config(
            'providers', 'pollinate.providers.nvidia_vgpu.NvidiaVGPUProvider')

    @mock.patch.dict(os.environ, {'LICENSE_TOKEN_ARDC': 'foo'})
    def test_nvidia_gpu_token(self, mock_keystone_client):
        with self.app.test_client() as client:
            ks = mock_keystone_client.return_value
            ks.projects.get.return_value = fakes.FakeProject()

            response = client.post('/',
                content_type='application/json',
                data=json.dumps(fakes.PROJECT_DATA),
                headers={'X-Identity-Status': 'Confirmed'})

            resp_data = {'nvidia_vgpu': {'license_token': 'foo'}}
            self.assertEqual(response.json, resp_data)
            self.assertEqual(response.status_code, 200)

    def test_nvidia_gpu_token_not_found(self, mock_keystone_client):
        with self.app.test_client() as client:
            ks = mock_keystone_client.return_value
            ks.projects.get.return_value = fakes.FakeProject()

            response = client.post('/',
                content_type='application/json',
                data=json.dumps(fakes.PROJECT_DATA),
                headers={'X-Identity-Status': 'Confirmed'})

            # TODO(andy): Work out how to test for the thrown Exception
            # License value for LICENSE_TOKEN_ARDC not found!
            self.assertEqual(response.json, {})
            self.assertEqual(response.status_code, 200)

    @mock.patch.dict(os.environ, {'LICENSE_TOKEN_ARDC': 'foo'})
    @mock.patch.dict(os.environ, {'LICENSE_TOKEN_MONASH': 'baz'})
    def test_nvidia_gpu_token_monash(self, mock_keystone_client):
        with self.app.test_client() as client:
            ks = mock_keystone_client.return_value
            ks.projects.get.return_value = fakes.FakeProject(
                compute_zones='monash-02')
            response = client.post('/',
                content_type='application/json',
                data=json.dumps(fakes.PROJECT_DATA),
                headers={'X-Identity-Status': 'Confirmed'})

            resp_data = {'nvidia_vgpu': {'license_token': 'baz'}}
            self.assertEqual(response.json, resp_data)
            self.assertEqual(response.status_code, 200)
