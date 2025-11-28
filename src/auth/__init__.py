"""
Authentication and user management module for AetherSignal.
Provides multi-tenant user authentication and data isolation.
"""

from .auth import (
    login_user,
    register_user,
    logout_user,
    get_current_user,
    reset_password,
    verify_email,
    is_authenticated
)

from .user_management import (
    get_user_profile,
    update_user_profile,
    get_user_role,
    set_user_role,
    get_user_company_id
)

__all__ = [
    'login_user',
    'register_user',
    'logout_user',
    'get_current_user',
    'reset_password',
    'verify_email',
    'is_authenticated',
    'get_user_profile',
    'update_user_profile',
    'get_user_role',
    'set_user_role',
    'get_user_company_id',
]

