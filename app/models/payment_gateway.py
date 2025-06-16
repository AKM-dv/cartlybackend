from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL

class PaymentGateway(db.Model):
    """Payment gateway configuration for stores."""
    
    __tablename__ = 'payment_gateways'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Gateway identification
    gateway_name = db.Column(VARCHAR(50), nullable=False)  # razorpay, paypal, stripe, phonepe
    gateway_type = db.Column(VARCHAR(20), nullable=False)  # online, offline, wallet
    display_name = db.Column(VARCHAR(100), nullable=False)
    
    # Configuration
    is_active = db.Column(BOOLEAN, default=False, nullable=False)
    is_test_mode = db.Column(BOOLEAN, default=True, nullable=False)
    priority = db.Column(db.Integer, default=0)  # Display order
    
    # Gateway credentials (encrypted in production)
    api_key = db.Column(VARCHAR(255))
    api_secret = db.Column(VARCHAR(255))
    webhook_secret = db.Column(VARCHAR(255))
    merchant_id = db.Column(VARCHAR(100))
    
    # Additional configuration
    config_data = db.Column(JSON, default=lambda: {})
    # Structure varies by gateway:
    # Razorpay: {"theme_color": "#3399cc", "checkout_logo": "url"}
    # PayPal: {"client_id": "xxx", "client_secret": "xxx", "mode": "sandbox"}
    # PhonePe: {"merchant_key": "xxx", "salt": "xxx", "env": "sandbox"}
    
    # Payment options
    supported_currencies = db.Column(JSON, default=lambda: ["USD"])
    min_amount = db.Column(DECIMAL(10, 2), default=0.01)
    max_amount = db.Column(DECIMAL(10, 2), nullable=True)
    
    # Fees and charges
    transaction_fee_type = db.Column(VARCHAR(20), default="percentage")  # percentage, fixed, mixed
    transaction_fee_value = db.Column(DECIMAL(5, 4), default=0.0000)  # 2.9% = 0.0290
    fixed_fee = db.Column(DECIMAL(10, 2), default=0.00)
    
    # Gateway-specific features
    supports_refunds = db.Column(BOOLEAN, default=True)
    supports_partial_refunds = db.Column(BOOLEAN, default=True)
    supports_recurring = db.Column(BOOLEAN, default=False)
    supports_preauth = db.Column(BOOLEAN, default=False)
    
    # UI configuration
    display_logo = db.Column(VARCHAR(255))  # Gateway logo URL
    display_description = db.Column(TEXT)
    button_color = db.Column(VARCHAR(7), default="#007bff")
    button_text_color = db.Column(VARCHAR(7), default="#ffffff")
    
    # Processing settings
    auto_capture = db.Column(BOOLEAN, default=True)
    payment_timeout = db.Column(db.Integer, default=900)  # seconds
    retry_attempts = db.Column(db.Integer, default=3)
    
    # Webhooks and callbacks
    webhook_url = db.Column(VARCHAR(255))
    success_url = db.Column(VARCHAR(255))
    failure_url = db.Column(VARCHAR(255))
    cancel_url = db.Column(VARCHAR(255))
    
    # Status and monitoring
    last_transaction_at = db.Column(DATETIME, nullable=True)
    total_transactions = db.Column(db.Integer, default=0)
    total_amount_processed = db.Column(DECIMAL(15, 2), default=0.00)
    failed_transactions = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    activated_at = db.Column(DATETIME, nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_store_gateway', 'store_id', 'gateway_name'),
        db.Index('idx_store_active', 'store_id', 'is_active'),
    )
    
    def to_dict(self):
        """Convert payment gateway to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'gateway_name': self.gateway_name,
            'gateway_type': self.gateway_type,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'is_test_mode': self.is_test_mode,
            'priority': self.priority,
            'supported_currencies': self.supported_currencies or [],
            'min_amount': float(self.min_amount) if self.min_amount else 0.01,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'transaction_fee_type': self.transaction_fee_type,
            'transaction_fee_value': float(self.transaction_fee_value) if self.transaction_fee_value else 0.0,
            'fixed_fee': float(self.fixed_fee) if self.fixed_fee else 0.0,
            'supports_refunds': self.supports_refunds,
            'supports_partial_refunds': self.supports_partial_refunds,
            'supports_recurring': self.supports_recurring,
            'supports_preauth': self.supports_preauth,
            'display_logo': self.display_logo,
            'display_description': self.display_description,
            'button_color': self.button_color,
            'button_text_color': self.button_text_color,
            'auto_capture': self.auto_capture,
            'payment_timeout': self.payment_timeout,
            'retry_attempts': self.retry_attempts,
            'total_transactions': self.total_transactions,
            'total_amount_processed': float(self.total_amount_processed) if self.total_amount_processed else 0.0,
            'failed_transactions': self.failed_transactions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None
        }
    
    def to_public_dict(self):
        """Convert to public dictionary (without sensitive credentials)."""
        return {
            'id': self.id,
            'gateway_name': self.gateway_name,
            'gateway_type': self.gateway_type,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'supported_currencies': self.supported_currencies or [],
            'min_amount': float(self.min_amount) if self.min_amount else 0.01,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'display_logo': self.display_logo,
            'display_description': self.display_description,
            'button_color': self.button_color,
            'button_text_color': self.button_text_color,
            'supports_refunds': self.supports_refunds,
            'payment_timeout': self.payment_timeout
        }
    
    def get_gateway_config(self):
        """Get gateway-specific configuration."""
        base_config = {
            'api_key': self.api_key,
            'is_test_mode': self.is_test_mode,
            'auto_capture': self.auto_capture,
            'webhook_url': self.webhook_url
        }
        
        if self.gateway_name == 'razorpay':
            base_config.update({
                'key_id': self.api_key,
                'key_secret': self.api_secret,
                'theme_color': self.config_data.get('theme_color', '#3399cc'),
                'checkout_logo': self.config_data.get('checkout_logo', '')
            })
        elif self.gateway_name == 'paypal':
            base_config.update({
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'mode': 'sandbox' if self.is_test_mode else 'live'
            })
        elif self.gateway_name == 'phonepe':
            base_config.update({
                'merchant_id': self.merchant_id,
                'merchant_key': self.api_key,
                'salt': self.api_secret,
                'env': 'sandbox' if self.is_test_mode else 'production'
            })
        
        return base_config
    
    def calculate_fees(self, amount):
        """Calculate transaction fees for given amount."""
        fees = 0.0
        
        if self.transaction_fee_type == 'percentage':
            fees = amount * float(self.transaction_fee_value or 0)
        elif self.transaction_fee_type == 'fixed':
            fees = float(self.fixed_fee or 0)
        elif self.transaction_fee_type == 'mixed':
            fees = (amount * float(self.transaction_fee_value or 0)) + float(self.fixed_fee or 0)
        
        return round(fees, 2)
    
    def is_amount_supported(self, amount):
        """Check if amount is within supported range."""
        if amount < self.min_amount:
            return False
        
        if self.max_amount and amount > self.max_amount:
            return False
        
        return True
    
    def is_currency_supported(self, currency):
        """Check if currency is supported."""
        supported = self.supported_currencies or []
        return currency.upper() in [c.upper() for c in supported]
    
    def update_transaction_stats(self, amount, success=True):
        """Update transaction statistics."""
        self.total_transactions += 1
        self.last_transaction_at = datetime.utcnow()
        
        if success:
            self.total_amount_processed += amount
        else:
            self.failed_transactions += 1
    
    def get_success_rate(self):
        """Calculate transaction success rate."""
        if self.total_transactions == 0:
            return 0.0
        
        successful_transactions = self.total_transactions - self.failed_transactions
        return round((successful_transactions / self.total_transactions) * 100, 2)
    
    def activate(self):
        """Activate the payment gateway."""
        self.is_active = True
        self.activated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the payment gateway."""
        self.is_active = False
    
    @classmethod
    def get_active_gateways(cls, store_id, currency=None):
        """Get active payment gateways for a store."""
        query = cls.query.filter_by(store_id=store_id, is_active=True).order_by(cls.priority.desc())
        
        gateways = query.all()
        
        if currency:
            gateways = [gw for gw in gateways if gw.is_currency_supported(currency)]
        
        return gateways
    
    @classmethod
    def get_by_gateway_name(cls, store_id, gateway_name):
        """Get gateway by name for a store."""
        return cls.query.filter_by(store_id=store_id, gateway_name=gateway_name).first()
    
    @classmethod
    def create_default_gateways(cls, store_id):
        """Create default payment gateways for a store."""
        default_gateways = [
            {
                'gateway_name': 'razorpay',
                'gateway_type': 'online',
                'display_name': 'Razorpay',
                'display_description': 'Pay securely with cards, UPI, wallets & more',
                'supported_currencies': ['INR'],
                'display_logo': '/static/payment-logos/razorpay.png'
            },
            {
                'gateway_name': 'paypal',
                'gateway_type': 'online',
                'display_name': 'PayPal',
                'display_description': 'Pay with your PayPal account',
                'supported_currencies': ['USD', 'EUR', 'GBP'],
                'display_logo': '/static/payment-logos/paypal.png'
            },
            {
                'gateway_name': 'phonepe',
                'gateway_type': 'wallet',
                'display_name': 'PhonePe',
                'display_description': 'Pay using PhonePe wallet',
                'supported_currencies': ['INR'],
                'display_logo': '/static/payment-logos/phonepe.png'
            },
            {
                'gateway_name': 'cod',
                'gateway_type': 'offline',
                'display_name': 'Cash on Delivery',
                'display_description': 'Pay when you receive your order',
                'supported_currencies': ['INR', 'USD'],
                'is_active': True,
                'display_logo': '/static/payment-logos/cod.png'
            }
        ]
        
        gateways = []
        for i, gateway_data in enumerate(default_gateways):
            gateway = cls(
                store_id=store_id,
                priority=i + 1,
                **gateway_data
            )
            gateways.append(gateway)
            db.session.add(gateway)
        
        db.session.commit()
        return gateways
    
    def __repr__(self):
        return f'<PaymentGateway {self.gateway_name} for {self.store_id}>'