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
from warre.worker import manager as worker_manager


@mock.patch('warre.common.blazar.BlazarClient')
@mock.patch('warre.app.create_app')
class TestManager(base.TestCase):

    def test_create_lease(self, mock_app, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2))

        fake_lease = {'id': 'fake-lease-id'}
        blazar_client.create_lease.return_value = fake_lease
        manager = worker_manager.Manager()

        with mock.patch.object(manager, 'get_bot_session') as get_session:
            session = get_session.return_value

            manager.create_lease(reservation.id)
            mock_blazar.assert_called_once_with(session=session)

            self.assertEqual('fake-lease-id', reservation.lease_id)
            self.assertEqual('ALLOCATED', reservation.status)

    def test_create_lease_error(self, mock_app, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2))

        blazar_client.create_lease.side_effect = Exception("Bad ERROR")
        manager = worker_manager.Manager()

        with mock.patch.object(manager, 'get_bot_session') as get_session:
            session = get_session.return_value

            manager.create_lease(reservation.id)
            mock_blazar.assert_called_once_with(session=session)

            self.assertIsNone(reservation.lease_id)
            self.assertEqual('ERROR', reservation.status)
            self.assertEqual('Bad ERROR', reservation.status_reason)
