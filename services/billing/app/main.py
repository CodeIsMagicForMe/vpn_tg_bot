from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .models import billing_rules
from .reminders import ReminderManager
from .schemas import (
    Tariff,
    PaymentIntent,
    PaymentStatus,
    Subscription,
    NotificationSchedule,
)

app = FastAPI(title="Billing Service", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins] if settings.allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TARIFFS = [
    Tariff(
        code="trial",
        name="Trial",
        price_stars=0,
        duration_days=billing_rules.trial_days,
        devices=2,
        nodes=1,
    ),
    Tariff(
        code="light",
        name="Light",
        price_stars=110,
        duration_days=30,
        speed_limit_mbps=100,
        devices=2,
        nodes=2,
    ),
    Tariff(
        code="family",
        name="Family",
        price_stars=200,
        duration_days=30,
        speed_limit_mbps=300,
        devices=5,
        nodes=4,
    ),
    Tariff(
        code="unlimited",
        name="Unlimited",
        price_stars=290,
        duration_days=30,
        devices=8,
        nodes=6,
        smartdns=True,
        speed_limit_mbps=None,
    ),
]

NOTIFICATION_SCHEDULE = [
    NotificationSchedule(
        phase="active", trigger_hours_before_end=72, message="Продлите со скидкой 15%"
    ),
    NotificationSchedule(
        phase="active",
        trigger_hours_before_end=24,
        message="Подписка заканчивается завтра",
    ),
    NotificationSchedule(
        phase="active",
        trigger_hours_before_end=0,
        message="Подписка закончилась, у вас 3 дня grace со скоростью до 10 Мбит/с",
    ),
    NotificationSchedule(
        phase="grace",
        trigger_hours_before_end=0,
        message="Последний шанс — продлите подписку и получите +3 дня в подарок",
    ),
]

reminder_manager = ReminderManager(NOTIFICATION_SCHEDULE)


@app.get("/health")
def health():
    return {"status": "ok", "provider": settings.telegram_payment_provider}


@app.get("/tariffs", response_model=list[Tariff])
def list_tariffs():
    return TARIFFS


@app.post("/payments/start", response_model=PaymentStatus)
def start_payment(intent: PaymentIntent):
    tariff = next((t for t in TARIFFS if t.code == intent.tariff_code), None)
    if not tariff:
        raise HTTPException(status_code=404, detail="Unknown tariff")
    invoice_id = f"invoice-{intent.user_id}-{intent.tariff_code}-{int(datetime.utcnow().timestamp())}"
    return PaymentStatus(
        status="pending",
        amount_stars=tariff.price_stars,
        invoice_id=invoice_id,
        redirect_url=f"https://t.me/pay?start={invoice_id}",
    )


@app.post("/payments/{invoice_id}/confirm", response_model=Subscription)
def confirm_payment(invoice_id: str):
    parts = invoice_id.split("-")
    if len(parts) < 4:
        raise HTTPException(status_code=400, detail="Malformed invoice")
    _, user_id, tariff_code, _ = parts
    tariff = next((t for t in TARIFFS if t.code == tariff_code), None)
    if not tariff:
        raise HTTPException(status_code=404, detail="Unknown tariff")
    now = datetime.utcnow()
    grace = now + timedelta(days=tariff.duration_days + billing_rules.grace_days)
    subscription = Subscription(
        user_id=int(user_id),
        tariff_code=tariff_code,
        active_until=now + timedelta(days=tariff.duration_days),
        grace_until=grace,
        speed_limit_mbps=tariff.speed_limit_mbps if tariff.speed_limit_mbps else None,
        grace_speed_mbps=billing_rules.grace_speed_mbps,
    )
    reminder_manager.schedule_subscription(subscription)
    return subscription


@app.post("/trial", response_model=Subscription)
def create_trial(user_id: int):
    subscription = Subscription.trial(user_id=user_id)
    reminder_manager.schedule_subscription(subscription)
    return subscription


@app.get("/notifications", response_model=list[NotificationSchedule])
def notification_plan():
    return NOTIFICATION_SCHEDULE


@app.on_event("startup")
def _start_scheduler():
    reminder_manager.start()


@app.on_event("shutdown")
def _stop_scheduler():
    reminder_manager.stop()
