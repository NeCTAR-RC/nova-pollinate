# Copyright 2018 ARDC
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
import mock

# This represents what Nova would pass to us in a real request
METADATA = {
    'hostname': 'foo',
    'image-id': '75a74383-f276-4774-8074-8c4e3ff2ca64',
    'instance-id': '2ae914e9-f5ab-44ce-b2a2-dcf8373d899d',
    'metadata': {},
    'project-id': '039d104b7a5c4631b4ba6524d0b9e981',
    'user-data': ''
}

FAKE_CREDS = {'username': 'hello',
              'password': 'world'}


class FakeProvider1(object):
    def __init__(self, context, keystone_client):
        self.name = 'fake_provider1'

    def run(self):
        return {'foo': 'bar'}


class FakeProvider2(object):
    def __init__(self, context, keystone_client):
        self.name = 'fake_provider2'

    def run(self):
        return {'username': 'hello',
                'password': 'world'}


FAKE_PROVIDERS = [FakeProvider1(METADATA, mock.Mock()),
                  FakeProvider2(METADATA, mock.Mock())]


class FakeProject(object):

    def __init__(self, project_id='039d104b7a5c4631b4ba6524d0b9e981',
                 name='MyProject', **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = project_id
        self.name = name

    def to_dict(self):
        return self.__dict__


class FakeCredential(object):

    def __init__(self, cred_type='cloudstor', blob=FAKE_CREDS,
                 project_id='039d104b7a5c4631b4ba6524d0b9e981',
                 user_id='1108df6dd8644030a701dd192e06cd4f'):
        self.type = cred_type
        self.project_id = project_id
        self.user_id = user_id
        self.blob = json.dumps(blob)

    def to_dict(self):
        return self.__dict__
