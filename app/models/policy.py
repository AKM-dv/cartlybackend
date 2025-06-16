from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON
from slugify import slugify

class Policy(db.Model):
    """Policy model for store legal pages and policies."""
    
    __tablename__ = 'policies'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Basic information
    title = db.Column(VARCHAR(255), nullable=False)
    slug = db.Column(VARCHAR(300), nullable=False)
    policy_type = db.Column(VARCHAR(50), nullable=False)
    # Types: privacy_policy, terms_of_service, shipping_policy, return_policy,
    # refund_policy, cookie_policy, disclaimer, about_us, contact_us, faq
    
    # Content
    content = db.Column(TEXT, nullable=False)
    excerpt = db.Column(VARCHAR(500))  # Short summary
    
    # Status and visibility
    is_published = db.Column(BOOLEAN, default=False)
    is_required = db.Column(BOOLEAN, default=False)  # Required for checkout
    show_in_footer = db.Column(BOOLEAN, default=True)
    
    # SEO
    meta_title = db.Column(VARCHAR(60))
    meta_description = db.Column(VARCHAR(160))
    meta_keywords = db.Column(VARCHAR(255))
    
    # Legal compliance
    last_reviewed_date = db.Column(DATETIME, nullable=True)
    next_review_date = db.Column(DATETIME, nullable=True)
    version = db.Column(VARCHAR(10), default='1.0')
    
    # Display settings
    display_order = db.Column(db.Integer, default=0)
    template = db.Column(VARCHAR(50), default='default')  # Template for rendering
    
    # Legal notices
    effective_date = db.Column(DATETIME, nullable=True)
    last_modified_date = db.Column(DATETIME, nullable=True)
    requires_acceptance = db.Column(BOOLEAN, default=False)  # User must accept
    
    # Automatic content sections (for templates)
    auto_sections = db.Column(JSON, default=lambda: {})
    # Structure: {
    #   "contact_info": true,
    #   "business_info": true,
    #   "data_collection": ["email", "name", "address"],
    #   "cookies_used": ["analytics", "marketing", "functional"],
    #   "third_party_services": ["google_analytics", "facebook_pixel"]
    # }
    
    # Custom fields for additional data
    custom_fields = db.Column(JSON, default=lambda: {})
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = db.Column(DATETIME, nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_policy', 'store_id', 'policy_type'),
        db.Index('idx_store_slug', 'store_id', 'slug'),
        db.Index('idx_store_published', 'store_id', 'is_published'),
        db.UniqueConstraint('store_id', 'slug', name='uq_store_policy_slug'),
        db.UniqueConstraint('store_id', 'policy_type', name='uq_store_policy_type'),
    )
    
    def __init__(self, **kwargs):
        super(Policy, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug()
    
    def generate_slug(self):
        """Generate URL-friendly slug from policy title."""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        while Policy.query.filter_by(store_id=self.store_id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def to_dict(self):
        """Convert policy to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'title': self.title,
            'slug': self.slug,
            'policy_type': self.policy_type,
            'content': self.content,
            'excerpt': self.excerpt,
            'is_published': self.is_published,
            'is_required': self.is_required,
            'show_in_footer': self.show_in_footer,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'last_reviewed_date': self.last_reviewed_date.isoformat() if self.last_reviewed_date else None,
            'next_review_date': self.next_review_date.isoformat() if self.next_review_date else None,
            'version': self.version,
            'display_order': self.display_order,
            'template': self.template,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None,
            'requires_acceptance': self.requires_acceptance,
            'auto_sections': self.auto_sections or {},
            'custom_fields': self.custom_fields or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
    def to_public_dict(self):
        """Convert policy to public dictionary (for frontend)."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'policy_type': self.policy_type,
            'content': self.get_rendered_content(),
            'excerpt': self.excerpt,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None,
            'version': self.version,
            'requires_acceptance': self.requires_acceptance
        }
    
    def get_rendered_content(self):
        """Get content with auto-sections rendered."""
        content = self.content or ""
        
        # If using auto-sections, merge with store data
        if self.auto_sections:
            content = self._merge_auto_sections(content)
        
        return content
    
    def _merge_auto_sections(self, content):
        """Merge auto-sections with content."""
        from app.models.store import Store
        from app.models.contact_details import ContactDetails
        
        # Get store and contact info
        store = Store.get_by_store_id(self.store_id)
        contact = ContactDetails.get_by_store_id(self.store_id)
        
        auto_sections = self.auto_sections or {}
        replacements = {}
        
        # Contact information
        if auto_sections.get('contact_info') and contact:
            replacements.update({
                '{{contact_email}}': contact.primary_email or '',
                '{{contact_phone}}': contact.primary_phone or '',
                '{{contact_address}}': contact.get_full_address() or '',
                '{{business_name}}': store.business_name or store.store_name if store else ''
            })
        
        # Business information
        if auto_sections.get('business_info') and store:
            replacements.update({
                '{{store_name}}': store.store_name or '',
                '{{business_name}}': store.business_name or '',
                '{{business_registration}}': store.business_registration or '',
                '{{tax_id}}': store.tax_id or '',
                '{{store_url}}': store.get_store_url() if store else ''
            })
        
        # Apply replacements
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        return content
    
    def publish(self):
        """Publish the policy."""
        self.is_published = True
        self.published_at = datetime.utcnow()
        self.last_modified_date = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the policy."""
        self.is_published = False
    
    def update_version(self, new_version=None):
        """Update policy version."""
        if new_version:
            self.version = new_version
        else:
            # Auto-increment version
            try:
                major, minor = map(int, self.version.split('.'))
                self.version = f"{major}.{minor + 1}"
            except:
                self.version = "1.1"
        
        self.last_modified_date = datetime.utcnow()
    
    def schedule_review(self, months=12):
        """Schedule next review date."""
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        self.last_reviewed_date = datetime.utcnow()
        self.next_review_date = datetime.utcnow() + relativedelta(months=months)
    
    def is_due_for_review(self):
        """Check if policy is due for review."""
        if not self.next_review_date:
            return False
        
        return datetime.utcnow() >= self.next_review_date
    
    def get_word_count(self):
        """Get word count of content."""
        if not self.content:
            return 0
        
        return len(self.content.split())
    
    def get_reading_time(self):
        """Estimate reading time in minutes (250 words per minute)."""
        word_count = self.get_word_count()
        return max(1, round(word_count / 250))
    
    @classmethod
    def get_by_slug(cls, store_id, slug):
        """Get policy by slug."""
        return cls.query.filter_by(
            store_id=store_id, 
            slug=slug, 
            is_published=True
        ).first()
    
    @classmethod
    def get_by_type(cls, store_id, policy_type):
        """Get policy by type."""
        return cls.query.filter_by(
            store_id=store_id, 
            policy_type=policy_type
        ).first()
    
    @classmethod
    def get_published_policies(cls, store_id):
        """Get all published policies."""
        return cls.query.filter_by(
            store_id=store_id,
            is_published=True
        ).order_by(cls.display_order).all()
    
    @classmethod
    def get_footer_policies(cls, store_id):
        """Get policies to show in footer."""
        return cls.query.filter_by(
            store_id=store_id,
            is_published=True,
            show_in_footer=True
        ).order_by(cls.display_order).all()
    
    @classmethod
    def get_required_policies(cls, store_id):
        """Get policies required for checkout."""
        return cls.query.filter_by(
            store_id=store_id,
            is_published=True,
            is_required=True
        ).all()
    
    @classmethod
    def get_policies_due_for_review(cls, store_id):
        """Get policies due for review."""
        return cls.query.filter(
            cls.store_id == store_id,
            cls.next_review_date <= datetime.utcnow()
        ).all()
    
    @classmethod
    def create_default_policies(cls, store_id):
        """Create default policies for a store."""
        default_policies = [
            {
                'title': 'Privacy Policy',
                'policy_type': 'privacy_policy',
                'content': cls._get_privacy_policy_template(),
                'is_required': True,
                'requires_acceptance': True,
                'auto_sections': {
                    'contact_info': True,
                    'business_info': True,
                    'data_collection': ['email', 'name', 'address', 'phone'],
                    'cookies_used': ['analytics', 'functional']
                },
                'display_order': 1
            },
            {
                'title': 'Terms of Service',
                'policy_type': 'terms_of_service',
                'content': cls._get_terms_template(),
                'is_required': True,
                'requires_acceptance': True,
                'auto_sections': {
                    'contact_info': True,
                    'business_info': True
                },
                'display_order': 2
            },
            {
                'title': 'Shipping Policy',
                'policy_type': 'shipping_policy',
                'content': cls._get_shipping_policy_template(),
                'auto_sections': {
                    'contact_info': True
                },
                'display_order': 3
            },
            {
                'title': 'Return & Refund Policy',
                'policy_type': 'return_policy',
                'content': cls._get_return_policy_template(),
                'auto_sections': {
                    'contact_info': True
                },
                'display_order': 4
            }
        ]
        
        policies = []
        for policy_data in default_policies:
            policy = cls(
                store_id=store_id,
                effective_date=datetime.utcnow(),
                **policy_data
            )
            policies.append(policy)
            db.session.add(policy)
        
        db.session.commit()
        return policies
    
    @staticmethod
    def _get_privacy_policy_template():
        """Get privacy policy template."""
        return """
# Privacy Policy

**Effective Date:** {{effective_date}}
**Last Updated:** {{last_modified_date}}

## Information We Collect

We collect information you provide directly to us, such as when you create an account, make a purchase, or contact us.

### Personal Information
- Name and contact information ({{contact_email}}, {{contact_phone}})
- Billing and shipping addresses
- Payment information
- Purchase history

### Automatically Collected Information
- Browser and device information
- Usage data and preferences
- Cookies and similar technologies

## How We Use Your Information

We use the information we collect to:
- Process and fulfill your orders
- Communicate with you about your account and orders
- Improve our services and customer experience
- Send marketing communications (with your consent)

## Information Sharing

We do not sell, trade, or otherwise transfer your personal information to third parties except as described in this policy.

## Contact Us

If you have any questions about this Privacy Policy, please contact us:
- Email: {{contact_email}}
- Phone: {{contact_phone}}
- Address: {{contact_address}}

{{business_name}}
"""
    
    @staticmethod
    def _get_terms_template():
        """Get terms of service template."""
        return """
# Terms of Service

**Effective Date:** {{effective_date}}
**Last Updated:** {{last_modified_date}}

## Acceptance of Terms

By accessing and using {{store_name}}, you accept and agree to be bound by the terms and provision of this agreement.

## Use License

Permission is granted to temporarily download one copy of the materials on {{store_name}} for personal, non-commercial transitory viewing only.

## Disclaimer

The materials on {{store_name}} are provided on an 'as is' basis. {{business_name}} makes no warranties, expressed or implied.

## Limitations

In no event shall {{business_name}} be liable for any damages arising out of the use or inability to use the materials on {{store_name}}.

## Contact Information

For questions about these Terms of Service, contact us:
- Email: {{contact_email}}
- Phone: {{contact_phone}}

{{business_name}}
"""
    
    @staticmethod
    def _get_shipping_policy_template():
        """Get shipping policy template."""
        return """
# Shipping Policy

## Processing Time

Orders are typically processed within 1-2 business days after payment confirmation.

## Shipping Methods

We offer various shipping options:
- Standard Shipping (3-7 business days)
- Express Shipping (1-3 business days)
- Same Day Delivery (select areas)

## Shipping Costs

Shipping costs are calculated based on weight, dimensions, and destination.

## International Shipping

We currently ship to select international destinations. Additional customs fees may apply.

## Contact Us

For shipping inquiries:
- Email: {{contact_email}}
- Phone: {{contact_phone}}
"""
    
    @staticmethod
    def _get_return_policy_template():
        """Get return policy template."""
        return """
# Return & Refund Policy

## Return Window

Items can be returned within 30 days of purchase for a full refund.

## Return Conditions

Items must be:
- In original condition
- Unworn and unwashed
- With original tags and packaging

## Return Process

1. Contact us at {{contact_email}} to initiate a return
2. Pack items securely with original packaging
3. Ship to our return address
4. Refund will be processed within 5-7 business days

## Non-Returnable Items

- Digital products
- Personalized items
- Perishable goods

## Contact Us

For return questions:
- Email: {{contact_email}}
- Phone: {{contact_phone}}
"""
    
    def __repr__(self):
        return f'<Policy {self.title} ({self.policy_type})>'