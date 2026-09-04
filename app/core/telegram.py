import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from fastapi import HTTPException


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> dict:
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", "")
    if not received_hash:
        raise HTTPException(401, "Telegram signature is missing")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(401, "Invalid Telegram signature")
    auth_date = int(values.get("auth_date", 0))
    if not auth_date or time.time() - auth_date > max_age:
        raise HTTPException(401, "Telegram authorization expired")
    try:
        return json.loads(values["user"])
    except (KeyError, json.JSONDecodeError):
        raise HTTPException(401, "Telegram user is missing")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

