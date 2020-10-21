from unittest.mock import patch

from flask_testing import TestCase

from tips.api.tip_generator import tips_pool
from tips.server import application
from tips.tests.fixtures.fixture import get_fixture


class ApiTests(TestCase):
    def create_app(self):
        app = application
        app.config['TESTING'] = True
        return app

    def _get_client_data(self):
        return get_fixture(optin=True)

    def test_moved_to_amsterdam(self):
        new_pool = [tip for tip in tips_pool if tip['id'] == "mijn-16"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Welkom in Amsterdam")

        client_data = self._get_client_data()

        with patch('tips.api.tip_generator.tips_pool', new_pool):
            # Previous city is Amsterdam: fail
            response = self.client.post('/tips/gettips', json=client_data)
            self.assertEqual(len(response.get_json()), 0)

            # change previous city: pass
            client_data['userData']['BRP']['adresHistorisch'][0]['woonplaatsNaam'] = 'Utrecht'
            response = self.client.post('/tips/gettips', json=client_data)
            self.assertEqual(len(response.get_json()), 1)

            # change date: fail
            client_data = self._get_client_data()
            client_data['userData']['BRP']['adres']['begindatumVerblijf'] = '2020-01-01T00:00:00Z'
            response = self.client.post('/tips/gettips', json=client_data)
            self.assertEqual(len(response.get_json()), 0)

            # change date and previous city: fail
            client_data = self._get_client_data()
            client_data['userData']['BRP']['adres']['begindatumVerblijf'] = '2020-01-01T00:00:00Z'
            client_data['userData']['BRP']['adresHistorisch'][0]['woonplaatsNaam'] = 'Utrecht'
            response = self.client.post('/tips/gettips', json=client_data)
            self.assertEqual(len(response.get_json()), 0)
