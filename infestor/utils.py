import random
import re
import string

from lightsteem.broadcast.key_objects import PasswordKey


def generate_keys(new_account_name, master_key, exclude_master=False):
    keys = {
        "master": master_key,
    }
    if exclude_master:
        keys = {}
    for key_type in ['posting', 'active', 'owner', 'memo']:
        private_key = PasswordKey(
            new_account_name, master_key, key_type
        ).get_private_key()
        keys[key_type] = {
            "public": str(private_key.pubkey),
            "private": str(private_key),
        }
    return keys


def username_is_valid(username):
    # regex pattern is found at
    # https://steemit.com/programming/@cryptosharon/the-5-rules-of-a-valid-username-on-the-steem-blockchain-and-a-3-sbd-contest-to-make-an-account-name-validation-regex#@cryptosharon/re-eonwarped-re-cryptosharon-re-eonwarped-re-cryptosharon-re-eonwarped-re-cryptosharon-re-artopium-re-cryptosharon-the-5-rules-of-a-valid-username-on-the-steem-blockchain-and-a-3-sbd-contest-to-make-an-account-name-validation-regex-20180313t214044982z
    return bool(re.search('^[a-z](-[a-z0-9](-[a-z0-9])*)?(-[a-z0-9]|[a-z0-9])'
                          '*(?:\.[a-z](-[a-z0-9](-[a-z0-9])*)?(-[a-z0-9]|'
                          '[a-z0-9])*)*$', username))


def generate_random_password():
    return 'P5' + ''.join(
        random.choices(
            string.ascii_uppercase + string.digits + string.ascii_lowercase,
            k=50))
