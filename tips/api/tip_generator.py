import json
import os

from objectpath import Tree

from tips.config import PROJECT_PATH
from tips.generator.rule_engine import apply_rules

TIPS_POOL_FILE = os.path.join(PROJECT_PATH, 'api', 'tips_pool.json')
TIP_ENRICHMENT_FILE = os.path.join(PROJECT_PATH, 'api', 'tip_enrichments.json')
COMPOUND_RULES_FILE = os.path.join(PROJECT_PATH, 'api', 'compound_rules.json')

FRONT_END_TIP_KEYS = ['datePublished', 'description', 'id', 'link', 'title', 'priority', 'imgUrl', 'isPersonalized', 'reason']


tips_pool = []
tip_enrichments = []
compound_rules = []


def refresh_tips_pool():
    global tips_pool
    with open(TIPS_POOL_FILE) as fp:
        tips_pool = json.load(fp)


def refresh_tip_enrichments():
    global tip_enrichments
    with open(TIP_ENRICHMENT_FILE) as fp:
        tip_enrichments = json.load(fp)


def refresh_compound_rules():
    global compound_rules
    with open(COMPOUND_RULES_FILE) as fp:
        compound_rules = json.load(fp)


def get_reasoning(tip):
    reasons = []
    reason = tip.get('reason')
    if reason:
        reasons.append(reason)
    rules = tip.get('rules', [])
    for rule in rules:
        if rule['type'] == 'ref':
            reasons.extend(get_reasoning(compound_rules[rule['ref_id']]))

    return reasons


refresh_tips_pool()
refresh_tip_enrichments()
refresh_compound_rules()

for tip in tips_pool:
    reasons = get_reasoning(tip)
    tip['reason'] = reasons


def tip_filter(tip, userdata_tree):
    """
    If tip has a field "rules", the result must be true for it to be included.
    If tip does not have "rules, it is included.
    """
    if not tip['active']:
        return False
    if 'rules' not in tip:
        return tip

    passed = apply_rules(userdata_tree, tip["rules"], compound_rules)
    return passed


def clean_tip(tip):
    """ Only select the relevant frontend fields and default isPersonalized to False. """
    if not tip.get('isPersonalized', False):
        tip['isPersonalized'] = False
    # Only add fields which are allowed to go to the frontend
    return {k: v for (k, v) in tip.items() if k in FRONT_END_TIP_KEYS}


def fix_id(tip, source):
    """ Some of our data sources do not follow our id guidelines, fix the tip here inplace. """
    if source == "belasting":
        tip['id'] = f"belasting-{tip['id']}"


def format_tip(tip):
    """ Make sure the tip has all the required fields. """
    if "link" in tip:
        link_data = tip["link"]
        link = {
            "title": link_data.get("title"),
            "to": link_data.get("to")
        }
    else:
        link = {"title": None, "to": None}

    return {
        "id": tip.get('id'),
        "active": True,
        "priority": tip.get('priority'),
        "datePublished": tip.get('datePublished'),
        "title": tip.get('title'),
        "description": tip.get('description'),
        "link": link,
        "imgUrl": tip.get("imgUrl")
    }


def get_tips_from_user_data(user_data):
    """ If the data from the client has source tips, return them as a list """
    source_tips = []
    for source, value in user_data['data'].items():
        if type(value) == dict and 'tips' in value:
            for tip in value['tips']:
                fix_id(tip, source)
            source_tips = source_tips + value['tips']

    # make sure they follow the format
    source_tips = [format_tip(tip) for tip in source_tips]

    # remove any conditionals because of security
    for tip in source_tips:
        if 'conditional' in tip:
            del tip['conditional']

    return source_tips


def apply_enrichment(tip, enrichment):
    for key, value in enrichment['fields'].items():
        tip[key] = value


def enrich_tip(tip):
    for enrichment in tip_enrichments:
        if tip['id'] in enrichment['for_ids']:
            apply_enrichment(tip, enrichment)
            break  # only one enrichment per tip allowed


def tips_generator(user_data, tips=None):
    """ Generate tips. """
    if tips is None:
        tips = tips_pool

    # add source tips
    source_tips = get_tips_from_user_data(user_data)
    if source_tips:
        tips = tips + source_tips

    if user_data['optin']:
        user_data_prepared = Tree(user_data['data'])
    else:
        user_data_prepared = Tree({})

    tips = [tip for tip in tips if tip_filter(tip, user_data_prepared)]
    tips = [clean_tip(tip) for tip in tips]
    for tip in tips:
        enrich_tip(tip)

    tips.sort(key=lambda t: t['priority'], reverse=True)

    # if optin is on, only show personalised tips
    if user_data['optin']:
        tips = [t for t in tips if t['isPersonalized']]

    return {
        "items": tips,
        "total": len(tips),
    }
