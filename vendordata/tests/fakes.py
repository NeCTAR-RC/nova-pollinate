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

METADATA = {
    'hostname': 'foo',
    'image-id': '75a74383-f276-4774-8074-8c4e3ff2ca64',
    'instance-id': '2ae914e9-f5ab-44ce-b2a2-dcf8373d899d',
    'metadata': {},
    'project-id': '039d104b7a5c4631b4ba6524d0b9e981',
    'user-data': ''
}

CLOUDSTOR_CREDS = {
    'username': 'foo',
    'password': 'bar',
}


class FakeProject(object):

    def __init__(self, project_id='dummy', name='MyProject',
                 domain_id='default', enabled=True, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = project_id
        self.name = name
        self.domain_id = domain_id
        self.enabled = True

    def to_dict(self):
        return self.__dict__
