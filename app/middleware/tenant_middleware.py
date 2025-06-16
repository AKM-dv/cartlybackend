from flask import request, g, jsonify, current_app
from functools import wraps
from app.config.multi_tenant import (
    TenantResolver, 
    set_tenant_context, 
    validate_store_access,
    get_tenant_config
)
import logging

class TenantMiddleware:
    """Middleware for handling multi-tenant requests."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process request before route handling."""
        # Skip tenant resolution for certain paths
        if self._should_skip_tenant_resolution():
            return None
        
        # Resolve tenant from request
        store_id = TenantResolver.get_store_id()
        
        # Handle missing store ID based on environment
        if not store_id:
            return self._handle_missing_store_id()
        
        # Validate store access
        is_valid, store_data = validate_store_access(store_id)
        
        if not is_valid:
            return self._handle_invalid_store(store_data)
        
        # Set tenant context
        set_tenant_context(store_id, store_data)
        
        # Log tenant resolution for debugging
        if current_app.config.get('DEBUG'):
            logging.debug(f"Tenant resolved: {store_id}")
        
        return None
    
    def after_request(self, response):
        """Process response after route handling."""
        # Add tenant information to response headers (for debugging)
        if current_app.config.get('DEBUG') and hasattr(g, 'tenant_context'):
            if g.tenant_context.store_id:
                response.headers['X-Tenant-ID'] = g.tenant_context.store_id
        
        return response
    
    def _should_skip_tenant_resolution(self):
        """Check if tenant resolution should be skipped for this request."""
        skip_paths = [
            '/health',
            '/metrics',
            '/static/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        # Skip for admin authentication routes
        if request.path.startswith('/api/auth/'):
            return True
        
        # Skip for system routes
        for path in skip_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    def _handle_missing_store_id(self):
        """Handle requests without store ID."""
        tenant_config = get_tenant_config()
        
        # For development, allow access with default store
        if current_app.config.get('ENV') == 'development':
            default_store = tenant_config.get('default_store')
            if default_store:
                set_tenant_context(default_store)
                return None
        
        # For API requests, return JSON error
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Store not found',
                'message': 'No store identified in request',
                'code': 'STORE_NOT_FOUND'
            }), 400
        
        # For web requests, could redirect to store selection page
        return jsonify({
            'error': 'Store not found',
            'message': 'Please specify a valid store'
        }), 400
    
    def _handle_invalid_store(self, error_message):
        """Handle invalid or inactive stores."""
        # Log security event
        logging.warning(f"Invalid store access attempt: {error_message}")
        
        # For API requests, return JSON error
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Store not available',
                'message': str(error_message),
                'code': 'STORE_NOT_AVAILABLE'
            }), 404
        
        # For web requests
        return jsonify({
            'error': 'Store not available',
            'message': 'This store is currently not available'
        }), 404

def require_tenant(f):
    """Decorator to ensure tenant context exists."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_context') or not g.tenant_context.is_valid():
            return jsonify({
                'error': 'Tenant required',
                'message': 'Valid store context required for this operation'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_active_store(f):
    """Decorator to ensure store is active and not in maintenance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_context') or not g.tenant_context.is_valid():
            return jsonify({
                'error': 'Store required',
                'message': 'Valid store required'
            }), 400
        
        store_data = g.tenant_context.get_store_data()
        
        if not store_data.is_active:
            return jsonify({
                'error': 'Store inactive',
                'message': 'This store is currently inactive'
            }), 403
        
        # Check subscription status
        if not store_data.is_subscription_active():
            return jsonify({
                'error': 'Subscription expired',
                'message': 'Store subscription has expired'
            }), 403
        
        # Check maintenance mode
        from app.models.store_settings import StoreSettings
        settings = StoreSettings.get_by_store_id(store_data.store_id)
        
        if settings and settings.maintenance_mode:
            # Allow access for whitelisted IPs
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            allowed_ips = settings.maintenance_allowed_ips or []
            
            if client_ip not in allowed_ips:
                return jsonify({
                    'error': 'Maintenance mode',
                    'message': settings.maintenance_message or 'Store is under maintenance'
                }), 503
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_store():
    """Get current store from tenant context."""
    if hasattr(g, 'tenant_context') and g.tenant_context.is_valid():
        return g.tenant_context.get_store_data()
    return None

def get_current_store_id():
    """Get current store ID from tenant context."""
    if hasattr(g, 'tenant_context') and g.tenant_context.is_valid():
        return g.tenant_context.get_store_id()
    return None

def switch_tenant_context(store_id):
    """Switch to different tenant context (for admin operations)."""
    is_valid, store_data = validate_store_access(store_id)
    
    if is_valid:
        set_tenant_context(store_id, store_data)
        return True
    
    return False

class TenantAwareQuery:
    """Helper class for tenant-aware database queries."""
    
    @staticmethod
    def filter_by_store(query_class, store_id=None):
        """Add store filter to query."""
        if store_id is None:
            store_id = get_current_store_id()
        
        if not store_id:
            raise ValueError("No store context available")
        
        return query_class.query.filter_by(store_id=store_id)
    
    @staticmethod
    def create_with_store(model_class, **kwargs):
        """Create model instance with current store ID."""
        store_id = get_current_store_id()
        
        if not store_id:
            raise ValueError("No store context available")
        
        kwargs['store_id'] = store_id
        return model_class(**kwargs)

def validate_store_limits(f):
    """Decorator to validate store subscription limits."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        store = get_current_store()
        
        if not store:
            return jsonify({
                'error': 'Store required',
                'message': 'Valid store required'
            }), 400
        
        # Check if store can perform the action based on limits
        action = request.endpoint
        
        if 'product' in action and request.method == 'POST':
            # Check product limits
            from app.models.product import Product
            current_count = Product.query.filter_by(store_id=store.store_id).count()
            
            if not store.can_add_products(current_count):
                return jsonify({
                    'error': 'Product limit exceeded',
                    'message': f'Your plan allows maximum {store.max_products} products',
                    'current_count': current_count,
                    'limit': store.max_products
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_tenant_activity(action, details=None):
    """Log tenant activity for analytics."""
    store_id = get_current_store_id()
    
    if store_id:
        # Update store's last activity
        store = get_current_store()
        if store:
            store.update_activity()
        
        # Log activity (you can implement detailed logging here)
        logging.info(f"Store {store_id} - {action}: {details}")

# Middleware instance
tenant_middleware = TenantMiddleware()