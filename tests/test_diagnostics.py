import asyncio
from types import SimpleNamespace

import app.bot.handlers as handlers
from app.bot.handlers import diagnostic_keyboard, start, system_status_text
from app.core.config import get_settings


class FakeUser:
    id = 42

    def model_dump(self):
        return {"id": 42, "username": "tester", "first_name": "Test"}


class FakeMessage:
    from_user = FakeUser()

    def __init__(self):
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))


def test_start_always_sends_diagnostics():
    message = FakeMessage()
    asyncio.run(start(message, SimpleNamespace(args=None)))
    assert "Telegram Bot подключён" in message.answers[0][0]
    assert "Telegram ID" in message.answers[0][0]


def test_diagnostic_state_and_keyboard():
    assert get_settings().vpn_diagnostic_status == "MOCK"
    assert diagnostic_keyboard().inline_keyboard[0][0].web_app is not None
    assert "HAVA SYSTEM TEST" in system_status_text(True)


def test_non_https_url_uses_safe_fallback():
    original = handlers.get_settings
    handlers.get_settings = lambda: SimpleNamespace(
        mini_app_ready=False,
        resolved_mini_app_url="http://localhost:8000",
        vpn_diagnostic_status="MOCK",
    )
    try:
        button = handlers.diagnostic_keyboard().inline_keyboard[0][0]
        assert button.web_app is None
        assert "HTTPS" in button.text
    finally:
        handlers.get_settings = original
