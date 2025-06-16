from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL

class StoreSettings(db.Model):
    """Store settings and configuration model."""
    
    __tablename__ = 'store_settings'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False, unique=True)
    
    # Basic store settings
    store_logo = db.Column(VARCHAR(255))  # Logo URL
    store_favicon = db.Column(VARCHAR(255))  # Favicon URL
    store_banner = db.Column(VARCHAR(255))  # Banner image URL
    
    # Theme and appearance
    theme_name = db.Column(VARCHAR(50), default='default')
    primary_color = db.Column(VARCHAR(7), default='#007bff')  # Hex color
    secondary_color = db.Column(VARCHAR(7), default='#6c757d')
    accent_color = db.Column(VARCHAR(7), default='#28a745')
    
    # Typography
    font_family = db.Column(VARCHAR(50), default='Inter')
    font_size_base = db.Column(VARCHAR(10), default='16px')
    
    # Currency and locale
    currency_code = db.Column(VARCHAR(3), default='USD')
    currency_symbol = db.Column(VARCHAR(5), default='$')
    currency_position = db.Column(VARCHAR(10), default='before')  # before, after
    decimal_places = db.Column(db.Integer, default=2)
    
    # Locale settings
    language = db.Column(VARCHAR(5), default='en')
    timezone = db.Column(VARCHAR(50), default='UTC')
    date_format = db.Column(VARCHAR(20), default='YYYY-MM-DD')
    time_format = db.Column(VARCHAR(10), default='24h')  # 12h, 24h
    
    # SEO settings
    meta_title = db.Column(VARCHAR(60))
    meta_description = db.Column(VARCHAR(160))
    meta_keywords = db.Column(TEXT)
    google_analytics_id = db.Column(VARCHAR(20))
    facebook_pixel_id = db.Column(VARCHAR(20))
    
    # Social media links
    social_media = db.Column(JSON, default=lambda: {
        'facebook': '',
        'instagram': '',
        'twitter': '',
        'youtube': '',
        'linkedin': '',
        'tiktok': ''
    })
    
    # Business hours
    business_hours = db.Column(JSON, default=lambda: {
        'monday': {'open': '09:00', 'close': '18:00', 'closed': False},
        'tuesday': {'open': '09:00', 'close': '18:00', 'closed': False},
        'wednesday': {'open': '09:00', 'close': '18:00', 'closed': False},
        'thursday': {'open': '09:00', 'close': '18:00', 'closed': False},
        'friday': {'open': '09:00', 'close': '18:00', 'closed': False},
        'saturday': {'open': '10:00', 'close': '16:00', 'closed': False},
        'sunday': {'open': '10:00', 'close': '16:00', 'closed': True}
    })
    
    # Order settings
    auto_accept_orders = db.Column(BOOLEAN, default=True)
    order_prefix = db.Column(VARCHAR(10), default='ORD')
    min_order_amount = db.Column(DECIMAL(10, 2), default=0.00)
    max_order_amount = db.Column(DECIMAL(10, 2), nullable=True)
    
    # Inventory settings
    track_inventory = db.Column(BOOLEAN, default=True)
    allow_backorders = db.Column(BOOLEAN, default=False)
    low_stock_threshold = db.Column(db.Integer, default=5)
    
    # Tax settings
    tax_inclusive = db.Column(BOOLEAN, default=False)
    default_tax_rate = db.Column(DECIMAL(5, 2), default=0.00)
    tax_name = db.Column(VARCHAR(50), default='Tax')
    
    # Shipping settings
    free_shipping_threshold = db.Column(DECIMAL(10, 2), nullable=True)
    default_shipping_rate = db.Column(DECIMAL(10, 2), default=0.00)
    
    # Email settings
    order_confirmation_email = db.Column(BOOLEAN, default=True)
    order_shipped_email = db.Column(BOOLEAN, default=True)
    low_stock_email = db.Column(BOOLEAN, default=True)
    admin_email_notifications = db.Column(BOOLEAN, default=True)
    
    # Feature toggles
    enable_reviews = db.Column(BOOLEAN, default=True)
    enable_wishlist = db.Column(BOOLEAN, default=True)
    enable_compare = db.Column(BOOLEAN, default=False)
    enable_guest_checkout = db.Column(BOOLEAN, default=True)
    enable_coupon_codes = db.Column(BOOLEAN, default=True)
    enable_loyalty_points = db.Column(BOOLEAN, default=False)
    
    # Maintenance mode
    maintenance_mode = db.Column(BOOLEAN, default=False)
    maintenance_message = db.Column(TEXT)
    maintenance_allowed_ips = db.Column(JSON, default=lambda: [])
    
    # API settings
    api_enabled = db.Column(BOOLEAN, default=False)
    api_key = db.Column(VARCHAR(100), nullable=True)
    webhook_url = db.Column(VARCHAR(255), nullable=True)
    
    # Custom CSS/JS
    custom_css = db.Column(TEXT)
    custom_js = db.Column(TEXT)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert settings to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'store_logo': self.store_logo,
            'store_favicon': self.store_favicon,
            'store_banner': self.store_banner,
            'theme_name': self.theme_name,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'font_family': self.font_family,
            'font_size_base': self.font_size_base,
            'currency_code': self.currency_code,
            'currency_symbol': self.currency_symbol,
            'currency_position': self.currency_position,
            'decimal_places': self.decimal_places,
            'language': self.language,
            'timezone': self.timezone,
            'date_format': self.date_format,
            'time_format': self.time_format,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'google_analytics_id': self.google_analytics_id,
            'facebook_pixel_id': self.facebook_pixel_id,
            'social_media': self.social_media or {},
            'business_hours': self.business_hours or {},
            'auto_accept_orders': self.auto_accept_orders,
            'order_prefix': self.order_prefix,
            'min_order_amount': float(self.min_order_amount) if self.min_order_amount else 0.00,
            'max_order_amount': float(self.max_order_amount) if self.max_order_amount else None,
            'track_inventory': self.track_inventory,
            'allow_backorders': self.allow_backorders,
            'low_stock_threshold': self.low_stock_threshold,
            'tax_inclusive': self.tax_inclusive,
            'default_tax_rate': float(self.default_tax_rate) if self.default_tax_rate else 0.00,
            'tax_name': self.tax_name,
            'free_shipping_threshold': float(self.free_shipping_threshold) if self.free_shipping_threshold else None,
            'default_shipping_rate': float(self.default_shipping_rate) if self.default_shipping_rate else 0.00,
            'order_confirmation_email': self.order_confirmation_email,
            'order_shipped_email': self.order_shipped_email,
            'low_stock_email': self.low_stock_email,
            'admin_email_notifications': self.admin_email_notifications,
            'enable_reviews': self.enable_reviews,
            'enable_wishlist': self.enable_wishlist,
            'enable_compare': self.enable_compare,
            'enable_guest_checkout': self.enable_guest_checkout,
            'enable_coupon_codes': self.enable_coupon_codes,
            'enable_loyalty_points': self.enable_loyalty_points,
            'maintenance_mode': self.maintenance_mode,
            'maintenance_message': self.maintenance_message,
            'maintenance_allowed_ips': self.maintenance_allowed_ips or [],
            'api_enabled': self.api_enabled,
            'api_key': self.api_key,
            'webhook_url': self.webhook_url,
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_theme_config(self):
        """Get theme configuration."""
        return {
            'theme_name': self.theme_name,
            'colors': {
                'primary': self.primary_color,
                'secondary': self.secondary_color,
                'accent': self.accent_color
            },
            'typography': {
                'font_family': self.font_family,
                'font_size_base': self.font_size_base
            }
        }
    
    def get_currency_config(self):
        """Get currency configuration."""
        return {
            'code': self.currency_code,
            'symbol': self.currency_symbol,
            'position': self.currency_position,
            'decimal_places': self.decimal_places
        }
    
    def format_currency(self, amount):
        """Format amount according to currency settings."""
        formatted_amount = f"{amount:.{self.decimal_places}f}"
        
        if self.currency_position == 'before':
            return f"{self.currency_symbol}{formatted_amount}"
        else:
            return f"{formatted_amount}{self.currency_symbol}"
    
    def is_store_open_now(self):
        """Check if store is currently open."""
        from datetime import datetime
        import pytz
        
        if self.maintenance_mode:
            return False
        
        # Get current time in store timezone
        tz = pytz.timezone(self.timezone)
        now = datetime.now(tz)
        current_day = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')
        
        business_hours = self.business_hours or {}
        day_hours = business_hours.get(current_day, {})
        
        if day_hours.get('closed', False):
            return False
        
        open_time = day_hours.get('open', '09:00')
        close_time = day_hours.get('close', '18:00')
        
        return open_time <= current_time <= close_time
    
    @classmethod
    def get_by_store_id(cls, store_id):
        """Get settings by store ID."""
        return cls.query.filter_by(store_id=store_id).first()
    
    @classmethod
    def create_default(cls, store_id):
        """Create default settings for a store."""
        settings = cls(store_id=store_id)
        db.session.add(settings)
        db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<StoreSettings for {self.store_id}>'