import os
import datetime

from flask_testing import TestCase

from tips.api.tip_generator import tips_pool
from tips.config import PROJECT_PATH
from tips.server import application
from tips.tests.fixtures.fixture import get_fixture


class ApiTests(TestCase):
    def create_app(self):
        app = application
        app.config['TESTING'] = True
        return app

    def _get_client_data(self):
        return get_fixture(optin=True)

    def test_health(self):
        response = self.client.get('/status/health')
        self.assert200(response)
        self.assertEqual(response.data, b"OK")

    def test_tips(self):

        client_data = self._get_client_data()
        recent_date = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Change date which we compare to now() in our tests.
        client_data['userData']['BRP']['adres']['begindatumVerblijf'] = recent_date

        for index, item in enumerate(client_data['userData']['FOCUS_AANVRAGEN']):
            if item['id'] == 'test-stadspas-validity':
                client_data['userData']['FOCUS_AANVRAGEN'][index]['steps'][-1]['datePublished'] = recent_date
                break

        response = self.client.post('/tips/gettips', json=client_data)

        tips = response.get_json()

        self.assertEqual(5, len(tips))

        self.assertEqual(tips[0]['title'], 'Laat geen geld liggen')
        self.assertEqual(tips[0]['reason'], ['U ziet deze tip omdat u een TOZO aanvraag heeft gedaan'])

        self.assertEqual(tips[1]['title'], 'Download de 020werkt-app')
        self.assertEqual(tips[1]['reason'], ['U ziet deze tip omdat u TOZO, stadspas of bijstandsuitkering heeft'])

        self.assertEqual(tips[2]['title'], 'Draag uw mondkapje')

        self.assertEqual(tips[3]['title'], 'Bekijk de afvalpunten in de buurt')
        self.assertEqual(tips[3]['reason'], ['U ziet deze tip omdat u net bent verhuisd'])

        self.assertEqual(tips[4]['title'], 'Op stap met uw Stadspas')
        self.assertEqual(tips[4]['reason'], ['U ziet deze tip omdat u een Stadspas hebt'])

    def test_tips_audience(self):
        response = self.client.post('/tips/gettips?audience=zakelijk', json=get_fixture(optin=False))
        tips = response.get_json()
        self.assertEqual(len(tips), 5)

        response = self.client.post('/tips/gettips?audience=persoonlijk', json=get_fixture(optin=False))
        tips = response.get_json()
        self.assertEqual(len(tips), 5)

        response = self.client.post('/tips/gettips?audience=zakelijk,persoonlijk', json=get_fixture(optin=False))
        tips = response.get_json()
        self.assertEqual(len(tips), 10)

    def test_income_tips(self):
        response = self.client.post('/tips/getincometips', json=self._get_client_data())

        tips = response.get_json()

        # Asserting the length of the response here would mean to fix all dates that compare to now() which is somewhat besides the point of this test.
        self.assertEqual(26, len(tips))

    def test_images(self):
        for tip in tips_pool:
            url = tip['imgUrl']
            url = url.lstrip('/api')  # api is from the load balancer, not this api
            response = self.client.get(url)
            self.assert200(response)


class ApiStaticFiles(TestCase):
    def create_app(self):
        app = application
        app.config['TESTING'] = True
        return app

    def test_get_valid(self):
        with open(os.path.join(PROJECT_PATH, "static/tip_images/afvalpunt.jpg"), 'rb') as img:

            response = self.client.get('/tips/static/tip_images/afvalpunt.jpg')
            self.assertEqual(response.data, img.read())
            self.assert200(response)

    def test_get_invalid(self):
        response = self.client.get('/tips/static/tip_images/nope.jpg')
        self.assert404(response)

    def test_traversal(self):
        with open(os.path.join(PROJECT_PATH, "config.py"), 'rb') as fh:
            response = self.client.get('/tips/static/tip_images/../../config.py')
            self.assert404(response)
            self.assertNotEqual(response.data, fh.read())
