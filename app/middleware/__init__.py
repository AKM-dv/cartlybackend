from .tenant_middleware import (
    TenantMiddleware,
    tenant_middleware,
    require_tenant,
    require_active_store,
    get_current_store,
    get_current_store_id,
    switch_tenant_context,
    TenantAwareQuery,
    validate_store_limits,
    log_tenant_activity
)

from .auth_middleware import (
    AuthMiddleware,
    auth_middleware,
    require_auth,
    require_role,
    require_permission,
    require_store_access,
    require_store_owner,
    optional_auth,
    get_current_user,
    is_authenticated,
    has_role,
    has_permission,
    can_access_store,
    require_api_key,
    rate_limit,
    log_security_event,
    validate_password_strength,
    generate_secure_token,
    hash_sensitive_data
)

from .cors_middleware import (
    CORSMiddleware,
    cors_middleware,
    configure_cors_for_environment,
    is_allowed_origin,
    add_cors_headers,
    handle_preflight_request
)

__all__ = [
    # Tenant Middleware
    'TenantMiddleware',
    'tenant_middleware',
    'require_tenant',
    'require_active_store',
    'get_current_store',
    'get_current_store_id',
    'switch_tenant_context',
    'TenantAwareQuery',
    'validate_store_limits',
    'log_tenant_activity',
    
    # Auth Middleware
    'AuthMiddleware',
    'auth_middleware',
    'require_auth',
    'require_role',
    'require_permission',
    'require_store_access',
    'require_store_owner',
    'optional_auth',
    'get_current_user',
    'is_authenticated',
    'has_role',
    'has_permission',
    'can_access_store',
    'require_api_key',
    'rate_limit',
    'log_security_event',
    'validate_password_strength',
    'generate_secure_token',
    'hash_sensitive_data',
    
    # CORS Middleware
    'CORSMiddleware',
    'cors_middleware',
    'configure_cors_for_environment',
    'is_allowed_origin',
    'add_cors_headers',
    'handle_preflight_request'
]

def init_middleware(app):
    """Initialize all middleware with Flask app."""
    # Initialize tenant middleware
    tenant_middleware.init_app(app)
    
    # Initialize auth middleware
    auth_middleware.init_app(app)
    
    # Initialize CORS middleware
    cors_middleware.init_app(app)
    
    # Register error handlers
    register_error_handlers(app)

def register_error_handlers(app):
    """Register global error handlers."""
    from flask import jsonify
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this resource'
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later'
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify({
            'error': 'Service Unavailable',
            'message': 'The service is temporarily unavailable'
        }), 503