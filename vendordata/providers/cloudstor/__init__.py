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

import json

from vendordata.providers import VendorDataProvider


class CloudStorProvider(VendorDataProvider):

    def __init__(self, context, keystone_client):
        super(CloudStorProvider, self).__init__(context, keystone_client)
        self.name = 'cloudstor'

    def run(self):
        """Return first set of CloudStor credentials found
        
        Cloudstor credentials are stored as keystone credential blobs under
        the admin user, but we do set the project ID to be for the actual
        user and we set the type to be 'cloudstor'. Unfortunately we can't
        filter by project ID via the API so we do this in Python here.
        """
        creds = self.keystone_client.credentials.list(type='cloudstor')
        try:
            data = next(c.blob for c in creds
                        if c.project_id == self.context['project-id'])
            return json.loads(data)
        except StopIteration:
            pass  # no creds found
