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

import copy
import operator
import socket

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


default_opts = [
    cfg.StrOpt('auth_strategy', default='keystone',
               choices=['noauth',
                        'keystone',
                        'testing'],
               help="The auth strategy for API requests."),
    cfg.StrOpt('host',
               default=socket.gethostname()),
    cfg.ListOpt('providers',
                default=[],
                help='Providers to load'),
]

flask_opts = [
    cfg.StrOpt('secret_key',
               help="Flask secret key",
               secret=True),
    cfg.StrOpt('host',
               help="The host or IP address to bind to",
               default='0.0.0.0'),
    cfg.IntOpt('port',
               help="The port to listen on",
               default=8612),
]

cfg.CONF.register_opts(flask_opts, group='flask')
cfg.CONF.register_opts(default_opts)

logging.register_options(cfg.CONF)

ks_loading.register_auth_conf_options(cfg.CONF, 'service_auth')
ks_loading.register_session_conf_options(cfg.CONF, 'service_auth')


def init(args=[]):
    cfg.CONF(args, project='pollinate')


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.

    :param conf: a cfg.ConfOpts object
    """
    product_name = "nova-pollinate"

    logging.setup(conf, product_name)
    LOG.info("Logging enabled!")


# Used by oslo-config-generator entry point
# https://docs.openstack.org/oslo.config/latest/cli/generator.html
def list_opts():
    return [
        ('DEFAULT', default_opts),
        ('flask', flask_opts),
        add_auth_opts(),
    ]


def add_auth_opts():
    opts = ks_loading.register_session_conf_options(cfg.CONF, 'service_auth')
    opt_list = copy.deepcopy(opts)
    opt_list.insert(0, ks_loading.get_auth_common_conf_options()[0])
    for plugin_option in ks_loading.get_auth_plugin_conf_options('password'):
        if all(option.name != plugin_option.name for option in opt_list):
            opt_list.append(plugin_option)
    opt_list.sort(key=operator.attrgetter('name'))
    return ('service_auth', opt_list)
