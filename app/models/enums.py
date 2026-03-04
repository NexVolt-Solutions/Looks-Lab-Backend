from enum import Enum


class PlanType(str, Enum):
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"

