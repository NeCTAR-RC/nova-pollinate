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

import copy


NOVA_VENDORDATA_CONTEXT = {
    'project-id': 'fake-project-id',
    'instance-id': 'fake-instance-id',
    'image-id': 'fake-image-id',
    'user-data': 'user-data',
    'hostname': 'fake-hostname',
    'metadata': 'fake-metadata',
}


class FakeProject:
    def __init__(self, id='dummy', name='MyProject', enabled=True, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = id
        self.name = name
        self.enabled = enabled

    def to_dict(self):
        return copy.copy(self.__dict__)


class FakeImage:
    def __init__(self, id='dummy', name='MyImage', enabled=True, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = id
        self.name = name
        self.enabled = enabled

    def set(self, k, v):
        setattr(self, k, v)

    def to_dict(self):
        return copy.copy(self.__dict__)


class FakeVolume:
    def __init__(self, id='dummy', name='MyVolume', enabled=True, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = id
        self.name = name
        self.enabled = enabled

    def set(self, k, v):
        setattr(self, k, v)

    def to_dict(self):
        return copy.copy(self.__dict__)


class FakeInstance:
    def __init__(
        self,
        id='dummy',
        name='MyServer',
        host='foo',
        hypervisor_hostname='foo.bar.baz',
        **kwargs,
    ):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = id
        self.name = name
        setattr(self, 'OS-EXT-SRV-ATTR:host', host)
        setattr(
            self, 'OS-EXT-SRV-ATTR:hypervisor_hostname', hypervisor_hostname
        )

    def set(self, k, v):
        setattr(self, k, v)

    def to_dict(self):
        return copy.copy(self.__dict__)
