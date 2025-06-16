from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, DECIMAL
from slugify import slugify

class Product(db.Model):
    """Product model for store inventory management."""
    
    __tablename__ = 'products'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Basic product information
    name = db.Column(VARCHAR(255), nullable=False)
    slug = db.Column(VARCHAR(300), nullable=False)
    sku = db.Column(VARCHAR(100), nullable=False)
    barcode = db.Column(VARCHAR(50))
    
    # Description and content
    short_description = db.Column(VARCHAR(500))
    description = db.Column(TEXT)
    specifications = db.Column(JSON, default=lambda: {})
    features = db.Column(JSON, default=lambda: [])
    
    # Category and classification
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    tags = db.Column(JSON, default=lambda: [])
    brand = db.Column(VARCHAR(100))
    
    # Pricing
    price = db.Column(DECIMAL(10, 2), nullable=False)
    compare_price = db.Column(DECIMAL(10, 2))  # Original price for sale items
    cost_price = db.Column(DECIMAL(10, 2))  # For profit calculation
    
    # Inventory management
    track_inventory = db.Column(BOOLEAN, default=True)
    inventory_quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    allow_backorders = db.Column(BOOLEAN, default=False)
    
    # Physical attributes
    weight = db.Column(DECIMAL(8, 3))  # kg
    length = db.Column(DECIMAL(8, 2))  # cm
    width = db.Column(DECIMAL(8, 2))   # cm
    height = db.Column(DECIMAL(8, 2))  # cm
    
    # Images
    featured_image = db.Column(VARCHAR(255))
    images = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "url": "/uploads/product1.jpg",
    #     "alt": "Product image",
    #     "order": 1,
    #     "is_featured": false
    #   }
    # ]
    
    # Product variants (size, color, etc.)
    has_variants = db.Column(BOOLEAN, default=False)
    variant_options = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "name": "Size",
    #     "values": ["S", "M", "L", "XL"]
    #   },
    #   {
    #     "name": "Color", 
    #     "values": ["Red", "Blue", "Green"]
    #   }
    # ]
    
    variants = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "id": 1,
    #     "sku": "PROD-001-S-RED",
    #     "options": {"Size": "S", "Color": "Red"},
    #     "price": 29.99,
    #     "inventory": 10,
    #     "image": "/uploads/variant1.jpg"
    #   }
    # ]
    
    # Status and visibility
    status = db.Column(VARCHAR(20), default='draft')  # draft, active, inactive, archived
    is_featured = db.Column(BOOLEAN, default=False)
    is_digital = db.Column(BOOLEAN, default=False)
    
    # SEO
    meta_title = db.Column(VARCHAR(60))
    meta_description = db.Column(VARCHAR(160))
    meta_keywords = db.Column(VARCHAR(255))
    
    # Shipping
    requires_shipping = db.Column(BOOLEAN, default=True)
    shipping_class = db.Column(VARCHAR(50))
    free_shipping = db.Column(BOOLEAN, default=False)
    
    # Tax
    tax_class = db.Column(VARCHAR(50), default='standard')
    tax_exempt = db.Column(BOOLEAN, default=False)
    
    # Reviews and ratings
    average_rating = db.Column(DECIMAL(3, 2), default=0.00)
    review_count = db.Column(db.Integer, default=0)
    
    # Sales data
    total_sales = db.Column(db.Integer, default=0)
    total_revenue = db.Column(DECIMAL(15, 2), default=0.00)
    
    # Additional options
    custom_fields = db.Column(JSON, default=lambda: {})
    download_files = db.Column(JSON, default=lambda: [])  # For digital products
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = db.Column(DATETIME, nullable=True)
    
    # Relationships
    category = db.relationship('Category', backref='products')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_product', 'store_id', 'slug'),
        db.Index('idx_store_sku', 'store_id', 'sku'),
        db.Index('idx_store_status', 'store_id', 'status'),
        db.Index('idx_store_category', 'store_id', 'category_id'),
        db.UniqueConstraint('store_id', 'slug', name='uq_store_product_slug'),
        db.UniqueConstraint('store_id', 'sku', name='uq_store_product_sku'),
    )
    
    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug()
    
    def generate_slug(self):
        """Generate URL-friendly slug from product name."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Product.query.filter_by(store_id=self.store_id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def to_dict(self):
        """Convert product to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'slug': self.slug,
            'sku': self.sku,
            'barcode': self.barcode,
            'short_description': self.short_description,
            'description': self.description,
            'specifications': self.specifications or {},
            'features': self.features or [],
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'tags': self.tags or [],
            'brand': self.brand,
            'price': float(self.price) if self.price else 0.0,
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'track_inventory': self.track_inventory,
            'inventory_quantity': self.inventory_quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'allow_backorders': self.allow_backorders,
            'weight': float(self.weight) if self.weight else None,
            'length': float(self.length) if self.length else None,
            'width': float(self.width) if self.width else None,
            'height': float(self.height) if self.height else None,
            'featured_image': self.featured_image,
            'images': self.images or [],
            'has_variants': self.has_variants,
            'variant_options': self.variant_options or [],
            'variants': self.variants or [],
            'status': self.status,
            'is_featured': self.is_featured,
            'is_digital': self.is_digital,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'requires_shipping': self.requires_shipping,
            'shipping_class': self.shipping_class,
            'free_shipping': self.free_shipping,
            'tax_class': self.tax_class,
            'tax_exempt': self.tax_exempt,
            'average_rating': float(self.average_rating) if self.average_rating else 0.0,
            'review_count': self.review_count,
            'total_sales': self.total_sales,
            'total_revenue': float(self.total_revenue) if self.total_revenue else 0.0,
            'custom_fields': self.custom_fields or {},
            'download_files': self.download_files or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
    def to_public_dict(self):
        """Convert product to public dictionary (for frontend)."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'sku': self.sku,
            'short_description': self.short_description,
            'description': self.description,
            'specifications': self.specifications or {},
            'features': self.features or [],
            'category_name': self.category.name if self.category else None,
            'tags': self.tags or [],
            'brand': self.brand,
            'price': float(self.price) if self.price else 0.0,
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'inventory_quantity': self.inventory_quantity if self.track_inventory else None,
            'in_stock': self.is_in_stock(),
            'weight': float(self.weight) if self.weight else None,
            'featured_image': self.featured_image,
            'images': self.images or [],
            'has_variants': self.has_variants,
            'variant_options': self.variant_options or [],
            'variants': self.get_public_variants(),
            'is_featured': self.is_featured,
            'is_digital': self.is_digital,
            'requires_shipping': self.requires_shipping,
            'free_shipping': self.free_shipping,
            'average_rating': float(self.average_rating) if self.average_rating else 0.0,
            'review_count': self.review_count
        }
    
    def get_public_variants(self):
        """Get variants without sensitive data."""
        if not self.has_variants:
            return []
        
        public_variants = []
        for variant in (self.variants or []):
            public_variants.append({
                'id': variant.get('id'),
                'sku': variant.get('sku'),
                'options': variant.get('options', {}),
                'price': variant.get('price'),
                'in_stock': variant.get('inventory', 0) > 0,
                'image': variant.get('image')
            })
        
        return public_variants
    
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        
        if self.has_variants:
            return any(v.get('inventory', 0) > 0 for v in (self.variants or []))
        
        return self.inventory_quantity > 0
    
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        
        if self.has_variants:
            return any(
                0 < v.get('inventory', 0) <= self.low_stock_threshold 
                for v in (self.variants or [])
            )
        
        return 0 < self.inventory_quantity <= self.low_stock_threshold
    
    def get_sale_percentage(self):
        """Calculate sale percentage if compare_price exists."""
        if not self.compare_price or self.compare_price <= self.price:
            return 0
        
        discount = self.compare_price - self.price
        return round((discount / self.compare_price) * 100)
    
    def get_profit_margin(self):
        """Calculate profit margin if cost_price exists."""
        if not self.cost_price:
            return 0
        
        profit = self.price - self.cost_price
        return round((profit / self.price) * 100, 2)
    
    def add_image(self, image_url, alt_text="", is_featured=False):
        """Add image to product."""
        images = self.images or []
        
        # Get next order number
        max_order = max([img.get('order', 0) for img in images], default=0)
        
        new_image = {
            'url': image_url,
            'alt': alt_text,
            'order': max_order + 1,
            'is_featured': is_featured
        }
        
        images.append(new_image)
        self.images = images
        
        # Set as featured image if specified or if it's the first image
        if is_featured or not self.featured_image:
            self.featured_image = image_url
    
    def remove_image(self, image_url):
        """Remove image from product."""
        if not self.images:
            return False
        
        self.images = [img for img in self.images if img.get('url') != image_url]
        
        # Update featured image if removed
        if self.featured_image == image_url:
            remaining_images = self.images or []
            self.featured_image = remaining_images[0].get('url') if remaining_images else None
        
        return True
    
    def add_variant(self, variant_data):
        """Add product variant."""
        variants = self.variants or []
        
        # Generate variant ID
        max_id = max([v.get('id', 0) for v in variants], default=0)
        variant_data['id'] = max_id + 1
        
        variants.append(variant_data)
        self.variants = variants
        self.has_variants = True
        
        return variant_data['id']
    
    def update_variant(self, variant_id, variant_data):
        """Update product variant."""
        variants = self.variants or []
        
        for i, variant in enumerate(variants):
            if variant.get('id') == variant_id:
                variants[i].update(variant_data)
                self.variants = variants
                return True
        
        return False
    
    def remove_variant(self, variant_id):
        """Remove product variant."""
        if not self.variants:
            return False
        
        self.variants = [v for v in self.variants if v.get('id') != variant_id]
        
        # Update has_variants flag
        if not self.variants:
            self.has_variants = False
        
        return True
    
    def get_variant_by_options(self, options):
        """Get variant by option combination."""
        if not self.has_variants:
            return None
        
        for variant in (self.variants or []):
            variant_options = variant.get('options', {})
            if all(variant_options.get(k) == v for k, v in options.items()):
                return variant
        
        return None
    
    def update_inventory(self, quantity, variant_id=None):
        """Update inventory quantity."""
        if variant_id:
            # Update variant inventory
            variants = self.variants or []
            for variant in variants:
                if variant.get('id') == variant_id:
                    variant['inventory'] = max(0, variant.get('inventory', 0) + quantity)
                    self.variants = variants
                    return True
            return False
        else:
            # Update main product inventory
            self.inventory_quantity = max(0, self.inventory_quantity + quantity)
            return True
    
    def publish(self):
        """Publish the product."""
        self.status = 'active'
        self.published_at = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the product."""
        self.status = 'inactive'
    
    def archive(self):
        """Archive the product."""
        self.status = 'archived'
    
    def update_rating(self, new_rating):
        """Update average rating when new review is added."""
        total_rating_points = self.average_rating * self.review_count
        total_rating_points += new_rating
        self.review_count += 1
        self.average_rating = round(total_rating_points / self.review_count, 2)
    
    def record_sale(self, quantity=1, sale_amount=None):
        """Record a sale for analytics."""
        self.total_sales += quantity
        if sale_amount:
            self.total_revenue += sale_amount
        
        # Update inventory if tracking
        if self.track_inventory:
            self.inventory_quantity = max(0, self.inventory_quantity - quantity)
    
    def get_total_inventory(self):
        """Get total inventory across all variants."""
        if not self.has_variants:
            return self.inventory_quantity
        
        return sum(v.get('inventory', 0) for v in (self.variants or []))
    
    def get_lowest_price(self):
        """Get lowest price among variants or main price."""
        if not self.has_variants:
            return float(self.price)
        
        variant_prices = [v.get('price', float(self.price)) for v in (self.variants or [])]
        return min([float(self.price)] + variant_prices)
    
    def get_highest_price(self):
        """Get highest price among variants or main price."""
        if not self.has_variants:
            return float(self.price)
        
        variant_prices = [v.get('price', float(self.price)) for v in (self.variants or [])]
        return max([float(self.price)] + variant_prices)
    
    @classmethod
    def get_by_slug(cls, store_id, slug):
        """Get product by slug."""
        return cls.query.filter_by(store_id=store_id, slug=slug, status='active').first()
    
    @classmethod
    def get_by_sku(cls, store_id, sku):
        """Get product by SKU."""
        return cls.query.filter_by(store_id=store_id, sku=sku).first()
    
    @classmethod
    def get_featured_products(cls, store_id, limit=10):
        """Get featured products for a store."""
        return cls.query.filter_by(
            store_id=store_id,
            status='active',
            is_featured=True
        ).limit(limit).all()
    
    @classmethod
    def get_products_by_category(cls, store_id, category_id, limit=None):
        """Get products by category."""
        query = cls.query.filter_by(
            store_id=store_id,
            category_id=category_id,
            status='active'
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def search_products(cls, store_id, search_term, limit=50):
        """Search products by name, description, or tags."""
        search_pattern = f"%{search_term}%"
        
        return cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'active',
            db.or_(
                cls.name.like(search_pattern),
                cls.short_description.like(search_pattern),
                cls.description.like(search_pattern),
                cls.tags.like(search_pattern)
            )
        ).limit(limit).all()
    
    @classmethod
    def get_low_stock_products(cls, store_id):
        """Get products with low stock."""
        return cls.query.filter(
            cls.store_id == store_id,
            cls.track_inventory == True,
            cls.inventory_quantity <= cls.low_stock_threshold,
            cls.inventory_quantity > 0,
            cls.status == 'active'
        ).all()
    
    @classmethod
    def get_out_of_stock_products(cls, store_id):
        """Get out of stock products."""
        return cls.query.filter(
            cls.store_id == store_id,
            cls.track_inventory == True,
            cls.inventory_quantity == 0,
            cls.status == 'active'
        ).all()
    
    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'