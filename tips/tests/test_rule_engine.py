from unittest import TestCase

import objectpath
import json
import os

from tips.generator.rule_engine import apply_rules
from tips.config import PROJECT_PATH
from tips.tests.fixtures.fixture import get_fixture

COMPOUND_RULES_FILE = os.path.join(PROJECT_PATH, 'api', 'compound_rules.json')


def get_compound_rules():
    with open(COMPOUND_RULES_FILE) as compound_rules_file:
        compound_rules = json.load(compound_rules_file)
    return compound_rules


compound_rules = get_compound_rules()


class RuleEngineTest(TestCase):
    def setUp(self) -> None:
        _test_data = {
            'a': [
                1, 2, 3
            ],
            'b': [
                {'x': True, 'y': True},
                {'x': True, 'y': False},
                {'x': False, 'y': True}
            ]
        }

        self.test_data = objectpath.Tree(_test_data)

    def test_apply_rules_simple(self):
        rules = [
            {"type": "rule", "rule": "2 > 1"}
        ]
        compound_rules = {}

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

        rules = [
            {"type": "rule", "rule": "2 > 1"},
            {"type": "rule", "rule": "false"},
        ]
        self.assertFalse(apply_rules(self.test_data, rules, compound_rules))

    def test_apply_rules_nested(self):
        compound_rules = {
            "1": {
                "name": "rule 1",
                "rules": [
                    {"type": "rule", "rule": "true"}
                ]
            },
            "2": {
                "name": "rule 2",
                "rules": [
                    {"type": "ref", "ref_id": "1"}
                ]
            }
        }

        rules = [
            {"type": "ref", "ref_id": "1"}
        ]
        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

        rules = [
            {"type": "ref", "ref_id": "1"}
        ]
        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_apply_rules_recursing(self):
        compound_rules = {
            "1": {
                "name": "rule 1",
                "rules": [
                    {"type": "ref", "ref_id": "2"}
                ]
            },
            "2": {
                "name": "rule 2",
                "rules": [
                    {"type": "ref", "ref_id": "1"}
                ]
            }
        }
        rules = [{"type": "ref", "ref_id": "1"}]
        with self.assertRaises(RecursionError):
            apply_rules(self.test_data, rules, compound_rules)

        # self referencing
        compound_rules = {
            "1": {
                "name": "rule 1",
                "rules": [
                    {"type": "ref", "ref_id": "1"}
                ]
            }
        }
        rules = [{"type": "ref", "ref_id": "1"}]
        with self.assertRaises(RecursionError):
            apply_rules(self.test_data, rules, compound_rules)

    def test_stadspas(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "1"}  # ID 1 is the stadspas rule
        ]
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['focus'][7]['processtappen']['beslissing']['datum'] = "2020-01-01T03:00:00+02:00"
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['focus'][7]['typeBesluit'] = 'Afwijzing'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['focus'][7]['soortProduct'] = 'Participatiewet'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

        # regression test for when there is no stadspas data
        fixture_no_stadspas = get_fixture()
        fixture_no_stadspas['data']['focus'] = [item for item in fixture_no_stadspas['data']['focus'] if item['naam'] != 'Stadspas']

        user_data = objectpath.Tree(fixture_no_stadspas)
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_is_18_of_ouder(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "2"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['persoon']['geboortedatum'] = '2002-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['persoon']['geboortedatum'] = '2018-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_woont_in_gemeente_Amsterdam(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "3"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['persoon']['mokum'] = True
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['persoon']['mokum'] = False
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_heeft_kinderen(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "4"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['kinderen'] = []
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_kind_is_tussen_2_en_18_jaar(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "5"}
        ]
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2012-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2012-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

    def test_kind_is_op_30_september_2020_geen_18(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        rules = [
            {"type": "ref", "ref_id": "6"}
        ]
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2000-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, compound_rules))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2000-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2000-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, compound_rules))

    def test_kind_is_10_11_12(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        pio_rule = {
            "1": {
                "name": "kind is 10,11 of 12",
                "rules": [
                    {"type": "rule",
                     "rule": "len($.brp.kinderen[now() - timeDelta(10, 0, 0, 0, 0, 0) >= dateTime(@.geboortedatum) and now() - timeDelta(12, 0, 0, 0, 0, 0) <= dateTime(@.geboortedatum)]) >= 1"}
                ]
            }
        }
        rules = [
            {"type": "rule",
             "rule": "len($.brp.kinderen[now() - timeDelta(10, 0, 0, 0, 0, 0) >= dateTime(@.geboortedatum) and now() - timeDelta(13, 0, 0, 0, 0, 0) < dateTime(@.geboortedatum)]) >= 1"}
        ]
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2010-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2010-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2010-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2002-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2009-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2009-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2008-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2008-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '2007-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '2007-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['kinderen'][0]['geboortedatum'] = '20011-01-01T00:00:00Z'
        fixture["data"]['brp']['kinderen'][1]['geboortedatum'] = '20011-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

    def test_is_66_of_ouder(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        pio_rule = {
            "1": {
                "name": "is 66",
                "rules": [
                    {"type": "rule",
                     "rule": "dateTime($.brp.persoon.geboortedatum) + timeDelta(66, 4, 0, 0, 0, 0) <= now()"}
                ]
            }
        }
        rules = [
            {"type": "rule",
             "rule": "dateTime($.brp.persoon.geboortedatum) + timeDelta(66, 4, 0, 0, 0, 0) <= now()"}
        ]
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['persoon']['geboortedatum'] = '1950-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['persoon']['geboortedatum'] = '2000-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

    def test_nationaliteit(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        pio_rule = {
            "1": {
                "name": "is 66",
                "rules": [
                    {"type": "rule",
                     "rule": "$.brp.persoon.nationaliteiten[@.omschrijving is Nederlandse]"}
                ]
            }
        }
        rules = [
            {"type": "rule",
             "rule": "$.brp.persoon.nationaliteiten[@.omschrijving is Nederlandse]"}
        ]
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['persoon']["nationaliteiten"][0] = {"omschrijving": "Nederlandse"}
        user_data = objectpath.Tree(fixture["data"])
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['persoon']["nationaliteiten"][0] = {"omschrijving": "Amerikaanse"}
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

    def test_is_21_of_ouder(self):
        fixture = get_fixture()
        user_data = objectpath.Tree(fixture["data"])
        pio_rule = {
            "1": {
                "name": "is 66",
                "rules": [
                    {"type": "rule",
                     "rule": "dateTime($.brp.persoon.geboortedatum) + timeDelta(21, 0, 0, 0, 0, 0) <= now()"}
                ]
            }
        }
        rules = [
            {"type": "rule",
             "rule": "dateTime($.brp.persoon.geboortedatum) + timeDelta(21, 0, 0, 0, 0, 0) <= now()"}
        ]
        self.assertTrue(apply_rules(user_data, rules, pio_rule))

        fixture["data"]['brp']['persoon']['geboortedatum'] = '2012-01-01T00:00:00Z'
        user_data = objectpath.Tree(fixture["data"])
        self.assertFalse(apply_rules(user_data, rules, pio_rule))

    def test_list_assertion(self):
        test_data = objectpath.Tree({
            "brp": {
                "kinderen": [{
                    "bsn": None,
                    "geboortedatum": "2006-07-08T09:14:58.963Z",
                    "geslachtsaanduiding": "M",
                    "geslachtsnaam": "Kosterijk",
                    "overlijdensdatum": None,
                    "voornamen": "Yassine",
                    "voorvoegselGeslachtsnaam": None
                },
                    {
                    "bsn": None,
                    "geboortedatum": "2018-06-04T09:14:58.963Z",
                    "geslachtsaanduiding": "M",
                    "geslachtsnaam": "Kosterijk",
                    "overlijdensdatum": None,
                    "voornamen": "Marwan",
                    "voorvoegselGeslachtsnaam": None
                }]
            }
        })
        compound_rules = {
            "1": {
                "name": "rule 1",
                "rules": [
                    {
                        "type": "rule",
                        "rule": "len($.brp.kinderen[now() - timeDelta(2, 0, 0, 0, 0, 0) >= dateTime(@.geboortedatum) and now() - timeDelta(18, 0, 0, 0, 0, 0) <= dateTime(@.geboortedatum)]) >= 1"
                    }
                ]
            }
        }
        rules = [
            {"type": "ref", "ref_id": "1"}
        ]
        self.assertTrue(apply_rules(test_data, rules, compound_rules))

        user_data = objectpath.Tree({
            "focus": [{
                "typeBesluit": "Toekenning",
                "soortProduct": "Minimafonds",
                "processtappen": {
                    "beslissing": {
                        "datum": "2020-04-15T00:00:00+02:00"
                    }
                }
            }]
        })
        ret5 = user_data.execute("len($.focus.*[@.soortProduct is 'Minimafonds' and @.typeBesluit is 'Toekenning' and now() - timeDelta(1, 0, 0, 0, 0, 0) <= dateTime(@.processtappen.beslissing.datum)]) >= 1")
        self.assertTrue(ret5)
