from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, INTEGER
from slugify import slugify

class Category(db.Model):
    """Product category model with hierarchical support."""
    
    __tablename__ = 'categories'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Basic category information
    name = db.Column(VARCHAR(255), nullable=False)
    slug = db.Column(VARCHAR(300), nullable=False)
    description = db.Column(TEXT)
    
    # Hierarchical structure
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    level = db.Column(INTEGER, default=0)  # 0 = root, 1 = subcategory, etc.
    sort_order = db.Column(INTEGER, default=0)
    
    # Images and display
    image = db.Column(VARCHAR(255))  # Category image
    icon = db.Column(VARCHAR(255))   # Category icon/symbol
    banner_image = db.Column(VARCHAR(255))  # Category page banner
    
    # Status and visibility
    is_active = db.Column(BOOLEAN, default=True)
    is_featured = db.Column(BOOLEAN, default=False)
    show_in_menu = db.Column(BOOLEAN, default=True)
    
    # SEO
    meta_title = db.Column(VARCHAR(60))
    meta_description = db.Column(VARCHAR(160))
    meta_keywords = db.Column(VARCHAR(255))
    
    # Display settings
    display_type = db.Column(VARCHAR(20), default='grid')  # grid, list, masonry
    products_per_page = db.Column(INTEGER, default=12)
    show_subcategories = db.Column(BOOLEAN, default=True)
    
    # Category-specific settings
    category_attributes = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "name": "Brand",
    #     "type": "select",
    #     "options": ["Nike", "Adidas", "Puma"],
    #     "filterable": true,
    #     "required": false
    #   }
    # ]
    
    # Filters and facets for this category
    available_filters = db.Column(JSON, default=lambda: [])
    # Structure: ["brand", "price", "color", "size", "rating"]
    
    # Category rules and automation
    auto_add_rules = db.Column(JSON, default=lambda: {})
    # Structure: {
    #   "tags": ["electronics", "gadgets"],
    #   "brand": ["Apple", "Samsung"],
    #   "price_range": {"min": 100, "max": 1000}
    # }
    
    # Statistics
    product_count = db.Column(INTEGER, default=0)
    total_sales = db.Column(INTEGER, default=0)
    total_revenue = db.Column(db.DECIMAL(15, 2), default=0.00)
    
    # Custom fields
    custom_fields = db.Column(JSON, default=lambda: {})
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='children')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_category', 'store_id', 'slug'),
        db.Index('idx_store_parent', 'store_id', 'parent_id'),
        db.Index('idx_store_active', 'store_id', 'is_active'),
        db.UniqueConstraint('store_id', 'slug', name='uq_store_category_slug'),
    )
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug()
        
        # Set level based on parent
        if self.parent_id:
            parent = Category.query.get(self.parent_id)
            if parent:
                self.level = parent.level + 1
    
    def generate_slug(self):
        """Generate URL-friendly slug from category name."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Category.query.filter_by(store_id=self.store_id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def to_dict(self):
        """Convert category to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'level': self.level,
            'sort_order': self.sort_order,
            'image': self.image,
            'icon': self.icon,
            'banner_image': self.banner_image,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'show_in_menu': self.show_in_menu,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'display_type': self.display_type,
            'products_per_page': self.products_per_page,
            'show_subcategories': self.show_subcategories,
            'category_attributes': self.category_attributes or [],
            'available_filters': self.available_filters or [],
            'auto_add_rules': self.auto_add_rules or {},
            'product_count': self.product_count,
            'total_sales': self.total_sales,
            'total_revenue': float(self.total_revenue) if self.total_revenue else 0.0,
            'custom_fields': self.custom_fields or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_public_dict(self):
        """Convert category to public dictionary (for frontend)."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'level': self.level,
            'image': self.image,
            'icon': self.icon,
            'banner_image': self.banner_image,
            'is_featured': self.is_featured,
            'product_count': self.product_count,
            'subcategories': [child.to_public_dict() for child in self.get_active_children()]
        }
    
    def get_breadcrumb(self):
        """Get category breadcrumb path."""
        breadcrumb = []
        current = self
        
        while current:
            breadcrumb.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        
        return breadcrumb
    
    def get_full_path(self):
        """Get full category path as string."""
        breadcrumb = self.get_breadcrumb()
        return ' > '.join([item['name'] for item in breadcrumb])
    
    def get_all_children(self):
        """Get all descendant categories (recursive)."""
        children = []
        
        for child in self.children:
            children.append(child)
            children.extend(child.get_all_children())
        
        return children
    
    def get_active_children(self):
        """Get active child categories."""
        return [child for child in self.children if child.is_active]
    
    def get_child_ids(self):
        """Get all child category IDs (recursive)."""
        child_ids = [self.id]
        
        for child in self.children:
            child_ids.extend(child.get_child_ids())
        
        return child_ids
    
    def update_product_count(self):
        """Update product count for this category."""
        from app.models.product import Product
        
        self.product_count = Product.query.filter_by(
            store_id=self.store_id,
            category_id=self.id,
            status='active'
        ).count()
    
    def can_delete(self):
        """Check if category can be deleted."""
        # Cannot delete if has products
        if self.product_count > 0:
            return False, "Category has products"
        
        # Cannot delete if has active children
        if any(child.is_active for child in self.children):
            return False, "Category has active subcategories"
        
        return True, "Can delete"
    
    def move_to_parent(self, new_parent_id):
        """Move category to a new parent."""
        if new_parent_id == self.id:
            return False, "Cannot set self as parent"
        
        # Check if new parent is not a descendant
        if new_parent_id:
            descendant_ids = self.get_child_ids()
            if new_parent_id in descendant_ids:
                return False, "Cannot move to descendant category"
        
        self.parent_id = new_parent_id
        
        # Update level
        if new_parent_id:
            parent = Category.query.get(new_parent_id)
            if parent:
                self.level = parent.level + 1
        else:
            self.level = 0
        
        # Update levels for all children
        self._update_children_levels()
        
        return True, "Category moved successfully"
    
    def _update_children_levels(self):
        """Update levels for all child categories."""
        for child in self.children:
            child.level = self.level + 1
            child._update_children_levels()
    
    def add_attribute(self, name, attribute_type, options=None, filterable=True, required=False):
        """Add category attribute."""
        attributes = self.category_attributes or []
        
        new_attribute = {
            'name': name,
            'type': attribute_type,
            'options': options or [],
            'filterable': filterable,
            'required': required
        }
        
        # Check if attribute already exists
        for i, attr in enumerate(attributes):
            if attr.get('name') == name:
                attributes[i] = new_attribute
                self.category_attributes = attributes
                return True
        
        attributes.append(new_attribute)
        self.category_attributes = attributes
        return True
    
    def remove_attribute(self, name):
        """Remove category attribute."""
        if not self.category_attributes:
            return False
        
        self.category_attributes = [
            attr for attr in self.category_attributes 
            if attr.get('name') != name
        ]
        return True
    
    def get_inherited_attributes(self):
        """Get attributes including inherited from parent categories."""
        attributes = self.category_attributes or []
        
        if self.parent:
            parent_attributes = self.parent.get_inherited_attributes()
            
            # Merge attributes, child overrides parent
            attribute_names = [attr.get('name') for attr in attributes]
            for parent_attr in parent_attributes:
                if parent_attr.get('name') not in attribute_names:
                    attributes.append(parent_attr)
        
        return attributes
    
    def record_sale(self, quantity=1, amount=0.0):
        """Record a sale for analytics."""
        self.total_sales += quantity
        self.total_revenue += amount
        
        # Also record for parent categories
        if self.parent:
            self.parent.record_sale(quantity, amount)
    
    @classmethod
    def get_by_slug(cls, store_id, slug):
        """Get category by slug."""
        return cls.query.filter_by(store_id=store_id, slug=slug, is_active=True).first()
    
    @classmethod
    def get_root_categories(cls, store_id):
        """Get root categories (no parent)."""
        return cls.query.filter_by(
            store_id=store_id,
            parent_id=None,
            is_active=True
        ).order_by(cls.sort_order).all()
    
    @classmethod
    def get_featured_categories(cls, store_id, limit=10):
        """Get featured categories."""
        return cls.query.filter_by(
            store_id=store_id,
            is_featured=True,
            is_active=True
        ).order_by(cls.sort_order).limit(limit).all()
    
    @classmethod
    def get_menu_categories(cls, store_id):
        """Get categories to show in menu."""
        return cls.query.filter_by(
            store_id=store_id,
            show_in_menu=True,
            is_active=True
        ).order_by(cls.level, cls.sort_order).all()
    
    @classmethod
    def rebuild_tree_stats(cls, store_id):
        """Rebuild product counts for all categories."""
        categories = cls.query.filter_by(store_id=store_id).all()
        
        for category in categories:
            category.update_product_count()
        
        db.session.commit()
    
    @classmethod
    def create_default_categories(cls, store_id):
        """Create default categories for a store."""
        default_categories = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'is_featured': True,
                'available_filters': ['brand', 'price', 'rating']
            },
            {
                'name': 'Clothing',
                'description': 'Fashion and apparel',
                'is_featured': True,
                'available_filters': ['brand', 'size', 'color', 'price']
            },
            {
                'name': 'Home & Garden',
                'description': 'Home improvement and garden supplies',
                'available_filters': ['brand', 'price', 'rating']
            },
            {
                'name': 'Books',
                'description': 'Books and literature',
                'available_filters': ['author', 'genre', 'price', 'rating']
            }
        ]
        
        categories = []
        for i, category_data in enumerate(default_categories):
            category = cls(
                store_id=store_id,
                sort_order=i + 1,
                **category_data
            )
            categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        return categories
    
    def __repr__(self):
        return f'<Category {self.name} (Level {self.level})>'