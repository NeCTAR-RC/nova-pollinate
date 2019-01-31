# Copyright 2016 Red Hat, Inc.
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

import itertools
import os

from oslo_config import cfg
from oslo_log import log

from six import moves


service_opts = [
    cfg.StrOpt('listen',
               default='0.0.0.0',
               help='IP address to listen on'),
    cfg.PortOpt('port',
                default=8912,
                help='Port to listen on'),
]


def _search_dirs(dirs, basename, extension=""):
    """Search a list of directories for a given filename.

    Iterator over the supplied directories, returning the first file
    found with the supplied name and extension.

    :param dirs: a list of directories
    :param basename: the filename, for example 'glance-api'
    :param extension: the file extension, for example '.conf'
    :returns: the path to a matching file, or None
    """
    for d in dirs:
        path = os.path.join(d, '%s%s' % (basename, extension))
        if os.path.exists(path):
            return path


def find_config_files():
    cfg_dirs = ['/etc/vendordata/']
    config_files = []
    extension = '.conf'
    config_files.append(_search_dirs(cfg_dirs, 'vendordata', extension))
    return list(moves.filter(bool, config_files))


CONF = cfg.CONF
CONF.register_opts(service_opts)
log.register_options(CONF)


def list_opts():
    return [
        ('DEFAULT',
            itertools.chain(
                service_opts,
            )),
    ]
