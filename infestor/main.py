import argparse
import getpass
import logging
import sys

from lightsteem.client import Client
from lightsteem.datastructures import Operation

from .utils import generate_keys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


class Infestor:

    def _prepare_claim_account_operation(self):
        return Operation(
            'claim_account',
            {
                'creator': self.creator,
                'fee': '0.000 STEEM',
                'extensions': [],
            }
        )

    def _prepare_create_claimed_account_operation(self, new_account_name, keys):
        op_data = {
            "creator": self.creator,
            "new_account_name": new_account_name,
            "json_metadata": "",
            "extensions": [],
        }
        for key_type, key_value in keys.items():
            if key_type == "master":
                continue
            if key_type == "memo":
                op_data.update({
                    "memo_key": key_value["public"]
                })
            else:
                op_data.update({
                    key_type: {
                        "account_auths": [],
                        "weight_threshold": 1,
                        "key_auths": [[key_value["public"], 1]],
                        "address_auths": []
                    }
                })

        op = Operation(
            'create_claimed_account',
            op_data,
        )
        return op

    def _get_active_key(self):
        return getpass.getpass("Creator account's active key:\n")

    def _get_new_account_master_key(self):
        return getpass.getpass("Master key for the new account:\n")

    def __init__(self, creator):
        self.creator = creator
        self.client = self.get_client_instance()

    def get_client_instance(self, keys=None):
        return Client(keys=keys)

    def claim_account(self):
        """
        Broadcasts a claim_account operation.
        Creator account's RC and the cost of claim_account's RC is calculated
        beforehand.
        :return:
        """
        print(f"Fetching RC details of {self.creator}")

        creator_account = self.client.account(self.creator)
        pending_claimed_accounts = creator_account.raw_data \
            ["pending_claimed_accounts"]

        rc_details = creator_account.get_resource_credit_info()
        current_mana = rc_details["current_mana"] / 1000000

        cost_of_claim_account = self.client.rc().get_cost(
            self._prepare_claim_account_operation())

        print(f"{self.creator} has {pending_claimed_accounts} "
              f"pending claimed accounts. Claiming an account requires"
              f" {cost_of_claim_account}MM mana, at the moment.")

        print(f"{self.creator} has {int(current_mana)}MM mana available and"
              f" can claim {int(current_mana / cost_of_claim_account)}"
              f" accounts more.")

        if cost_of_claim_account > current_mana:
            print("Stopped. Insufficient mana.", file=sys.stderr)
            sys.exit(-1)

        active_key = self._get_active_key()

        self.client.keys = [active_key, ]
        self.client.broadcast(self._prepare_claim_account_operation())

        pending_claimed_accounts = self.client.account(
            self.creator).raw_data["pending_claimed_accounts"]

        print(f"Success! {self.creator} have {pending_claimed_accounts} "
              f"pending claimed accounts, now.")

    def create_claimed_account(self, new_account_name):
        """
        Creates a discounted claimed account.
        Corresponding private and public keys are generated based on the
        master key.
        """

        if not new_account_name:
            print(
                "Add a --new-account-name <account_name> to the command.",
                file=sys.stderr
            )
            sys.exit(-1)

        active_key = self._get_active_key()
        new_account_master_key = self._get_new_account_master_key()

        # check the username is already exists?
        accounts = self.client.get_accounts([new_account_name])
        if len(accounts):
            print(
                f"{new_account_name} is already exists. Pick another.",
                file=sys.stderr)
            sys.exit(-1)

        keys = generate_keys(new_account_name, new_account_master_key)
        op = self._prepare_create_claimed_account_operation(
            new_account_name, keys)

        creator_account = self.client.account(self.creator)
        rc_details = creator_account.get_resource_credit_info()
        pending_claimed_accounts = creator_account.raw_data \
            ["pending_claimed_accounts"]

        if pending_claimed_accounts == 0:
            print(
                f"Stopped. {self.creator} has 0 pending claimed accounts.",
                file=sys.stderr
            )
            sys.exit(-1)

        current_mana = rc_details["current_mana"] / 1000000
        cost_of_create_account = self.client.rc().get_cost(op)

        if cost_of_create_account > current_mana:
            print("Stopped. Insufficient mana.", file=sys.stderr)
            sys.exit(-1)

        self.client.keys = [active_key, ]
        self.client.broadcast(op)

        print(f"{new_account_name} is successfully created."
              f" Save your passwords:")
        for key, subkeys in keys.items():
            if 'public' in subkeys:
                print(f"Type: {key}")
                print(f"Public: {subkeys['public']}\nPrivate:"
                      f" {subkeys['private']}\n--")
            else:
                print(f"Master Password: {subkeys}\n--")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        help="An action to perform.",
        choices=["claim_account", "create_claimed_account"])
    parser.add_argument(
        '--creator', help="Creator account", required=True)
    parser.add_argument('--new-account-name', help="New account name")

    args = parser.parse_args()

    infestor = Infestor(args.creator)
    if args.action == "claim_account":
        infestor.claim_account()
    else:
        infestor.create_claimed_account(args.new_account_name)


if __name__ == '__main__':
    main()
