# HAVA VPN Telegram Bot

Тестовый интерфейс Telegram-бота HAVA VPN без платежей, базы данных, Mini App и VPN-интеграций.

## Возможности

- приветственный экран `/start`;
- постоянное нижнее меню;
- экраны подписки на месяц и год;
- навигация внутри одного сообщения через inline-кнопки;
- тестовый выбор языка в памяти процесса;
- кабинет, магазин, помощь и информация о боте;
- заглушка покупки без проведения платежа.

## Запуск

Требуется Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

В `.env` требуется только токен:

```dotenv
BOT_TOKEN=your_telegram_bot_token
```
