from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, PreCheckoutQuery, ReplyKeyboardMarkup, WebAppInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.bot.instance import bot
from app.core.config import get_settings
from app.db.base import Order, OrderStatus, Payment, Plan, Subscription, User
from app.db.session import SessionLocal
from app.services.subscriptions import provision
from app.services.users import get_or_create_user

router = Router()


def webapp_keyboard():
    url = get_settings().public_url
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌬 Открыть HAVA VPN", web_app=WebAppInfo(url=url))], [KeyboardButton(text="💎 Тарифы"), KeyboardButton(text="🔑 Моя подписка")], [KeyboardButton(text="📱 Устройства"), KeyboardButton(text="❓ Помощь")]], resize_keyboard=True)


@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    async with SessionLocal() as db:
        ref = None
        if command.args and command.args.startswith("ref_"):
            try: ref = int(command.args[4:])
            except ValueError: pass
        user = await get_or_create_user(db, message.from_user.model_dump(), ref)
        sub = await db.scalar(select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.user_id == user.id))
    if sub and sub.status.value == "ACTIVE":
        text = f"HAVA VPN активен ✅\nТариф: <b>{sub.plan.name}</b>\nАктивен до: {sub.expires_at:%d.%m.%Y}"
    else:
        text = "Добро пожаловать в <b>HAVA VPN</b> 🌬\nБезопасное и быстрое подключение без лишних настроек."
    await message.answer(text, reply_markup=webapp_keyboard())


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

