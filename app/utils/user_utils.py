"""
User utility functions.
Pure helper functions only - no database operations.
Business logic has been moved to app/services/user_service.py

DEPRECATED: Import from app.services.user_service.UserService instead.
"""

# This file is deprecated and kept only for backward compatibility.
# All user business logic has been moved to UserService.
#
# Migration guide:
# - Old: from app.utils.user_utils import get_user_or_404, update_user_fields
# - New: from app.services.user_service import UserService
#        service = UserService(db)
#        user = service.get_user_by_id(user_id)
#        updated = service.update_user(user_id, payload)


