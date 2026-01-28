"""
Insight utility functions.
Pure helper functions only - no database operations.
Business logic has been moved to app/services/insight_service.py

DEPRECATED: Import from app.services.insight_service.InsightService instead.
"""

# This file is deprecated and kept only for backward compatibility.
# All insight business logic has been moved to InsightService.
#
# Migration guide:
# - Old: from app.utils.insight_utils import create_insight_entry, get_user_insights
# - New: from app.services.insight_service import InsightService
#        service = InsightService(db)
#        insight = service.create_insight(payload)
#        insights = service.get_user_insights(user_id)

