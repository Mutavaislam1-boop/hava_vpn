# HAVA VPN Telegram Bot

Telegram-бот, Mini App и backend HAVA VPN с переключаемым VPN provider.

## Возможности

- приветственный экран `/start`;
- постоянное нижнее меню;
- экраны подписки на месяц и год;
- навигация внутри одного сообщения через inline-кнопки;
- тестовый выбор языка в памяти процесса;
- кабинет, магазин, помощь и информация о боте;
- заглушка покупки без проведения платежа;
- локальная HAVA DB для связи Telegram-пользователя и VPN-аккаунта;
- provider abstraction (`mock` / VPNResellers API 4.1);
- собственная защищённая subscription URL и QR.

## Запуск

Требуется Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Скопируйте настройки из `.env.example`. Для безопасной разработки оставьте mock:

```dotenv
BOT_TOKEN=your_telegram_bot_token
VPN_PROVIDER=mock
```

Для реального provider добавьте API 4.1 token только в `.env`, затем установите
`VPN_PROVIDER=vpnresellers`. Backend проверит `GET /accounts` при старте, но не
создаст тестовый аккаунт. Реальная выдача реализована в
`provision_paid_subscription()` и должна вызываться только после подтверждения оплаты.

Никогда не добавляйте `.env` или API token в Git, frontend и Telegram handlers.
