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

from vendordata import test
from vendordata.tests import fakes

from vendordata.providers.keystone import KeystoneProvider


class TestKeystoneProvider(test.TestCase):

    def test_keystone_name(self):
        provider = KeystoneProvider(fakes.METADATA, mock.Mock())
        self.assertEqual(provider.name, 'keystone')

    def test_keystone_project_details(self):
        provider = KeystoneProvider(fakes.METADATA, mock.Mock())
        with mock.patch.object(provider, 'keystone_client') as mock_kclient:
            project = fakes.FakeProject()
            mock_kclient.get_project.return_value = project
            output = provider.run()
            expected = {'project_id': project.id,
                        'project_name': project.name}
            self.assertEqual(expected, output)
