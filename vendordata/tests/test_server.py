# Copyright 2018 Australian Research Data Commons
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

import mock
import os
import webtest

from keystoneauth1 import fixture as ksa_fixture
from keystonemiddleware import auth_token
from keystonemiddleware import fixture as ksm_fixture

from paste.deploy import loadapp

import webob.exc

from vendordata import test
from vendordata import keystone_client  # noqa
from vendordata.tests import fakes


class TestServer(test.TestCase):

    @staticmethod
    def create_token():
        """Create a fake token that will be used in testing"""

        # Creates a project scoped V3 token, with 1 entry in the catalog
        token = ksa_fixture.V3Token()
        token.set_project_scope()

        s = token.add_service('identity')
        s.add_standard_endpoints(
            public='http://example.com/identity/public',
            admin='http://example.com/identity/admin',
            internal='http://example.com/identity/internal',
            region='RegionOne')

        return token

    def load_app(self, cloudstor_creds=None):
        with mock.patch('vendordata.keystone_client') as mock_keystone:
            # default fake project and creds
            mock_keystone.get_credentials.return_value = cloudstor_creds

            # create our app. webtest gives us a callable interface to it
            name = 'vendordata'
            test_dir = os.path.dirname(__file__)
            app = loadapp('config:test.ini#%s' % name, relative_to=test_dir)

            # load your wsgi app here, wrapped in auth_token middleware
            service = auth_token.AuthProtocol(app, {})
            return webtest.TestApp(service)

    def setUp(self):
        super(TestServer, self).setUp()

        # stub out auth_token middleware
        self.auth_token_fixture = self.useFixture(
            ksm_fixture.AuthTokenFixture())

        # create a token, mock it and save it and the ID for later use
        self.token = self.create_token()
        self.token_id = self.auth_token_fixture.add_token(self.token)

    def test_server_with_creds(self):
        creds = fakes.CLOUDSTOR_CREDS

        app = self.load_app(cloudstor_creds=creds)
        response = app.post_json('/', fakes.METADATA,
                                 headers={'X-Auth-Token': self.token_id},
                                 expect_errors=True)

        expected = {
            'cloudstor': {
                'password': creds.get('password'),
                'username': creds.get('username'),
            },
        }
        self.assertEqual(expected, response.json)
        self.assertEqual(webob.exc.HTTPOk.code, response.status_int)

    def test_server_no_creds(self):
        creds = None

        app = self.load_app(cloudstor_creds=creds)
        response = app.post_json('/', fakes.METADATA,
                                 headers={'X-Auth-Token': self.token_id})

        expected = {}
        self.assertEqual(expected, response.json)
        self.assertEqual(webob.exc.HTTPOk.code, response.status_int)

    def test_server_bad_auth(self):
        creds = fakes.CLOUDSTOR_CREDS

        app = self.load_app(cloudstor_creds=creds)
        response = app.post_json('/', fakes.METADATA,
                                 headers={'X-Auth-Token': 'bad'},
                                 expect_errors=True)
        self.assertEqual(webob.exc.HTTPUnauthorized.code, response.status_int)

    def test_server_project_not_given(self):
        creds = None

        metadata = dict(fakes.METADATA)
        del metadata['project-id']

        app = self.load_app(cloudstor_creds=creds)
        response = app.post_json('/', metadata,
                                 headers={'X-Auth-Token': self.token_id},
                                 expect_errors=True)
        expected = 'Project ID value not given'
        self.assertTrue(expected in response)
        self.assertEqual(webob.exc.HTTPBadRequest.code, response.status_int)
