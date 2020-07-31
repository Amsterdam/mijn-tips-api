import json
import os

_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# these fixtures are copied from the frontend
BRP = os.path.join(_FIXTURE_PATH, "brp.json")
FOCUS = os.path.join(_FIXTURE_PATH, "focus_aanvragen.json")
WMO = os.path.join(_FIXTURE_PATH, "wmo.json")
BELASTING = os.path.join(_FIXTURE_PATH, "belasting.json")
ERFPACHT = os.path.join(_FIXTURE_PATH, "erfpacht.json")


def get_fixture(optin=False):
    with open(BRP) as brp_file:
        brp = json.load(brp_file)

    with open(FOCUS) as focus_file:
        focus = json.load(focus_file)

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
            "FOCUS_AANVRAGEN": focus,
            "WMO": wmo,
            "BELASTING": belasting,
            "ERFPACHT": erfpacht
        }
    }
