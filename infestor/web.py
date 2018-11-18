import os

from flask import Flask, render_template, request, g
from lightsteem.client import Client as LightSteemClient

from .main import Infestor
from .utils import username_is_valid, generate_random_password, generate_keys

app = Flask(__name__)
INFESTOR_CREATOR_ACCOUNT = os.getenv('INFESTOR_CREATOR_ACCOUNT')
INFESTOR_ACTIVE_KEY = os.getenv('INFESTOR_ACTIVE_KEY')
INFESTOR_MONGO_URI = os.getenv("INFESTOR_MONGO_URI", "localhost")


@app.before_request
def set_lightsteem_client():
    g.lightsteem_client = LightSteemClient()
    g.infestor = Infestor(
        INFESTOR_CREATOR_ACCOUNT,
        mongodb_connection_uri=INFESTOR_MONGO_URI)

    if not INFESTOR_ACTIVE_KEY or not INFESTOR_CREATOR_ACCOUNT:
        raise RuntimeError("Missing environment variables: "
                           "INFESTOR_CREATOR_ACCOUNT, INFESTOR_ACTIVE_KEY ")


@app.route('/', methods=["GET", "POST"])
def index():
    gift_code = request.form.get(
        "gift_code", request.args.get("gift_code", ""))
    username = request.form.get("username", "")

    defaults = {
        "gift_code": gift_code,
        "username": username,
    }

    if request.method == 'GET':
        if gift_code:
            # validate the gift code from internal mongo database
            if not g.infestor.gift_code_manager.code_is_valid(gift_code):
                defaults.update({"error": "Invalid gift code."})
                return render_template(
                    "create_account.html",
                    **defaults
                )
        return render_template(
            "create_account.html",
            **defaults
        )
    else:

        # validate the gift code from internal mongo database
        if not g.infestor.gift_code_manager.code_is_valid(gift_code):
            defaults.update({"error": "Invalid gift code."})
            return render_template(
                "create_account.html",
                **defaults
            )

        # check the username is a valid username
        if not username_is_valid(defaults.get("username")):
            error = "Invalid username"
            defaults.update({"error": error})
            return render_template(
                "create_account.html",
                **defaults
            )

        # check the username is already taken
        if len(g.lightsteem_client.get_accounts([defaults.get("username")])):
            error = "Username is already taken."
            defaults.update({"error": error})
            return render_template(
                "create_account.html",
                **defaults
            )

        # generate the random password and keys
        password = generate_random_password()
        keys = generate_keys(username, password, exclude_master=True)

        # attach active key of the creator to the lightsteem client
        g.lightsteem_client.keys = [INFESTOR_ACTIVE_KEY, ]

        op = g.infestor._prepare_create_claimed_account_operation(
            username,
            keys,
        )

        defaults.update({
            "password": password,
            "keys": keys,
        })

        try:
            g.lightsteem_client.broadcast(op)
        except Exception as e:
            print(e)
            error = "roadcasting the create_claimed_account transaction"
            defaults.update({
                "error": error,
            })
            return render_template(
                "create_account.html",
                **defaults
            )

        g.infestor.gift_code_manager.mark_code_as_used(gift_code)
        return render_template("success.html", **defaults)


@app.route('/success')
def success():
    return render_template("success.html")
