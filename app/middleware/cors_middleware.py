from flask import request, current_app
from flask_cors import CORS
from app.middleware.tenant_middleware import get_current_store

class CORSMiddleware:
    """Enhanced CORS middleware with tenant-aware configuration."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize CORS middleware with Flask app."""
        # Basic CORS configuration
        self.cors = CORS(app, resources={
            r"/api/*": {
                "origins": self._get_allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-Store-ID",
                    "X-API-Key",
                    "X-Requested-With",
                    "Accept",
                    "Origin",
                    "Cache-Control"
                ],
                "expose_headers": [
                    "X-Total-Count",
                    "X-Page-Count",
                    "X-Current-Page",
                    "X-Rate-Limit-Remaining",
                    "X-Rate-Limit-Reset"
                ],
                "supports_credentials": True,
                "max_age": 86400  # 24 hours
            }
        })
        
        # Register after_request handler for custom headers
        app.after_request(self._after_request)
    
    def _get_allowed_origins(self):
        """Get allowed origins based on environment and store configuration."""
        allowed_origins = []
        
        # Development origins
        if current_app.config.get('ENV') == 'development':
            allowed_origins.extend([
                'http://localhost:3000',
                'http://localhost:3001',
                'http://localhost:5000',
                'http://127.0.0.1:3000',
                'http://127.0.0.1:3001',
                'http://127.0.0.1:5000'
            ])
        
        # Production origins
        else:
            # Add main domain
            main_domain = current_app.config.get('MAIN_DOMAIN')
            if main_domain:
                allowed_origins.extend([
                    f"https://{main_domain}",
                    f"https://www.{main_domain}",
                    f"https://admin.{main_domain}"
                ])
        
        # Store-specific origins
        store = get_current_store()
        if store:
            # Add store's custom domain
            if store.custom_domain:
                allowed_origins.extend([
                    f"https://{store.custom_domain}",
                    f"https://www.{store.custom_domain}"
                ])
            
            # Add store's subdomain
            if store.subdomain:
                base_domain = current_app.config.get('BASE_DOMAIN', 'yourdomain.com')
                allowed_origins.append(f"https://{store.subdomain}.{base_domain}")
        
        # Remove duplicates and None values
        allowed_origins = list(filter(None, set(allowed_origins)))
        
        return allowed_origins
    
    def _after_request(self, response):
        """Add custom headers after request processing."""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # API versioning
        if request.path.startswith('/api/'):
            response.headers['X-API-Version'] = '1.0'
        
        # Store information (for debugging in development)
        if current_app.config.get('DEBUG'):
            store = get_current_store()
            if store:
                response.headers['X-Store-ID'] = store.store_id
        
        return response

def configure_cors_for_environment(app):
    """Configure CORS based on environment."""
    env = app.config.get('ENV', 'development')
    
    if env == 'development':
        # Permissive CORS for development
        return {
            'origins': ['*'],
            'methods': ['*'],
            'allow_headers': ['*'],
            'supports_credentials': True
        }
    
    elif env == 'production':
        # Strict CORS for production
        return {
            'origins': [],  # Will be populated dynamically
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
            'allow_headers': [
                'Content-Type',
                'Authorization',
                'X-Store-ID',
                'X-API-Key'
            ],
            'supports_credentials': True,
            'max_age': 86400
        }
    
    else:
        # Testing environment
        return {
            'origins': ['http://localhost:3000'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'allow_headers': ['Content-Type', 'Authorization'],
            'supports_credentials': False
        }

def is_allowed_origin(origin):
    """Check if origin is allowed."""
    if not origin:
        return False
    
    # Get current allowed origins
    cors_middleware = CORSMiddleware()
    allowed_origins = cors_middleware._get_allowed_origins()
    
    return origin in allowed_origins

def add_cors_headers(response, origin=None):
    """Manually add CORS headers to response."""
    if origin and is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Store-ID, X-API-Key'
    
    return response

def handle_preflight_request():
    """Handle CORS preflight requests."""
    from flask import jsonify
    
    origin = request.headers.get('Origin')
    
    if is_allowed_origin(origin):
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Store-ID, X-API-Key'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response, 200
    
    return jsonify({'error': 'Origin not allowed'}), 403

# Middleware instance
cors_middleware = CORSMiddleware()