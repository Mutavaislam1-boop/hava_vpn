from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, PreCheckoutQuery, ReplyKeyboardMarkup, WebAppInfo
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.bot.instance import bot
from app.bot.diagnostics import runtime
from app.core.config import get_settings
from app.db.base import Order, OrderStatus, Payment, Plan, Subscription, User
from app.db.session import SessionLocal
from app.services.subscriptions import provision
from app.services.users import get_or_create_user

router = Router()


def webapp_keyboard():
    settings = get_settings()
    rows = []
    if settings.mini_app_ready:
        rows.append([KeyboardButton(text="🌬 Открыть HAVA VPN", web_app=WebAppInfo(url=settings.resolved_mini_app_url))])
    else:
        rows.append([KeyboardButton(text="⚠️ Mini App ещё не подключён к HTTPS")])
    rows.extend([[KeyboardButton(text="💎 Тарифы"), KeyboardButton(text="🔑 Моя подписка")], [KeyboardButton(text="📱 Устройства"), KeyboardButton(text="❓ Помощь")]])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def diagnostic_keyboard():
    settings = get_settings()
    rows = []
    if settings.mini_app_ready:
        rows.append([InlineKeyboardButton(text="🌬 Открыть HAVA VPN", web_app=WebAppInfo(url=settings.resolved_mini_app_url))])
    else:
        rows.append([InlineKeyboardButton(text="⚠️ Mini App ещё не подключён к HTTPS", callback_data="diag:no_webapp")])
    rows.extend([
        [InlineKeyboardButton(text="🧪 Проверить backend", callback_data="diag:backend")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="diag:profile")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def database_online() -> bool:
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        runtime.database_ready = True
    except Exception:
        runtime.database_ready = False
    return runtime.database_ready


def system_status_text(database_ready: bool) -> str:
    settings = get_settings()
    return (
        "<b>✅ HAVA SYSTEM TEST</b>\n\n"
        "Telegram Bot: ONLINE\n"
        f"Backend API: {'ONLINE' if runtime.backend_ready else 'STARTING'}\n"
        f"Database: {'ONLINE' if database_ready else 'OFFLINE'}\n"
        f"VPN Provider: {settings.vpn_diagnostic_status}\n"
        f"Mini App URL: {'READY' if settings.mini_app_ready else 'NOT CONFIGURED'}"
    )


@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    settings = get_settings()
    text_value = (
        "<b>🌬 HAVA VPN</b>\n\n"
        "<b>✅ Telegram Bot подключён</b>\n"
        "Бот успешно работает и связан с backend.\n\n"
        f"Telegram ID: <code>{message.from_user.id}</code>\n"
        "Backend: ONLINE\n"
        f"VPN Provider: {settings.vpn_diagnostic_status}\n"
        "Version: MVP TEST"
    )
    await message.answer(text_value, reply_markup=diagnostic_keyboard())
    try:
        async with SessionLocal() as db:
            ref = None
            if command.args and command.args.startswith("ref_"):
                try: ref = int(command.args[4:])
                except ValueError: pass
            await get_or_create_user(db, message.from_user.model_dump(), ref)
    except Exception:
        # Diagnostics must answer even while the database is unavailable.
        runtime.database_ready = False


@router.message(Command("status"))
async def status(message: Message):
    await message.answer(system_status_text(await database_online()), reply_markup=diagnostic_keyboard())


@router.callback_query(F.data == "diag:backend")
async def check_backend(callback: CallbackQuery):
    await callback.message.answer(system_status_text(await database_online()))
    await callback.answer("Проверка завершена")


@router.callback_query(F.data == "diag:no_webapp")
async def no_webapp(callback: CallbackQuery):
    await callback.answer("Укажите HTTPS-адрес в MINI_APP_URL", show_alert=True)


@router.callback_query(F.data == "diag:profile")
async def diagnostic_profile(callback: CallbackQuery):
    try:
        async with SessionLocal() as db:
            user = await get_or_create_user(db, callback.from_user.model_dump())
        await callback.message.answer(f"<b>👤 Профиль HAVA</b>\n\nHAVA ID: #{user.id}\nTelegram ID: <code>{user.telegram_id}</code>\nUsername: @{user.username or 'не указан'}")
    except Exception:
        await callback.message.answer("Профиль временно недоступен, но Telegram Bot и backend работают.")
    await callback.answer()


@router.message(F.text == "⚠️ Mini App ещё не подключён к HTTPS")
async def mini_app_not_ready(message: Message):
    await message.answer("⚠️ Mini App ещё не подключён к HTTPS. Укажите публичный адрес в MINI_APP_URL.")


@router.message(Command("paysupport"))
async def paysupport(message: Message):
    await message.answer("По вопросам оплаты напишите в поддержку через HAVA VPN → Профиль → Поддержка. Укажите дату платежа и Telegram ID, но не отправляйте пароли или коды.")


@router.message(F.text == "💎 Тарифы")
async def show_plans(message: Message):
    async with SessionLocal() as db:
        plans = (await db.scalars(select(Plan).where(Plan.is_active).order_by(Plan.sort_order))).all()
    rows = [[InlineKeyboardButton(text=f"{p.name} — {p.price_stars} ⭐", callback_data=f"buy:{p.id}")] for p in plans]
    await message.answer("Выберите тариф HAVA:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("buy:"))
async def buy(callback):
    plan_id = int(callback.data.split(":")[1])
    async with SessionLocal() as db:
        user = await get_or_create_user(db, callback.from_user.model_dump())
        plan = await db.get(Plan, plan_id)
        if not plan or not plan.is_active:
            return await callback.answer("Тариф недоступен", show_alert=True)
        order = Order(user_id=user.id, plan_id=plan.id, amount=plan.price_stars)
        db.add(order); await db.commit(); await db.refresh(order)
    await bot.send_invoice(callback.from_user.id, title=plan.name, description=f"HAVA VPN на {plan.duration_days} дней", payload=f"order:{order.id}", currency="XTR", prices=[{"label": plan.name, "amount": plan.price_stars}])
    await callback.answer()


@router.pre_checkout_query()
async def checkout(query: PreCheckoutQuery):
    ok, error = False, "Заказ не найден"
    try:
        order_id = int(query.invoice_payload.split(":")[1])
        async with SessionLocal() as db:
            order = await db.get(Order, order_id)
            user = await db.get(User, order.user_id) if order else None
            ok = bool(order and user and user.telegram_id == query.from_user.id and order.status == OrderStatus.PENDING and order.amount == query.total_amount and query.currency == "XTR")
            if not ok: error = "Параметры заказа изменились. Создайте новый заказ."
    except Exception:
        pass
    await query.answer(ok=ok, error_message=None if ok else error)


@router.message(F.successful_payment)
async def paid(message: Message):
    payment = message.successful_payment
    order_id = int(payment.invoice_payload.split(":")[1])
    async with SessionLocal() as db:
        duplicate = await db.scalar(select(Payment).where(Payment.telegram_payment_charge_id == payment.telegram_payment_charge_id))
        if duplicate:
            return
        order = await db.scalar(select(Order).options(selectinload(Order.plan)).where(Order.id == order_id))
        user = await db.get(User, order.user_id) if order else None
        if not order or not user or user.telegram_id != message.from_user.id or order.amount != payment.total_amount:
            return await message.answer("Платёж получен, но заказ требует ручной проверки. Напишите /paysupport.")
        db.add(Payment(order_id=order.id, telegram_payment_charge_id=payment.telegram_payment_charge_id, provider_payment_id=payment.provider_payment_charge_id, amount=payment.total_amount, currency=payment.currency, raw_reference=payment.model_dump(mode="json")))
        order.status, order.provisioning_status = OrderStatus.PAID, "PENDING"
        await db.commit()
        await message.answer("Платёж получен ✅\nHAVA настраивается. Обычно это занимает несколько секунд.")
        try:
            _, raw_token = await provision(db, user, order.plan)
            order.provisioning_status = "READY"; await db.commit()
            link = f"{get_settings().public_url}/s/{raw_token}" if raw_token else get_settings().public_url
            await message.answer(f"HAVA готов ✅\nОткройте кабинет, чтобы подключиться.\n{link}", reply_markup=webapp_keyboard())
        except Exception:
            order.provisioning_status = "PENDING"; await db.commit()
            await message.answer("Настройка задерживается. Платёж сохранён — система повторит создание доступа.")


@router.message(F.text.in_({"🔑 Моя подписка", "📱 Устройства", "❓ Помощь"}))
async def open_app(message: Message):
    await message.answer("Откройте кабинет HAVA:", reply_markup=webapp_keyboard())
