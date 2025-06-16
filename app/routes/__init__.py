"""
Routes package initialization.
Registers all blueprints for the Flask application.
"""

def register_blueprints(app):
    """Register all route blueprints with the Flask app."""
    
    # Import blueprints
    from .auth import auth_bp
    from .store import store_bp
    from .categories import categories_bp
    from .products import products_bp
    from .orders import orders_bp
    from .customers import customers_bp
    from .hero_section import hero_section_bp
    from .blogs import blogs_bp
    from .policies import policies_bp
    from .analytics import analytics_bp
    from .dashboard import dashboard_bp
    from .contact import contact_bp
    from .payment_gateways import payment_gateways_bp  
    from .shipping import shipping_bp
    from .store_settings import store_settings_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(hero_section_bp)
    app.register_blueprint(blogs_bp)
    app.register_blueprint(policies_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(payment_gateways_bp)
    app.register_blueprint(shipping_bp)
    app.register_blueprint(store_settings_bp)