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

from importlib import import_module

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def log_request(req, resp, data=None):
    """Log a web request and response"""
    log = []
    log.append(req.remote_addr or 'unknown')
    log.append(f'"{req.method.upper()} {req.script_name}{req.path_info}"')
    if resp:
        log.append(f'status: {resp.status_code}')

    if data:
        log.append('instance-id: {}'.format(data.get('instance-id')))
        log.append('project-id: {}'.format(data.get('project-id')))

    LOG.info(' '.join(log))


def load_provider(name):
    """Load provider from a given name"""
    try:
        LOG.debug('Loading provider %s', name)
        module_path, _, class_name = name.rpartition('.')
        mod = import_module(module_path)
        provider = getattr(mod, class_name)
        return provider
    except Exception:
        LOG.warning('Cannot load provider: %s', name, exc_info=True)


def get_providers(context):
    providers = []
    for p in CONF.providers:
        try:
            provider = load_provider(p)(context)
            providers.append(provider)
        except Exception:
            LOG.warning('Cannot load provider: %s', p, exc_info=True)

    return providers
