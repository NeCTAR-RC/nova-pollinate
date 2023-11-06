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

from cinderclient import client as cinder_client
from glanceclient import client as glance_client
from keystoneclient.v3 import client as ks_client
from novaclient import client as nova_client

from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def get_keystone_client(session):
    return ks_client.Client(session=session)


def get_glance_client(session):
    return glance_client.Client('2', session=session)


def get_nova_client(session):
    return nova_client.Client('2', session=session)


def get_cinder_client(session):
    return cinder_client.Client('3', session=session)
