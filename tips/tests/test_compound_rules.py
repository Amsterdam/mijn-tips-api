import json
import os
import datetime
from unittest import TestCase

from dateutil import relativedelta

from tips.api.user_data_tree import UserDataTree
from tips.config import PROJECT_PATH
from tips.generator.rule_engine import apply_rules
from tips.server import get_tips_request_data
from tips.tests.fixtures.fixture import get_fixture

COMPOUND_RULES_FILE = os.path.join(PROJECT_PATH, 'api', 'compound_rules.json')
def get_compound_rules():
    with open(COMPOUND_RULES_FILE) as compound_rules_file:
        compound_rules = json.load(compound_rules_file)
    return compound_rules


compound_rules = get_compound_rules()


def get_date_years_ago(years):
    return (datetime.datetime.now() - relativedelta.relativedelta(years=years)).strftime("%Y-%m-%dT%H:%M:%SZ")


class TestCompountRules(TestCase):

    def _get_tips_request_data(self):
        return get_tips_request_data(get_fixture())

    def test_stadspas(self):
        # Stadspas rule
        rules = [
            {"type": "ref", "ref_id": "1"}
        ]

        def is_valid(stadspas):
            user_data = UserDataTree({"FOCUS_AANVRAGEN": [stadspas]})
            return apply_rules(user_data, rules, compound_rules)

        # Use invalid date
        invalid_date = get_date_years_ago(2)

        stadspas = {
            "productTitle": "Stadspas",
            "steps": [{"datePublished": invalid_date, "decision": "toekenning"}]
        }
        self.assertFalse(is_valid(stadspas))

        # Use valid date
        valid_date = get_date_years_ago(1)

        stadspas = {
            "productTitle": "Stadspas",
            "steps": [{"datePublished": valid_date, "decision": "toekenning"}]
        }
        self.assertTrue(is_valid(stadspas))

        # Use invalid decision
        stadspas = {
            "productTitle": "Stadspas",
            "steps": [{"datePublished": valid_date, "decision": "afwijzing"}]
        }
        self.assertFalse(is_valid(stadspas))

        # Use invalid productTitle
        stadspas = {
            "productTitle": "Bijstandsuitkering",
            "steps": [{"datePublished": valid_date, "decision": "toekenning"}]
        }
        self.assertFalse(is_valid(stadspas))

        # regression test for when there is no stadspas data or malformed stadspas data
        self.assertFalse(is_valid(None))
        self.assertFalse(is_valid({"steps": ["hy"]}))

        user_data = UserDataTree({"bliep": None})
        is_valid_data = apply_rules(user_data, rules, compound_rules)
        self.assertFalse(is_valid_data)

    def test_is_18_of_ouder(self):
        fixture = self._get_tips_request_data()

        rules = [
            {"type": "ref", "ref_id": "2"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(19)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(18)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(17)
        self.assertFalse(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(1)
        self.assertFalse(get_result())

    def test_woont_in_gemeente_Amsterdam(self):
        fixture = self._get_tips_request_data()
        user_data = UserDataTree(fixture["user_data"])
        rules = [
            {"type": "ref", "ref_id": "3"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["user_data"]['BRP']['persoon']['mokum'] = True
        user_data = UserDataTree(fixture["user_data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["user_data"]['BRP']['persoon']['mokum'] = False
        user_data = UserDataTree(fixture["user_data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_heeft_kinderen(self):
        fixture = self._get_tips_request_data()
        user_data = UserDataTree(fixture["user_data"])
        rules = [
            {"type": "ref", "ref_id": "4"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["user_data"]['BRP']['kinderen'] = []
        user_data = UserDataTree(fixture["user_data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_kind_is_tussen_2_en_18_jaar(self):
        fixture = self._get_tips_request_data()

        rules = [
            {"type": "ref", "ref_id": "5"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(1)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(19)
        self.assertFalse(get_result())

        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(1)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(3)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(2)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(18)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(11)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(16)
        self.assertTrue(get_result())

    def test_kind_is_10_11_12(self):
        fixture = self._get_tips_request_data()

        rules = [
            {"type": "ref", "ref_id": "8"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        # mixed valid / invalid
        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(12)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(5)
        self.assertTrue(get_result())

        # mixed valid / invalid
        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(10)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(14)
        self.assertTrue(get_result())

        # both valid age
        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(11)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(11)
        self.assertTrue(get_result())

        # both children are younger
        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(5)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(2)
        self.assertFalse(get_result())

        # both children are older
        fixture["user_data"]['BRP']['kinderen'][0]['geboortedatum'] = get_date_years_ago(15)
        fixture["user_data"]['BRP']['kinderen'][1]['geboortedatum'] = get_date_years_ago(22)
        self.assertFalse(get_result())

    def test_is_66_of_ouder(self):
        fixture = self._get_tips_request_data()

        rules = [
            {"type": "ref", "ref_id": "6"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(67)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(66)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(55)
        self.assertFalse(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(65)
        self.assertFalse(get_result())

    def test_nationaliteit(self):
        fixture = self._get_tips_request_data()

        pio_rule = {
            "1": {
                "name": "is 66",
                "rules": [
                    {"type": "rule",
                     "rule": "$.BRP.persoon.nationaliteiten[@.omschrijving is Nederlandse]"}
                ]
            }
        }
        rules = [
            {"type": "ref", "ref_id": "1"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, pio_rule)

        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']["nationaliteiten"][0] = {"omschrijving": "Nederlandse"}
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']["nationaliteiten"][0] = {"omschrijving": "Amerikaanse"}
        self.assertFalse(get_result())

    def test_is_21_of_ouder(self):
        fixture = self._get_tips_request_data()

        rules = [
            {"type": "ref", "ref_id": "7"}
        ]

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(22)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(21)
        self.assertTrue(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(14)
        self.assertFalse(get_result())

        fixture["user_data"]['BRP']['persoon']['geboortedatum'] = get_date_years_ago(20)
        self.assertFalse(get_result())

    def test_heeft_nederlandse_nationaliteit(self):
        fixture = self._get_tips_request_data()

        def get_result():
            user_data = UserDataTree(fixture["user_data"])
            return apply_rules(user_data, rules, compound_rules)

        rules = [
            {"type": "ref", "ref_id": "13"}
        ]

        self.assertTrue(get_result())

        # remove Nederlandse
        del(fixture["user_data"]["BRP"]["persoon"]["nationaliteiten"][0])
        self.assertFalse(get_result())
