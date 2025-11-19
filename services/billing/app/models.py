from dataclasses import dataclass


@dataclass(frozen=True)
class BillingRules:
    """Central place for core billing timings and throttling rules."""

    trial_days: int = 7
    grace_days: int = 3
    grace_speed_mbps: int = 10


billing_rules = BillingRules()
