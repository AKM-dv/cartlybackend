# ====================
# Path: config.py
# ====================

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'multistore_admin'
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
                              f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Multi-tenant settings
    TENANT_DATABASE_PREFIX = os.environ.get('TENANT_DATABASE_PREFIX') or 'store_'
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Redis settings for caching and sessions
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API settings
    API_VERSION = 'v1'
    API_TITLE = 'MultiStore API'
    
    # Pagination settings
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# ====================
# Path: app/config/__init__.py
# ====================

"""
Configuration package initialization.
Contains database, multi-tenant, and application configuration.
"""

from .database import db, db_manager, init_db, get_db, get_store_db
from .multi_tenant import (
    get_current_tenant,
    set_current_tenant,
    get_store_config,
    switch_tenant_context,
    TenantContext
)

__all__ = [
    'db',
    'db_manager', 
    'init_db',
    'get_db',
    'get_store_db',
    'get_current_tenant',
    'set_current_tenant',
    'get_store_config',
    'switch_tenant_context',
    'TenantContext'
]

# ====================
# Path: app/config/multi_tenant.py
# ====================

"""
Multi-tenant configuration and context management.
"""

from flask import g, current_app
from contextlib import contextmanager
import threading

# Thread-local storage for tenant context
_local = threading.local()

class TenantContext:
    """Tenant context manager for multi-tenant operations."""
    
    def __init__(self, store_id):
        self.store_id = store_id
        self.previous_store_id = None
    
    def __enter__(self):
        self.previous_store_id = get_current_tenant()
        set_current_tenant(self.store_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_current_tenant(self.previous_store_id)

def get_current_tenant():
    """Get current tenant store ID from context."""
    return getattr(_local, 'store_id', None) or getattr(g, 'store_id', None)

def set_current_tenant(store_id):
    """Set current tenant store ID in context."""
    _local.store_id = store_id
    g.store_id = store_id

def get_store_config(store_id):
    """Get configuration for specific store."""
    from app.models.store import Store
    from app.models.store_settings import StoreSettings
    
    store = Store.get_by_store_id(store_id)
    if not store:
        return None
    
    settings = StoreSettings.get_by_store_id(store_id)
    
    return {
        'store_id': store_id,
        'store_name': store.store_name,
        'domain': store.domain,
        'subdomain': store.subdomain,
        'custom_domain': store.custom_domain,
        'settings': settings.to_dict() if settings else {},
        'is_active': store.is_active,
        'is_setup_complete': store.is_setup_complete
    }

@contextmanager
def switch_tenant_context(store_id):
    """Context manager for switching tenant context."""
    previous_store_id = get_current_tenant()
    try:
        set_current_tenant(store_id)
        yield store_id
    finally:
        set_current_tenant(previous_store_id)

def clear_tenant_context():
    """Clear current tenant context."""
    _local.store_id = None
    if hasattr(g, 'store_id'):
        g.store_id = None