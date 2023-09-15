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
import pprint

from flask import Flask

from oslo_config import cfg
from oslo_log import log as logging
from oslo_middleware import healthcheck
from oslo_middleware import request_id

from pollinate import config
from pollinate import keystone
from pollinate import providers
from pollinate import secrets
from pollinate import service


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def create_app(test_config=None, conf_file=None, init_config=True):
    # create and configure the app
    if init_config:
        if conf_file:
            config.init(conf_file=conf_file)
        else:
            config.init()
    app = Flask(__name__)
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=CONF.flask.secret_key,
        )
    else:
        app.config.update(test_config)

    # Enable debug logging set in Flask
    if app.config['DEBUG']:
        CONF.set_override('debug', True)

    # Setup logging
    config.setup_logging(CONF)
    LOG.debug("Configuration: %s", pprint.pformat(dict(CONF)))

    app.register_blueprint(service.bp)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.wsgi_app = healthcheck.Healthcheck(app.wsgi_app)
    app.wsgi_app = request_id.RequestId(app.wsgi_app)

    if CONF.auth_strategy == 'keystone':
        app.wsgi_app = keystone.KeystoneContext(app.wsgi_app)
        app.wsgi_app = keystone.SkippingAuthProtocol(app.wsgi_app, {})

    # Shared keystone session
    app.ks_session = keystone.KeystoneSession().get_session()

    # Vault login
    app.secrets = secrets.PollinateSecrets()

    # Load providers
    app.providers = providers.PollinateProvider.load()
    LOG.debug('Loaded providers: %s', app.providers)

    return app
