from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class Tariff(BaseModel):
    code: str
    name: str
    price_stars: int
    duration_days: int
    speed_limit_mbps: Optional[int] = None
    devices: int
    nodes: int
    smartdns: bool = True


class PaymentIntent(BaseModel):
    user_id: int
    tariff_code: str
    referral: Optional[str] = None
    promo_code: Optional[str] = None


class PaymentStatus(BaseModel):
    status: str
    amount_stars: int
    invoice_id: str
    redirect_url: Optional[str] = None


class Subscription(BaseModel):
    user_id: int
    tariff_code: str
    active_until: datetime
    grace_until: datetime
    speed_limit_mbps: Optional[int] = None

    @classmethod
    def trial(cls, user_id: int, duration_days: int = 3) -> "Subscription":
        now = datetime.utcnow()
        return cls(
            user_id=user_id,
            tariff_code="trial",
            active_until=now + timedelta(days=duration_days),
            grace_until=now + timedelta(days=duration_days + 3),
            speed_limit_mbps=None,
        )


class NotificationSchedule(BaseModel):
    trigger_hours_before_end: int = Field(..., description="Hours before end to notify")
    message: str
