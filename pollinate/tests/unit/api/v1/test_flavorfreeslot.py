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

from datetime import datetime
from unittest import mock

from warre import models
from warre.tests.unit import base


@mock.patch('warre.quota.get_enforcer', new=mock.Mock())
class TestFlavorFreeSlotAPI(base.ApiTestCase):

    def setUp(self):
        super().setUp()
        self.one_slot_flavor = self.create_flavor()
        self.two_slot_flavor = self.create_flavor(slots=2)

    def test_list_empty_free_slot(self):
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        response = self.client.get(url)
        self.assertStatus(response, 200)
        # only 1 big freeslot
        results = response.get_json()
        self.assertEqual(1, len(results))

        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        response = self.client.get(url)
        self.assertStatus(response, 200)
        # only 1 big freeslot
        results = response.get_json()
        self.assertEqual(1, len(results))

    def test_querystring(self):
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-02-01'
        end_date = '2021-03-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertIn(start_date, results[0]['start'])
        self.assertIn(end_date, results[0]['end'])

    def test_one_slot_two_reservations(self):
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 5, 1),
                                end=datetime(2021, 6, 1))
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(3, len(results))

    def test_one_slot_one_reservation(self):
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(2, len(results))

    def test_continious_reservations(self):
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 3, 1),
                                end=datetime(2021, 4, 1))
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(2, len(results))

    def test_two_slots_one_reservation(self):
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(1, len(results))
        self.assertIn(start_date, results[0]['start'])
        self.assertIn(end_date, results[0]['end'])

    def test_two_slots_two_reservations(self):
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 5, 1),
                                end=datetime(2021, 6, 1))
        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(1, len(results))
        self.assertIn(start_date, results[0]['start'])
        self.assertIn(end_date, results[0]['end'])

    def test_two_slots_overlapping_reservations(self):
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 3, 1))
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 10),
                                end=datetime(2021, 3, 10))
        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(2, len(results))
        self.assertIn('2021-02-10', results[0]['end'])
        self.assertIn('2021-03-01', results[1]['start'])

    def test_querystring_shorter(self):
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 10, 1))
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-05-01'
        end_date = '2021-09-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(0, len(results))

    def test_querystring_overlapping(self):
        self.create_reservation(flavor_id=self.one_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1),
                                end=datetime(2021, 10, 1))
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-05-01'
        end_date = '2022-01-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(1, len(results))
        self.assertIn('2021-10-01', results[0]['start'])
        self.assertIn('2022-01-01', results[0]['end'])

    def test_minutes_reservations(self):
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1, 11),
                                end=datetime(2021, 2, 1, 20))
        self.create_reservation(flavor_id=self.two_slot_flavor.id,
                                status=models.Reservation.ALLOCATED,
                                start=datetime(2021, 2, 1, 16),
                                end=datetime(2021, 2, 1, 22))
        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        start_date = '2021-02-01'
        end_date = '2022-02-02'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertEqual(2, len(results))
        self.assertIn('2021-02-01T16', results[0]['end'])
        self.assertIn('2021-02-01T20', results[1]['start'])

    def test_flavor_start_end(self):
        start = datetime(2021, 1, 10)
        end = datetime(2021, 1, 20)
        flavor = self.create_flavor(start=start, end=end)
        url = f'/v1/flavors/{flavor.id}/freeslots/'
        start_date = '2021-01-01'
        end_date = '2021-03-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertIn("2021-01-10T00:00:00", results[0]['start'])
        self.assertIn("2021-01-20T00:00:00", results[0]['end'])
