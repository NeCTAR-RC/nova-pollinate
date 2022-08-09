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

import os

from flask import current_app

from glanceclient import exc as glance_exc

from oslo_log import log as logging

from pollinate import clients
from pollinate.providers import PollinateProvider


LOG = logging.getLogger(__name__)


class NvidiaVGPUProvider(PollinateProvider):

    def __init__(self, context):
        super(NvidiaVGPUProvider, self).__init__(context)
        self.name = 'nvidia_vgpu'

    def get_license(self, name):
        license_token_name = 'LICENSE_TOKEN_{}'.format(name.upper())
        value = os.environ.get(license_token_name)
        if not value:
            raise Exception(
                'License value for {} not found!'.format(license_token_name))
        return value

    def run(self):
        ks_session = current_app.ks_session
        keystone_client = clients.get_keystone_client(ks_session)
        glance_client = clients.get_glance_client(ks_session)

        project = keystone_client.projects.get(self.context['project-id'])

        try:
            image = glance_client.images.get(self.context['image-id'])
        except glance_exc.HTTPNotFound:
            LOG.warning('Image %s not found' % self.context['image-id'])
            return

        # Require the nectar_vgpu property on the image to release
        # the license token
        if not image.get('nectar_vgpu'):
            LOG.warning('nectar_vgpu property not set on image %s (%s)',
                      image.id, image.name)
            return

        token = None
        compute_zones = getattr(project, 'compute_zones', None)
        if compute_zones:
            zones = compute_zones.split(',')
            if any([z.startswith('monash') for z in zones]):
                token = self.get_license('monash')
        else:
            # National ARDC license
            token = self.get_license('ardc')

        if token:
            return {'license_token': token}
