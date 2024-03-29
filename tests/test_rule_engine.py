import json
import os
from unittest import TestCase

from tips.api.user_data_tree import UserDataTree
from tips.config import PROJECT_PATH
from tips.generator.rule_engine import apply_rules

COMPOUND_RULES_FILE = os.path.join(PROJECT_PATH, "api", "compound_rules.json")


def get_compound_rules():
    with open(COMPOUND_RULES_FILE) as compound_rules_file:
        compound_rules = json.load(compound_rules_file)
        compound_rules_file.close()
    return compound_rules


compound_rules = get_compound_rules()


class RuleEngineTest(TestCase):
    def setUp(self) -> None:
        _test_data = {
            "a": [1, 2, 3],
            "b": [
                {"x": True, "y": True},
                {"x": True, "y": False},
                {"x": False, "y": True},
            ],
        }

        self.test_data = UserDataTree(_test_data)

    def test_apply_rules_simple(self):
        rules = [{"type": "rule", "rule": "2 > 1"}]
        compound_rules = {}

        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

        rules = [
            {"type": "rule", "rule": "2 > 1"},
            {"type": "rule", "rule": "false"},
        ]
        self.assertFalse(apply_rules(self.test_data, rules, compound_rules))

    def test_apply_rules_nested(self):
        compound_rules = {
            "1": {"name": "rule 1", "rules": [{"type": "rule", "rule": "true"}]},
            "2": {"name": "rule 2", "rules": [{"type": "ref", "ref_id": "1"}]},
        }

        rules = [{"type": "ref", "ref_id": "1"}]
        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

        rules = [{"type": "ref", "ref_id": "1"}]
        self.assertTrue(apply_rules(self.test_data, rules, compound_rules))

    def test_apply_rules_recursing(self):
        compound_rules = {
            "1": {"name": "rule 1", "rules": [{"type": "ref", "ref_id": "2"}]},
            "2": {"name": "rule 2", "rules": [{"type": "ref", "ref_id": "1"}]},
        }
        rules = [{"type": "ref", "ref_id": "1"}]
        with self.assertRaises(RecursionError):
            apply_rules(self.test_data, rules, compound_rules)

        # self referencing
        compound_rules = {
            "1": {"name": "rule 1", "rules": [{"type": "ref", "ref_id": "1"}]}
        }
        rules = [{"type": "ref", "ref_id": "1"}]
        with self.assertRaises(RecursionError):
            apply_rules(self.test_data, rules, compound_rules)

    def test_objectpath_assertions(self):
        rules = [{"type": "rule", "rule": "$.BRP.kinderen"}]

        data = {"BRP": {"kinderen": []}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), False)

        data = {"BRP": {"kinderen": None}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), False)

        data = {"BRP": {"kinderen": ["kind1"]}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), True)

        data = {"BRP": {"kinderen": ""}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), False)

        data = {"BRP": {"kinderen": "ja"}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), True)

        data = {"BRP": {"kinderen": 0}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), False)

        data = {"BRP": {"kinderen": 1}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), True)

        rules = [{"type": "rule", "rule": "len($.BRP.kinderen) is 0"}]

        data = {"BRP": {"kinderen": []}}

        self.assertEqual(apply_rules(UserDataTree(data), rules, {}), True)
