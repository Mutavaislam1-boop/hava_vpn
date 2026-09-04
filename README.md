# HAVA VPN

MVP единой системы продажи VPN-доступа: Telegram-бот, Mini App, FastAPI backend, Telegram Stars, PostgreSQL, web-admin и подключение внешнего VPN по API-ключу.

## Что уже работает

- `/start`, меню, `/paysupport` и запуск Mini App;
- тарифы из БД и редактируемые admin API;
- Stars invoice → `pre_checkout_query` → идемпотентный `successful_payment`;
- раздельные состояния оплаты и provisioning;
- создание и продление VPN-профиля через внешний API;
- случайная subscription URL, отзыв и перевыпуск;
- локальная генерация QR API без сторонних сервисов;
- Mini App с экранами Главная, Тарифы, VPN и Профиль;
- базовый dashboard `/admin`, обращения поддержки и audit log;
- единый VPN API client без собственной VPN-инфраструктуры и протокольной логики.

## Локальный запуск

Требуется Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Откройте `http://localhost:8000/health`. При локальном `PUBLIC_URL` бот сам запускается через long polling. Mini App авторизуется только внутри Telegram; это ожидаемое ограничение безопасности.

## Диагностический режим

- `/start` и `/status` показывают состояние Telegram, backend, базы, VPN API и Mini App;
- при запуске выполняется Telegram `getMe()` и в терминал выводятся реальные username и ID бота;
- ожидаемый username задаётся через `EXPECTED_BOT_USERNAME`;
- HTTPS-адрес Mini App задаётся отдельно через `MINI_APP_URL`;
- без HTTPS команда `/start` продолжает работать и показывает предупреждение вместо Web App-кнопки.

Для Telegram Mini App нужен публичный HTTPS URL. Укажите его в `PUBLIC_URL`, настройте URL Mini App через BotFather и установите webhook:

```text
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR_DOMAIN/telegram/webhook/WEBHOOK_SECRET&secret_token=WEBHOOK_SECRET
```

Не вставляйте реальный токен в URL истории терминала. Для production лучше выполнить запрос через безопасный deployment secret.

## Подключение VPN API

В `.env`:

```dotenv
VPN_API_URL=https://provider.example/api
VPN_API_KEY=...
VPN_API_AUTH_HEADER=Authorization
```

По умолчанию ключ передаётся как `Authorization: Bearer <VPN_API_KEY>`. Если сервис использует `X-API-Key`, задайте `VPN_API_AUTH_HEADER=X-API-Key`.

Ожидаемый контракт внешнего сервиса:

```text
POST   /users
PATCH  /users/{username}
POST   /users/{username}/enable
POST   /users/{username}/disable
DELETE /users/{username}
GET    /users/{username}/subscription
```

Последний endpoint должен возвращать JSON с полем `subscription` или `config`. При получении документации конкретного VPN API меняется только [client.py](app/vpn/client.py).

## Важное перед production

1. Перевыпустите Telegram bot token в BotFather: текущий токен был опубликован в переписке.
2. Замените `ADMIN_TOKEN` и `WEBHOOK_SECRET` длинными случайными значениями.
3. Укажите HTTPS-домен, строгий `CORS_ORIGINS`, PostgreSQL, `VPN_API_URL` и `VPN_API_KEY`.
4. Поставьте reverse proxy, rate limiting, резервное копирование и worker для повторов provisioning/уведомлений.
5. Добавьте admin 2FA, юридические документы и мониторинг.

## Структура

```text
app/api/       REST и subscription endpoint
app/bot/       aiogram handlers и Stars
app/core/      настройки и проверка Telegram initData
app/db/        модели и async session
app/services/  пользователи и provisioning
app/vpn/       клиент внешнего VPN API по API-ключу
app/static/    Mini App и базовая web-admin
tests/         проверки security primitives
```
