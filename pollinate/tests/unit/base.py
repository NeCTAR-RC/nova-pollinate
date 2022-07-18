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

from unittest import mock

import flask_testing
from oslo_config import cfg
from oslo_context import context

from warre import app
from warre.common import keystone
from warre import extensions
from warre.extensions import db
from warre import models


PROJECT_ID = 'ksprojectid1'
USER_ID = 'ksuserid1'


class TestCase(flask_testing.TestCase):

    def create_app(self):
        return app.create_app({
            'SECRET_KEY': 'secret',
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': "sqlite://",
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }, conf_file='warre/tests/etc/warre.conf')

    def setUp(self):
        super().setUp()
        self.addCleanup(mock.patch.stopall)
        db.create_all()
        self.context = context.RequestContext(user_id=USER_ID,
                                              project_id=PROJECT_ID)

    def tearDown(self):
        super().tearDown()
        db.session.remove()
        db.drop_all()
        cfg.CONF.reset()
        extensions.api.resources = []

    def create_flavor(self, name='test.small', description='Test Flavor',
                      vcpu=4, memory_mb=1024, disk_gb=30, **kwargs):
        flavor = models.Flavor(name=name, description=description, vcpu=vcpu,
                               memory_mb=memory_mb, disk_gb=disk_gb, **kwargs)
        db.session.add(flavor)
        db.session.commit()
        return flavor

    def create_flavorproject(self, **kwargs):
        flavorproject = models.FlavorProject(**kwargs)
        db.session.add(flavorproject)
        db.session.commit()
        return flavorproject

    def create_reservation(self, project_id=PROJECT_ID, **kwargs):
        reservation = models.Reservation(**kwargs)
        reservation.user_id = USER_ID
        reservation.project_id = project_id
        db.session.add(reservation)
        db.session.commit()
        return reservation


class TestKeystoneWrapper(object):

    def __init__(self, app, roles):
        self.app = app
        self.roles = roles

    def __call__(self, environ, start_response):
        cntx = context.RequestContext(roles=self.roles,
                                      project_id=PROJECT_ID,
                                      user_id=USER_ID)
        environ[keystone.REQUEST_CONTEXT_ENV] = cntx

        return self.app(environ, start_response)


class ApiTestCase(TestCase):

    ROLES = ['member']

    def setUp(self):
        super().setUp()
        self.init_context()

    def init_context(self):
        self.app.wsgi_app = TestKeystoneWrapper(self.app.wsgi_app, self.ROLES)
