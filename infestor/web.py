import os
import random

from flask import Flask, render_template, request, g
from lighthive.client import Client as LightSteemClient
from lighthive.helpers.account import Account
from steemconnect.client import Client as ScClient
from .main import Infestor
from .utils import username_is_valid, generate_random_password, generate_keys

app = Flask(__name__)
app.debug = True
INFESTOR_CREATOR_ACCOUNT = os.getenv('INFESTOR_CREATOR_ACCOUNT')
INFESTOR_ACTIVE_KEY = os.getenv('INFESTOR_ACTIVE_KEY')
INFESTOR_MONGO_URI = os.getenv("INFESTOR_MONGO_URI", "localhost")
SC_CLIENT_ID = os.getenv("INFESTOR_SC_CLIENT_ID", "infestor.app")
SC_SECRET = os.getenv("INFESTOR_SC_SECRET")
SITE_URL = os.getenv("INFESTOR_SITE_URL", "http://localhost:8000")
MINIMUM_REP = os.getenv("INFESTOR_MINIMUM_REP", "60")
OPERATOR_WITNESS = os.getenv("INFESTOR_OPERATOR_WITNESS", "emrebeyler")


@app.before_request
def set_lightsteem_client():
    g.lightsteem_client = LightSteemClient()
    g.infestor = Infestor(
        INFESTOR_CREATOR_ACCOUNT,
        mongodb_connection_uri=INFESTOR_MONGO_URI)
    g.operator_witness = OPERATOR_WITNESS
    g.minimum_rep = int(MINIMUM_REP)
    if os.getenv('INFESTOR_FOOTER_TEMPLATE'):
        with open(os.getenv('INFESTOR_FOOTER_TEMPLATE'), 'r') as f:
            g.footer = f.read()

    if not INFESTOR_ACTIVE_KEY or not INFESTOR_CREATOR_ACCOUNT:
        raise RuntimeError("Missing environment variables: "
                           "INFESTOR_CREATOR_ACCOUNT, INFESTOR_ACTIVE_KEY ")


@app.route('/', methods=["GET", "POST"])
def index():
    creator_account = g.lightsteem_client.get_accounts(
        [INFESTOR_CREATOR_ACCOUNT])[0]

    if creator_account["pending_claimed_accounts"] == 0:
        return "Free account pool is exhausted. Please, try again later on."

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
            error = "Error while broadcasting the create_claimed_account " \
                    "transaction"
            defaults.update({
                "error": error,
            })
            return render_template(
                "create_account.html",
                **defaults
            )

        g.infestor.gift_code_manager.mark_code_as_used(gift_code)
        return render_template("success.html", **defaults)


@app.route('/login', methods=["GET"])
def login():
    sc_client = ScClient(
        client_id=SC_CLIENT_ID,
        client_secret=SC_SECRET,
        oauth_base_url="https://hivesigner.com/oauth2/",
        sc2_api_base_url="https://hivesigner.com/api/")
    login_url = sc_client.get_login_url(
        f"{SITE_URL}/gift-codes",
        "login",
    )
    return render_template("login.html", login_url=login_url)


@app.route('/gift-codes/', methods=["GET"])
def gift_codes():
    sc_client = ScClient(
        access_token=request.args.get("access_token"),
        oauth_base_url="https://hivesigner.com/oauth2/",
        sc2_api_base_url="https://hivesigner.com/api/"
    )
    me = sc_client.me()
    if 'error' in me:
        return "Invalid access token"

    # if the user already claimed their gift codes,
    # then there is no need to create new gift codes
    if g.infestor.gift_code_manager.get_gift_code_count_by_user(
            me["account"]["name"]) > 0:
        gift_codes = g.infestor.gift_code_manager.get_gift_codes_by_user(
            me["account"]["name"]
        )
        return render_template("gift_codes.html", user=me,
                               gift_codes=gift_codes)

    # quick hack
    # no need to fill all account data into Lighthive.helpers.Account
    # since all we're interested in is reputation figure.
    acc = Account(client=g.lightsteem_client)
    acc.raw_data = {"reputation": me["account"]["reputation"]}

    gift_code_count = 0
    if acc.reputation() < g.minimum_rep:
        error = "Your reputation is not enough to claim a free account."
        return render_template("gift_codes.html", error=error)
    else:
        gift_code_count += 1
        # check if the account is eligible for the bonus
        if OPERATOR_WITNESS in me["account"]["witness_votes"]:
            gift_code_count += 1

    # create gift_codes based on the *gift_code_count*
    for i in range(gift_code_count):
        code = random.randint(1000000, 999999999)
        g.infestor.gift_code_manager.add_code(
            code, created_for=me["account"]["name"])
    gift_codes = g.infestor.gift_code_manager.get_gift_codes_by_user(
        me["account"]["name"])

    return render_template(
        "gift_codes.html", user=me, gift_codes=gift_codes, error=None)
