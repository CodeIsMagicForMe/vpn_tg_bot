from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from .schemas import NotificationSchedule, Subscription


class ReminderManager:
    """Simple APScheduler wrapper for lifecycle reminders."""

    def __init__(
        self,
        schedule: Iterable[NotificationSchedule],
        timezone: str = "UTC",
    ) -> None:
        self.schedule = list(schedule)
        self._scheduler = BackgroundScheduler(timezone=timezone)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def stop(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def schedule_subscription(self, subscription: Subscription) -> None:
        """Create reminder jobs for a subscription lifecycle."""

        if not self._started:
            # Avoid silently failing during unit tests/startup
            self.start()

        for entry in self.schedule:
            if entry.phase == "active":
                fire_at = subscription.active_until - timedelta(
                    hours=entry.trigger_hours_before_end
                )
            else:
                fire_at = subscription.grace_until - timedelta(
                    hours=entry.trigger_hours_before_end
                )

            if fire_at <= datetime.utcnow():
                continue

            trigger = DateTrigger(run_date=fire_at)
            self._scheduler.add_job(
                self._emit_notification,
                trigger=trigger,
                args=[subscription.user_id, entry],
                id=f"notify-{subscription.user_id}-{subscription.tariff_code}-{entry.phase}-{entry.trigger_hours_before_end}-{fire_at.timestamp()}",
                replace_existing=True,
            )

    @staticmethod
    def _emit_notification(user_id: int, entry: NotificationSchedule) -> None:
        # Placeholder for integration with Telegram bot webhook/Redis queue
        print(
            f"[reminder] user={user_id} phase={entry.phase} +{entry.trigger_hours_before_end}h message={entry.message}"
        )
