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

from oslo_config import cfg
import testtools

from pollinate import app


CONF = cfg.CONF


class TestCase(testtools.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.override_config('auth_strategy', 'noauth')
        self.app = self.create_app()

    def create_app(self):
        return app.create_app({
            'DEBUG': False,  # Set to True for test debugging
            'TESTING': True,
        })

    def override_config(self, name, override, group=None):
        """Cleanly override CONF variables."""
        CONF.set_override(name, override, group)
        self.addCleanup(CONF.clear_override, name, group)
