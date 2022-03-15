import json
import os

_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# these fixtures are copied from the frontend
BRP = os.path.join(_FIXTURE_PATH, "brp.json")
WPI_AANVRAGEN = os.path.join(_FIXTURE_PATH, "wpi_aanvragen.json")
WPI_TOZO = os.path.join(_FIXTURE_PATH, "wpi_tozo.json")
WPI_TONK = os.path.join(_FIXTURE_PATH, "wpi_tonk.json")
WPI_STADSPAS = os.path.join(_FIXTURE_PATH, "wpi_stadspas.json")
WMO = os.path.join(_FIXTURE_PATH, "wmo.json")
BELASTING = os.path.join(_FIXTURE_PATH, "belasting.json")
ERFPACHT = os.path.join(_FIXTURE_PATH, "erfpacht.json")
VERGUNNINGEN = os.path.join(_FIXTURE_PATH, "vergunningen.json")
TOERISTISCHE_VERHUUR = os.path.join(_FIXTURE_PATH, "toeristische_verhuur.json")


def get_fixture(optin=False):
    with open(BRP) as brp_file:
        brp = json.load(brp_file)
        brp_file.close()

    with open(WPI_AANVRAGEN) as wpi_file:
        wpi_aanvragen = json.load(wpi_file)
        wpi_file.close()

    with open(WPI_TOZO) as wpi_tozo_file:
        wpi_tozo = json.load(wpi_tozo_file)
        wpi_tozo_file.close()

    with open(WPI_TONK) as wpi_tonk_file:
        wpi_tonk = json.load(wpi_tonk_file)
        wpi_tonk_file.close()

    with open(WPI_STADSPAS) as wpi_stadspas_file:
        wpi_stadspas = json.load(wpi_stadspas_file)
        wpi_stadspas_file.close()

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
        "tips": belasting["tips"],
        "userData": {
            "BRP": brp,
            "WPI_AANVRAGEN": wpi_aanvragen,
            "WPI_TOZO": wpi_tozo,
            "WPI_TONK": wpi_tonk,
            "WPI_STADSPAS": wpi_stadspas,
            "WMO": wmo,
            "BELASTINGEN": belasting,
            "ERFPACHT": erfpacht,
            "TOERISTISCHE_VERHUUR": toeristische_verhuur,
        },
    }


def get_fixture_without_source_tips(optin=False):
    data = get_fixture(optin)
    data["tips"] = []
    return data
