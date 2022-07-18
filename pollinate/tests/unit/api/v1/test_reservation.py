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

import datetime
from unittest import mock

from warre.tests.unit import base


@mock.patch('warre.quota.get_enforcer', new=mock.Mock())
class TestReservationAPI(base.ApiTestCase):

    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_list_reservations(self):
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2))
        response = self.client.get('/v1/reservations/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

    def test_list_reservations_non_project(self):
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2),
                                project_id="notmine")
        response = self.client.get('/v1/reservations/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(0, len(results))

    def test_create_resevation(self):
        data = {'flavor_id': self.flavor.id, 'start': '2020-01-01 00:00',
                'end': '2020-01-01 01:00'}
        response = self.client.post('/v1/reservations/', json=data)
        self.assert200(response)
        self.assertEqual(1, response.get_json().get('instance_count'))

    def test_create_resevation_multiple_instances(self):
        data = {'flavor_id': self.flavor.id, 'start': '2020-01-01 00:00',
                'end': '2020-01-01 01:00', 'instance_count': 2}
        response = self.client.post('/v1/reservations/', json=data)
        self.assert200(response)
        self.assertEqual(2, response.get_json().get('instance_count'))

    def test_create_resevation_noinput(self):
        data = {}
        response = self.client.post('/v1/reservations/', json=data)
        self.assert400(response)

    def test_create_resevation_bad_flavor(self):
        data = {'flavor_id': 'bogus', 'start': '2020-01-01 00:00',
                'end': '2020-02-02 00:00'}
        response = self.client.post('/v1/reservations/', json=data)
        self.assert404(response)

    def test_create_resevation_missing_args(self):
        data = {'flavor_id': self.flavor.id, 'start': '2020-01-01 00:00'}
        response = self.client.post('/v1/reservations/', json=data)
        self.assertStatus(response, 422)


class TestAdminReservationAPI(TestReservationAPI):

    ROLES = ['admin']

    def test_list_reservations_all_projects(self):
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2),
                                project_id='123')
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2),
                                project_id='987')
        response = self.client.get('/v1/reservations/?all_projects=1')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(2, len(results))

    def test_list_reservations_other_project(self):
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2),
                                project_id='123')
        self.create_reservation(flavor_id=self.flavor.id,
                                start=datetime.datetime(2021, 1, 1),
                                end=datetime.datetime(2021, 1, 2),
                                project_id='987')
        response = self.client.get('/v1/reservations/?all_projects=1')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(2, len(results))
