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

from importlib import metadata

from flask import current_app
from flask import g
from oslo_config import cfg
from oslo_log import log as logging

from pollinate import clients


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

PROVIDERS_GROUP = 'pollinate.providers'


class PollinateProviderException(Exception):
    pass


class PollinateProvider:
    @classmethod
    def load(cls):
        providers = []
        entry_points = metadata.entry_points(group=PROVIDERS_GROUP)
        LOG.debug('Found entrypoints: %s', entry_points)
        for entry_point in entry_points:
            if entry_point.name in CONF.providers:
                providers.append(entry_point.load())
        return providers

    def run(self):
        raise PollinateProviderException('Not Implemented')

    def get_instance(self, context):
        """Return the Nova server for this request, fetched once and shared.

        Several providers need the instance's server object. The lookup is
        memoised on the Flask request global so they don't each issue an
        identical ``servers.get()`` call. ``g`` is request-scoped, so the
        cached instance never leaks across requests.
        """
        if 'instance' not in g:
            nova_client = clients.get_nova_client(current_app.ks_session)
            g.instance = nova_client.servers.get(context['instance-id'])
        return g.instance
