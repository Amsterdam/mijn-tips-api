from unittest.mock import patch

from flask_testing import TestCase
from freezegun import freeze_time

from tips.api.tip_generator import tips_pool
from tips.server import application
from tests.fixtures.fixture import get_fixture_without_source_tips, get_fixture


class ApiTests(TestCase):
    def create_app(self):
        app = application
        app.config["TESTING"] = True
        return app

    def _get_client_data(self):
        return get_fixture_without_source_tips(optin=True)

    def test_belasting_tip(self):
        client_data = get_fixture(optin=True)

        response = self.client.post("/tips/gettips", json=client_data)

        belasting_tip = None
        for i in response.get_json():
            if i["id"] == "belasting-5":
                belasting_tip = i

        self.assertEqual(
            belasting_tip["reason"],
            ["U krijgt deze tip omdat u nog niet via automatische incasso betaalt"],
        )
        self.assertEqual(
            belasting_tip["imgUrl"], "api/tips/static/tip_images/belastingen.jpg"
        )

    def test_belasting_tip_no_optin(self):
        client_data = get_fixture(optin=False)

        response = self.client.post("/tips/gettips", json=client_data)

        belasting_tip = None
        for i in response.get_json():
            if i["id"] == "belasting-5":
                belasting_tip = i

        self.assertIsNone(belasting_tip)

    @freeze_time("2021-01-01")
    def test_moved_to_amsterdam(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-16"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Welkom in Amsterdam")

        client_data = self._get_client_data()

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            # Previous city is Amsterdam: fail
            response = self.client.post("/tips/gettips", json=client_data)
            self.assertEqual(len(response.get_json()), 0)

            # change previous city: pass
            client_data["userData"]["BRP"]["adresHistorisch"][0][
                "woonplaatsNaam"
            ] = "Utrecht"
            response = self.client.post("/tips/gettips", json=client_data)
            self.assertEqual(len(response.get_json()), 1)

            # change date: fail
            client_data = self._get_client_data()
            client_data["userData"]["BRP"]["adres"][
                "begindatumVerblijf"
            ] = "2020-01-01T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            self.assertEqual(len(response.get_json()), 0)

            # change date and previous city: fail
            client_data = self._get_client_data()
            client_data["userData"]["BRP"]["adres"][
                "begindatumVerblijf"
            ] = "2020-01-01T00:00:00Z"
            client_data["userData"]["BRP"]["adresHistorisch"][0][
                "woonplaatsNaam"
            ] = "Utrecht"
            response = self.client.post("/tips/gettips", json=client_data)
            self.assertEqual(len(response.get_json()), 0)

    @freeze_time("2021-03-09")
    def test_laat_geen_geld_liggen(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-22"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Laat geen geld liggen")

        client_data = self._get_client_data()

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Laat geen geld liggen")

            # remove tozo docs
            client_data["userData"]["FOCUS_TOZO"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    @freeze_time("2021-03-09")
    def test_020werkt(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-23"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Download de 020werkt-app")

        client_data = self._get_client_data()

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Download de 020werkt-app")

            # remove tozo
            old_tozo = client_data["userData"]["FOCUS_TOZO"]
            client_data["userData"]["FOCUS_TOZO"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # also remove bijstandsuitkering
            aanvragen = [
                i
                for i in client_data["userData"]["FOCUS_AANVRAGEN"]
                if i["productTitle"] != "Bijstandsuitkering"
            ]
            client_data["userData"]["FOCUS_AANVRAGEN"] = aanvragen
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # also remove stadspas
            aanvragen = [
                i
                for i in client_data["userData"]["FOCUS_AANVRAGEN"]
                if i["productTitle"] != "Stadspas"
            ]
            client_data["userData"]["FOCUS_AANVRAGEN"] = aanvragen
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # add back tozo
            client_data["userData"]["FOCUS_TOZO"] = old_tozo
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

    def test_draag_uw_mondkapje(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-24"]

        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Draag uw mondkapje")

        client_data = self._get_client_data()
        with patch("tips.api.tip_generator.tips_pool", new_pool):
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Draag uw mondkapje")

            wmodata = client_data["userData"]["WMO"]
            for i in wmodata:
                if i.get("voorzieningsoortcode") == "AOV":
                    i["isActual"] = False

            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    @freeze_time("2021-03-09")
    def test_ID_voor_stemmen(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-27"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Gratis ID-kaart om te stemmen")

        # user must not have a valid id
        # user must have stadspas groene met stip

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # set both identiteitsbewijzen to be expired before election date
            client_data["userData"]["BRP"]["identiteitsbewijzen"][0][
                "datumAfloop"
            ] = "2021-03-16T00:00:00Z"
            client_data["userData"]["BRP"]["identiteitsbewijzen"][1][
                "datumAfloop"
            ] = "2021-03-16T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Gratis ID-kaart om te stemmen")

            # set one ID to be valid on election
            client_data["userData"]["BRP"]["identiteitsbewijzen"][1][
                "datumAfloop"
            ] = "2021-03-18T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # remove stadspas and set id back to be expired
            client_data["userData"]["BRP"]["identiteitsbewijzen"][1][
                "datumAfloop"
            ] = "2021-03-16T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # test with no ids
            client_data["userData"]["BRP"]["identiteitsbewijzen"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # no stadspas
            client_data["userData"]["FOCUS_STADSPAS"] = None
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    @freeze_time("2018-07-15")
    def test_pingping(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-28"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Breng je basis op orde")

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # exactly 18
            client_data["userData"]["BRP"]["persoon"][
                "geboortedatum"
            ] = "2000-07-15T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # 1 day future
            client_data["userData"]["BRP"]["persoon"][
                "geboortedatum"
            ] = "2000-07-16T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # 1 day past
            client_data["userData"]["BRP"]["persoon"][
                "geboortedatum"
            ] = "2000-07-14T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # 17 years 9 months -1 day old
            client_data["userData"]["BRP"]["persoon"][
                "geboortedatum"
            ] = "2000-10-18T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # 18 years 6 months 1 day
            client_data["userData"]["BRP"]["persoon"][
                "geboortedatum"
            ] = "2000-01-14T00:00:00Z"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    @freeze_time("2021-08-15")
    def test_vakantie_verhuur(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-33"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Particuliere vakantieverhuur")

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # Initial state has vakantieverhuurvergunnings aanvraag and registratienummer
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Has Vakantieverhuurvergunnings aanvraag
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"][0][
                "caseType"
            ] = "Vakantieverhuur vergunningsaanvraag"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Particuliere vakantieverhuur")

            # Has Vakantieverhuur
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"][0][
                "caseType"
            ] = "Vakantieverhuur"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Particuliere vakantieverhuur")

            # No registratienummers en vergunningen
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    def test_bb_vergunning(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-34"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Overgangsrecht bij Bed and breakfast")

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # Initial state BB result is 'geweigerd'
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Result is Verleend met overgangsrecht
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"][1][
                "hasTransitionAgreement"
            ] = True
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Overgangsrecht bij Bed and breakfast")

            # No case type BB - vergunning
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"][1][
                "caseType"
            ] = "Vakantieverhuur"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # No vergunningen at all
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    def test_bb_vergunning_personal(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-35"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Bed & breakfast")

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # Initial state has b&b-vergunning and registratienummer
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Has b&b-vergunning and no registraties
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)
            self.assertEqual(json[0]["title"], "Bed & breakfast")

            # Has b&b-vergunning and no registraties and no amsterdam bsn
            client_data["userData"]["BRP"]["persoon"]["mokum"] = False
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Has Vakantieverhuur vergunning and no registraties
            client_data["userData"]["BRP"]["persoon"]["mokum"] = True
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"][1][
                "caseType"
            ] = "Vakantieverhuur"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # No registratienummers en vergunningen
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["registraties"] = []
            client_data["userData"]["TOERISTISCHE_VERHUUR"]["vergunningen"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

    @freeze_time("2021-08-15")
    def test_sportvergoeding_kinderen_personal(self):
        new_pool = [tip for tip in tips_pool if tip["id"] == "mijn-36"]
        self.assertEqual(len(new_pool), 1)
        self.assertEqual(new_pool[0]["title"], "Sportvergoeding voor kinderen")

        with patch("tips.api.tip_generator.tips_pool", new_pool):
            client_data = self._get_client_data()

            # Initial state has Tozo and Tonk with intrekking and bijstands and stadspas
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Remove stadspas
            client_data["userData"]["FOCUS_STADSPAS"] = None
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)

            # Tozo with toekenning
            client_data["userData"]["FOCUS_TOZO"][0]["decision"] = "toekenning"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # No tozo but tonk with 'toekenning' and no 'terugtrekking'
            client_data["userData"]["FOCUS_TOZO"] = []
            client_data["userData"]["FOCUS_TONK"][0]["decision"] = "toekenning"
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # No tozo and tonk and no stadspas but bijstands
            client_data["userData"]["FOCUS_TONK"] = []
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 1)

            # No tozo and tonk and no stadspas and no bijstands
            aanvragen = [
                i
                for i in client_data["userData"]["FOCUS_AANVRAGEN"]
                if i["productTitle"] != "Bijstandsuitkering"
            ]
            client_data["userData"]["FOCUS_AANVRAGEN"] = aanvragen
            response = self.client.post("/tips/gettips", json=client_data)
            json = response.get_json()
            self.assertEqual(len(json), 0)
