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

import sys

from oslo_log import log as logging

from paste.deploy import loadapp
from paste import httpserver
from paste.translogger import TransLogger

from vendordata import config
from vendordata import keystone_client

CONF = config.CONF

LOG = logging.getLogger(__name__)


def main():
    keystone_client.register_keystoneauth_opts(CONF)

    CONF(sys.argv[1:],
         default_config_files=config.find_config_files())

    logging.setup(CONF, 'vendordata')

    LOG.debug("Configuration:")
    CONF.log_opt_values(LOG, logging.DEBUG)

    # Start the web server
    app = loadapp('config:api-paste.ini', relative_to='/etc/vendordata')
    log_app = TransLogger(app)
    httpserver.serve(log_app, host=CONF.listen, port=CONF.port,
                     use_threadpool=True)


if __name__ == '__main__':
    main()
