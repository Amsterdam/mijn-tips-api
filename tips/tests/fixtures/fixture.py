import json
import os

_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# these fixtures are copied from the frontend
BRP = os.path.join(_FIXTURE_PATH, "brp.json")
FOCUS_AANVRAGEN = os.path.join(_FIXTURE_PATH, "focus_aanvragen.json")
FOCUS_TOZO = os.path.join(_FIXTURE_PATH, "focus_tozo.json")
WMO = os.path.join(_FIXTURE_PATH, "wmo.json")
BELASTING = os.path.join(_FIXTURE_PATH, "belasting.json")
ERFPACHT = os.path.join(_FIXTURE_PATH, "erfpacht.json")


def get_fixture(optin=False):
    with open(BRP) as brp_file:
        brp = json.load(brp_file)

    with open(FOCUS_AANVRAGEN) as focus_file:
        focus_aanvragen = json.load(focus_file)

    with open(FOCUS_TOZO) as focus_tozo_file:
        focus_tozo = json.load(focus_tozo_file)

    with open(WMO) as wmo_file:
        wmo = json.load(wmo_file)

    with open(BELASTING) as belasting_file:
        belasting = json.load(belasting_file)

    with open(ERFPACHT) as erfpacht_file:
        erfpacht = json.load(erfpacht_file)

    return {
        "optin": optin,
        "tips": belasting['tips'],
        "userData": {
            "BRP": brp,
            "FOCUS_AANVRAGEN": focus_aanvragen,
            "FOCUS_TOZO": focus_tozo,
            "WMO": wmo,
            "BELASTINGEN": belasting,
            "ERFPACHT": erfpacht
        }
    }
