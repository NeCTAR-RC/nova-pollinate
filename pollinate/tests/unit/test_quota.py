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

from warre import models
from warre import quota
from warre.tests.unit import base


class TestQuota(base.TestCase):

    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_get_usage_by_project_reservation(self):
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'reservation')
        self.assertEqual(0, usage)
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=self.flavor.id,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'reservation')
        self.assertEqual(1, usage)
        self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=self.flavor.id,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'reservation')
        self.assertEqual(2, usage)
        self.create_reservation(
            status=models.Reservation.COMPLETE,
            flavor_id=self.flavor.id,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'reservation')
        self.assertEqual(2, usage)

    def test_get_usage_by_project_hours(self):
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'hours')
        self.assertEqual(0, usage)
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=self.flavor.id,
            start=datetime(2021, 3, 1, 10, 0, 0),
            end=datetime(2021, 3, 1, 11, 0, 0))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'hours')
        self.assertEqual(1, usage)
        self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=self.flavor.id,
            start=datetime(2021, 3, 2, 10, 0, 0),
            end=datetime(2021, 3, 2, 13, 0, 0))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'hours')
        self.assertEqual(4, usage)
        self.create_reservation(
            status=models.Reservation.ERROR,
            flavor_id=self.flavor.id,
            start=datetime(2021, 3, 2, 10, 0, 0),
            end=datetime(2021, 3, 2, 13, 0, 0))
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'hours')
        self.assertEqual(4, usage)

    def test_get_usage_by_project_hours_multiple_instances(self):
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=self.flavor.id,
            start=datetime(2021, 3, 1, 10, 0, 0),
            end=datetime(2021, 3, 1, 12, 0, 0),
            instance_count=7)
        usage = quota.get_usage_by_project(base.PROJECT_ID, 'hours')
        self.assertEqual(14, usage)
