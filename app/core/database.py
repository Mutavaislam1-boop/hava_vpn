import asyncio
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    language TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS subscriptions (
    telegram_user_id INTEGER PRIMARY KEY REFERENCES users(telegram_user_id),
    vpnresellers_account_id INTEGER UNIQUE,
    vpnresellers_username TEXT UNIQUE,
    vpnresellers_password TEXT,
    vpn_status TEXT NOT NULL DEFAULT 'not_provisioned',
    plan TEXT,
    subscription_started_at TEXT,
    subscription_expires_at TEXT,
    subscription_token_hash TEXT UNIQUE,
    subscription_token TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or get_settings().database_path)
        self._lock = asyncio.Lock()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    async def initialize(self) -> None:
        def run():
            with self._connect() as connection:
                connection.executescript(SCHEMA)
            os.chmod(self.path, 0o600)
        await asyncio.to_thread(run)

    async def upsert_user(self, user: Dict[str, Any]) -> None:
        def run():
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO users (telegram_user_id, username, first_name, language)
                    VALUES (?, ?, ?, ?) ON CONFLICT(telegram_user_id) DO UPDATE SET
                    username=excluded.username, first_name=excluded.first_name,
                    language=excluded.language, updated_at=CURRENT_TIMESTAMP""",
                    (user["id"], user.get("username"), user.get("first_name"), user.get("language_code")),
                )
        async with self._lock:
            await asyncio.to_thread(run)

    async def get_subscription(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return await self._one("SELECT * FROM subscriptions WHERE telegram_user_id = ?", (telegram_id,))

    async def get_subscription_by_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        return await self._one("SELECT * FROM subscriptions WHERE subscription_token_hash = ?", (token_hash,))

    async def save_subscription(self, data: Dict[str, Any]) -> None:
        columns = list(data)
        values = tuple(data[column] for column in columns)
        updates = ", ".join(f"{column}=excluded.{column}" for column in columns if column != "telegram_user_id")
        query = f"INSERT INTO subscriptions ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) ON CONFLICT(telegram_user_id) DO UPDATE SET {updates}, updated_at=CURRENT_TIMESTAMP"
        def run():
            with self._connect() as connection:
                connection.execute(query, values)
        async with self._lock:
            await asyncio.to_thread(run)

    async def _one(self, query: str, params: tuple) -> Optional[Dict[str, Any]]:
        def run():
            with self._connect() as connection:
                row = connection.execute(query, params).fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(run)


db = Database()
