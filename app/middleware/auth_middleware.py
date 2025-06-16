from flask import request, g, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from functools import wraps
from app.models.admin_user import AdminUser
from app.middleware.tenant_middleware import get_current_store_id
import logging

class AuthMiddleware:
    """Middleware for handling authentication and authorization."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        # No global before_request needed for auth
        pass

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            
            # Get user identity from JWT
            user_id = get_jwt_identity()
            
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Valid authentication token required'
                }), 401
            
            # Load user data
            user = AdminUser.get_by_user_id(user_id)
            
            if not user:
                return jsonify({
                    'error': 'User not found',
                    'message': 'Authentication token is invalid'
                }), 401
            
            # Check if user is active
            if not user.is_active:
                return jsonify({
                    'error': 'Account disabled',
                    'message': 'Your account has been disabled'
                }), 403
            
            # Check if account is locked
            if user.is_locked:
                return jsonify({
                    'error': 'Account locked',
                    'message': 'Your account has been locked due to security reasons'
                }), 403
            
            # Set user in request context
            g.current_user = user
            
            # Update last activity
            user.update_last_login()
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Invalid or expired token'
            }), 401
    
    return decorated_function

def require_role(*allowed_roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            if user.role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Required roles: {", ".join(allowed_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_permission(permission):
    """Decorator to require specific permission."""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            if not user.has_permission(permission):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'Required permission: {permission}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_store_access(f):
    """Decorator to ensure user has access to current store."""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        user = g.current_user
        store_id = get_current_store_id()
        
        if not store_id:
            return jsonify({
                'error': 'Store context required',
                'message': 'Valid store context required'
            }), 400
        
        # Super admin can access any store
        if user.is_super_admin():
            return f(*args, **kwargs)
        
        # Check if user has access to this store
        if not user.can_access_store(store_id):
            return jsonify({
                'error': 'Store access denied',
                'message': 'You do not have access to this store'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_store_owner(f):
    """Decorator to require store owner access."""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        user = g.current_user
        store_id = get_current_store_id()
        
        if not store_id:
            return jsonify({
                'error': 'Store context required',
                'message': 'Valid store context required'
            }), 400
        
        # Super admin can access any store
        if user.is_super_admin():
            return f(*args, **kwargs)
        
        # Check if user is owner of this store
        if not (user.is_store_owner() and user.store_id == store_id):
            return jsonify({
                'error': 'Store owner access required',
                'message': 'Only store owners can perform this action'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            
            # Get user identity from JWT
            user_id = get_jwt_identity()
            
            if user_id:
                # Load user data
                user = AdminUser.get_by_user_id(user_id)
                
                if user and user.is_active and not user.is_locked:
                    g.current_user = user
                    user.update_last_login()
                else:
                    g.current_user = None
            else:
                g.current_user = None
                
        except Exception as e:
            logging.debug(f"Optional auth failed: {str(e)}")
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current authenticated user."""
    return getattr(g, 'current_user', None)

def is_authenticated():
    """Check if current request is authenticated."""
    return get_current_user() is not None

def has_role(*roles):
    """Check if current user has any of the specified roles."""
    user = get_current_user()
    return user and user.role in roles

def has_permission(permission):
    """Check if current user has specific permission."""
    user = get_current_user()
    return user and user.has_permission(permission)

def can_access_store(store_id):
    """Check if current user can access specific store."""
    user = get_current_user()
    return user and user.can_access_store(store_id)

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'X-API-Key header is required'
            }), 401
        
        # Validate API key against store settings
        store_id = get_current_store_id()
        if not store_id:
            return jsonify({
                'error': 'Store context required',
                'message': 'Valid store context required'
            }), 400
        
        from app.models.store_settings import StoreSettings
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings or not settings.api_enabled:
            return jsonify({
                'error': 'API disabled',
                'message': 'API access is disabled for this store'
            }), 403
        
        if settings.api_key != api_key:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 401
        
        # Set API context
        g.api_authenticated = True
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(max_requests=100, window=3600):
    """Decorator for rate limiting."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting implementation
            # In production, use Redis or a proper rate limiting service
            
            # Get client identifier
            if is_authenticated():
                client_id = f"user_{get_current_user().user_id}"
            else:
                client_id = f"ip_{request.remote_addr}"
            
            # For now, just log the request
            # Implement actual rate limiting with Redis/cache
            logging.debug(f"Rate limit check for {client_id}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_security_event(event_type, details=None, user_id=None):
    """Log security-related events."""
    if not user_id and is_authenticated():
        user_id = get_current_user().user_id
    
    log_data = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat(),
        'details': details
    }
    
    # Log to security log
    logging.warning(f"Security Event: {log_data}")

def validate_password_strength(password):
    """Validate password strength."""
    import re
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def generate_secure_token(length=32):
    """Generate secure random token."""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_sensitive_data(data):
    """Hash sensitive data for logging."""
    import hashlib
    
    if not data:
        return None
    
    return hashlib.sha256(str(data).encode()).hexdigest()[:8]

# Middleware instance
auth_middleware = AuthMiddleware()