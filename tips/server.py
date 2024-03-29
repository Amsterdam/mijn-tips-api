import connexion
import sentry_sdk
import os
import json

from tips.config import PROJECT_PATH
from flask import request, send_from_directory
from sentry_sdk.integrations.flask import FlaskIntegration

from tips.api.tip_generator import tips_generator
from tips.config import get_sentry_dsn, get_photo_path

app = connexion.FlaskApp(__name__, specification_dir="api/")

if get_sentry_dsn():  # pragma: no cover
    sentry_sdk.init(
        dsn=get_sentry_dsn(),
        integrations=[FlaskIntegration()],
        with_locals=False,
        request_bodies="never",
    )


def get_tips_request_data(request_data):
    user_data = {}
    source_tips = []
    optin = False

    if "userData" in request_data:
        user_data = request_data["userData"]

    if "tips" in request_data:
        source_tips = request_data["tips"]

    if "optin" in request_data and type(request_data["optin"]) is bool:
        optin = request_data["optin"]

    return {"optin": optin, "user_data": user_data, "source_tips": source_tips}


# Route is defined in openapi.yaml
def get_tips():
    # This is a POST because the user data gets sent in the body.
    # This data is too large and inappropriate for a GET, also because of privacy reasons
    audience = request.args.get("audience", None)
    if audience:
        audience = audience.split(",")

    request_data = get_tips_request_data(request_data=request.get_json())
    tips_data = tips_generator(request_data, audience=audience)

    return tips_data


@app.route("/tips/static/tip_images/<path:filename>")
def download_file(filename):
    return send_from_directory(get_photo_path(), filename, as_attachment=True)


@app.route("/status/health")
def health_check():
    return "OK"


app.add_api("openapi.yaml")

# set the WSGI application callable to allow using uWSGI:
application = app.app
if __name__ == "__main__":  # pragma: no cover
    app.run()
