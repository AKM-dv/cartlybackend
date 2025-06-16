from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL

class ShippingPartner(db.Model):
    """Shipping partner configuration for stores."""
    
    __tablename__ = 'shipping_partners'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Partner identification
    partner_name = db.Column(VARCHAR(50), nullable=False)  # shiprocket, delhivery, bluedart, fedex
    display_name = db.Column(VARCHAR(100), nullable=False)
    partner_type = db.Column(VARCHAR(20), nullable=False)  # courier, logistics, local
    
    # Configuration
    is_active = db.Column(BOOLEAN, default=False, nullable=False)
    is_test_mode = db.Column(BOOLEAN, default=True, nullable=False)
    priority = db.Column(db.Integer, default=0)  # Display order
    
    # API credentials
    api_key = db.Column(VARCHAR(255))
    api_secret = db.Column(VARCHAR(255))
    api_token = db.Column(VARCHAR(500))  # For authentication
    merchant_id = db.Column(VARCHAR(100))
    
    # Additional configuration
    config_data = db.Column(JSON, default=lambda: {})
    # Structure for Shiprocket:
    # {
    #   "company_name": "Your Company",
    #   "pickup_location": "warehouse1",
    #   "channel_id": "123456",
    #   "default_length": 10,
    #   "default_width": 10,
    #   "default_height": 10,
    #   "default_weight": 0.5
    # }
    
    # Service capabilities
    supports_cod = db.Column(BOOLEAN, default=True)
    supports_prepaid = db.Column(BOOLEAN, default=True)
    supports_international = db.Column(BOOLEAN, default=False)
    supports_reverse_pickup = db.Column(BOOLEAN, default=True)
    supports_tracking = db.Column(BOOLEAN, default=True)
    
    # Delivery options
    same_day_delivery = db.Column(BOOLEAN, default=False)
    next_day_delivery = db.Column(BOOLEAN, default=False)
    express_delivery = db.Column(BOOLEAN, default=True)
    standard_delivery = db.Column(BOOLEAN, default=True)
    
    # Coverage areas
    serviceable_cities = db.Column(JSON, default=lambda: [])  # List of cities
    serviceable_states = db.Column(JSON, default=lambda: [])  # List of states
    serviceable_pincodes = db.Column(JSON, default=lambda: [])  # List of pincodes
    non_serviceable_areas = db.Column(JSON, default=lambda: [])  # Excluded areas
    
    # Pricing configuration
    pricing_type = db.Column(VARCHAR(20), default="weight_based")  # weight_based, zone_based, flat_rate
    base_rate = db.Column(DECIMAL(10, 2), default=0.00)
    per_kg_rate = db.Column(DECIMAL(10, 2), default=0.00)
    fuel_surcharge = db.Column(DECIMAL(5, 2), default=0.00)  # Percentage
    
    # Weight and dimension limits
    min_weight = db.Column(DECIMAL(8, 3), default=0.001)  # kg
    max_weight = db.Column(DECIMAL(8, 3), default=50.000)  # kg
    max_length = db.Column(DECIMAL(8, 2), default=100.00)  # cm
    max_width = db.Column(DECIMAL(8, 2), default=100.00)  # cm
    max_height = db.Column(DECIMAL(8, 2), default=100.00)  # cm
    
    # Delivery time estimates
    standard_delivery_days = db.Column(db.Integer, default=3)
    express_delivery_days = db.Column(db.Integer, default=1)
    
    # Pickup configuration
    pickup_enabled = db.Column(BOOLEAN, default=True)
    pickup_address = db.Column(JSON, default=lambda: {})
    # {
    #   "contact_name": "John Doe",
    #   "phone": "+919876543210",
    #   "address_line_1": "123 Business St",
    #   "address_line_2": "Near Mall",
    #   "city": "Mumbai",
    #   "state": "Maharashtra",
    #   "pincode": "400001",
    #   "country": "India"
    # }
    
    pickup_timings = db.Column(JSON, default=lambda: {
        'monday': {'start': '10:00', 'end': '18:00', 'available': True},
        'tuesday': {'start': '10:00', 'end': '18:00', 'available': True},
        'wednesday': {'start': '10:00', 'end': '18:00', 'available': True},
        'thursday': {'start': '10:00', 'end': '18:00', 'available': True},
        'friday': {'start': '10:00', 'end': '18:00', 'available': True},
        'saturday': {'start': '10:00', 'end': '16:00', 'available': True},
        'sunday': {'start': '10:00', 'end': '16:00', 'available': False}
    })
    
    # Return and exchange
    return_policy_days = db.Column(db.Integer, default=7)
    supports_exchange = db.Column(BOOLEAN, default=True)
    return_charges = db.Column(DECIMAL(10, 2), default=0.00)
    
    # Insurance and additional services
    insurance_available = db.Column(BOOLEAN, default=True)
    fragile_handling = db.Column(BOOLEAN, default=False)
    signature_required = db.Column(BOOLEAN, default=False)
    
    # Webhook and notifications
    webhook_url = db.Column(VARCHAR(255))
    sms_notifications = db.Column(BOOLEAN, default=True)
    email_notifications = db.Column(BOOLEAN, default=True)
    whatsapp_notifications = db.Column(BOOLEAN, default=False)
    
    # Statistics
    total_shipments = db.Column(db.Integer, default=0)
    successful_deliveries = db.Column(db.Integer, default=0)
    failed_deliveries = db.Column(db.Integer, default=0)
    average_delivery_time = db.Column(DECIMAL(5, 2), default=0.00)  # in days
    last_shipment_at = db.Column(DATETIME, nullable=True)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    activated_at = db.Column(DATETIME, nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_partner', 'store_id', 'partner_name'),
        db.Index('idx_store_active', 'store_id', 'is_active'),
    )
    
    def to_dict(self):
        """Convert shipping partner to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'partner_name': self.partner_name,
            'display_name': self.display_name,
            'partner_type': self.partner_type,
            'is_active': self.is_active,
            'is_test_mode': self.is_test_mode,
            'priority': self.priority,
            'supports_cod': self.supports_cod,
            'supports_prepaid': self.supports_prepaid,
            'supports_international': self.supports_international,
            'supports_reverse_pickup': self.supports_reverse_pickup,
            'supports_tracking': self.supports_tracking,
            'same_day_delivery': self.same_day_delivery,
            'next_day_delivery': self.next_day_delivery,
            'express_delivery': self.express_delivery,
            'standard_delivery': self.standard_delivery,
            'serviceable_cities': self.serviceable_cities or [],
            'serviceable_states': self.serviceable_states or [],
            'serviceable_pincodes': self.serviceable_pincodes or [],
            'pricing_type': self.pricing_type,
            'base_rate': float(self.base_rate) if self.base_rate else 0.0,
            'per_kg_rate': float(self.per_kg_rate) if self.per_kg_rate else 0.0,
            'fuel_surcharge': float(self.fuel_surcharge) if self.fuel_surcharge else 0.0,
            'min_weight': float(self.min_weight) if self.min_weight else 0.001,
            'max_weight': float(self.max_weight) if self.max_weight else 50.0,
            'max_length': float(self.max_length) if self.max_length else 100.0,
            'max_width': float(self.max_width) if self.max_width else 100.0,
            'max_height': float(self.max_height) if self.max_height else 100.0,
            'standard_delivery_days': self.standard_delivery_days,
            'express_delivery_days': self.express_delivery_days,
            'pickup_enabled': self.pickup_enabled,
            'pickup_address': self.pickup_address or {},
            'pickup_timings': self.pickup_timings or {},
            'return_policy_days': self.return_policy_days,
            'supports_exchange': self.supports_exchange,
            'return_charges': float(self.return_charges) if self.return_charges else 0.0,
            'insurance_available': self.insurance_available,
            'total_shipments': self.total_shipments,
            'successful_deliveries': self.successful_deliveries,
            'failed_deliveries': self.failed_deliveries,
            'average_delivery_time': float(self.average_delivery_time) if self.average_delivery_time else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_shipping_config(self):
        """Get shipping configuration for API integration."""
        config = {
            'partner_name': self.partner_name,
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'api_token': self.api_token,
            'is_test_mode': self.is_test_mode,
            'webhook_url': self.webhook_url
        }
        
        if self.partner_name == 'shiprocket':
            config.update({
                'company_name': self.config_data.get('company_name', ''),
                'pickup_location': self.config_data.get('pickup_location', ''),
                'channel_id': self.config_data.get('channel_id', '')
            })
        
        return config
    
    def calculate_shipping_cost(self, weight, dimensions=None, destination_pincode=None):
        """Calculate shipping cost based on weight and dimensions."""
        if not self.is_serviceable(destination_pincode):
            return None
        
        cost = float(self.base_rate or 0)
        
        if self.pricing_type == 'weight_based':
            cost += weight * float(self.per_kg_rate or 0)
        
        # Add fuel surcharge
        if self.fuel_surcharge:
            cost += cost * (float(self.fuel_surcharge) / 100)
        
        return round(cost, 2)
    
    def is_serviceable(self, pincode):
        """Check if delivery is available to the pincode."""
        if not pincode:
            return False
        
        # Check if in non-serviceable areas
        if pincode in (self.non_serviceable_areas or []):
            return False
        
        # Check if in serviceable pincodes (if specified)
        serviceable_pincodes = self.serviceable_pincodes or []
        if serviceable_pincodes and pincode not in serviceable_pincodes:
            return False
        
        return True
    
    def is_weight_acceptable(self, weight):
        """Check if weight is within limits."""
        return self.min_weight <= weight <= self.max_weight
    
    def is_dimensions_acceptable(self, length, width, height):
        """Check if dimensions are within limits."""
        return (length <= self.max_length and 
                width <= self.max_width and 
                height <= self.max_height)
    
    def get_delivery_estimate(self, service_type='standard'):
        """Get delivery time estimate."""
        if service_type == 'express' and self.express_delivery:
            return self.express_delivery_days
        else:
            return self.standard_delivery_days
    
    def update_shipment_stats(self, delivered=True, delivery_days=None):
        """Update shipment statistics."""
        self.total_shipments += 1
        self.last_shipment_at = datetime.utcnow()
        
        if delivered:
            self.successful_deliveries += 1
            if delivery_days:
                # Update average delivery time
                total_days = (self.average_delivery_time * (self.successful_deliveries - 1)) + delivery_days
                self.average_delivery_time = total_days / self.successful_deliveries
        else:
            self.failed_deliveries += 1
    
    def get_delivery_success_rate(self):
        """Calculate delivery success rate."""
        if self.total_shipments == 0:
            return 0.0
        
        return round((self.successful_deliveries / self.total_shipments) * 100, 2)
    
    def activate(self):
        """Activate the shipping partner."""
        self.is_active = True
        self.activated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the shipping partner."""
        self.is_active = False
    
    @classmethod
    def get_active_partners(cls, store_id):
        """Get active shipping partners for a store."""
        return cls.query.filter_by(
            store_id=store_id, 
            is_active=True
        ).order_by(cls.priority.desc()).all()
    
    @classmethod
    def get_by_partner_name(cls, store_id, partner_name):
        """Get partner by name for a store."""
        return cls.query.filter_by(store_id=store_id, partner_name=partner_name).first()
    
    @classmethod
    def get_serviceable_partners(cls, store_id, pincode, weight=None):
        """Get partners that can deliver to the pincode."""
        partners = cls.get_active_partners(store_id)
        serviceable = []
        
        for partner in partners:
            if partner.is_serviceable(pincode):
                if weight is None or partner.is_weight_acceptable(weight):
                    serviceable.append(partner)
        
        return serviceable
    
    @classmethod
    def create_default_partners(cls, store_id):
        """Create default shipping partners for a store."""
        default_partners = [
            {
                'partner_name': 'shiprocket',
                'display_name': 'Shiprocket',
                'partner_type': 'logistics',
                'supports_cod': True,
                'supports_prepaid': True,
                'supports_tracking': True,
                'express_delivery': True,
                'standard_delivery': True,
                'serviceable_states': ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu']
            },
            {
                'partner_name': 'delhivery',
                'display_name': 'Delhivery',
                'partner_type': 'logistics',
                'supports_cod': True,
                'supports_prepaid': True,
                'supports_tracking': True,
                'express_delivery': True,
                'standard_delivery': True
            },
            {
                'partner_name': 'local_delivery',
                'display_name': 'Local Delivery',
                'partner_type': 'local',
                'supports_cod': True,
                'supports_prepaid': True,
                'same_day_delivery': True,
                'is_active': True,
                'base_rate': 50.0
            }
        ]
        
        partners = []
        for i, partner_data in enumerate(default_partners):
            partner = cls(
                store_id=store_id,
                priority=i + 1,
                **partner_data
            )
            partners.append(partner)
            db.session.add(partner)
        
        db.session.commit()
        return partners
    
    def __repr__(self):
        return f'<ShippingPartner {self.partner_name} for {self.store_id}>'