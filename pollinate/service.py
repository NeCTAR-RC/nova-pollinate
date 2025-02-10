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

import yaml

from flask import abort
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from hvac import exceptions as vault_exc
from oslo_log import log as logging
from werkzeug.exceptions import HTTPException


LOG = logging.getLogger(__name__)

bp = Blueprint('service', __name__)


@bp.route('/', methods=['POST'])
def pollinate():
    identity_status = request.headers.get('X-Identity-Status')
    if not identity_status:
        msg = (
            'X-Identity-Status header not found in request. '
            'Is Keystone auth middleware configured?'
        )
        LOG.error(msg)
        abort(401, msg)
    if identity_status != 'Confirmed':
        msg = 'Nova vendordata_dynamic_auth user is not authenticated'
        LOG.error(msg)
        abort(401, msg)

    try:
        if not request.data:
            msg = 'No input data provided by Nova'
            LOG.warning(msg)
            abort(400, msg)

        context = request.json
        LOG.debug(f'Nova input data: {context}')

        if 'project-id' not in context:
            msg = 'Project ID value not provided by Nova'
            LOG.warning(msg)
            abort(400, msg)

        result = {}
        cloud_config = {}

        # Cycle through our providers
        providers = current_app.providers
        LOG.debug(f'Running with providers: {providers}')
        for provider in providers:
            try:
                # Run the provider
                LOG.debug(f'Running provider: {provider.name}')
                output = provider().run(context)
                LOG.debug(f'Provider {provider.name} output: {output}')
                if output:
                    # Strip out any cloud-init config for processing later
                    if 'cloud-config' in output:
                        cc = output.pop('cloud-config')
                        cloud_config.update(cc)
                    # Prefix data with provider name
                    result.update({provider.name: output})
            except Exception:
                LOG.warning(
                    "Failed to run provider: %s", provider.name, exc_info=True
                )

        # cloud-init config needs to a valid cloud-init YAML document
        # under the key 'cloud-init'. For details, see the the docs at:
        # https://cloudinit.readthedocs.io/en/stable/topics/datasources/openstack.html
        if cloud_config:
            cloud_yaml = yaml.dump(cloud_config)
            result['cloud-init'] = '#cloud-config\n' + cloud_yaml

        return jsonify(result)

    except HTTPException:
        # Simply return any raised aborts
        raise

    except Exception as e:
        # Catch any other exceptions
        LOG.warning(e, exc_info=True)
        abort(500, e)


@bp.route('/test', methods=['GET'])
def test():
    result = {'Error': 'Unknown error'}
    try:
        current_app.secrets.get_secrets()
        result = {'OK': 'Success'}
        return jsonify(result)
    except vault_exc.Forbidden as e:
        LOG.error('Vault error: %s', e)
        result = {'Error': 'Failed to get secrets'}
    except Exception as e:
        LOG.exception(e)
    return jsonify(result), 500
