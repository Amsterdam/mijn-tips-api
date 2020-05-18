from unittest import TestCase

import objectpath
import json

from tips.generator.rule_engine import apply_rules

from tips.tests.fixtures.fixture import get_fixture

with open("C:/xampp/htdocs/Stage_Amsterdam/mijn-tips-api/tips/api/compound_rules.json") as compound_rules_file:
    compound_rules = json.load(compound_rules_file)

# with open("C:/xampp/htdocs/Stage_Amsterdam/mijn-tips-api/tips/api/persoonlijk_inkomens_tips.json") as rules_file:
#     rules = json.load(rules_file)


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

        # Als line 7 niet werkt met objectpath
        _user_data = {
            'persoon': {
                'geboortedatum': '1950-01-01T00:00:00Z'
            },
            'foo': _test_data
        }

        self.test_data = objectpath.Tree(_test_data)
        self.user_data = objectpath.Tree(_user_data)
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
        
        stadspas_rule = "$.focus.*[@.soortProduct is 'Minimafonds' and @.typeBesluit is 'Toekenning']"

        rules = [{"type": "rule", "rule": "$.focus.*[@.soortProduct is 'Minimafonds' and @.typeBesluit is 'Toekenning']"}]
        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_is_18(self):
        is_18_rule = "dateTime($.brp.persoon.geboortedatum) - timeDelta(18, 0, 0, 0, 0, 0) <= now()"
        rules = [{"type": "rule", "rule": "dateTime($.brp.persoon.geboortedatum) - timeDelta(18, 0, 0, 0, 0, 0) <= now()"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_woont_in_gemeente_Amsterdam(self):
        woont_amsterdam_rule = "$.brp.persoon.mokum is true"
        rules = [{"type": "rule", "rule": "$.brp.persoon.mokum is true"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_heeft_kinderen(self):
        heeft_kinderen_rule = "$.brp.kinderen is true"
        rules = [{"type": "rule", "rule": "$.brp.kinderen is true"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_is_ingeschreven_in_Amsterdam(self):
        ingeschreven_amsterdam_rule = "$.brp@gemeentenaamInschrijving is Amsterdam"
        rules = [{"type": "rule", "rule": "$.brp@gemeentenaamInschrijving is Amsterdam"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_kind_is_tussen_2_en_18_jaar(self):
        kind_tussen_2_en_18_rule = "dateTime($.brp.kinderen.geboortedatum) - timeDelta(2, 0, 0, 0, 0, 0) => now() and dateTime($.brp.kinderen.geboortedatum) - timeDelta(18, 0, 0, 0, 0, 0) <= now()"
        rules = [{"type": "rule", "rule": "dateTime($.brp.kinderen.geboortedatum) - timeDelta(2, 0, 0, 0, 0, 0) => now() and dateTime($.brp.kinderen.geboortedatum) - timeDelta(18, 0, 0, 0, 0, 0) <= now()"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_kind_is_op_30_september_2020_geen_18(self):
        kind_op_30_september_2020_geen_18_rule = "dateTime($.brp.kinderen.geboortedatum) + timeDelta(18, 0, 0, 0, 0, 0) > dateTime($.info)"
        rules = [{"type": "rule", "rule": "dateTime($.brp.kinderen.geboortedatum) + timeDelta(18, 0, 0, 0, 0, 0) > dateTime($.info)"}]

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))