from lightsteem.broadcast.key_objects import PasswordKey


def generate_keys(new_account_name, master_key):
    keys = {
        "master": master_key,
    }
    for key_type in ['posting', 'active', 'owner', 'memo']:
        private_key = PasswordKey(
            new_account_name, master_key, key_type
        ).get_private_key()
        keys[key_type] = {
            "public": str(private_key.pubkey),
            "private": str(private_key),
        }
    return keys
