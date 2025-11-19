from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field
from .models import billing_rules


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
    grace_speed_mbps: Optional[int] = None

    @classmethod
    def trial(cls, user_id: int, duration_days: int | None = None) -> "Subscription":
        """Construct a trial subscription respecting central billing rules."""

        duration = duration_days or billing_rules.trial_days
        now = datetime.utcnow()
        return cls(
            user_id=user_id,
            tariff_code="trial",
            active_until=now + timedelta(days=duration),
            grace_until=now + timedelta(days=duration + billing_rules.grace_days),
            speed_limit_mbps=None,
            grace_speed_mbps=billing_rules.grace_speed_mbps,
        )


class NotificationSchedule(BaseModel):
    phase: Literal["active", "grace"] = Field(
        default="active", description="Lifecycle phase the reminder belongs to"
    )
    trigger_hours_before_end: int = Field(
        ..., description="Hours relative to the phase end when reminder fires"
    )
    message: str
