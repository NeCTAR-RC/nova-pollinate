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

import glanceclient.exc as glance_exc
from flask import current_app
from oslo_log import log as logging

from pollinate import clients
from pollinate.providers import PollinateProvider


LOG = logging.getLogger(__name__)


class WindowsProductKeyProvider(PollinateProvider):

    name = 'windows_product_key'

    def run(self, context):
        ks_session = current_app.ks_session
        nova_client = clients.get_nova_client(ks_session)
        glance_client = clients.get_glance_client(ks_session)

        try:
            image_id = context['image-id']
            image = glance_client.images.get(image_id)
        except glance_exc.HTTPNotFound:
            LOG.warning('Image %s not found', image_id)
            return

        # Require the nectar_windows property on the image to release
        # the product key
        if not image.get('nectar_windows'):
            LOG.warning('nectar_windows property not set on image %s (%s)',
                      image.id, image.name)
            return

        instance = nova_client.servers.get(context['instance-id'])
        # Use hypervisor name, but uppercase
        hostname = getattr(instance, 'OS-EXT-SRV-ATTR:host').upper()

        try:
            vault_key = 'WINDOWS_PRODUCT_KEY_{}'.format(hostname.upper())
            product_key = current_app.secrets.get(vault_key)
            return {'product_key': product_key}
        except KeyError:
            LOG.warning('Windows product key for %s not found!', hostname)
