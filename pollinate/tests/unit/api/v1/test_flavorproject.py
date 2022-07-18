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

from warre.extensions import db
from warre import models
from warre.tests.unit import base


@mock.patch('warre.quota.get_enforcer', new=mock.Mock())
class TestFlavorProjectAPI(base.ApiTestCase):

    ROLES = ['admin']

    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_list_flavorprojects(self):

        fp = models.FlavorProject(project_id='fp-project-id',
                                  flavor_id=self.flavor.id)
        db.session.add(fp)
        db.session.commit()
        response = self.client.get('/v1/flavorprojects/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))
        api_fp = results[0]
        self.assertEqual('fp-project-id', api_fp.get('project_id'))
        self.assertEqual(self.flavor.id, api_fp.get('flavor'))

    def test_list_flavorprojects_filter_project(self):

        fp = models.FlavorProject(project_id='fp-project-id',
                                  flavor_id=self.flavor.id)
        db.session.add(fp)
        db.session.commit()
        response = self.client.get(
            '/v1/flavorprojects/?project_id=fp-project-id')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

        response = self.client.get(
            '/v1/flavorprojects/?project_id=bogus-id')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(0, len(results))

    def test_list_flavorprojects_filter_flavor(self):

        fp = models.FlavorProject(project_id='fp-project-id',
                                  flavor_id=self.flavor.id)
        db.session.add(fp)
        db.session.commit()
        response = self.client.get(
            '/v1/flavorprojects/?flavor_id=%s' % self.flavor.id)

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

        response = self.client.get(
            '/v1/flavorprojects/?flavor_id=bogus')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(0, len(results))

    def test_create_flavorproject(self):
        data = {'flavor_id': self.flavor.id, 'project_id': 'xyz'}
        response = self.client.post('/v1/flavorprojects/', json=data)
        self.assert200(response)
        fp = db.session.query(models.FlavorProject).all()[0]
        api_fp = response.get_json()
        self.assertEqual(self.flavor, fp.flavor)
        self.assertEqual(self.flavor.id, api_fp.get('flavor'))
        self.assertEqual('xyz', fp.project_id)
        self.assertEqual('xyz', api_fp.get('project_id'))

    def test_create_flavorproject_bad_flavor(self):
        data = {'flavor_id': 'bad-flavor-id', 'project_id': 'xyz'}
        response = self.client.post('/v1/flavorprojects/', json=data)
        self.assert404(response)

    def test_delete_flavorproject(self):
        fp = models.FlavorProject(project_id='fp-project-id',
                                  flavor_id=self.flavor.id)
        db.session.add(fp)
        db.session.commit()

        response = self.client.delete(f'/v1/flavorprojects/{fp.id}/')
        self.assertStatus(response, 204)
