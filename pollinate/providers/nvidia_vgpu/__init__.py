# Copyright 2022 Australian Research Data Commons
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

from flask import current_app
from oslo_log import log as logging

from pollinate import clients
from pollinate.providers import PollinateProvider


LOG = logging.getLogger(__name__)


class NvidiaVGPUProvider(PollinateProvider):
    name = 'nvidia_vgpu'

    def get_license(self, name):
        vault_key = f'LICENSE_TOKEN_{name.upper()}'
        value = current_app.secrets.get(vault_key)
        if not value:
            raise Exception(f'License value for {vault_key} not found!')
        return value

    def run(self, context):
        ks_session = current_app.ks_session
        keystone_client = clients.get_keystone_client(ks_session)

        project = keystone_client.projects.get(context['project-id'])

        # National ARDC license
        token = self.get_license('ardc')

        # Override with any local license servers, if applicable
        compute_zones = getattr(project, 'compute_zones', None)
        if compute_zones:
            zones = compute_zones.split(',')
            if any([z.startswith('monash') for z in zones]):
                token = self.get_license('monash')

        return {'license_token': token}
