"""
Subscription utility functions.
Pure helper functions only - no database operations.
Business logic has been moved to app/services/subscription_service.py

DEPRECATED: Import from app.services.subscription_service.SubscriptionService instead.
"""

# This file is deprecated and kept only for backward compatibility.
# All subscription business logic has been moved to SubscriptionService.
#
# Migration guide:
# - Old: from app.utils.subscription_utils import create_subscription_entry
# - New: from app.services.subscription_service import SubscriptionService
#        service = SubscriptionService(db)
#        subscription = service.create_subscription(payload)

