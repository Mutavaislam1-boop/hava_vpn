import hashlib, hmac, json, time
from urllib.parse import urlencode
from app.core.telegram import token_hash, validate_init_data


def test_token_hash_not_plaintext():
    assert token_hash("secret") != "secret"


def test_valid_init_data():
    token = "123:test"
    values = {"auth_date": str(int(time.time())), "query_id": "q", "user": json.dumps({"id": 42})}
    check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    assert validate_init_data(urlencode(values), token)["id"] == 42

