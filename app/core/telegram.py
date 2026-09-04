import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86_400) -> dict:
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", "")
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram signature is missing")

    check_string = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    auth_date = int(values.get("auth_date", 0))
    if not auth_date or time.time() - auth_date > max_age:
        raise HTTPException(status_code=401, detail="Telegram authorization expired")

    try:
        return json.loads(values["user"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Telegram user is missing") from exc
