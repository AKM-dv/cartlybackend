from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON

class ContactDetails(db.Model):
    """Contact details and address information for stores."""
    
    __tablename__ = 'contact_details'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False, unique=True)
    
    # Primary contact information
    primary_email = db.Column(VARCHAR(120), nullable=False)
    secondary_email = db.Column(VARCHAR(120))
    customer_service_email = db.Column(VARCHAR(120))
    
    # Phone numbers
    primary_phone = db.Column(VARCHAR(20), nullable=False)
    secondary_phone = db.Column(VARCHAR(20))
    whatsapp_number = db.Column(VARCHAR(20))
    toll_free_number = db.Column(VARCHAR(20))
    
    # Physical address
    address_line_1 = db.Column(VARCHAR(255), nullable=False)
    address_line_2 = db.Column(VARCHAR(255))
    city = db.Column(VARCHAR(100), nullable=False)
    state = db.Column(VARCHAR(100), nullable=False)
    postal_code = db.Column(VARCHAR(20), nullable=False)
    country = db.Column(VARCHAR(100), nullable=False)
    
    # Geographic coordinates
    latitude = db.Column(VARCHAR(20))
    longitude = db.Column(VARCHAR(20))
    
    # Billing address (if different from physical)
    billing_same_as_physical = db.Column(BOOLEAN, default=True)
    billing_address_line_1 = db.Column(VARCHAR(255))
    billing_address_line_2 = db.Column(VARCHAR(255))
    billing_city = db.Column(VARCHAR(100))
    billing_state = db.Column(VARCHAR(100))
    billing_postal_code = db.Column(VARCHAR(20))
    billing_country = db.Column(VARCHAR(100))
    
    # Additional contact methods
    website_url = db.Column(VARCHAR(255))
    support_url = db.Column(VARCHAR(255))
    contact_form_email = db.Column(VARCHAR(120))
    
    # Business information
    business_registration_number = db.Column(VARCHAR(100))
    tax_identification_number = db.Column(VARCHAR(100))
    vat_number = db.Column(VARCHAR(100))
    
    # Store hours and contact preferences
    contact_hours = db.Column(JSON, default=lambda: {
        'monday': {'start': '09:00', 'end': '18:00', 'available': True},
        'tuesday': {'start': '09:00', 'end': '18:00', 'available': True},
        'wednesday': {'start': '09:00', 'end': '18:00', 'available': True},
        'thursday': {'start': '09:00', 'end': '18:00', 'available': True},
        'friday': {'start': '09:00', 'end': '18:00', 'available': True},
        'saturday': {'start': '10:00', 'end': '16:00', 'available': True},
        'sunday': {'start': '10:00', 'end': '16:00', 'available': False}
    })
    
    # Emergency contact
    emergency_contact_name = db.Column(VARCHAR(100))
    emergency_contact_phone = db.Column(VARCHAR(20))
    emergency_contact_email = db.Column(VARCHAR(120))
    
    # Delivery and pickup information
    pickup_available = db.Column(BOOLEAN, default=False)
    pickup_instructions = db.Column(TEXT)
    delivery_areas = db.Column(JSON, default=lambda: [])  # List of serviceable areas
    
    # Contact form settings
    enable_contact_form = db.Column(BOOLEAN, default=True)
    contact_form_recipients = db.Column(JSON, default=lambda: [])  # Email addresses to receive form submissions
    auto_reply_enabled = db.Column(BOOLEAN, default=True)
    auto_reply_message = db.Column(TEXT, default="Thank you for contacting us. We will get back to you within 24 hours.")
    
    # Map settings
    show_map = db.Column(BOOLEAN, default=True)
    map_zoom_level = db.Column(db.Integer, default=15)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert contact details to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'primary_email': self.primary_email,
            'secondary_email': self.secondary_email,
            'customer_service_email': self.customer_service_email,
            'primary_phone': self.primary_phone,
            'secondary_phone': self.secondary_phone,
            'whatsapp_number': self.whatsapp_number,
            'toll_free_number': self.toll_free_number,
            'address_line_1': self.address_line_1,
            'address_line_2': self.address_line_2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'billing_same_as_physical': self.billing_same_as_physical,
            'billing_address_line_1': self.billing_address_line_1,
            'billing_address_line_2': self.billing_address_line_2,
            'billing_city': self.billing_city,
            'billing_state': self.billing_state,
            'billing_postal_code': self.billing_postal_code,
            'billing_country': self.billing_country,
            'website_url': self.website_url,
            'support_url': self.support_url,
            'contact_form_email': self.contact_form_email,
            'business_registration_number': self.business_registration_number,
            'tax_identification_number': self.tax_identification_number,
            'vat_number': self.vat_number,
            'contact_hours': self.contact_hours or {},
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_email': self.emergency_contact_email,
            'pickup_available': self.pickup_available,
            'pickup_instructions': self.pickup_instructions,
            'delivery_areas': self.delivery_areas or [],
            'enable_contact_form': self.enable_contact_form,
            'contact_form_recipients': self.contact_form_recipients or [],
            'auto_reply_enabled': self.auto_reply_enabled,
            'auto_reply_message': self.auto_reply_message,
            'show_map': self.show_map,
            'map_zoom_level': self.map_zoom_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_full_address(self):
        """Get formatted full address."""
        address_parts = [self.address_line_1]
        
        if self.address_line_2:
            address_parts.append(self.address_line_2)
        
        address_parts.extend([
            self.city,
            self.state,
            self.postal_code,
            self.country
        ])
        
        return ', '.join(filter(None, address_parts))
    
    def get_billing_address(self):
        """Get formatted billing address."""
        if self.billing_same_as_physical:
            return self.get_full_address()
        
        address_parts = [self.billing_address_line_1]
        
        if self.billing_address_line_2:
            address_parts.append(self.billing_address_line_2)
        
        if all([self.billing_city, self.billing_state, self.billing_postal_code, self.billing_country]):
            address_parts.extend([
                self.billing_city,
                self.billing_state,
                self.billing_postal_code,
                self.billing_country
            ])
        
        return ', '.join(filter(None, address_parts))
    
    def get_contact_methods(self):
        """Get all available contact methods."""
        methods = []
        
        if self.primary_email:
            methods.append({'type': 'email', 'value': self.primary_email, 'label': 'Primary Email'})
        
        if self.primary_phone:
            methods.append({'type': 'phone', 'value': self.primary_phone, 'label': 'Primary Phone'})
        
        if self.whatsapp_number:
            methods.append({'type': 'whatsapp', 'value': self.whatsapp_number, 'label': 'WhatsApp'})
        
        if self.customer_service_email:
            methods.append({'type': 'email', 'value': self.customer_service_email, 'label': 'Customer Service'})
        
        return methods
    
    def is_contact_hours_now(self):
        """Check if current time is within contact hours."""
        from datetime import datetime
        import pytz
        
        # This would need the store's timezone from settings
        now = datetime.now()
        current_day = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')
        
        contact_hours = self.contact_hours or {}
        day_hours = contact_hours.get(current_day, {})
        
        if not day_hours.get('available', False):
            return False
        
        start_time = day_hours.get('start', '09:00')
        end_time = day_hours.get('end', '18:00')
        
        return start_time <= current_time <= end_time
    
    def is_delivery_available_in_area(self, area):
        """Check if delivery is available in specific area."""
        delivery_areas = self.delivery_areas or []
        return area.lower() in [da.lower() for da in delivery_areas]
    
    @classmethod
    def get_by_store_id(cls, store_id):
        """Get contact details by store ID."""
        return cls.query.filter_by(store_id=store_id).first()
    
    @classmethod
    def create_default(cls, store_id, email, phone, address_data):
        """Create default contact details for a store."""
        contact = cls(
            store_id=store_id,
            primary_email=email,
            primary_phone=phone,
            **address_data
        )
        db.session.add(contact)
        db.session.commit()
        return contact
    
    def __repr__(self):
        return f'<ContactDetails for {self.store_id}>'