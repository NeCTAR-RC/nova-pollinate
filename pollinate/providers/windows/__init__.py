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
import glanceclient.exc as glance_exc
from oslo_log import log as logging

from pollinate import clients
from pollinate.providers import PollinateProvider


LOG = logging.getLogger(__name__)

TRAIT = 'trait:CUSTOM_NECTAR_WINDOWS'


class WindowsProductKeyProvider(PollinateProvider):
    name = 'windows_product_key'

    def run(self, context):
        ks_session = current_app.ks_session
        nova_client = clients.get_nova_client(ks_session)
        glance_client = clients.get_glance_client(ks_session)
        cinder_client = clients.get_cinder_client(ks_session)

        instance_id = context['instance-id']
        image_id = context['image-id']

        instance = nova_client.servers.get(instance_id)
        has_trait = False

        # Require the Windows trait on the image or volume to release the
        # product key
        if image_id:
            try:
                image = glance_client.images.get(image_id)
                if hasattr(image, TRAIT):
                    has_trait = True
            except glance_exc.HTTPNotFound:
                LOG.warning('Image %s not found', image_id)
                return
        else:
            volumes_attached = getattr(
                instance, 'os-extended-volumes:volumes_attached'
            )
            for volume in volumes_attached:
                v = cinder_client.volumes.get(volume['id'])
                if v.bootable and TRAIT in v.volume_image_metadata:
                    has_trait = True
                    break

        if not has_trait:
            LOG.info('Trait not found for instance %s', instance_id)
            return

        # Use hypervisor name, but uppercase
        hostname = getattr(instance, 'OS-EXT-SRV-ATTR:host').upper()

        try:
            vault_key = f'WINDOWS_PRODUCT_KEY_{hostname.upper()}'
            product_key = current_app.secrets.get(vault_key)
            LOG.info(
                'Instance %s requested product key for %s',
                context['instance-id'],
                hostname,
            )
            return {'product_key': product_key}
        except KeyError:
            LOG.warning('Windows product key for %s not found!', hostname)
