from unittest import TestCase

import objectpath

from tips.generator.rule_engine import apply_rules, get_tips
from tips.tests.fixtures.fixture import get_fixture

import dictquery as dq


def get_fixture_stadspas():
    return {
        "focus": [
            {
                "_id": "1-0",
                "_meest_recent": "beslissing",
                "dienstverleningstermijn": 56,
                "naam": "Stadspas",
                "processtappen": {
                    "aanvraag": {
                        "_id": 0,
                        "datum": "2019-04-08T15:05:52+02:00",
                        "document": []
                    },
                    "beslissing": {
                        "_id": 3,
                        "datum": "2019-04-28T00:00:00+02:00",
                        "document": [],
                        "reden": "Test Stadspas"
                    },
                    "bezwaar": None,
                    "herstelTermijn": None,
                    "inBehandeling": {
                        "_id": 1,
                        "datum": "2019-04-10T15:05:52+02:00",
                        "document": []
                    }
                },
                "soortProduct": "Minimafonds",
                "typeBesluit": "Afwijzing"
            },
            {
                "_id": "1-1",
                "_meest_recent": "beslissing",
                "dienstverleningstermijn": 56,
                "naam": "Stadspas",
                "processtappen": {
                    "aanvraag": {
                        "_id": 0,
                        "datum": "2019-05-08T15:05:52+02:00",
                        "document": [
                            {
                                "$ref": "focus/document?id=4400000013&isBulk=true&isDms=false",
                                "id": 4400000013,
                                "isBulk": True,
                                "isDms": False,
                                "omschrijving": "Aanvraag Stadspas (balie)"
                            }
                        ]
                    },
                    "beslissing": {
                        "_id": 3,
                        "datum": "2019-06-07T15:05:52+02:00",
                        "document": []
                    },
                    "bezwaar": None,
                    "herstelTermijn": {
                        "_id": 2,
                        "aantalDagenHerstelTermijn": "20",
                        "datum": "2019-05-17T15:05:52+02:00",
                        "document": []
                    },
                    "inBehandeling": {
                        "_id": 1,
                        "datum": "2019-05-10T15:05:52+02:00",
                        "document": []
                    }
                },
                "soortProduct": "Minimafonds",
                "typeBesluit": "Toekenning"
            }
        ]
    }


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


compound_rules = {
    "1": {
        "name": "Heeft geldige stadspas",
        "rules": [
            {
                'type': 'rule',
                'rule': '$.focus.*[@.soortProduct is "Minimafonds" and @.typeBesluit is "Toekenning"]'
            }
        ]
    },
    "2": {
        "name": "is 18",
        "rules": [
            {
                'type': 'rule',
                'rule': 'age($.brp.persoon.geboortedatum)).years > 18'
            }
        ]
    },
    "3": {
        "name": "Leeft nog",
        "rules": [
            {
                'type': 'rule',
                'rule': 'true'
            }
        ]
    }
}


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


class RuleEngineTestRealLifeData(TestCase):
    def setUp(self) -> None:
        pass

    def test_apply_rules(self):

        # moet hebben: 1 focus entry hebben die voldoen aan:
        #  soortProduct == "Minimafonds"
        #  typeBesluit == "Toekenning"
        #  processtappen.beslissing.datum   minder dan een jaar geleden

        # loopen door de entries, scope setten naar de entry. 1 moet True zijn   <-- nesting
        #   > tests uitvoeren


        userdata = get_fixture_stadspas()

        # tree = objectpath.Tree(userdata)
        # result = tree.execute('$.focus.*[age(dateTime(@.processtappen.beslissing.datum)) ]')
        # result = tree.execute('$.focus.*[@.soortProduct is "Minimafonds" and @.typeBesluit is "Toekenning" and age(dateTime(@.processstappen.beslissing.datum))]')

        # print(result)


        result = get_tips(userdata, tips_pool, compound_rules)
        print("result", result)


        # from pprint import pprint
        # pprint([i for i in result])


