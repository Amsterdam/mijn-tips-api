from tips.api.user_data_tree import UserDataTree
from unittest import TestCase

from freezegun import freeze_time

from tips.api.tip_generator import (
    tip_filter,
    tips_generator,
    fix_id,
    format_tip,
    format_source_tips,
    FRONT_END_TIP_KEYS,
)
from tips.tests.fixtures.fixture import get_fixture, get_fixture_without_source_tips
from tips.server import get_tips_request_data

_counter = 0


def get_tip(priority=50):
    global _counter
    counter = _counter
    _counter += 1
    return {
        "id": f"test-{counter}",
        "active": True,
        "priority": priority,
        "datePublished": "2019-07-24",
        "audience": [],
        "description": "Tip description %i" % counter,
        "link": {"title": "Tip link title %i" % counter, "to": "https://amsterdam.nl/"},
        "title": "Tip title %i" % counter,
        "imgUrl": "/api/tips/static/tip_images/erfpacht.jpg",
        "reason": ["The reason for this Tip to appear", "and more"],
    }


def new_rule(rule: str):
    return {"type": "rule", "rule": rule}


class TipsGeneratorTest(TestCase):
    def setUp(self) -> None:
        pass

    def get_client_data(self):
        return get_tips_request_data(get_fixture_without_source_tips())

    def test_allow_listed_fields(self):
        tip1_mock = get_tip()
        tip2_mock = get_tip()
        tip1_mock["isPersonalized"] = True
        tip2_mock["isPersonalized"] = True
        tips_pool = [tip1_mock, tip2_mock]

        tips = tips_generator(get_tips_request_data(get_fixture(optin=True)), tips_pool)

        # only these fields are allowed
        extended_fields_list = sorted(FRONT_END_TIP_KEYS)

        fields = sorted(tips[0].keys())
        self.assertEqual(extended_fields_list, fields)

        fields = sorted(tips[1].keys())
        self.assertEqual(extended_fields_list, fields)

    def test_generator(self):
        tip0 = get_tip(10)
        tip1 = get_tip(20)
        tip2 = get_tip(30)
        tip3 = get_tip(40)
        tip4 = get_tip(50)

        tip4["rules"] = [new_rule("False")]

        # add them out of order to test the ordering
        tips_pool = [tip1, tip0, tip2, tip3, tip4]
        tips = tips_generator(self.get_client_data(), tips_pool)

        self.assertEqual(len(tips), 4)

        # check order
        self.assertEqual(tips[3]["id"], tip0["id"])
        self.assertEqual(tips[2]["id"], tip1["id"])
        self.assertEqual(tips[1]["id"], tip2["id"])
        self.assertEqual(tips[0]["id"], tip3["id"])


