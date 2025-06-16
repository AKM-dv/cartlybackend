import re
from flask import request, g, current_app
from urllib.parse import urlparse
import logging

class TenantResolver:
    """Resolves tenant/store from request."""
    
    @staticmethod
    def extract_store_from_subdomain(host):
        """Extract store ID from subdomain."""
        if not host:
            return None
        
        # Remove port if present
        host = host.split(':')[0]
        
        # Skip if it's localhost or IP
        if host in ['localhost', '127.0.0.1'] or re.match(r'^\d+\.\d+\.\d+\.\d+$', host):
            return None
        
        # Extract subdomain
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.com
            return parts[0]
        
        return None
    
    @staticmethod
    def extract_store_from_path():
        """Extract store ID from URL path."""
        path = request.path
        
        # Pattern: /store/{store_id}/...
        match = re.match(r'^/store/([^/]+)', path)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_store_from_header():
        """Extract store ID from custom header."""
        return request.headers.get('X-Store-ID')
    
    @staticmethod
    def get_store_id():
        """Get store ID using multiple methods in priority order."""
        
        # Method 1: Custom header (highest priority for API calls)
        store_id = TenantResolver.extract_store_from_header()
        if store_id:
            return store_id.lower()
        
        # Method 2: Subdomain (for web requests)
        store_id = TenantResolver.extract_store_from_subdomain(request.host)
        if store_id:
            return store_id.lower()
        
        # Method 3: URL path (fallback)
        store_id = TenantResolver.extract_store_from_path()
        if store_id:
            return store_id.lower()
        
        return None

class TenantContext:
    """Manages tenant context throughout request lifecycle."""
    
    def __init__(self):
        self.store_id = None
        self.store_data = None
        self.db_session = None
    
    def set_store(self, store_id, store_data=None):
        """Set current store context."""
        self.store_id = store_id
        self.store_data = store_data
    
    def get_store_id(self):
        """Get current store ID."""
        return self.store_id
    
    def get_store_data(self):
        """Get current store data."""
        return self.store_data
    
    def is_valid(self):
        """Check if tenant context is valid."""
        return self.store_id is not None

def get_tenant_context():
    """Get current tenant context from Flask g."""
    if not hasattr(g, 'tenant_context'):
        g.tenant_context = TenantContext()
    return g.tenant_context

def set_tenant_context(store_id, store_data=None):
    """Set tenant context in Flask g."""
    context = get_tenant_context()
    context.set_store(store_id, store_data)

def get_current_store_id():
    """Get current store ID from context."""
    context = get_tenant_context()
    return context.get_store_id()

def validate_store_access(store_id):
    """Validate if store exists and is accessible."""
    from app.models.store import Store
    
    try:
        # Query from admin database
        store = Store.query.filter_by(
            store_id=store_id,
            is_active=True
        ).first()
        
        if not store:
            return False, "Store not found or inactive"
        
        return True, store
        
    except Exception as e:
        logging.error(f"Error validating store access: {e}")
        return False, "Database error"

def get_store_config(store_id):
    """Get configuration for specific store."""
    from app.models.store_settings import StoreSettings
    
    try:
        settings = StoreSettings.query.filter_by(store_id=store_id).first()
        if settings:
            return settings.to_dict()
        return {}
        
    except Exception as e:
        logging.error(f"Error getting store config: {e}")
        return {}

# Tenant configuration for different environments
TENANT_CONFIGS = {
    'development': {
        'allow_localhost': True,
        'require_subdomain': False,
        'default_store': 'demo'
    },
    'production': {
        'allow_localhost': False,
        'require_subdomain': True,
        'default_store': None
    },
    'testing': {
        'allow_localhost': True,
        'require_subdomain': False,
        'default_store': 'test'
    }
}

def get_tenant_config():
    """Get tenant configuration for current environment."""
    env = current_app.config.get('ENV', 'development')
    return TENANT_CONFIGS.get(env, TENANT_CONFIGS['development'])