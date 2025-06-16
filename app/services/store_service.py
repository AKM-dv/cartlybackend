from datetime import datetime
from app.config.database import db, db_manager
from app.models.store import Store
from app.models.admin_user import AdminUser
from app.models.store_settings import StoreSettings
from app.models.contact_details import ContactDetails
from app.models.hero_section import HeroSection
from app.models.payment_gateway import PaymentGateway
from app.models.shipping_partner import ShippingPartner
from app.models.category import Category
from app.models.policy import Policy
import logging

class StoreService:
    """Service for handling store operations."""
    
    @staticmethod
    def create_store(store_data, owner_data):
        """Create new store with default settings."""
        try:
            # Validate store data
            required_fields = ['store_name', 'domain', 'subdomain']
            for field in required_fields:
                if not store_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }
            
            # Check domain uniqueness
            if Store.get_by_domain(store_data['domain']):
                return {
                    'success': False,
                    'message': 'Domain is already in use',
                    'code': 'DOMAIN_EXISTS'
                }
            
            if Store.query.filter_by(subdomain=store_data['subdomain']).first():
                return {
                    'success': False,
                    'message': 'Subdomain is already in use',
                    'code': 'SUBDOMAIN_EXISTS'
                }
            
            # Create store
            store = Store(
                store_name=store_data['store_name'],
                store_description=store_data.get('store_description'),
                domain=store_data['domain'],
                subdomain=store_data['subdomain'],
                custom_domain=store_data.get('custom_domain'),
                owner_name=owner_data['owner_name'],
                owner_email=owner_data['owner_email'],
                owner_phone=owner_data.get('owner_phone'),
                business_name=store_data.get('business_name'),
                business_type=store_data.get('business_type', 'retail'),
                plan_type=store_data.get('plan_type', 'basic')
            )
            
            db.session.add(store)
            db.session.flush()  # Get store ID
            
            # Create store database
            if not db_manager.create_store_database(store.store_id):
                db.session.rollback()
                return {
                    'success': False,
                    'message': 'Failed to create store database',
                    'code': 'DATABASE_CREATE_ERROR'
                }
            
            # Create store owner admin user
            owner = AdminUser(
                email=owner_data['owner_email'],
                first_name=owner_data['first_name'],
                last_name=owner_data['last_name'],
                phone=owner_data.get('phone'),
                role='store_admin',
                store_id=store.store_id,
                is_verified=True  # Auto-verify store owners
            )
            
            if 'password' in owner_data:
                owner.set_password(owner_data['password'])
            
            db.session.add(owner)
            
            # Create default store settings
            settings = StoreSettings.create_default(store.store_id)
            
            # Create default contact details
            contact_data = {
                'address_line_1': store_data.get('address_line_1', ''),
                'city': store_data.get('city', ''),
                'state': store_data.get('state', ''),
                'postal_code': store_data.get('postal_code', ''),
                'country': store_data.get('country', 'India')
            }
            
            contact = ContactDetails.create_default(
                store.store_id,
                owner_data['owner_email'],
                owner_data.get('owner_phone', ''),
                contact_data
            )
            
            # Create default hero section
            hero = HeroSection.create_default(store.store_id)
            
            # Create default payment gateways
            payment_gateways = PaymentGateway.create_default_gateways(store.store_id)
            
            # Create default shipping partners
            shipping_partners = ShippingPartner.create_default_partners(store.store_id)
            
            # Create default categories
            categories = Category.create_default_categories(store.store_id)
            
            # Create default policies
            policies = Policy.create_default_policies(store.store_id)
            
            # Mark setup as complete
            store.mark_setup_complete()
            
            db.session.commit()
            
            logging.info(f"New store created: {store.store_name} ({store.store_id})")
            
            return {
                'success': True,
                'message': 'Store created successfully',
                'data': {
                    'store': store.to_dict(),
                    'owner': owner.to_dict(),
                    'setup_complete': True
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store creation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating the store',
                'code': 'STORE_CREATE_ERROR'
            }
    
    @staticmethod
    def get_store(store_id):
        """Get store by ID."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            return {
                'success': True,
                'message': 'Store retrieved successfully',
                'data': {
                    'store': store.to_dict()
                }
            }
            
        except Exception as e:
            logging.error(f"Get store error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving the store',
                'code': 'STORE_GET_ERROR'
            }
    
    @staticmethod
    def update_store(store_id, update_data):
        """Update store information."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            # Update allowed fields
            allowed_fields = [
                'store_name', 'store_description', 'business_name', 
                'business_type', 'business_registration', 'tax_id',
                'custom_domain'
            ]
            
            for field in allowed_fields:
                if field in update_data:
                    setattr(store, field, update_data[field])
            
            db.session.commit()
            
            logging.info(f"Store updated: {store.store_id}")
            
            return {
                'success': True,
                'message': 'Store updated successfully',
                'data': {
                    'store': store.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating the store',
                'code': 'STORE_UPDATE_ERROR'
            }
    
    @staticmethod
    def delete_store(store_id):
        """Delete store and all associated data."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            # Delete store database
            if not db_manager.delete_store_database(store_id):
                logging.warning(f"Failed to delete database for store: {store_id}")
            
            # Delete store record
            db.session.delete(store)
            db.session.commit()
            
            logging.info(f"Store deleted: {store_id}")
            
            return {
                'success': True,
                'message': 'Store deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store deletion error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while deleting the store',
                'code': 'STORE_DELETE_ERROR'
            }
    
    @staticmethod
    def get_store_settings(store_id):
        """Get store settings."""
        try:
            settings = StoreSettings.get_by_store_id(store_id)
            
            if not settings:
                # Create default settings if not exists
                settings = StoreSettings.create_default(store_id)
            
            return {
                'success': True,
                'message': 'Store settings retrieved successfully',
                'data': {
                    'settings': settings.to_dict()
                }
            }
            
        except Exception as e:
            logging.error(f"Get store settings error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving store settings',
                'code': 'SETTINGS_GET_ERROR'
            }
    
    @staticmethod
    def update_store_settings(store_id, settings_data):
        """Update store settings."""
        try:
            settings = StoreSettings.get_by_store_id(store_id)
            
            if not settings:
                settings = StoreSettings(store_id=store_id)
                db.session.add(settings)
            
            # Update allowed settings
            allowed_fields = [
                'theme_name', 'primary_color', 'secondary_color', 'accent_color',
                'currency_code', 'currency_symbol', 'language', 'timezone',
                'meta_title', 'meta_description', 'meta_keywords',
                'auto_accept_orders', 'track_inventory', 'tax_inclusive',
                'default_tax_rate', 'free_shipping_threshold', 'enable_reviews',
                'enable_wishlist', 'enable_guest_checkout', 'maintenance_mode'
            ]
            
            for field in allowed_fields:
                if field in settings_data:
                    setattr(settings, field, settings_data[field])
            
            db.session.commit()
            
            logging.info(f"Store settings updated: {store_id}")
            
            return {
                'success': True,
                'message': 'Store settings updated successfully',
                'data': {
                    'settings': settings.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store settings update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating store settings',
                'code': 'SETTINGS_UPDATE_ERROR'
            }
    
    @staticmethod
    def get_store_stats(store_id):
        """Get store statistics."""
        try:
            from app.models.product import Product
            from app.models.order import Order
            from app.models.customer import Customer
            
            # Get basic counts
            total_products = Product.query.filter_by(store_id=store_id).count()
            active_products = Product.query.filter_by(store_id=store_id, status='active').count()
            total_orders = Order.query.filter_by(store_id=store_id).count()
            total_customers = Customer.query.filter_by(store_id=store_id).count()
            
            # Get revenue stats
            paid_orders = Order.query.filter_by(store_id=store_id, payment_status='paid').all()
            total_revenue = sum(float(order.total_amount) for order in paid_orders)
            
            # Get recent activity
            recent_orders = Order.get_recent_orders(store_id, days=30)
            monthly_revenue = sum(float(order.total_amount) for order in recent_orders if order.payment_status == 'paid')
            
            return {
                'success': True,
                'message': 'Store statistics retrieved successfully',
                'data': {
                    'products': {
                        'total': total_products,
                        'active': active_products,
                        'inactive': total_products - active_products
                    },
                    'orders': {
                        'total': total_orders,
                        'recent': len(recent_orders)
                    },
                    'customers': {
                        'total': total_customers
                    },
                    'revenue': {
                        'total': total_revenue,
                        'monthly': monthly_revenue
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"Store stats error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving store statistics',
                'code': 'STATS_ERROR'
            }
    
    @staticmethod
    def toggle_maintenance_mode(store_id, enabled=None, message=None):
        """Toggle store maintenance mode."""
        try:
            settings = StoreSettings.get_by_store_id(store_id)
            
            if not settings:
                return {
                    'success': False,
                    'message': 'Store settings not found',
                    'code': 'SETTINGS_NOT_FOUND'
                }
            
            if enabled is not None:
                settings.maintenance_mode = enabled
            else:
                settings.maintenance_mode = not settings.maintenance_mode
            
            if message:
                settings.maintenance_message = message
            
            db.session.commit()
            
            status = "enabled" if settings.maintenance_mode else "disabled"
            logging.info(f"Maintenance mode {status} for store: {store_id}")
            
            return {
                'success': True,
                'message': f'Maintenance mode {status}',
                'data': {
                    'maintenance_mode': settings.maintenance_mode,
                    'maintenance_message': settings.maintenance_message
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Maintenance mode toggle error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while toggling maintenance mode',
                'code': 'MAINTENANCE_ERROR'
            }
    
    @staticmethod
    def list_stores(page=1, per_page=20, search=None, status=None):
        """List all stores with pagination and filters."""
        try:
            query = Store.query
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        Store.store_name.like(search_term),
                        Store.domain.like(search_term),
                        Store.owner_email.like(search_term)
                    )
                )
            
            if status:
                if status == 'active':
                    query = query.filter_by(is_active=True)
                elif status == 'inactive':
                    query = query.filter_by(is_active=False)
                elif status == 'trial':
                    query = query.filter_by(subscription_status='trial')
                elif status == 'suspended':
                    query = query.filter_by(subscription_status='suspended')
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            stores = query.order_by(Store.created_at.desc()).offset(
                (page - 1) * per_page
            ).limit(per_page).all()
            
            return {
                'success': True,
                'message': 'Stores retrieved successfully',
                'data': {
                    'stores': [store.to_dict() for store in stores],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"List stores error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving stores',
                'code': 'STORES_LIST_ERROR'
            }
    
    @staticmethod
    def change_store_plan(store_id, new_plan):
        """Change store subscription plan."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            # Define plan limits
            plan_limits = {
                'basic': {
                    'max_products': 100,
                    'max_storage_mb': 500,
                    'max_orders_per_month': 1000
                },
                'premium': {
                    'max_products': 1000,
                    'max_storage_mb': 5000,
                    'max_orders_per_month': 10000
                },
                'enterprise': {
                    'max_products': -1,  # Unlimited
                    'max_storage_mb': -1,  # Unlimited
                    'max_orders_per_month': -1  # Unlimited
                }
            }
            
            if new_plan not in plan_limits:
                return {
                    'success': False,
                    'message': 'Invalid plan type',
                    'code': 'INVALID_PLAN'
                }
            
            # Update store plan
            store.plan_type = new_plan
            limits = plan_limits[new_plan]
            
            for limit_key, limit_value in limits.items():
                setattr(store, limit_key, limit_value)
            
            db.session.commit()
            
            logging.info(f"Store plan changed to {new_plan}: {store_id}")
            
            return {
                'success': True,
                'message': f'Store plan changed to {new_plan}',
                'data': {
                    'store': store.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Plan change error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while changing the plan',
                'code': 'PLAN_CHANGE_ERROR'
            }
    
    @staticmethod
    def suspend_store(store_id, reason=None):
        """Suspend store operations."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            store.subscription_status = 'suspended'
            store.is_active = False
            
            # Enable maintenance mode
            settings = StoreSettings.get_by_store_id(store_id)
            if settings:
                settings.maintenance_mode = True
                settings.maintenance_message = reason or "Store is temporarily suspended"
            
            db.session.commit()
            
            logging.warning(f"Store suspended: {store_id} - {reason}")
            
            return {
                'success': True,
                'message': 'Store suspended successfully',
                'data': {
                    'store': store.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store suspension error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while suspending the store',
                'code': 'STORE_SUSPEND_ERROR'
            }
    
    @staticmethod
    def reactivate_store(store_id):
        """Reactivate suspended store."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            store.subscription_status = 'active'
            store.is_active = True
            
            # Disable maintenance mode
            settings = StoreSettings.get_by_store_id(store_id)
            if settings:
                settings.maintenance_mode = False
                settings.maintenance_message = None
            
            db.session.commit()
            
            logging.info(f"Store reactivated: {store_id}")
            
            return {
                'success': True,
                'message': 'Store reactivated successfully',
                'data': {
                    'store': store.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Store reactivation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while reactivating the store',
                'code': 'STORE_REACTIVATE_ERROR'
            }
    
    @staticmethod
    def validate_domain(domain, store_id=None):
        """Validate if domain is available."""
        try:
            existing_store = Store.get_by_domain(domain)
            
            # Domain is available if no store uses it, or it's the same store
            if not existing_store or (store_id and existing_store.store_id == store_id):
                return {
                    'success': True,
                    'message': 'Domain is available',
                    'data': {
                        'available': True
                    }
                }
            else:
                return {
                    'success': True,
                    'message': 'Domain is not available',
                    'data': {
                        'available': False
                    }
                }
                
        except Exception as e:
            logging.error(f"Domain validation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while validating domain',
                'code': 'DOMAIN_VALIDATION_ERROR'
            }
    
    @staticmethod
    def get_store_health(store_id):
        """Get store health status and recommendations."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            health_data = {
                'overall_score': 0,
                'checks': [],
                'recommendations': []
            }
            
            score = 0
            total_checks = 0
            
            # Check store setup completion
            total_checks += 1
            if store.is_setup_complete:
                score += 1
                health_data['checks'].append({
                    'name': 'Store Setup',
                    'status': 'passed',
                    'message': 'Store setup is complete'
                })
            else:
                health_data['checks'].append({
                    'name': 'Store Setup',
                    'status': 'failed',
                    'message': 'Store setup is incomplete'
                })
                health_data['recommendations'].append('Complete your store setup')
            
            # Check if store has products
            from app.models.product import Product
            total_checks += 1
            product_count = Product.query.filter_by(store_id=store_id).count()
            
            if product_count > 0:
                score += 1
                health_data['checks'].append({
                    'name': 'Products',
                    'status': 'passed',
                    'message': f'Store has {product_count} products'
                })
            else:
                health_data['checks'].append({
                    'name': 'Products',
                    'status': 'failed',
                    'message': 'Store has no products'
                })
                health_data['recommendations'].append('Add products to your store')
            
            # Check payment gateway configuration
            total_checks += 1
            active_gateways = PaymentGateway.get_active_gateways(store_id)
            
            if active_gateways:
                score += 1
                health_data['checks'].append({
                    'name': 'Payment Gateways',
                    'status': 'passed',
                    'message': f'{len(active_gateways)} payment gateways configured'
                })
            else:
                health_data['checks'].append({
                    'name': 'Payment Gateways',
                    'status': 'failed',
                    'message': 'No payment gateways configured'
                })
                health_data['recommendations'].append('Configure payment gateways')
            
            # Check shipping configuration
            total_checks += 1
            active_shipping = ShippingPartner.get_active_partners(store_id)
            
            if active_shipping:
                score += 1
                health_data['checks'].append({
                    'name': 'Shipping Partners',
                    'status': 'passed',
                    'message': f'{len(active_shipping)} shipping partners configured'
                })
            else:
                health_data['checks'].append({
                    'name': 'Shipping Partners',
                    'status': 'failed',
                    'message': 'No shipping partners configured'
                })
                health_data['recommendations'].append('Configure shipping partners')
            
            # Calculate overall score
            health_data['overall_score'] = round((score / total_checks) * 100)
            
            return {
                'success': True,
                'message': 'Store health retrieved successfully',
                'data': health_data
            }
            
        except Exception as e:
            logging.error(f"Store health check error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while checking store health',
                'code': 'HEALTH_CHECK_ERROR'
            }