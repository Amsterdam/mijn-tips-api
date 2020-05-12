from unittest import TestCase

import objectpath

from tips.generator.rule_engine import apply_rules

from tips.tests.fixtures.fixture import get_fixture


tips_pool = [
    {
        "id": "mijn-1",
        "active": True,
        "priority": 50,
        "datePublished": "2019-07-24",
        "title": "Geen telefoon op de fiets",
        "description": "U mag geen telefoon meer vasthouden op de fiets",
        "link": {
            "title": "Meer informatie",
            "to": "https://www.rijksoverheid.nl/onderwerpen/fiets/vraag-en-antwoord/mag-ik-bellen-en-naar-muziek-luisteren-op-de-fiets"
        },
        "imgUrl": "api/tips/static/tip_images/bellenopfiets.jpg"

    },
    {
        "id": "mijn-11",
        "active": True,
        "priority": 70,
        "datePublished": "2019-10-22",
        "title": "Wat kan ik doen met mijn Stadspas?",
        "description": "U hebt een Stadspas",
        "rules": [
            {"type": "ref", "ref_id": "3"},
            {"type": "ref", "ref_id": "1"},
        ],
        "isPersonalized": True,
        "link": {
            "title": "Bekijk de aanbiedingen",
            "to": "https://www.amsterdam.nl/toerisme-vrije-tijd/stadspas/"
        },
        "imgUrl": "/api/tips/static/tip_images/stadspas.jpg"
    }
]



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

    def test_compound_rules(self):
        rules = {}

        print("HDBHDB", compound_rules)

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

