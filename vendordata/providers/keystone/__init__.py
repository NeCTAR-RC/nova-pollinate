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

from vendordata.providers import VendorDataProvider


class KeystoneProvider(VendorDataProvider):

    def __init__(self, context, keystone_client):
        super(KeystoneProvider, self).__init__(context, keystone_client)
        self.name = 'keystone'

    def run(self):
        project = self.keystone_client.get_project(self.context['project-id'])
        resp = {'project_id': project.id,
                'project_name': project.name}
        return resp
