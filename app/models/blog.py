from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, INTEGER
from slugify import slugify

class Blog(db.Model):
    """Blog model for content management and SEO."""
    
    __tablename__ = 'blogs'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False)
    
    # Basic information
    title = db.Column(VARCHAR(255), nullable=False)
    slug = db.Column(VARCHAR(300), nullable=False)
    excerpt = db.Column(VARCHAR(500))  # Short summary
    content = db.Column(TEXT, nullable=False)
    
    # Author information
    author_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    author_name = db.Column(VARCHAR(100))  # For guest authors or custom names
    
    # Featured image
    featured_image = db.Column(VARCHAR(255))
    featured_image_alt = db.Column(VARCHAR(255))
    
    # Categories and tags
    blog_category = db.Column(VARCHAR(100))
    tags = db.Column(JSON, default=lambda: [])
    
    # Status and visibility
    status = db.Column(VARCHAR(20), default='draft')  # draft, published, scheduled, archived
    is_featured = db.Column(BOOLEAN, default=False)
    allow_comments = db.Column(BOOLEAN, default=True)
    
    # SEO
    meta_title = db.Column(VARCHAR(60))
    meta_description = db.Column(VARCHAR(160))
    meta_keywords = db.Column(VARCHAR(255))
    focus_keyword = db.Column(VARCHAR(100))  # Primary SEO keyword
    
    # Social media
    social_title = db.Column(VARCHAR(60))  # For social sharing
    social_description = db.Column(VARCHAR(160))
    social_image = db.Column(VARCHAR(255))
    
    # Publishing
    published_at = db.Column(DATETIME, nullable=True)
    scheduled_at = db.Column(DATETIME, nullable=True)  # For scheduled posts
    
    # Reading and engagement
    reading_time = db.Column(INTEGER, default=0)  # Estimated reading time in minutes
    view_count = db.Column(INTEGER, default=0)
    like_count = db.Column(INTEGER, default=0)
    share_count = db.Column(INTEGER, default=0)
    
    # Content structure
    table_of_contents = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "id": "section-1",
    #     "title": "Introduction",
    #     "level": 2,
    #     "anchor": "#introduction"
    #   }
    # ]
    
    # Related content
    related_products = db.Column(JSON, default=lambda: [])  # Product IDs
    related_posts = db.Column(JSON, default=lambda: [])     # Blog post IDs
    
    # Content settings
    content_type = db.Column(VARCHAR(20), default='article')
    # Types: article, tutorial, news, review, guide, announcement
    
    # Language and localization
    language = db.Column(VARCHAR(5), default='en')
    
    # Comments (if enabled)
    comments = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "id": 1,
    #     "author_name": "John Doe",
    #     "author_email": "john@example.com",
    #     "content": "Great article!",
    #     "created_at": "2024-01-01T10:00:00Z",
    #     "is_approved": true,
    #     "parent_id": null  # For replies
    #   }
    # ]
    
    # Custom fields
    custom_fields = db.Column(JSON, default=lambda: {})
    
    # Analytics and tracking
    utm_source = db.Column(VARCHAR(100))
    utm_medium = db.Column(VARCHAR(100))
    utm_campaign = db.Column(VARCHAR(100))
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    author = db.relationship('AdminUser', backref='blog_posts')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_store_blog', 'store_id', 'slug'),
        db.Index('idx_store_status', 'store_id', 'status'),
        db.Index('idx_store_category', 'store_id', 'blog_category'),
        db.Index('idx_store_published', 'store_id', 'published_at'),
        db.UniqueConstraint('store_id', 'slug', name='uq_store_blog_slug'),
    )
    
    def __init__(self, **kwargs):
        super(Blog, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = self.generate_slug()
        
        # Calculate reading time if content is provided
        if self.content:
            self.reading_time = self.calculate_reading_time()
    
    def generate_slug(self):
        """Generate URL-friendly slug from blog title."""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        while Blog.query.filter_by(store_id=self.store_id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def calculate_reading_time(self):
        """Calculate estimated reading time (250 words per minute)."""
        if not self.content:
            return 0
        
        word_count = len(self.content.split())
        return max(1, round(word_count / 250))
    
    def generate_table_of_contents(self):
        """Generate table of contents from content headings."""
        import re
        
        if not self.content:
            return []
        
        # Find all headings (h1-h6)
        heading_pattern = r'<h([1-6])[^>]*>(.*?)</h[1-6]>'
        headings = re.findall(heading_pattern, self.content, re.IGNORECASE)
        
        toc = []
        for i, (level, title) in enumerate(headings):
            # Clean title text
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            anchor = slugify(clean_title)
            
            toc.append({
                'id': f"section-{i+1}",
                'title': clean_title,
                'level': int(level),
                'anchor': f"#{anchor}"
            })
        
        self.table_of_contents = toc
        return toc
    
    def to_dict(self):
        """Convert blog to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author_name or (self.author.get_full_name() if self.author else None),
            'featured_image': self.featured_image,
            'featured_image_alt': self.featured_image_alt,
            'blog_category': self.blog_category,
            'tags': self.tags or [],
            'status': self.status,
            'is_featured': self.is_featured,
            'allow_comments': self.allow_comments,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'focus_keyword': self.focus_keyword,
            'social_title': self.social_title,
            'social_description': self.social_description,
            'social_image': self.social_image,
            'content_type': self.content_type,
            'language': self.language,
            'reading_time': self.reading_time,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'share_count': self.share_count,
            'table_of_contents': self.table_of_contents or [],
            'related_products': self.related_products or [],
            'related_posts': self.related_posts or [],
            'custom_fields': self.custom_fields or {},
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_public_dict(self):
        """Convert blog to public dictionary (for frontend)."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'content': self.content,
            'author_name': self.author_name or (self.author.get_full_name() if self.author else 'Anonymous'),
            'featured_image': self.featured_image,
            'featured_image_alt': self.featured_image_alt,
            'blog_category': self.blog_category,
            'tags': self.tags or [],
            'content_type': self.content_type,
            'reading_time': self.reading_time,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'table_of_contents': self.table_of_contents or [],
            'related_products': self.related_products or [],
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
    def publish(self):
        """Publish the blog post."""
        self.status = 'published'
        self.published_at = datetime.utcnow()
    
    def unpublish(self):
        """Unpublish the blog post."""
        self.status = 'draft'
    
    def schedule(self, scheduled_time):
        """Schedule the blog post for future publication."""
        self.status = 'scheduled'
        self.scheduled_at = scheduled_time
    
    def archive(self):
        """Archive the blog post."""
        self.status = 'archived'
    
    def increment_view(self):
        """Increment view count."""
        self.view_count += 1
    
    def add_like(self):
        """Increment like count."""
        self.like_count += 1
    
    def add_share(self):
        """Increment share count."""
        self.share_count += 1
    
    def add_comment(self, author_name, author_email, content, parent_id=None):
        """Add comment to blog post."""
        if not self.allow_comments:
            return False
        
        comments = self.comments or []
        
        # Generate comment ID
        max_id = max([comment.get('id', 0) for comment in comments], default=0)
        
        new_comment = {
            'id': max_id + 1,
            'author_name': author_name,
            'author_email': author_email,
            'content': content,
            'created_at': datetime.utcnow().isoformat(),
            'is_approved': False,  # Require moderation by default
            'parent_id': parent_id
        }
        
        comments.append(new_comment)
        self.comments = comments
        
        return new_comment['id']
    
    def approve_comment(self, comment_id):
        """Approve a comment."""
        comments = self.comments or []
        
        for comment in comments:
            if comment.get('id') == comment_id:
                comment['is_approved'] = True
                self.comments = comments
                return True
        
        return False
    
    def get_approved_comments(self):
        """Get approved comments."""
        if not self.comments:
            return []
        
        return [comment for comment in self.comments if comment.get('is_approved')]
    
    def add_related_product(self, product_id):
        """Add related product."""
        related = self.related_products or []
        if product_id not in related:
            related.append(product_id)
            self.related_products = related
    
    def remove_related_product(self, product_id):
        """Remove related product."""
        if self.related_products and product_id in self.related_products:
            related = self.related_products.copy()
            related.remove(product_id)
            self.related_products = related
    
    def add_related_post(self, post_id):
        """Add related blog post."""
        related = self.related_posts or []
        if post_id not in related and post_id != self.id:
            related.append(post_id)
            self.related_posts = related
    
    def remove_related_post(self, post_id):
        """Remove related blog post."""
        if self.related_posts and post_id in self.related_posts:
            related = self.related_posts.copy()
            related.remove(post_id)
            self.related_posts = related
    
    def get_engagement_rate(self):
        """Calculate engagement rate based on views, likes, and shares."""
        if self.view_count == 0:
            return 0.0
        
        engagements = self.like_count + self.share_count + len(self.get_approved_comments())
        return round((engagements / self.view_count) * 100, 2)
    
    def is_published(self):
        """Check if blog post is published."""
        return self.status == 'published' and self.published_at is not None
    
    def is_scheduled(self):
        """Check if blog post is scheduled."""
        return self.status == 'scheduled' and self.scheduled_at is not None
    
    def should_be_published(self):
        """Check if scheduled post should be published now."""
        if not self.is_scheduled():
            return False
        
        return datetime.utcnow() >= self.scheduled_at
    
    @classmethod
    def get_by_slug(cls, store_id, slug):
        """Get blog post by slug."""
        return cls.query.filter_by(
            store_id=store_id, 
            slug=slug, 
            status='published'
        ).first()
    
    @classmethod
    def get_published_posts(cls, store_id, limit=None):
        """Get published blog posts."""
        query = cls.query.filter_by(
            store_id=store_id,
            status='published'
        ).order_by(cls.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_featured_posts(cls, store_id, limit=5):
        """Get featured blog posts."""
        return cls.query.filter_by(
            store_id=store_id,
            status='published',
            is_featured=True
        ).order_by(cls.published_at.desc()).limit(limit).all()
    
    @classmethod
    def get_posts_by_category(cls, store_id, category, limit=None):
        """Get blog posts by category."""
        query = cls.query.filter_by(
            store_id=store_id,
            blog_category=category,
            status='published'
        ).order_by(cls.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_posts_by_tag(cls, store_id, tag, limit=None):
        """Get blog posts by tag."""
        query = cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'published',
            cls.tags.contains(tag)
        ).order_by(cls.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def search_posts(cls, store_id, search_term, limit=50):
        """Search blog posts."""
        search_pattern = f"%{search_term}%"
        
        return cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'published',
            db.or_(
                cls.title.like(search_pattern),
                cls.excerpt.like(search_pattern),
                cls.content.like(search_pattern),
                cls.tags.like(search_pattern)
            )
        ).order_by(cls.published_at.desc()).limit(limit).all()
    
    @classmethod
    def get_scheduled_posts(cls, store_id):
        """Get posts that should be published now."""
        return cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'scheduled',
            cls.scheduled_at <= datetime.utcnow()
        ).all()
    
    @classmethod
    def get_popular_posts(cls, store_id, limit=10):
        """Get popular posts by view count."""
        return cls.query.filter_by(
            store_id=store_id,
            status='published'
        ).order_by(cls.view_count.desc()).limit(limit).all()
    
    @classmethod
    def get_recent_posts(cls, store_id, days=30, limit=10):
        """Get recent posts."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'published',
            cls.published_at >= cutoff_date
        ).order_by(cls.published_at.desc()).limit(limit).all()
    
    @classmethod
    def get_categories(cls, store_id):
        """Get all blog categories."""
        categories = db.session.query(cls.blog_category).filter(
            cls.store_id == store_id,
            cls.status == 'published',
            cls.blog_category.isnot(None)
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]
    
    @classmethod
    def get_all_tags(cls, store_id):
        """Get all blog tags."""
        posts = cls.query.filter_by(
            store_id=store_id,
            status='published'
        ).all()
        
        all_tags = set()
        for post in posts:
            if post.tags:
                all_tags.update(post.tags)
        
        return sorted(list(all_tags))
    
    @classmethod
    def get_analytics_data(cls, store_id, start_date=None, end_date=None):
        """Get blog analytics data."""
        query = cls.query.filter(
            cls.store_id == store_id,
            cls.status == 'published'
        )
        
        if start_date:
            query = query.filter(cls.published_at >= start_date)
        if end_date:
            query = query.filter(cls.published_at <= end_date)
        
        posts = query.all()
        
        return {
            'total_posts': len(posts),
            'total_views': sum(post.view_count for post in posts),
            'total_likes': sum(post.like_count for post in posts),
            'total_shares': sum(post.share_count for post in posts),
            'total_comments': sum(len(post.get_approved_comments()) for post in posts),
            'average_reading_time': sum(post.reading_time for post in posts) / len(posts) if posts else 0,
            'engagement_rate': sum(post.get_engagement_rate() for post in posts) / len(posts) if posts else 0
        }
    
    @classmethod
    def auto_publish_scheduled(cls):
        """Auto-publish scheduled posts that are due."""
        scheduled_posts = cls.query.filter(
            cls.status == 'scheduled',
            cls.scheduled_at <= datetime.utcnow()
        ).all()
        
        published_count = 0
        for post in scheduled_posts:
            post.publish()
            published_count += 1
        
        if published_count > 0:
            db.session.commit()
        
        return published_count
    
    def __repr__(self):
        return f'<Blog {self.title} ({self.status})>'