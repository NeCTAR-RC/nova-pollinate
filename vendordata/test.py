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

import contextlib
import os
import testtools

from oslo_config import cfg
from oslo_config import fixture as oslo_fixture

from vendordata import config

config_file = os.path.realpath(os.path.join(
    os.path.dirname(__file__),
    'tests/vendordata.conf'))

CONF = config.CONF
# CONF([], project='vendordata', default_config_files=[config_file])


@contextlib.contextmanager
def nested(*contexts):
    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(c) for c in contexts]


class TestCase(testtools.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()

        self.conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        self.conf.set_config_files([config_file])
