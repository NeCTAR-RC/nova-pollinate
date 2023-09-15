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

from pkg_resources import iter_entry_points

from oslo_config import cfg
from oslo_log import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PollinateProviderException(Exception):
    pass


class PollinateProvider(object):

    @classmethod
    def load(cls):
        providers = []
        for entry_point in iter_entry_points(group='pollinate.providers'):
            if entry_point.name in CONF.providers:
                LOG.info('Loading provider: %s', entry_point.name)
                providers.append(entry_point.load())
        return providers

    def run(self):
        raise PollinateProviderException('Not Implemented')
