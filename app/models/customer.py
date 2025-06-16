from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL

class Customer(db.Model):
    """Customer model for store customers."""
    
    __tablename__ = 'customers'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Basic information
    email = db.Column(VARCHAR(120), nullable=False, index=True)
    password_hash = db.Column(VARCHAR(255), nullable=True)  # Null for guest customers
    
    # Personal details
    first_name = db.Column(VARCHAR(50), nullable=False)
    last_name = db.Column(VARCHAR(50), nullable=False)
    phone = db.Column(VARCHAR(20))
    date_of_birth = db.Column(DATETIME, nullable=True)
    gender = db.Column(VARCHAR(10))  # male, female, other, prefer_not_to_say
    
    # Account status
    is_active = db.Column(BOOLEAN, default=True)
    is_verified = db.Column(BOOLEAN, default=False)
    verification_token = db.Column(VARCHAR(100), nullable=True)
    
    # Marketing preferences
    accepts_marketing = db.Column(BOOLEAN, default=True)
    marketing_opt_in_date = db.Column(DATETIME, nullable=True)
    
    # Customer addresses
    addresses = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "id": 1,
    #     "type": "billing", # billing, shipping, both
    #     "is_default": true,
    #     "first_name": "John",
    #     "last_name": "Doe",
    #     "company": "Company Inc",
    #     "address_line_1": "123 Main St",
    #     "address_line_2": "Apt 4B",
    #     "city": "New York",
    #     "state": "NY",
    #     "postal_code": "10001",
    #     "country": "USA",
    #     "phone": "+1234567890"
    #   }
    # ]
    
    # Customer segments/tags
    tags = db.Column(JSON, default=lambda: [])
    customer_group = db.Column(VARCHAR(50), default='regular')  # vip, wholesale, regular
    
    # Purchase history and analytics
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(DECIMAL(15, 2), default=0.00)
    average_order_value = db.Column(DECIMAL(10, 2), default=0.00)
    last_order_date = db.Column(DATETIME, nullable=True)
    first_order_date = db.Column(DATETIME, nullable=True)
    
    # Customer lifecycle
    customer_lifetime_value = db.Column(DECIMAL(15, 2), default=0.00)
    loyalty_points = db.Column(db.Integer, default=0)
    referral_code = db.Column(VARCHAR(20), nullable=True)
    referred_by = db.Column(VARCHAR(20), nullable=True)
    
    # Preferences
    preferred_language = db.Column(VARCHAR(5), default='en')
    preferred_currency = db.Column(VARCHAR(3), default='USD')
    timezone = db.Column(VARCHAR(50), default='UTC')
    
    # Wishlist
    wishlist = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "product_id": 123,
    #     "variant_id": 1,
    #     "added_at": "2024-01-01T10:00:00Z",
    #     "notes": "For birthday gift"
    #   }
    # ]
    
    # Cart (persistent)
    cart_items = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "product_id": 123,
    #     "variant_id": 1,
    #     "quantity": 2,
    #     "added_at": "2024-01-01T10:00:00Z"
    #   }
    # ]
    
    # Login and session tracking
    last_login = db.Column(DATETIME, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(DATETIME, nullable=True)
    
    # Password reset
    reset_token = db.Column(VARCHAR(100), nullable=True)
    reset_token_expires = db.Column(DATETIME, nullable=True)
    
    # Additional metadata
    registration_source = db.Column(VARCHAR(50), default='website')  # website, mobile, social, import
    utm_source = db.Column(VARCHAR(100))  # Marketing attribution
    utm_medium = db.Column(VARCHAR(100))
    utm_campaign = db.Column(VARCHAR(100))
    
    # Custom fields for additional data
    custom_fields = db.Column(JSON, default=lambda: {})
    
    # Notes from admin
    admin_notes = db.Column(TEXT)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_email', 'store_id', 'email'),
        db.Index('idx_store_phone', 'store_id', 'phone'),
        db.Index('idx_store_group', 'store_id', 'customer_group'),
        db.UniqueConstraint('store_id', 'email', name='uq_store_customer_email'),
    )
    
    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
    
    def generate_referral_code(self):
        """Generate unique referral code."""
        import uuid
        import random
        import string
        
        # Generate 8-character alphanumeric code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ensure uniqueness
        while Customer.query.filter_by(store_id=self.store_id, referral_code=code).first():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        return code
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get customer's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self):
        """Convert customer to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'accepts_marketing': self.accepts_marketing,
            'addresses': self.addresses or [],
            'tags': self.tags or [],
            'customer_group': self.customer_group,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent) if self.total_spent else 0.0,
            'average_order_value': float(self.average_order_value) if self.average_order_value else 0.0,
            'last_order_date': self.last_order_date.isoformat() if self.last_order_date else None,
            'first_order_date': self.first_order_date.isoformat() if self.first_order_date else None,
            'customer_lifetime_value': float(self.customer_lifetime_value) if self.customer_lifetime_value else 0.0,
            'loyalty_points': self.loyalty_points,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'preferred_language': self.preferred_language,
            'preferred_currency': self.preferred_currency,
            'timezone': self.timezone,
            'registration_source': self.registration_source,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'custom_fields': self.custom_fields or {},
            'admin_notes': self.admin_notes,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_public_dict(self):
        """Convert customer to public dictionary (without sensitive data)."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'addresses': self.addresses or [],
            'customer_group': self.customer_group,
            'loyalty_points': self.loyalty_points,
            'total_orders': self.total_orders,
            'preferred_language': self.preferred_language,
            'preferred_currency': self.preferred_currency
        }
    
    def add_address(self, address_data):
        """Add new address to customer."""
        addresses = self.addresses or []
        
        # Generate new address ID
        max_id = max([addr.get('id', 0) for addr in addresses], default=0)
        address_data['id'] = max_id + 1
        
        # If this is the first address, make it default
        if not addresses:
            address_data['is_default'] = True
        
        addresses.append(address_data)
        self.addresses = addresses
        
        return address_data['id']
    
    def update_address(self, address_id, address_data):
        """Update existing address."""
        addresses = self.addresses or []
        
        for i, address in enumerate(addresses):
            if address.get('id') == address_id:
                addresses[i].update(address_data)
                self.addresses = addresses
                return True
        
        return False
    
    def remove_address(self, address_id):
        """Remove address from customer."""
        if not self.addresses:
            return False
        
        addresses = [addr for addr in self.addresses if addr.get('id') != address_id]
        
        # If removed address was default, make first remaining address default
        if addresses and not any(addr.get('is_default') for addr in addresses):
            addresses[0]['is_default'] = True
        
        self.addresses = addresses
        return True
    
    def get_default_address(self, address_type='both'):
        """Get default address of specified type."""
        for address in (self.addresses or []):
            if address.get('is_default') and address.get('type') in [address_type, 'both']:
                return address
        
        # Fallback to first address of type
        for address in (self.addresses or []):
            if address.get('type') in [address_type, 'both']:
                return address
        
        return None
    
    def add_to_wishlist(self, product_id, variant_id=None, notes=None):
        """Add product to wishlist."""
        wishlist = self.wishlist or []
        
        # Check if already in wishlist
        for item in wishlist:
            if (item.get('product_id') == product_id and 
                item.get('variant_id') == variant_id):
                return False
        
        wishlist_item = {
            'product_id': product_id,
            'variant_id': variant_id,
            'added_at': datetime.utcnow().isoformat(),
            'notes': notes
        }
        
        wishlist.append(wishlist_item)
        self.wishlist = wishlist
        return True
    
    def remove_from_wishlist(self, product_id, variant_id=None):
        """Remove product from wishlist."""
        if not self.wishlist:
            return False
        
        self.wishlist = [
            item for item in self.wishlist
            if not (item.get('product_id') == product_id and 
                   item.get('variant_id') == variant_id)
        ]
        return True
    
    def is_in_wishlist(self, product_id, variant_id=None):
        """Check if product is in wishlist."""
        for item in (self.wishlist or []):
            if (item.get('product_id') == product_id and 
                item.get('variant_id') == variant_id):
                return True
        return False
    
    def add_to_cart(self, product_id, quantity=1, variant_id=None):
        """Add product to persistent cart."""
        cart_items = self.cart_items or []
        
        # Check if item already in cart
        for item in cart_items:
            if (item.get('product_id') == product_id and 
                item.get('variant_id') == variant_id):
                item['quantity'] = item.get('quantity', 0) + quantity
                self.cart_items = cart_items
                return True
        
        # Add new item
        cart_item = {
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity,
            'added_at': datetime.utcnow().isoformat()
        }
        
        cart_items.append(cart_item)
        self.cart_items = cart_items
        return True
    
    def update_cart_item(self, product_id, quantity, variant_id=None):
        """Update cart item quantity."""
        cart_items = self.cart_items or []
        
        for item in cart_items:
            if (item.get('product_id') == product_id and 
                item.get('variant_id') == variant_id):
                if quantity <= 0:
                    cart_items.remove(item)
                else:
                    item['quantity'] = quantity
                self.cart_items = cart_items
                return True
        
        return False
    
    def remove_from_cart(self, product_id, variant_id=None):
        """Remove item from cart."""
        if not self.cart_items:
            return False
        
        self.cart_items = [
            item for item in self.cart_items
            if not (item.get('product_id') == product_id and 
                   item.get('variant_id') == variant_id)
        ]
        return True
    
    def clear_cart(self):
        """Clear all items from cart."""
        self.cart_items = []
    
    def get_cart_total_quantity(self):
        """Get total quantity of items in cart."""
        return sum(item.get('quantity', 0) for item in (self.cart_items or []))
    
    def add_tag(self, tag):
        """Add tag to customer."""
        tags = self.tags or []
        if tag not in tags:
            tags.append(tag)
            self.tags = tags
    
    def remove_tag(self, tag):
        """Remove tag from customer."""
        if self.tags and tag in self.tags:
            tags = self.tags.copy()
            tags.remove(tag)
            self.tags = tags
    
    def add_loyalty_points(self, points):
        """Add loyalty points."""
        self.loyalty_points = (self.loyalty_points or 0) + points
    
    def redeem_loyalty_points(self, points):
        """Redeem loyalty points."""
        if (self.loyalty_points or 0) >= points:
            self.loyalty_points -= points
            return True
        return False
    
    def record_order(self, order_amount):
        """Record new order for analytics."""
        self.total_orders += 1
        self.total_spent = (self.total_spent or 0) + order_amount
        self.average_order_value = self.total_spent / self.total_orders
        self.last_order_date = datetime.utcnow()
        
        if not self.first_order_date:
            self.first_order_date = datetime.utcnow()
        
        # Update customer lifetime value (simplified calculation)
        self.customer_lifetime_value = self.total_spent
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def increment_failed_login(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def is_account_locked(self):
        """Check if account is locked."""
        if not self.account_locked_until:
            return False
        
        return datetime.utcnow() < self.account_locked_until
    
    def unlock_account(self):
        """Unlock customer account."""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def generate_reset_token(self):
        """Generate password reset token."""
        import uuid
        from datetime import timedelta
        
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
    
    def get_customer_segment(self):
        """Determine customer segment based on purchase behavior."""
        if self.total_orders == 0:
            return 'new'
        elif self.total_orders == 1:
            return 'one_time'
        elif self.total_spent > 1000:
            return 'vip'
        elif self.total_orders >= 5:
            return 'loyal'
        else:
            return 'regular'
    
    def days_since_last_order(self):
        """Calculate days since last order."""
        if not self.last_order_date:
            return None
        
        delta = datetime.utcnow() - self.last_order_date
        return delta.days
    
    def is_at_risk(self):
        """Check if customer is at risk of churning."""
        days_since_last = self.days_since_last_order()
        return days_since_last and days_since_last > 90
    
    @classmethod
    def get_by_email(cls, store_id, email):
        """Get customer by email."""
        return cls.query.filter_by(store_id=store_id, email=email.lower()).first()
    
    @classmethod
    def get_by_phone(cls, store_id, phone):
        """Get customer by phone."""
        return cls.query.filter_by(store_id=store_id, phone=phone).first()
    
    @classmethod
    def get_by_referral_code(cls, store_id, referral_code):
        """Get customer by referral code."""
        return cls.query.filter_by(store_id=store_id, referral_code=referral_code).first()
    
    @classmethod
    def get_vip_customers(cls, store_id, min_spent=1000):
        """Get VIP customers based on spending."""
        return cls.query.filter(
            cls.store_id == store_id,
            cls.total_spent >= min_spent,
            cls.is_active == True
        ).order_by(cls.total_spent.desc()).all()
    
    @classmethod
    def get_customers_by_segment(cls, store_id, segment):
        """Get customers by segment."""
        if segment == 'new':
            return cls.query.filter_by(store_id=store_id, total_orders=0).all()
        elif segment == 'one_time':
            return cls.query.filter_by(store_id=store_id, total_orders=1).all()
        elif segment == 'vip':
            return cls.query.filter(
                cls.store_id == store_id,
                cls.total_spent > 1000
            ).all()
        elif segment == 'loyal':
            return cls.query.filter(
                cls.store_id == store_id,
                cls.total_orders >= 5
            ).all()
        else:
            return cls.query.filter_by(store_id=store_id).all()
    
    @classmethod
    def get_at_risk_customers(cls, store_id, days=90):
        """Get customers at risk of churning."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.store_id == store_id,
            cls.last_order_date < cutoff_date,
            cls.total_orders > 0,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_customer_stats(cls, store_id):
        """Get customer statistics for store."""
        customers = cls.query.filter_by(store_id=store_id, is_active=True).all()
        
        if not customers:
            return {
                'total_customers': 0,
                'new_customers': 0,
                'vip_customers': 0,
                'average_ltv': 0.0,
                'average_orders': 0.0
            }
        
        return {
            'total_customers': len(customers),
            'new_customers': len([c for c in customers if c.total_orders == 0]),
            'vip_customers': len([c for c in customers if c.total_spent > 1000]),
            'average_ltv': sum(float(c.customer_lifetime_value or 0) for c in customers) / len(customers),
            'average_orders': sum(c.total_orders for c in customers) / len(customers)
        }
    
    def __repr__(self):
        return f'<Customer {self.email} ({self.get_full_name()})>'