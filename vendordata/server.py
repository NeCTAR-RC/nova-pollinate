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

import json

from webob.dec import wsgify
import webob.exc
from webob import Response

from oslo_config import cfg
from oslo_log import log as logging

from vendordata import keystone
from vendordata import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Application(object):

    def __init__(self):
        self.keystone_client = keystone.get_client()

    @wsgify
    def __call__(self, req):
        identity_status = req.environ.get('HTTP_X_IDENTITY_STATUS')
        if not identity_status:
            msg = ("Keystone middleware HTTP_X_IDENTITY_STATUS header "
                   "not found in request")
            return webob.exc.HTTPUnauthorized(msg)

        if identity_status != 'Confirmed':
            msg = 'User is not authenticated'
            LOG.warning(msg)
            raise webob.exc.HTTPUnauthorized()

        try:
            data = req.environ.get('wsgi.input').read()
            if not data:
                msg = 'No data provided'
                LOG.warning(msg)
                raise webob.exc.HTTPBadRequest(explanation=msg)

            context = json.loads(data)

            if 'project-id' not in context:
                msg = 'Project ID value not given'
                LOG.warning(msg)
                raise webob.exc.HTTPBadRequest(explanation=msg)

            result = {}

            for provider in utils.get_providers(
                    context, self.keystone_client):
                try:
                    result[provider.name] = provider.run()
                except Exception:
                    LOG.warning("Failed to run provider: %s", provider,
                                exc_info=True)

            result_json = json.dumps(result)
            resp = Response(status=200,
                            content_type='application/json',
                            body=result_json,
                            charset='UTF-8')
            utils.log_request(req, resp, data=context)
            return resp

        except webob.exc.WSGIHTTPException as e:
            raise e
        except Exception as e:
            LOG.warning(e, exc_info=True)
            raise webob.exc.HTTPInternalServerError(explanation=e)


def app_factory(global_config, **local_config):
    return Application()
