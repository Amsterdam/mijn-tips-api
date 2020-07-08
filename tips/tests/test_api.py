import os

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
        response = self.client.post('/tips/gettips', json=self._get_client_data())

        data = response.get_json()
        tips = data['items']
        self.assertEqual(1, len(tips))
        self.assertEqual(tips[0]['title'], 'Bekijk de afvalpunten in de buurt')
        
        self.assertEqual(tips[0]['reason'], ["Afgelopen 3 maanden verhuisd"])

    def test_income_tips(self):
        response = self.client.post('/tips/getincometips', json=self._get_client_data())

        data = response.get_json()
        tips = data['items']
        self.assertEqual(24, len(tips))
        
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
