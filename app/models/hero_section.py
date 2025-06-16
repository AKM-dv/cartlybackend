from datetime import datetime
from app.config.database import db
from sqlalchemy.dialects.mysql import VARCHAR, TEXT, BOOLEAN, DATETIME, JSON, INTEGER

class HeroSection(db.Model):
    """Hero section configuration including top bar, hero banners, and popups."""
    
    __tablename__ = 'hero_sections'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Store association
    store_id = db.Column(VARCHAR(50), db.ForeignKey('stores.store_id'), nullable=False, unique=True)
    
    # Top Bar Configuration
    enable_top_bar = db.Column(BOOLEAN, default=True)
    top_bar_text = db.Column(VARCHAR(255), default="Free shipping on orders over $50!")
    top_bar_link = db.Column(VARCHAR(255))
    top_bar_link_text = db.Column(VARCHAR(100))
    top_bar_bg_color = db.Column(VARCHAR(7), default="#000000")
    top_bar_text_color = db.Column(VARCHAR(7), default="#ffffff")
    top_bar_position = db.Column(VARCHAR(10), default="top")  # top, bottom
    
    # Main Hero Section
    hero_type = db.Column(VARCHAR(20), default="slideshow")  # slideshow, single_image, video
    hero_height = db.Column(VARCHAR(10), default="500px")
    hero_overlay_opacity = db.Column(INTEGER, default=30)  # 0-100
    
    # Hero Slides (for slideshow)
    hero_slides = db.Column(JSON, default=lambda: [])
    # Structure: [
    #   {
    #     "id": 1,
    #     "image_url": "/uploads/hero1.jpg",
    #     "mobile_image_url": "/uploads/hero1_mobile.jpg",
    #     "title": "Summer Sale",
    #     "subtitle": "Up to 50% off",
    #     "description": "Shop the latest trends",
    #     "button_text": "Shop Now",
    #     "button_link": "/collections/sale",
    #     "text_position": "center",
    #     "text_color": "#ffffff",
    #     "overlay_color": "#000000",
    #     "overlay_opacity": 30,
    #     "animation": "fade",
    #     "duration": 5000,
    #     "active": true,
    #     "order": 1
    #   }
    # ]
    
    # Slideshow settings
    auto_play = db.Column(BOOLEAN, default=True)
    slide_duration = db.Column(INTEGER, default=5000)  # milliseconds
    show_navigation = db.Column(BOOLEAN, default=True)
    show_pagination = db.Column(BOOLEAN, default=True)
    slide_animation = db.Column(VARCHAR(20), default="fade")  # fade, slide, zoom
    
    # Single image hero (when hero_type = "single_image")
    single_image_url = db.Column(VARCHAR(255))
    single_mobile_image_url = db.Column(VARCHAR(255))
    single_title = db.Column(VARCHAR(200))
    single_subtitle = db.Column(VARCHAR(200))
    single_description = db.Column(TEXT)
    single_button_text = db.Column(VARCHAR(50))
    single_button_link = db.Column(VARCHAR(255))
    single_text_position = db.Column(VARCHAR(20), default="center")  # left, center, right
    single_text_color = db.Column(VARCHAR(7), default="#ffffff")
    
    # Video hero (when hero_type = "video")
    video_url = db.Column(VARCHAR(255))
    video_poster = db.Column(VARCHAR(255))  # Poster image for video
    video_autoplay = db.Column(BOOLEAN, default=True)
    video_muted = db.Column(BOOLEAN, default=True)
    video_loop = db.Column(BOOLEAN, default=True)
    
    # Popup Configuration
    enable_popup = db.Column(BOOLEAN, default=False)
    popup_type = db.Column(VARCHAR(20), default="newsletter")  # newsletter, promotion, announcement
    popup_title = db.Column(VARCHAR(200))
    popup_content = db.Column(TEXT)
    popup_image = db.Column(VARCHAR(255))
    popup_button_text = db.Column(VARCHAR(50))
    popup_button_link = db.Column(VARCHAR(255))
    
    # Popup behavior
    popup_delay = db.Column(INTEGER, default=3000)  # milliseconds
    popup_frequency = db.Column(VARCHAR(20), default="once_per_session")  # once_per_session, daily, always
    popup_position = db.Column(VARCHAR(20), default="center")  # center, bottom-right, bottom-left
    popup_size = db.Column(VARCHAR(20), default="medium")  # small, medium, large
    
    # Popup styling
    popup_bg_color = db.Column(VARCHAR(7), default="#ffffff")
    popup_text_color = db.Column(VARCHAR(7), default="#333333")
    popup_overlay_color = db.Column(VARCHAR(7), default="#000000")
    popup_overlay_opacity = db.Column(INTEGER, default=50)
    
    # Exit intent popup
    enable_exit_intent = db.Column(BOOLEAN, default=False)
    exit_intent_title = db.Column(VARCHAR(200))
    exit_intent_content = db.Column(TEXT)
    exit_intent_discount_code = db.Column(VARCHAR(50))
    
    # Mobile responsiveness
    hide_on_mobile = db.Column(BOOLEAN, default=False)
    mobile_hero_height = db.Column(VARCHAR(10), default="300px")
    mobile_text_size = db.Column(VARCHAR(10), default="14px")
    
    # Performance settings
    lazy_load_images = db.Column(BOOLEAN, default=True)
    preload_next_slide = db.Column(BOOLEAN, default=True)
    
    # Analytics
    track_clicks = db.Column(BOOLEAN, default=True)
    
    # Timestamps
    created_at = db.Column(DATETIME, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert hero section to dictionary."""
        return {
            'id': self.id,
            'store_id': self.store_id,
            'enable_top_bar': self.enable_top_bar,
            'top_bar_text': self.top_bar_text,
            'top_bar_link': self.top_bar_link,
            'top_bar_link_text': self.top_bar_link_text,
            'top_bar_bg_color': self.top_bar_bg_color,
            'top_bar_text_color': self.top_bar_text_color,
            'top_bar_position': self.top_bar_position,
            'hero_type': self.hero_type,
            'hero_height': self.hero_height,
            'hero_overlay_opacity': self.hero_overlay_opacity,
            'hero_slides': self.hero_slides or [],
            'auto_play': self.auto_play,
            'slide_duration': self.slide_duration,
            'show_navigation': self.show_navigation,
            'show_pagination': self.show_pagination,
            'slide_animation': self.slide_animation,
            'single_image_url': self.single_image_url,
            'single_mobile_image_url': self.single_mobile_image_url,
            'single_title': self.single_title,
            'single_subtitle': self.single_subtitle,
            'single_description': self.single_description,
            'single_button_text': self.single_button_text,
            'single_button_link': self.single_button_link,
            'single_text_position': self.single_text_position,
            'single_text_color': self.single_text_color,
            'video_url': self.video_url,
            'video_poster': self.video_poster,
            'video_autoplay': self.video_autoplay,
            'video_muted': self.video_muted,
            'video_loop': self.video_loop,
            'enable_popup': self.enable_popup,
            'popup_type': self.popup_type,
            'popup_title': self.popup_title,
            'popup_content': self.popup_content,
            'popup_image': self.popup_image,
            'popup_button_text': self.popup_button_text,
            'popup_button_link': self.popup_button_link,
            'popup_delay': self.popup_delay,
            'popup_frequency': self.popup_frequency,
            'popup_position': self.popup_position,
            'popup_size': self.popup_size,
            'popup_bg_color': self.popup_bg_color,
            'popup_text_color': self.popup_text_color,
            'popup_overlay_color': self.popup_overlay_color,
            'popup_overlay_opacity': self.popup_overlay_opacity,
            'enable_exit_intent': self.enable_exit_intent,
            'exit_intent_title': self.exit_intent_title,
            'exit_intent_content': self.exit_intent_content,
            'exit_intent_discount_code': self.exit_intent_discount_code,
            'hide_on_mobile': self.hide_on_mobile,
            'mobile_hero_height': self.mobile_hero_height,
            'mobile_text_size': self.mobile_text_size,
            'lazy_load_images': self.lazy_load_images,
            'preload_next_slide': self.preload_next_slide,
            'track_clicks': self.track_clicks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_active_slides(self):
        """Get only active slides sorted by order."""
        slides = self.hero_slides or []
        active_slides = [slide for slide in slides if slide.get('active', True)]
        return sorted(active_slides, key=lambda x: x.get('order', 0))
    
    def add_slide(self, slide_data):
        """Add a new slide to the hero section."""
        slides = self.hero_slides or []
        
        # Generate new ID
        max_id = max([slide.get('id', 0) for slide in slides], default=0)
        slide_data['id'] = max_id + 1
        
        # Set order if not provided
        if 'order' not in slide_data:
            max_order = max([slide.get('order', 0) for slide in slides], default=0)
            slide_data['order'] = max_order + 1
        
        slides.append(slide_data)
        self.hero_slides = slides
        return slide_data['id']
    
    def update_slide(self, slide_id, slide_data):
        """Update an existing slide."""
        slides = self.hero_slides or []
        
        for i, slide in enumerate(slides):
            if slide.get('id') == slide_id:
                slides[i].update(slide_data)
                self.hero_slides = slides
                return True
        
        return False
    
    def delete_slide(self, slide_id):
        """Delete a slide."""
        slides = self.hero_slides or []
        self.hero_slides = [slide for slide in slides if slide.get('id') != slide_id]
        return True
    
    def reorder_slides(self, slide_orders):
        """Reorder slides based on provided order mapping."""
        slides = self.hero_slides or []
        
        for slide in slides:
            slide_id = slide.get('id')
            if slide_id in slide_orders:
                slide['order'] = slide_orders[slide_id]
        
        self.hero_slides = slides
    
    def get_top_bar_config(self):
        """Get top bar configuration."""
        return {
            'enabled': self.enable_top_bar,
            'text': self.top_bar_text,
            'link': self.top_bar_link,
            'link_text': self.top_bar_link_text,
            'bg_color': self.top_bar_bg_color,
            'text_color': self.top_bar_text_color,
            'position': self.top_bar_position
        }
    
    def get_popup_config(self):
        """Get popup configuration."""
        return {
            'enabled': self.enable_popup,
            'type': self.popup_type,
            'title': self.popup_title,
            'content': self.popup_content,
            'image': self.popup_image,
            'button_text': self.popup_button_text,
            'button_link': self.popup_button_link,
            'delay': self.popup_delay,
            'frequency': self.popup_frequency,
            'position': self.popup_position,
            'size': self.popup_size,
            'styling': {
                'bg_color': self.popup_bg_color,
                'text_color': self.popup_text_color,
                'overlay_color': self.popup_overlay_color,
                'overlay_opacity': self.popup_overlay_opacity
            },
            'exit_intent': {
                'enabled': self.enable_exit_intent,
                'title': self.exit_intent_title,
                'content': self.exit_intent_content,
                'discount_code': self.exit_intent_discount_code
            }
        }
    
    def get_hero_config(self):
        """Get hero section configuration for frontend."""
        config = {
            'type': self.hero_type,
            'height': self.hero_height,
            'mobile_height': self.mobile_hero_height,
            'overlay_opacity': self.hero_overlay_opacity,
            'hide_on_mobile': self.hide_on_mobile
        }
        
        if self.hero_type == 'slideshow':
            config.update({
                'slides': self.get_active_slides(),
                'auto_play': self.auto_play,
                'slide_duration': self.slide_duration,
                'show_navigation': self.show_navigation,
                'show_pagination': self.show_pagination,
                'animation': self.slide_animation,
                'lazy_load': self.lazy_load_images,
                'preload_next': self.preload_next_slide
            })
        elif self.hero_type == 'single_image':
            config.update({
                'image_url': self.single_image_url,
                'mobile_image_url': self.single_mobile_image_url,
                'title': self.single_title,
                'subtitle': self.single_subtitle,
                'description': self.single_description,
                'button_text': self.single_button_text,
                'button_link': self.single_button_link,
                'text_position': self.single_text_position,
                'text_color': self.single_text_color
            })
        elif self.hero_type == 'video':
            config.update({
                'video_url': self.video_url,
                'poster': self.video_poster,
                'autoplay': self.video_autoplay,
                'muted': self.video_muted,
                'loop': self.video_loop
            })
        
        return config
    
    @classmethod
    def get_by_store_id(cls, store_id):
        """Get hero section by store ID."""
        return cls.query.filter_by(store_id=store_id).first()
    
    @classmethod
    def create_default(cls, store_id):
        """Create default hero section for a store."""
        hero = cls(
            store_id=store_id,
            hero_slides=[{
                'id': 1,
                'image_url': '/static/default-hero.jpg',
                'title': 'Welcome to Our Store',
                'subtitle': 'Discover Amazing Products',
                'description': 'Shop the latest trends and find everything you need',
                'button_text': 'Shop Now',
                'button_link': '/products',
                'text_position': 'center',
                'text_color': '#ffffff',
                'overlay_color': '#000000',
                'overlay_opacity': 30,
                'animation': 'fade',
                'duration': 5000,
                'active': True,
                'order': 1
            }]
        )
        db.session.add(hero)
        db.session.commit()
        return hero
    
    def __repr__(self):
        return f'<HeroSection for {self.store_id}>'