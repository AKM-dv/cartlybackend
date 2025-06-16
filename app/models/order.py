from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL, INTEGER

class Order(db.Model):
    """Order model for managing customer orders."""
    
    __tablename__ = 'orders'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Order identification
    order_number = db.Column(VARCHAR(50), nullable=False, unique=True)
    order_token = db.Column(VARCHAR(100), nullable=False)  # For guest access
    
    # Customer information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    is_guest_order = db.Column(BOOLEAN, default=False)
    
    # Customer details (for guest orders or snapshot)
    customer_email = db.Column(VARCHAR(120), nullable=False)
    customer_phone = db.Column(VARCHAR(20))
    customer_name = db.Column(VARCHAR(200), nullable=False)
    
    # Billing address
    billing_address = db.Column(JSON, nullable=False)
    # Structure: {
    #   "first_name": "John",
    #   "last_name": "Doe", 
    #   "company": "Company Inc",
    #   "address_line_1": "123 Main St",
    #   "address_line_2": "Apt 4B",
    #   "city": "New York",
    #   "state": "NY",
    #   "postal_code": "10001",
    #   "country": "USA",
    #   "phone": "+1234567890"
    # }
    
    # Shipping address
    shipping_address = db.Column(JSON, nullable=False)
    same_as_billing = db.Column(BOOLEAN, default=True)
    
    # Order items
    order_items = db.Column(JSON, nullable=False)
    # Structure: [
    #   {
    #     "product_id": 123,
    #     "product_name": "Product Name",
    #     "product_sku": "SKU-001",
    #     "variant_id": 1,
    #     "variant_options": {"Size": "M", "Color": "Red"},
    #     "quantity": 2,
    #     "unit_price": 29.99,
    #     "total_price": 59.98,
    #     "product_image": "/uploads/product.jpg"
    #   }
    # ]
    
    # Pricing breakdown
    subtotal = db.Column(DECIMAL(10, 2), nullable=False)
    tax_amount = db.Column(DECIMAL(10, 2), default=0.00)
    shipping_amount = db.Column(DECIMAL(10, 2), default=0.00)
    discount_amount = db.Column(DECIMAL(10, 2), default=0.00)
    total_amount = db.Column(DECIMAL(10, 2), nullable=False)
    
    # Currency
    currency = db.Column(VARCHAR(3), default='USD')
    exchange_rate = db.Column(DECIMAL(10, 4), default=1.0000)
    
    # Order status
    status = db.Column(VARCHAR(20), default='pending')
    # pending, confirmed, processing, shipped, delivered, cancelled, refunded
    
    payment_status = db.Column(VARCHAR(20), default='pending')
    # pending, paid, partially_paid, failed, refunded, partially_refunded
    
    fulfillment_status = db.Column(VARCHAR(20), default='unfulfilled')
    # unfulfilled, partial, fulfilled, returned
    
    # Payment information
    payment_method = db.Column(VARCHAR(50))
    payment_gateway = db.Column(VARCHAR(50))
    payment_transaction_id = db.Column(VARCHAR(100))
    payment_reference = db.Column(VARCHAR(100))
    
    # Shipping information
    shipping_method = db.Column(VARCHAR(100))
    shipping_partner = db.Column(VARCHAR(50))
    tracking_number = db.Column(VARCHAR(100))
    tracking_url = db.Column(VARCHAR(500))
    expected_delivery_date = db.Column(DATETIME)
    
    # Discounts and coupons
    coupon_code = db.Column(VARCHAR(50))
    coupon_discount = db.Column(DECIMAL(10, 2), default=0.00)
    
    # Notes and instructions
    customer_notes = db.Column(TEXT)
    admin_notes = db.Column(TEXT)
    special_instructions = db.Column(TEXT)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    confirmed_at = db.Column(DATETIME, nullable=True)
    shipped_at = db.Column(DATETIME, nullable=True)
    delivered_at = db.Column(DATETIME, nullable=True)
    cancelled_at = db.Column(DATETIME, nullable=True)
    
    # Additional metadata
    source = db.Column(VARCHAR(20), default='website')  # website, mobile_app, admin, api
    user_agent = db.Column(TEXT)
    ip_address = db.Column(VARCHAR(45))
    
    # Order tags for organization
    tags = db.Column(JSON, default=lambda: [])
    
    # Risk assessment
    risk_level = db.Column(VARCHAR(10), default='low')  # low, medium, high
    fraud_score = db.Column(INTEGER, default=0)  # 0-100
    
    # Relationships
    customer = db.relationship('Customer', backref='orders')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_order', 'store_id', 'order_number'),
        db.Index('idx_store_customer', 'store_id', 'customer_id'),
        db.Index('idx_store_status', 'store_id', 'status'),
        db.Index('idx_store_payment_status', 'store_id', 'payment_status'),
        db.Index('idx_store_created', 'store_id', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.order_token:
            self.order_token = self.generate_order_token()
    
    def generate_order_number(self):
        """Generate unique order number."""
        import uuid
        from app.models.store_settings import StoreSettings
        
        # Get order prefix from store settings
        settings = StoreSettings.get_by_store_id(self.store_id)
        prefix = settings.order_prefix if settings else 'ORD'
        
        # Generate number with timestamp and random component
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().int)[:6]
        
        order_number = f"{prefix}-{timestamp}-{random_part}"
        
        # Ensure uniqueness
        counter = 1
        base_number = order_number
        while Order.query.filter_by(order_number=order_number).first():
            order_number = f"{base_number}-{counter}"
            counter += 1
        
        return order_number
    
    def generate_order_token(self):
        """Generate order token for guest access."""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self):
        """Convert order to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'order_number': self.order_number,
            'order_token': self.order_token,
            'customer_id': self.customer_id,
            'is_guest_order': self.is_guest_order,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'billing_address': self.billing_address or {},
            'shipping_address': self.shipping_address or {},
            'same_as_billing': self.same_as_billing,
            'order_items': self.order_items or [],
            'subtotal': float(self.subtotal) if self.subtotal else 0.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0.0,
            'shipping_amount': float(self.shipping_amount) if self.shipping_amount else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else 1.0,
            'status': self.status,
            'payment_status': self.payment_status,
            'fulfillment_status': self.fulfillment_status,
            'payment_method': self.payment_method,
            'payment_gateway': self.payment_gateway,
            'payment_transaction_id': self.payment_transaction_id,
            'payment_reference': self.payment_reference,
            'shipping_method': self.shipping_method,
            'shipping_partner': self.shipping_partner,
            'tracking_number': self.tracking_number,
            'tracking_url': self.tracking_url,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'coupon_code': self.coupon_code,
            'coupon_discount': float(self.coupon_discount) if self.coupon_discount else 0.0,
            'customer_notes': self.customer_notes,
            'admin_notes': self.admin_notes,
            'special_instructions': self.special_instructions,
            'source': self.source,
            'tags': self.tags or [],
            'risk_level': self.risk_level,
            'fraud_score': self.fraud_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }
    
    def to_public_dict(self):
        """Convert order to public dictionary (for customer view)."""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'payment_status': self.payment_status,
            'fulfillment_status': self.fulfillment_status,
            'order_items': self.get_public_order_items(),
            'subtotal': float(self.subtotal) if self.subtotal else 0.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0.0,
            'shipping_amount': float(self.shipping_amount) if self.shipping_amount else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'currency': self.currency,
            'billing_address': self.billing_address,
            'shipping_address': self.shipping_address,
            'shipping_method': self.shipping_method,
            'tracking_number': self.tracking_number,
            'tracking_url': self.tracking_url,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }
    
    def get_public_order_items(self):
        """Get order items without sensitive data."""
        public_items = []
        for item in (self.order_items or []):
            public_items.append({
                'product_name': item.get('product_name'),
                'product_sku': item.get('product_sku'),
                'variant_options': item.get('variant_options', {}),
                'quantity': item.get('quantity'),
                'unit_price': item.get('unit_price'),
                'total_price': item.get('total_price'),
                'product_image': item.get('product_image')
            })
        return public_items
    
    def get_total_quantity(self):
        """Get total quantity of items in order."""
        return sum(item.get('quantity', 0) for item in (self.order_items or []))
    
    def get_item_count(self):
        """Get number of different items in order."""
        return len(self.order_items or [])
    
    def can_cancel(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed'] and self.payment_status != 'paid'
    
    def can_refund(self):
        """Check if order can be refunded."""
        return self.payment_status in ['paid', 'partially_paid']
    
    def can_ship(self):
        """Check if order can be shipped."""
        return (self.status == 'confirmed' and 
                self.payment_status == 'paid' and 
                self.fulfillment_status == 'unfulfilled')
    
    def confirm(self):
        """Confirm the order."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = datetime.utcnow()
            return True
        return False
    
    def ship(self, tracking_number=None, shipping_partner=None):
        """Mark order as shipped."""
        if self.can_ship():
            self.status = 'shipped'
            self.fulfillment_status = 'fulfilled'
            self.shipped_at = datetime.utcnow()
            
            if tracking_number:
                self.tracking_number = tracking_number
            if shipping_partner:
                self.shipping_partner = shipping_partner
            
            return True
        return False
    
    def deliver(self):
        """Mark order as delivered."""
        if self.status == 'shipped':
            self.status = 'delivered'
            self.delivered_at = datetime.utcnow()
            return True
        return False
    
    def cancel(self, reason=None):
        """Cancel the order."""
        if self.can_cancel():
            self.status = 'cancelled'
            self.cancelled_at = datetime.utcnow()
            
            if reason:
                self.admin_notes = f"Cancelled: {reason}"
            
            return True
        return False
    
    def add_tag(self, tag):
        """Add tag to order."""
        tags = self.tags or []
        if tag not in tags:
            tags.append(tag)
            self.tags = tags
    
    def remove_tag(self, tag):
        """Remove tag from order."""
        if self.tags and tag in self.tags:
            tags = self.tags.copy()
            tags.remove(tag)
            self.tags = tags
    
    def update_payment_status(self, status, transaction_id=None):
        """Update payment status."""
        self.payment_status = status
        
        if transaction_id:
            self.payment_transaction_id = transaction_id
        
        # Auto-confirm order if payment is successful
        if status == 'paid' and self.status == 'pending':
            self.confirm()
    
    def calculate_totals(self):
        """Recalculate order totals."""
        self.subtotal = sum(
            item.get('total_price', 0) 
            for item in (self.order_items or [])
        )
        
        self.total_amount = (
            self.subtotal + 
            (self.tax_amount or 0) + 
            (self.shipping_amount or 0) - 
            (self.discount_amount or 0) - 
            (self.coupon_discount or 0)
        )
    
    def get_status_history(self):
        """Get order status change history."""
        history = []
        
        if self.created_at:
            history.append({
                'status': 'created',
                'timestamp': self.created_at,
                'label': 'Order Created'
            })
        
        if self.confirmed_at:
            history.append({
                'status': 'confirmed',
                'timestamp': self.confirmed_at,
                'label': 'Order Confirmed'
            })
        
        if self.shipped_at:
            history.append({
                'status': 'shipped',
                'timestamp': self.shipped_at,
                'label': 'Order Shipped'
            })
        
        if self.delivered_at:
            history.append({
                'status': 'delivered',
                'timestamp': self.delivered_at,
                'label': 'Order Delivered'
            })
        
        if self.cancelled_at:
            history.append({
                'status': 'cancelled',
                'timestamp': self.cancelled_at,
                'label': 'Order Cancelled'
            })
        
        return sorted(history, key=lambda x: x['timestamp'])
    
    @classmethod
    def get_by_order_number(cls, store_id, order_number):
        """Get order by order number."""
        return cls.query.filter_by(store_id=store_id, order_number=order_number).first()
    
    @classmethod
    def get_by_token(cls, order_token):
        """Get order by token (for guest access)."""
        return cls.query.filter_by(order_token=order_token).first()
    
    @classmethod
    def get_customer_orders(cls, store_id, customer_id, limit=None):
        """Get orders for a customer."""
        query = cls.query.filter_by(store_id=store_id, customer_id=customer_id)
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_pending_orders(cls, store_id):
        """Get pending orders that need attention."""
        return cls.query.filter_by(
            store_id=store_id,
            status='pending'
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_orders_by_status(cls, store_id, status, limit=None):
        """Get orders by status."""
        query = cls.query.filter_by(store_id=store_id, status=status)
        
        if limit:
            query = query.limit(limit)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent_orders(cls, store_id, days=7, limit=50):
        """Get recent orders."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.store_id == store_id,
            cls.created_at >= cutoff_date
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_sales_stats(cls, store_id, start_date=None, end_date=None):
        """Get sales statistics for a date range."""
        query = cls.query.filter(
            cls.store_id == store_id,
            cls.payment_status == 'paid'
        )
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        orders = query.all()
        
        return {
            'total_orders': len(orders),
            'total_revenue': sum(float(order.total_amount) for order in orders),
            'average_order_value': sum(float(order.total_amount) for order in orders) / len(orders) if orders else 0,
            'total_items_sold': sum(order.get_total_quantity() for order in orders)
        }
    
    def __repr__(self):
        return f'<Order {self.order_number} ({self.status})>'