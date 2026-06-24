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


class TestService(base.TestCase):
    def test_service(self):
        with self.app.test_client() as client:
            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {})

    def test_service_auth_fail(self):
        with self.app.test_client() as client:
            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
            )
            self.assertEqual(response.status_code, 401)

    def test_service_no_data(self):
        with self.app.test_client() as client:
            response = client.post(
                '/',
                content_type='application/json',
                data=None,
                headers={'X-Identity-Status': 'Confirmed'},
            )
            self.assertEqual(response.status_code, 400)

    def test_service_no_project_id(self):
        with self.app.test_client() as client:
            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps({}),
                headers={'X-Identity-Status': 'Confirmed'},
            )
            self.assertEqual(response.status_code, 400)

    def test_healthcheck(self):
        # /healthcheck is served by oslo.middleware.healthcheck mounted via
        # werkzeug's dispatcher. A 200 is all the liveness probe needs; the
        # body is not asserted as the middleware does not populate it under
        # Werkzeug 3.
        with self.app.test_client() as client:
            response = client.get('/healthcheck')
            self.assertEqual(response.status_code, 200)

    @mock.patch.object(secrets.PollinateSecrets, 'get')
    @mock.patch('pollinate.clients.get_glance_client')
    @mock.patch('pollinate.clients.get_nova_client')
    def test_instance_fetched_once_across_providers(
        self, mock_nova_client, mock_glance_client, mock_secrets_get
    ):
        """The Nova instance is fetched once and shared between providers."""
        # Enable two providers that both need the server object.
        self.override_config(
            'providers', ['crowdstrike', 'windows_product_key']
        )
        app = self.create_app()

        nc = mock_nova_client.return_value
        nc.servers.get.return_value = fakes.FakeInstance(
            availability_zone='melbourne-qh2'
        )
        # Make both providers skip cheaply; we only care about the Nova call.
        mock_secrets_get.side_effect = KeyError('not found')

        with app.test_client() as client:
            response = client.post(
                '/',
                content_type='application/json',
                data=json.dumps(fakes.NOVA_VENDORDATA_CONTEXT),
                headers={'X-Identity-Status': 'Confirmed'},
            )

        self.assertEqual(response.status_code, 200)
        # Both providers ran, but the server was only fetched once.
        nc.servers.get.assert_called_once_with('fake-instance-id')
