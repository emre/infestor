import getpass
import logging
import sys

from lightsteem.client import Client
from lightsteem.datastructures import Operation

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

    def __init__(self, creator):
        self.creator = creator
        self.client = self.get_client_instance()

    def get_client_instance(self, keys=None):
        return Client(keys=keys)

    def claim_account(self):
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

        active_key = getpass.getpass("Creator account's active key?")

        self.client.keys = [active_key, ]
        self.client.broadcast(self._prepare_claim_account_operation())

        pending_claimed_accounts = self.client.account(
            self.creator).raw_data["pending_claimed_accounts"]

        print(f"Success! {self.creator} have {pending_claimed_accounts} "
              f"pending claimed accounts, now.")


if __name__ == '__main__':
    infestor = Infestor('emrebeyler')
    # infestor.claim_account()
    # infestor.create_claimed_account('test-user', 'test-pass')
