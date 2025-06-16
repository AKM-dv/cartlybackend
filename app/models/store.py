from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME
import uuid

class Store(db.Model):
    """Store model for multi-tenant ecommerce platform."""
    
    __tablename__ = 'stores'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store identification
    store_id = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)
    store_name = db.Column(VARCHAR(100), nullable=False)
    store_description = db.Column(TEXT)
    
    # Domain and URL settings
    domain = db.Column(VARCHAR(100), unique=True, nullable=False)
    subdomain = db.Column(VARCHAR(50), unique=True, nullable=False)
    custom_domain = db.Column(VARCHAR(100), unique=True, nullable=True)
    
    # Store owner details
    owner_name = db.Column(VARCHAR(100), nullable=False)
    owner_email = db.Column(VARCHAR(100), nullable=False)
    owner_phone = db.Column(VARCHAR(20))
    
    # Business details
    business_name = db.Column(VARCHAR(150))
    business_type = db.Column(VARCHAR(50))  # retail, wholesale, services
    business_registration = db.Column(VARCHAR(100))
    tax_id = db.Column(VARCHAR(50))
    
    # Store status
    is_active = db.Column(BOOLEAN, default=True, nullable=False)
    is_setup_complete = db.Column(BOOLEAN, default=False, nullable=False)
    subscription_status = db.Column(VARCHAR(20), default='trial')  # trial, active, suspended, cancelled
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    setup_completed_at = db.Column(DATETIME, nullable=True)
    last_activity = db.Column(DATETIME, default=datetime.utcnow)
    
    # Subscription details
    plan_type = db.Column(VARCHAR(20), default='basic')  # basic, premium, enterprise
    subscription_start = db.Column(DATETIME, default=datetime.utcnow)
    subscription_end = db.Column(DATETIME, nullable=True)
    
    # Store limits based on plan
    max_products = db.Column(db.Integer, default=100)
    max_storage_mb = db.Column(db.Integer, default=500)
    max_orders_per_month = db.Column(db.Integer, default=1000)
    
    # Relationships
    settings = db.relationship('StoreSettings', backref='store', uselist=False, cascade='all, delete-orphan')
    contact_details = db.relationship('ContactDetails', backref='store', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Store, self).__init__(**kwargs)
        if not self.store_id:
            self.store_id = self.generate_store_id()
    
    @staticmethod
    def generate_store_id():
        """Generate unique store ID."""
        return str(uuid.uuid4()).replace('-', '')[:12]
    
    def to_dict(self):
        """Convert store to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'store_name': self.store_name,
            'store_description': self.store_description,
            'domain': self.domain,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'owner_name': self.owner_name,
            'owner_email': self.owner_email,
            'owner_phone': self.owner_phone,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'business_registration': self.business_registration,
            'tax_id': self.tax_id,
            'is_active': self.is_active,
            'is_setup_complete': self.is_setup_complete,
            'subscription_status': self.subscription_status,
            'plan_type': self.plan_type,
            'max_products': self.max_products,
            'max_storage_mb': self.max_storage_mb,
            'max_orders_per_month': self.max_orders_per_month,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'setup_completed_at': self.setup_completed_at.isoformat() if self.setup_completed_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None
        }
    
    def get_store_url(self):
        """Get store frontend URL."""
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return f"https://{self.subdomain}.yourdomain.com"
    
    def is_subscription_active(self):
        """Check if subscription is active."""
        if self.subscription_status == 'active':
            if self.subscription_end:
                return datetime.utcnow() <= self.subscription_end
            return True
        return self.subscription_status == 'trial'
    
    def can_add_products(self, current_count):
        """Check if store can add more products."""
        return current_count < self.max_products
    
    def get_storage_usage_mb(self):
        """Get current storage usage (to be implemented)."""
        # TODO: Calculate actual storage usage
        return 0
    
    def can_use_storage(self, additional_mb):
        """Check if store can use additional storage."""
        current_usage = self.get_storage_usage_mb()
        return (current_usage + additional_mb) <= self.max_storage_mb
    
    def mark_setup_complete(self):
        """Mark store setup as complete."""
        self.is_setup_complete = True
        self.setup_completed_at = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    @classmethod
    def get_by_store_id(cls, store_id):
        """Get store by store_id."""
        return cls.query.filter_by(store_id=store_id, is_active=True).first()
    
    @classmethod
    def get_by_domain(cls, domain):
        """Get store by domain or subdomain."""
        return cls.query.filter(
            db.or_(
                cls.domain == domain,
                cls.subdomain == domain,
                cls.custom_domain == domain
            ),
            cls.is_active == True
        ).first()
    
    def __repr__(self):
        return f'<Store {self.store_name} ({self.store_id})>'



        """Convert store to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'store_name': self.store_name,
            'store_description': self.store_description,
            'domain': self.domain,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'owner_name': self.owner_name,
            'owner_email': self.owner_email,
            'owner_phone': self.owner_phone,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'business_registration': self.business_registration,
            'tax_id': self.tax_id,
            'is_active': self.is_active,
            'is_setup_complete': self.is_setup_complete,
            'subscription_status': self.subscription_status,
            'plan_type': self.plan_type,
            'max_products': self.max_products,
            'max_storage_mb': self.max_storage_mb,
            'max_orders_per_month': self.max_orders_per_month,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'setup_completed_at': self.setup_completed_at.isoformat() if self.setup_completed_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None
        }
    
    def get_store_url(self):
        """Get full store URL."""
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return f"https://{self.subdomain}.{self.domain}"
    
    def get_admin_url(self):
        """Get admin panel URL."""
        return f"https://admin.{self.domain}"
    
    @classmethod
    def get_by_store_id(cls, store_id):
        """Get store by store_id."""
        return cls.query.filter_by(store_id=store_id).first()
    
    @classmethod
    def get_by_domain(cls, domain):
        """Get store by domain or subdomain."""
        return cls.query.filter(
            (cls.domain == domain) | 
            (cls.subdomain == domain) | 
            (cls.custom_domain == domain)
        ).first()
    
    def update_last_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        db.session.commit()