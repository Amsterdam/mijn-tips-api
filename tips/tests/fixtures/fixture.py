import json
import os

_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# these fixtures are copied from the frontend
BRP = os.path.join(_FIXTURE_PATH, "brp.json")
FOCUS_AANVRAGEN = os.path.join(_FIXTURE_PATH, "focus_aanvragen.json")
FOCUS_TOZO = os.path.join(_FIXTURE_PATH, "focus_tozo.json")
FOCUS_TONK = os.path.join(_FIXTURE_PATH, "focus_tonk.json")
FOCUS_STADSPAS = os.path.join(_FIXTURE_PATH, "focus_stadspas.json")
WMO = os.path.join(_FIXTURE_PATH, "wmo.json")
BELASTING = os.path.join(_FIXTURE_PATH, "belasting.json")
ERFPACHT = os.path.join(_FIXTURE_PATH, "erfpacht.json")
VERGUNNINGEN = os.path.join(_FIXTURE_PATH, "vergunningen.json")
TOERISTISCHE_VERHUUR = os.path.join(_FIXTURE_PATH, "toeristische_verhuur.json")


def get_fixture(optin=False):
    with open(BRP) as brp_file:
        brp = json.load(brp_file)
        brp_file.close()

    with open(FOCUS_AANVRAGEN) as focus_file:
        focus_aanvragen = json.load(focus_file)
        focus_file.close()

    with open(FOCUS_TOZO) as focus_tozo_file:
        focus_tozo = json.load(focus_tozo_file)
        focus_tozo_file.close()

    with open(FOCUS_TONK) as focus_tonk_file:
        focus_tonk = json.load(focus_tonk_file)
        focus_tonk_file.close()

    with open(FOCUS_STADSPAS) as focus_stadspas_file:
        focus_stadspas = json.load(focus_stadspas_file)
        focus_stadspas_file.close()

    with open(WMO) as wmo_file:
        wmo = json.load(wmo_file)
        wmo_file.close()

    with open(BELASTING) as belasting_file:
        belasting = json.load(belasting_file)
        belasting_file.close()

    with open(ERFPACHT) as erfpacht_file:
        erfpacht = json.load(erfpacht_file)
        erfpacht_file.close()

    with open(TOERISTISCHE_VERHUUR) as toeristische_verhuur_file:
        toeristische_verhuur = json.load(toeristische_verhuur_file)
        toeristische_verhuur_file.close()

    return {
        "optin": optin,
        "tips": belasting['tips'],
        "userData": {
            "BRP": brp,
            "FOCUS_AANVRAGEN": focus_aanvragen,
            "FOCUS_TOZO": focus_tozo,
            "FOCUS_TONK": focus_tonk,
            "FOCUS_STADSPAS": focus_stadspas,
            "WMO": wmo,
            "BELASTINGEN": belasting,
            "ERFPACHT": erfpacht,
            "TOERISTISCHE_VERHUUR": toeristische_verhuur
        }
    }


def get_fixture_without_source_tips(optin=False):
    data = get_fixture(optin)
    data['tips'] = []
    return data
