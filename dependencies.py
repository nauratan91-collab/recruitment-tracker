"""
Key Dynamics Solutions - Dependency Injection & Token Authentication Engine
Provides cryptographic access token services, dependency providers, and route injection decorators.
"""

import os
import functools
import inspect
from flask import request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from database import get_db, get_user_by_id

# Secret key for token cryptographic signing
TOKEN_SECRET_KEY = os.environ.get('SECRET_KEY', 'keydynamics_corporate_recruitment_portal_jwt_secret_2026')
TOKEN_SALT = 'keydynamics-api-access-token-v1'
TOKEN_MAX_AGE = int(os.environ.get('TOKEN_MAX_AGE', 86400 * 7))  # 7 days validity

_serializer = URLSafeTimedSerializer(TOKEN_SECRET_KEY, salt=TOKEN_SALT)


# -------------------------------------------------------------------
# TOKEN SERVICES
# -------------------------------------------------------------------
def generate_access_token(user, expires_in=TOKEN_MAX_AGE):
    """
    Generate a tamper-proof cryptographically signed access token.
    Encodes user identification, role, rights summary, and issue time.
    """
    payload = {
        'uid': user['id'],
        'usr': user['username'],
        'eml': user.get('email', ''),
        'rol': user['role'],
        'rgt': user.get('rights') or user.get('rights_parsed') or {}
    }
    return _serializer.dumps(payload)


def verify_access_token(token):
    """
    Verify access token signature and expiration.
    Returns payload dictionary if valid, or (None, error_message).
    """
    if not token:
        return None, "Missing authorization token."

    # Strip 'Bearer ' prefix if present
    if token.startswith('Bearer ') or token.startswith('bearer '):
        token = token.split(' ', 1)[1].strip()

    try:
        payload = _serializer.loads(token, max_age=TOKEN_MAX_AGE)
        return payload, None
    except SignatureExpired:
        return None, "Access token has expired. Please sign in again."
    except BadSignature:
        return None, "Invalid or tampered access token."
    except Exception as e:
        return None, f"Token validation error: {str(e)}"


def extract_token_from_request():
    """
    Extract token from Authorization header or 'token' query parameter (for downloads/media).
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and (auth_header.startswith('Bearer ') or auth_header.startswith('bearer ')):
        return auth_header.split(' ', 1)[1].strip()

    # Query param fallback for browser links (resumes, compliance docs)
    token_param = request.args.get('token')
    if token_param:
        return token_param.strip()

    return None


# -------------------------------------------------------------------
# DEPENDENCY PROVIDERS
# -------------------------------------------------------------------
def provide_db():
    """
    Database dependency provider.
    Yields or returns an active SQLite database connection for the request context.
    """
    if 'db_conn' not in g:
        g.db_conn = get_db()
    return g.db_conn


def provide_current_user(optional=False):
    """
    Authenticated user dependency provider.
    Extracts and verifies access token, fetches fresh user from DB, and checks status.
    """
    token = extract_token_from_request()
    if not token:
        if optional:
            return None
        return AuthError(401, "Authorization required. Please provide a valid Bearer token.", code="AUTH_REQUIRED")

    payload, err = verify_access_token(token)
    if err or not payload:
        if optional:
            return None
        return AuthError(401, err or "Invalid authorization token.", code="INVALID_TOKEN")

    user_id = payload.get('uid')
    user = get_user_by_id(user_id)
    if not user:
        if optional:
            return None
        return AuthError(401, "Authenticated user account not found or removed.", code="USER_NOT_FOUND")

    if user.get('status') == 'Inactive':
        return AuthError(403, "User account is inactive. Please contact the administrator.", code="ACCOUNT_INACTIVE")

    return user


class AuthError:
    """Represents an authorization/authentication dependency resolution error."""
    def __init__(self, status_code, message, code="AUTH_ERROR"):
        self.status_code = status_code
        self.message = message
        self.code = code

    def to_response(self):
        return jsonify({
            'error': self.message,
            'code': self.code,
            'success': False
        }), self.status_code


# -------------------------------------------------------------------
# DEPENDENCY INJECTION DECORATOR
# -------------------------------------------------------------------
def inject(require_auth=True, roles=None, rights=None, inject_db=True):
    """
    Dependency Injection decorator for Flask API route handlers.
    
    Automatically resolves and injects requested dependencies based on handler argument names:
      - 'current_user': Injects authenticated user object.
      - 'db' or 'conn': Injects active database connection.
    
    Enforces authentication, RBAC roles, and fine-grained rights guards before execution.
    """
    if roles and isinstance(roles, str):
        roles = [roles]
    if rights and isinstance(rights, str):
        rights = [rights]

    def decorator(fn):
        sig = inspect.signature(fn)
        param_names = set(sig.parameters.keys())

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # 1. Resolve Authentication Dependency
            current_user = None
            if require_auth:
                res = provide_current_user(optional=False)
                if isinstance(res, AuthError):
                    return res.to_response()
                current_user = res

                # Enforce Role Guards
                if roles:
                    user_role = current_user.get('role')
                    user_rights = current_user.get('rights_parsed') or current_user.get('rights') or {}
                    if not isinstance(user_rights, dict):
                        user_rights = {}
                    can_admin = (user_role == 'Admin') or bool(user_rights.get('can_access_admin'))

                    if user_role not in roles and not ('Admin' in roles and can_admin):
                        return jsonify({
                            'error': f"Access forbidden. Required role: {', '.join(roles)}.",
                            'code': 'FORBIDDEN_ROLE',
                            'success': False
                        }), 403

                # Enforce Rights Guards
                if rights:
                    user_rights = current_user.get('rights_parsed') or current_user.get('rights') or {}
                    if not isinstance(user_rights, dict):
                        user_rights = {}
                    user_role = current_user.get('role')
                    
                    # Admin bypasses specific rights unless explicit
                    if user_role != 'Admin':
                        missing = [r for r in rights if not user_rights.get(r)]
                        if missing:
                            return jsonify({
                                'error': f"Access forbidden. Missing required permissions: {', '.join(missing)}.",
                                'code': 'FORBIDDEN_PERMISSION',
                                'success': False
                            }), 403
            else:
                # Optional auth
                res = provide_current_user(optional=True)
                if not isinstance(res, AuthError):
                    current_user = res

            # 2. Resolve Database Dependency
            db_conn = None
            if inject_db or 'db' in param_names or 'conn' in param_names:
                db_conn = provide_db()

            # 3. Inject parameters into kwargs if the function signature accepts them
            if 'current_user' in param_names and 'current_user' not in kwargs:
                kwargs['current_user'] = current_user
            if 'db' in param_names and 'db' not in kwargs:
                kwargs['db'] = db_conn
            if 'conn' in param_names and 'conn' not in kwargs:
                kwargs['conn'] = db_conn

            return fn(*args, **kwargs)

        return wrapper
    return decorator