class ConditionalTest(TestCase):
    def get_client_data(self, optin=False):
        return get_tips_request_data(get_fixture_without_source_tips(optin))

    def test_active(self):
        """Add one active and one inactive tip."""

        tip1_mock = get_tip()
        tip1_mock["active"] = False
        tip2_mock = get_tip()

        tips_pool = [tip1_mock, tip2_mock]

        tips = tips_generator(self.get_client_data(), tips_pool)
        self.assertEqual(len(tips), 1)

        # Test if the correct ones are accepted
        ids = [tip["id"] for tip in tips]
        self.assertEqual(ids, [tip2_mock["id"]])

    def test_conditional(self):
        """Test one passing conditional, one failing and one without (the default)"""
        tip1_mock = get_tip()
        tip1_mock["rules"] = [new_rule("false")]
        tip2_mock = get_tip()
        tip2_mock["rules"] = [new_rule("true")]
        tip3_mock = get_tip()

        tips_pool = [tip1_mock, tip2_mock, tip3_mock]
        tips = tips_generator(self.get_client_data(), tips_pool)
        self.assertEqual(len(tips), 2)

        # Test if the correct ones are accepted
        ids = [tip["id"] for tip in tips]
        self.assertEqual(ids, [tip2_mock["id"], tip3_mock["id"]])

    def test_conditional_exception(self):
        """Test that invalid conditional is (silently) ignored. Probably not the best idea..."""
        tip1_mock = get_tip()
        tip1_mock["rules"] = [new_rule("@")]
        tip2_mock = get_tip()

        tips_pool = [tip1_mock, tip2_mock]
        tips = tips_generator(self.get_client_data(), tips_pool)

        # make sure the other is in there
        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["id"], tip2_mock["id"])

    def test_conditional_invalid(self):
        """Test that it errors on completely wrong conditional."""
        tip1_mock = get_tip()
        tip1_mock["rules"] = new_rule("true")
        tip2_mock = get_tip()

        tips_pool = [tip1_mock, tip2_mock]
        with self.assertRaises(TypeError):
            tips_generator(self.get_client_data(), tips_pool)

    def test_data_based_tip(self):
        """
        Test whether a tip works correctly when based on user data.
        """
        tip1_mock = get_tip()
        tip1_mock["rule"] = [new_rule("$.ERFPACHT.isKnown is true")]
        tip1_mock["isPersonalized"] = True
        tip2_mock = get_tip()
        tips_pool = [tip1_mock, tip2_mock]

        client_data = self.get_client_data(optin=True)

        tips = tips_generator(client_data, tips_pool)

        # make sure the other is in there
        self.assertEqual(len(tips), 1)

    def test_data_based_tip_path(self):
        tip1_mock = get_tip()
        tip1_mock["rules"] = [new_rule("$.ERFPACHT.isKnown is true")]
        tip1_mock["isPersonalized"] = True
        tip2_mock = get_tip()
        # 18 or older
        tip2_mock["rules"] = [{"type": "ref", "ref_id": "2"}]
        tip2_mock["isPersonalized"] = True
        tips_pool = [tip1_mock, tip2_mock]

        client_data = self.get_client_data(optin=True)

        tips = tips_generator(client_data, tips_pool)

        # make sure the other is in there
        self.assertEqual(len(tips), 2)
        self.assertEqual(tips[0]["id"], tip1_mock["id"])
        self.assertEqual(tips[0]["isPersonalized"], True)
        self.assertEqual(tips[1]["id"], tip2_mock["id"])
        self.assertEqual(tips[0]["isPersonalized"], True)

    def test_data_based_tip_with_list(self):
        tip1_mock = get_tip()
        tip1_mock["rules"] = [
            new_rule(
                "$.FOCUS_AANVRAGEN[@.id is '810805911' and @.steps.*[@.id is 'aanvraag']]"
            )
        ]
        tip1_mock["isPersonalized"] = True
        tips_pool = [tip1_mock]

        client_data = self.get_client_data(optin=True)
        tips = tips_generator(client_data, tips_pool)

        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["id"], tip1_mock["id"])
        self.assertEqual(tips[0]["isPersonalized"], True)

    def test_is_personalized_optin(self):
        tip1_mock = get_tip()
        tip1_mock["rules"] = [new_rule("True")]
        tip1_mock["isPersonalized"] = True

        tip2_mock = get_tip()
        tip2_mock["rules"] = [new_rule("True")]
        # do not add isPersonalized to tip 2. It should default to False
        tips_pool = [tip1_mock, tip2_mock]

        tips = tips_generator(self.get_client_data(True), tips_pool)

        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["isPersonalized"], True)

    def test_is_personalized_no_optin(self):
        tip1_mock = get_tip()
        tip1_mock["rules"] = [new_rule("True")]
        tip1_mock["isPersonalized"] = True

        tip2_mock = get_tip()
        tips_pool = [tip1_mock, tip2_mock]

        tips = tips_generator(self.get_client_data(), tips_pool)

        self.assertEqual(len(tips), 1)
        self.assertEqual(tips[0]["id"], tip2_mock["id"])

    def test_audience(self):
        tip1_mock = get_tip()
        tip1_mock["audience"] = ["zakelijk"]

        tips_pool = [tip1_mock]

        tips = tips_generator(self.get_client_data(), tips_pool, audience=["zakelijk"])
        self.assertEqual(len(tips), 1)

        tips = tips_generator(
            self.get_client_data(), tips_pool, audience=["somethingelse"]
        )
        self.assertEqual(len(tips), 0)

        # should not take audience into account when its not passed in
        tips = tips_generator(self.get_client_data(), tips_pool)
        self.assertEqual(len(tips), 1)

    @freeze_time("2021-03-15")
    def test_active_date(self):
        tip1_mock = get_tip()

        def test_start_end(start_date: str, end_date: str, expected: bool):
            tip1_mock["dateActiveStart"] = start_date
            tip1_mock["dateActiveEnd"] = end_date

            tips_pool = [tip1_mock]

            tips = tips_generator(self.get_client_data(), tips_pool)
            if expected:
                self.assertEqual(len(tips), 1)
            else:
                self.assertEqual(len(tips), 0)

        # current time is between start and end
        test_start_end("2021-03-14", "2021-03-16", True)  # between
        test_start_end("2021-03-15", "2021-03-16", True)  # start is on today
        test_start_end("2021-03-14", "2021-03-15", True)  # end is on today
        test_start_end("2021-03-12", "2021-03-14", False)  # start and end before today
        test_start_end("2021-03-16", "2021-03-17", False)  # start and end after today


