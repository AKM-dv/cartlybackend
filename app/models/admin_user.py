from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON
import uuid

class AdminUser(db.Model):
    """Admin user model for store management."""
    
    __tablename__ = 'admin_users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    user_id = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)
    email = db.Column(VARCHAR(120), unique=True, nullable=False, index=True)
    username = db.Column(VARCHAR(80), unique=True, nullable=False)
    
    # Authentication
    password_hash = db.Column(VARCHAR(255), nullable=False)
    is_verified = db.Column(BOOLEAN, default=False, nullable=False)
    verification_token = db.Column(VARCHAR(100), nullable=True)
    
    # Personal information
    first_name = db.Column(VARCHAR(50), nullable=False)
    last_name = db.Column(VARCHAR(50), nullable=False)
    phone = db.Column(VARCHAR(20))
    avatar = db.Column(VARCHAR(255))  # Profile picture URL
    
    # Role and permissions
    role = db.Column(VARCHAR(20), default='store_admin', nullable=False)  # super_admin, store_admin, staff
    permissions = db.Column(JSON, default=lambda: [])  # List of specific permissions
    
    # Account status
    is_active = db.Column(BOOLEAN, default=True, nullable=False)
    is_locked = db.Column(BOOLEAN, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=True)  # Null for super admin
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(DATETIME, nullable=True)
    password_changed_at = db.Column(DATETIME, default=datetime.utcnow)
    
    # Password reset
    reset_token = db.Column(VARCHAR(100), nullable=True)
    reset_token_expires = db.Column(DATETIME, nullable=True)
    
    # Relationships
    store = db.relationship('Store', backref='admin_users')
    
    def __init__(self, **kwargs):
        super(AdminUser, self).__init__(**kwargs)
        if not self.user_id:
            self.user_id = self.generate_user_id()
    
    @staticmethod
    def generate_user_id():
        """Generate unique user ID."""
        return str(uuid.uuid4()).replace('-', '')[:12]
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'avatar': self.avatar,
            'role': self.role,
            'permissions': self.permissions or [],
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_locked': self.is_locked,
            'store_id': self.store_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None
        }
    
    def to_public_dict(self):
        """Convert user to public dictionary (without sensitive data)."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.get_full_name(),
            'avatar': self.avatar,
            'role': self.role,
            'is_active': self.is_active
        }
    
    def has_permission(self, permission):
        """Check if user has specific permission."""
        if self.role == 'super_admin':
            return True
        
        return permission in (self.permissions or [])
    
    def add_permission(self, permission):
        """Add permission to user."""
        if not self.permissions:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """Remove permission from user."""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)
    
    def is_store_owner(self):
        """Check if user is store owner."""
        return self.role in ['store_admin'] and self.store_id is not None
    
    def is_super_admin(self):
        """Check if user is super admin."""
        return self.role == 'super_admin'
    
    def can_access_store(self, store_id):
        """Check if user can access specific store."""
        if self.is_super_admin():
            return True
        
        return self.store_id == store_id
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.is_locked = True
    
    def unlock_account(self):
        """Unlock user account."""
        self.is_locked = False
        self.failed_login_attempts = 0
    
    def generate_reset_token(self):
        """Generate password reset token."""
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token."""
        if not self.reset_token or not self.reset_token_expires:
            return False
        
        if self.reset_token != token:
            return False
        
        return datetime.utcnow() <= self.reset_token_expires
    
    def clear_reset_token(self):
        """Clear password reset token."""
        self.reset_token = None
        self.reset_token_expires = None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email."""
        return cls.query.filter_by(email=email.lower()).first()
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username."""
        return cls.query.filter_by(username=username.lower()).first()
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """Get user by user_id."""
        return cls.query.filter_by(user_id=user_id).first()
    
    @classmethod
    def get_store_admins(cls, store_id):
        """Get all admins for a store."""
        return cls.query.filter_by(store_id=store_id, is_active=True).all()
    
    def __repr__(self):
        return f'<AdminUser {self.username} ({self.email})>'