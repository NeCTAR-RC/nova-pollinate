# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

from vendordata import keystone_client

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Application(object):

    def __init__(self):
        self._keystone_client = None

    def _log(self, req, resp, data=None):
        log = []
        log.append(req.remote_addr or 'unknown')
        log.append('"{} {}{}"'.format(req.method.upper(),
                                      req.script_name,
                                      req.path_info))
        if resp:
            log.append('status: {}'.format(resp.status_code))

        if data:
            log.append('instance-id: {}'.format(data.get('instance-id')))
            log.append('project-id: {}'.format(data.get('project-id')))

        LOG.info(' '.join(log))

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

            indata = json.loads(data.decode('utf-8'))

            if 'project-id' not in indata:
                msg = 'Project ID value not given'
                LOG.warning(msg)
                raise webob.exc.HTTPBadRequest(explanation=msg)

            # Keystone
            project = keystone_client.get_project(indata['project-id'])
            if not project:
                msg = 'Project not found'
                LOG.warning(msg)
                raise webob.exc.HTTPNotFound(explanation=msg)

            result = {}

            result['project'] = {
                'project_id': project.id,
                'project_name': project.name,
            }

            # CloudStor config from Keystone
            creds = keystone_client.get_credentials(indata['project-id'])
            if creds:
                result['cloudstor'] = creds

            resp = Response(status=200,
                            content_type='application/json',
                            body=json.dumps(result),
                            charset='UTF-8')
            self._log(req, resp=resp, data=indata)
            return resp

        except webob.exc.WSGIHTTPException as e:
            raise e
        except Exception as e:
            LOG.warning(e)
            raise webob.exc.HTTPInternalServerError(explanation=e)


def app_factory(global_config, **local_config):
    return Application()
