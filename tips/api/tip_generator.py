import json
import os
from datetime import date, datetime
from typing import List

from tips.api.user_data_tree import UserDataTree
from tips.config import PROJECT_PATH
from tips.generator.rule_engine import apply_rules

TIPS_POOL_FILE = os.path.join(PROJECT_PATH, "api", "tips_pool.json")
TIP_ENRICHMENT_FILE = os.path.join(PROJECT_PATH, "api", "tip_enrichments.json")
COMPOUND_RULES_FILE = os.path.join(PROJECT_PATH, "api", "compound_rules.json")

FRONT_END_TIP_KEYS = [
    "datePublished",
    "description",
    "id",
    "link",
    "title",
    "priority",
    "imgUrl",
    "isPersonalized",
    "reason",
    "audience",
]


tips_pool = []
tip_enrichments = []
compound_rules = []


def refresh_tips_pool():
    global tips_pool
    with open(TIPS_POOL_FILE) as fp:
        tips_pool = json.load(fp)
        fp.close()


def refresh_tip_enrichments():
    global tip_enrichments
    with open(TIP_ENRICHMENT_FILE) as fp:
        tip_enrichments = json.load(fp)
        fp.close()


def refresh_compound_rules():
    global compound_rules
    with open(COMPOUND_RULES_FILE) as fp:
        compound_rules = json.load(fp)
        fp.close()


def get_reasoning(tip):
    reasons = []
    reason = tip.get("reason")
    if reason:
        reasons.append(reason)
    rules = tip.get("rules", [])
    for rule in rules:
        if rule["type"] == "ref":
            reasons.extend(get_reasoning(compound_rules[rule["ref_id"]]))

    return reasons


refresh_tips_pool()
refresh_tip_enrichments()
refresh_compound_rules()

for tip in tips_pool:
    reason = tip.get("reason")

    # if tip has a reason, only use that one.
    if reason:
        tip["reason"] = [reason]
        continue

    # recursively built reasons
    reasons = get_reasoning(tip)
    tip["reason"] = reasons


def tip_filter(tip, userdata_tree, optin: bool = False):
    """
    If tip has a field "rules", the result must be true for it to be included.
    If tip does not have "rules, it is included.
    """

    # Return early if basic conditions are not met
    # Don't process personalized tips if optin doesn't match the personalization key of the tip
    if not tip.get("alwaysVisible", False):
        if optin != tip["isPersonalized"]:
            return False

    if not tip["active"]:
        return False

    today = date.today()

    if tip.get("dateActiveStart"):
        date_active_start = datetime.strptime(tip["dateActiveStart"], "%Y-%m-%d").date()
        if date_active_start > today:
            return False

    if tip.get("dateActiveEnd"):
        date_active_end = datetime.strptime(tip["dateActiveEnd"], "%Y-%m-%d").date()
        if date_active_end < today:
            return False

    # No need to process tips that don't have rules, we can safely show them
    if "rules" not in tip:
        return True

    passed = apply_rules(userdata_tree, tip["rules"], compound_rules)

    return passed


def normalize_tip_output(tip):
    """Only select the relevant frontend fields."""

    # Only add fields which are allowed to go to the frontend
    return {k: v for (k, v) in tip.items() if k in FRONT_END_TIP_KEYS}


def normalize_tip_personalization(tip):
    if not tip.get("isPersonalized", False):
        tip["isPersonalized"] = False
    return tip


def fix_id(tip, source):
    """Some of our data sources do not follow our id guidelines, fix the tip here inplace."""
    if source == "BELASTINGEN":
        tip["id"] = f"belasting-{tip['id']}"


def format_tip(tip):
    """Make sure the tip has all the required fields.
    no audience by default.
    """
    if "link" in tip:
        link_data = tip["link"]
        link = {"title": link_data.get("title"), "to": link_data.get("to")}
    else:
        link = {"title": None, "to": None}

    reason = []
    if tip.get("reason"):
        reason.append(tip["reason"])

    return {
        "id": tip.get("id"),
        "active": True,
        "priority": tip.get("priority"),
        "datePublished": tip.get("datePublished"),
        "title": tip.get("title"),
        "description": tip.get("description"),
        "link": link,
        "imgUrl": tip.get("imgUrl"),
        "reason": reason,
        "isPersonalized": True,
    }


def format_source_tips(source_tips=None):
    """If the data from the client has source tips, return them as a list"""
    if source_tips is None:
        source_tips = []

    # make sure they follow the format
    source_tips = [format_tip(tip) for tip in source_tips]

    # remove any conditionals because of security
    for tip in source_tips:
        if "conditional" in tip:
            del tip["conditional"]

    return source_tips


def apply_enrichment(tip, enrichment):
    for key, value in enrichment["fields"].items():
        tip[key] = value


def enrich_tip(tip):
    for enrichment in tip_enrichments:
        if tip["id"] in enrichment["for_ids"]:
            apply_enrichment(tip, enrichment)
            break  # only one enrichment per tip allowed


def tips_generator(request_data=None, tips=None, audience: List[str] = None):
    """Generate tips."""
    if request_data is None:
        request_data = {}

    if tips is None:
        tips = tips_pool

    # add source tips
    if request_data["source_tips"]:
        tips = tips + format_source_tips(request_data["source_tips"])

    tips = [normalize_tip_personalization(tip) for tip in tips]

    if request_data["optin"]:
        user_data_prepared = UserDataTree(request_data["user_data"])
    else:
        user_data_prepared = UserDataTree({})

    for tip in tips:
        enrich_tip(tip)

    if audience:
        tips = [
            tip
            for tip in tips
            if set(tip.get("audience", [])).intersection(set(audience))
        ]

    tips = [
        tip
        for tip in tips
        if tip_filter(tip, user_data_prepared, request_data["optin"])
    ]

    tips = [normalize_tip_output(tip) for tip in tips]

    tips.sort(key=lambda t: t["priority"], reverse=True)

    return tips
