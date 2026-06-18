from functools import wraps
from flask import jsonify, redirect, url_for
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import get_user_by_id

# ── Role Constants ────────────────────────────────────────────────────────────
ROLE_ADMIN     = 'admin'       # Full system access, manage users, view all cases
ROLE_AUTHORITY = 'authority'   # Police/Security: view cases, dispatch, resolve
ROLE_USER      = 'user'        # General public: trigger alerts, witness reports

def get_current_user():
    user_id = get_jwt_identity()
    return get_user_by_id(user_id)

def role_required(*roles):
    """Decorator: restrict route to specific roles"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user or user.get('role') not in roles:
                return jsonify({
                    'error': 'Access denied',
                    'required_roles': list(roles),
                    'your_role': user.get('role') if user else 'none'
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    return role_required(ROLE_ADMIN)(fn)

def authority_required(fn):
    return role_required(ROLE_ADMIN, ROLE_AUTHORITY)(fn)

def user_required(fn):
    return role_required(ROLE_ADMIN, ROLE_AUTHORITY, ROLE_USER)(fn)
