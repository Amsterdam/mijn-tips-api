from unittest.mock import patch

from flask_testing import TestCase

from tips.api.tip_generator import tips_pool
from tips.server import application
from tips.tests.fixtures.fixture import get_fixture_without_source_tips, get_fixture


class ApiTests(TestCase):
    def create_app(self):
        app = application
        app.config['TESTING'] = True
        return app

    def _get_client_data(self):
        return get_fixture_without_source_tips(optin=True)

    def test_belasting_tip(self):
        client_data = get_fixture(optin=True)

        response = self.client.post('/tips/gettips', json=client_data)

        belasting_tip = None
        for i in response.get_json():
            if i['id'] == "belasting-5":
                belasting_tip = i

        self.assertEqual(belasting_tip['reason'], ['U krijgt deze tip omdat u nog niet via automatische incasso betaalt'])
        self.assertEqual(belasting_tip['imgUrl'], 'api/tips/static/tip_images/belastingen.jpg')

    def test_belasting_tip_no_optin(self):
        client_data = get_fixture(optin=False)

        response = self.client.post('/tips/gettips', json=client_data)

        belasting_tip = None
        for i in response.get_json():
            if i['id'] == "belasting-5":
                belasting_tip = i

        self.assertIsNone(belasting_tip)

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

    def test_laat_geen_geld_liggen(self):
        new_pool = [tip for tip in tips_pool if tip['id'] == "mijn-22"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Laat geen geld liggen")

        client_data = self._get_client_data()

        with patch('tips.api.tip_generator.tips_pool', new_pool):
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]['title'], 'Laat geen geld liggen')

            # remove tozo docs
            client_data['userData']['FOCUS_TOZO'] = []
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    def test_020werkt(self):
        new_pool = [tip for tip in tips_pool if tip['id'] == "mijn-23"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Download de 020werkt-app")

        client_data = self._get_client_data()
        with patch('tips.api.tip_generator.tips_pool', new_pool):
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]['title'], 'Download de 020werkt-app')

            # remove tozo
            old_tozo = client_data['userData']['FOCUS_TOZO']
            client_data['userData']['FOCUS_TOZO'] = []
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # also remove bijstandsuitkering
            aanvragen = [i for i in client_data['userData']['FOCUS_AANVRAGEN'] if i['productTitle'] != 'Bijstandsuitkering']
            client_data['userData']['FOCUS_AANVRAGEN'] = aanvragen
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # also remove stadspas
            aanvragen = [i for i in client_data['userData']['FOCUS_AANVRAGEN'] if i['productTitle'] != 'Stadspas']
            client_data['userData']['FOCUS_AANVRAGEN'] = aanvragen
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # add back tozo
            client_data['userData']['FOCUS_TOZO'] = old_tozo
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

    def test_draag_uw_mondkapje(self):
        new_pool = [tip for tip in tips_pool if tip['id'] == "mijn-24"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Draag uw mondkapje")

        client_data = self._get_client_data()
        with patch('tips.api.tip_generator.tips_pool', new_pool):
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]['title'], 'Draag uw mondkapje')

            wmodata = client_data['userData']['WMO']
            for i in wmodata:
                if i.get('voorzieningsoortcode') == "AOV":
                    i['isActual'] = False

            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    def test_ID_voor_stemmen(self):
        new_pool = [tip for tip in tips_pool if tip['id'] == "mijn-27"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Gratis ID-kaart om te stemmen")

        # user must not have a valid id
        # user must have stadspas groene met stip

        with patch('tips.api.tip_generator.tips_pool', new_pool):
            client_data = self._get_client_data()

            # set both identiteitsbewijzen to be expired before election date
            client_data['userData']['BRP']['identiteitsbewijzen'][0]['datumAfloop'] = "2021-03-16T00:00:00Z"
            client_data['userData']['BRP']['identiteitsbewijzen'][1]['datumAfloop'] = "2021-03-16T00:00:00Z"
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]['title'], 'Gratis ID-kaart om te stemmen')

            # set one ID to be valid on election
            client_data['userData']['BRP']['identiteitsbewijzen'][1]['datumAfloop'] = "2021-03-18T00:00:00Z"
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # remove stadspas and set id back to be expired
            client_data['userData']['FOCUS_AANVRAGEN'] = []
            client_data['userData']['BRP']['identiteitsbewijzen'][1]['datumAfloop'] = "2021-03-16T00:00:00Z"
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # test with no ids
            client_data['userData']['BRP']['identiteitsbewijzen'] = []
            response = self.client.post('/tips/gettips', json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)
