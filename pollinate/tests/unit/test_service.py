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

from pollinate.tests.unit import base
from pollinate.tests.unit import fakes


class TestService(base.TestCase):

    def test_service(self):
        with self.app.test_client() as client:
            response = client.post('/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_service_auth_fail(self):
        with self.app.test_client() as client:
            response = client.post('/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT))
            self.assertEqual(response.status_code, 401)

    def test_service_no_data(self):
        with self.app.test_client() as client:
            response = client.post('/',
                content_type='application/json',
                data=None,
                headers={'X-Identity-Status': 'Confirmed'})
            self.assertEqual(response.status_code, 400)

    def test_service_no_project_id(self):
        with self.app.test_client() as client:
            response = client.post('/',
                content_type='application/json',
                data=json.dumps({}),
                headers={'X-Identity-Status': 'Confirmed'})
            self.assertEqual(response.status_code, 400)
