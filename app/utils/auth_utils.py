"""
Authentication utility functions.
Pure helper functions only - no database operations.
Business logic has been moved to app/services/auth_service.py

DEPRECATED: Import from app.services.auth_service.AuthService instead.
"""

# This file is deprecated and kept only for backward compatibility.
# All authentication business logic has been moved to AuthService.
#
# Migration guide:
# - Old: from app.utils.auth_utils import get_or_create_user
# - New: from app.services.auth_service import AuthService
#        service = AuthService(db)
#        user = service.get_or_create_user(...)