class SourceTipsTests(TestCase):
    def setUp(self) -> None:
        pass

    def test_format_source_tips(self):
        source_tips = [
            {"id": "source1-1", "rules": ["true"]},
            {"id": "foo-1", "rules": ["new_rule('print(\"something\")')"]},
            {"id": "foo-2"},
        ]

        result = format_source_tips(source_tips)

        # make sure they are all picked up
        self.assertEqual(result[0]["id"], "source1-1")
        self.assertEqual(result[1]["id"], "foo-1")
        self.assertEqual(result[2]["id"], "foo-2")

        # make sure the conditional is removed
        self.assertNotIn("rules", result[0])
        self.assertNotIn("rules", result[1])
        self.assertNotIn("rules", result[2])

    def test_format_tip(self):
        # test all the fill cases
        result = format_tip({})
        expected = {
            "id": None,
            "active": True,
            "priority": None,
            "datePublished": None,
            "title": None,
            "description": None,
            "link": {"title": None, "to": None},
            "imgUrl": None,
            "reason": [],
            "isPersonalized": True,
        }
        self.assertEqual(expected, result)

        # test with extra data
        tip = {"id": 1, "foo": "bar"}
        result = format_tip(tip)
        self.assertEqual(tip["id"], 1)
        self.assertNotIn("foo", result)

    def test_fix_id(self):
        belasting_tip = {
            "id": 1,
            "title": "foo",
        }
        fix_id(belasting_tip, "BELASTINGEN")
        self.assertEqual(belasting_tip["id"], "belasting-1")

        other_tip = {
            "id": "1",
            "title": "bar",
        }
        fix_id(other_tip, "something else")
        self.assertEqual(other_tip["id"], "1")

    def test_tip_filter(self):
        tip1 = {"isPersonalized": True}
        optin = False

        showTip = tip_filter(tip1, UserDataTree({}), optin)

        self.assertEqual(showTip, False)

        tip1 = {"isPersonalized": False, "active": True}

        showTip = tip_filter(tip1, UserDataTree({}), False)

        self.assertEqual(showTip, True)

        optin = True
        tip1 = {"isPersonalized": True, "active": False}

        showTip = tip_filter(tip1, UserDataTree({}), optin)

        self.assertEqual(showTip, False)

        optin = True
        tip1 = {"isPersonalized": True, "active": True}

        showTip = tip_filter(tip1, UserDataTree({}), optin)

        self.assertEqual(showTip, True)
