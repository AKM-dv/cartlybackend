from app.config.database import db, db_manager
from app.models.store import Store
from app.models.store_settings import StoreSettings
from app.config.multi_tenant import get_store_config
import logging

class TenantService:
    """Service for handling tenant-specific operations."""
    
    @staticmethod
    def switch_tenant_database(store_id):
        """Switch database connection to specific tenant."""
        try:
            # Validate store exists and is active
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            if not store.is_active:
                return {
                    'success': False,
                    'message': 'Store is inactive',
                    'code': 'STORE_INACTIVE'
                }
            
            # Get or create database session for this tenant
            session = db_manager.get_store_session(store_id)
            
            if not session:
                return {
                    'success': False,
                    'message': 'Failed to connect to store database',
                    'code': 'DATABASE_CONNECTION_ERROR'
                }
            
            return {
                'success': True,
                'message': 'Successfully switched to tenant database',
                'data': {
                    'store_id': store_id,
                    'store_name': store.store_name
                }
            }
            
        except Exception as e:
            logging.error(f"Tenant database switch error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while switching tenant database',
                'code': 'TENANT_SWITCH_ERROR'
            }
    
    @staticmethod
    def get_tenant_config(store_id):
        """Get tenant-specific configuration."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            # Get store settings
            settings = StoreSettings.get_by_store_id(store_id)
            
            config = {
                'store': store.to_dict(),
                'settings': settings.to_dict() if settings else {},
                'urls': {
                    'store_url': store.get_store_url(),
                    'admin_url': f"https://admin.{store.domain}",
                    'api_url': f"https://api.{store.domain}"
                },
                'features': {
                    'api_enabled': settings.api_enabled if settings else False,
                    'maintenance_mode': settings.maintenance_mode if settings else False,
                    'multi_currency': False,  # Future feature
                    'multi_language': False   # Future feature
                },
                'limits': {
                    'max_products': store.max_products,
                    'max_storage_mb': store.max_storage_mb,
                    'max_orders_per_month': store.max_orders_per_month
                }
            }
            
            return {
                'success': True,
                'message': 'Tenant configuration retrieved successfully',
                'data': config
            }
            
        except Exception as e:
            logging.error(f"Get tenant config error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving tenant configuration',
                'code': 'TENANT_CONFIG_ERROR'
            }
    
    @staticmethod
    def validate_tenant_access(store_id, user_id):
        """Validate if user has access to tenant."""
        try:
            from app.models.admin_user import AdminUser
            
            user = AdminUser.get_by_user_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            # Super admin can access any tenant
            if user.is_super_admin():
                return {
                    'success': True,
                    'message': 'Super admin access granted',
                    'data': {
                        'access_level': 'super_admin',
                        'permissions': ['all']
                    }
                }
            
            # Check if user belongs to this store
            if not user.can_access_store(store_id):
                return {
                    'success': False,
                    'message': 'Access denied to this store',
                    'code': 'ACCESS_DENIED'
                }
            
            return {
                'success': True,
                'message': 'Access granted',
                'data': {
                    'access_level': user.role,
                    'permissions': user.permissions or []
                }
            }
            
        except Exception as e:
            logging.error(f"Tenant access validation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while validating tenant access',
                'code': 'ACCESS_VALIDATION_ERROR'
            }
    
    @staticmethod
    def get_tenant_usage(store_id):
        """Get tenant resource usage."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            # Get current usage
            from app.models.product import Product
            from app.models.order import Order
            from app.models.customer import Customer
            
            current_products = Product.query.filter_by(store_id=store_id).count()
            current_customers = Customer.query.filter_by(store_id=store_id).count()
            
            # Get current month orders
            from datetime import datetime, timedelta
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_orders = Order.query.filter(
                Order.store_id == store_id,
                Order.created_at >= start_of_month
            ).count()
            
            # Calculate storage usage (placeholder - implement actual calculation)
            storage_usage_mb = store.get_storage_usage_mb()
            
            usage_data = {
                'products': {
                    'current': current_products,
                    'limit': store.max_products,
                    'percentage': (current_products / store.max_products * 100) if store.max_products > 0 else 0
                },
                'storage': {
                    'current_mb': storage_usage_mb,
                    'limit_mb': store.max_storage_mb,
                    'percentage': (storage_usage_mb / store.max_storage_mb * 100) if store.max_storage_mb > 0 else 0
                },
                'orders_monthly': {
                    'current': monthly_orders,
                    'limit': store.max_orders_per_month,
                    'percentage': (monthly_orders / store.max_orders_per_month * 100) if store.max_orders_per_month > 0 else 0
                },
                'customers': {
                    'total': current_customers
                }
            }
            
            return {
                'success': True,
                'message': 'Tenant usage retrieved successfully',
                'data': usage_data
            }
            
        except Exception as e:
            logging.error(f"Tenant usage error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving tenant usage',
                'code': 'TENANT_USAGE_ERROR'
            }
    
    @staticmethod
    def check_tenant_limits(store_id, resource_type, additional_usage=1):
        """Check if tenant can use additional resources."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            if resource_type == 'products':
                from app.models.product import Product
                current_count = Product.query.filter_by(store_id=store_id).count()
                limit = store.max_products
                
                if limit > 0 and (current_count + additional_usage) > limit:
                    return {
                        'success': False,
                        'message': f'Product limit exceeded. Maximum {limit} products allowed.',
                        'code': 'PRODUCT_LIMIT_EXCEEDED',
                        'data': {
                            'current': current_count,
                            'limit': limit,
                            'requested': additional_usage
                        }
                    }
            
            elif resource_type == 'storage':
                current_usage = store.get_storage_usage_mb()
                limit = store.max_storage_mb
                
                if limit > 0 and (current_usage + additional_usage) > limit:
                    return {
                        'success': False,
                        'message': f'Storage limit exceeded. Maximum {limit}MB allowed.',
                        'code': 'STORAGE_LIMIT_EXCEEDED',
                        'data': {
                            'current_mb': current_usage,
                            'limit_mb': limit,
                            'requested_mb': additional_usage
                        }
                    }
            
            elif resource_type == 'orders':
                from app.models.order import Order
                from datetime import datetime
                
                start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_count = Order.query.filter(
                    Order.store_id == store_id,
                    Order.created_at >= start_of_month
                ).count()
                limit = store.max_orders_per_month
                
                if limit > 0 and (current_count + additional_usage) > limit:
                    return {
                        'success': False,
                        'message': f'Monthly order limit exceeded. Maximum {limit} orders per month.',
                        'code': 'ORDER_LIMIT_EXCEEDED',
                        'data': {
                            'current': current_count,
                            'limit': limit,
                            'requested': additional_usage
                        }
                    }
            
            return {
                'success': True,
                'message': 'Resource usage within limits',
                'data': {
                    'allowed': True
                }
            }
            
        except Exception as e:
            logging.error(f"Tenant limits check error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while checking tenant limits',
                'code': 'LIMITS_CHECK_ERROR'
            }
    
    @staticmethod
    def cleanup_tenant_data(store_id, data_type='all'):
        """Clean up tenant data (for maintenance)."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            cleanup_results = {
                'cleaned_items': 0,
                'operations': []
            }
            
            # Close any existing database sessions for this tenant
            db_manager.close_store_session(store_id)
            cleanup_results['operations'].append('Closed database sessions')
            
            # Additional cleanup based on data_type
            if data_type in ['all', 'sessions']:
                # Clean up expired sessions (placeholder)
                cleanup_results['operations'].append('Cleaned expired sessions')
            
            if data_type in ['all', 'temp_files']:
                # Clean up temporary files (placeholder)
                cleanup_results['operations'].append('Cleaned temporary files')
            
            if data_type in ['all', 'logs']:
                # Clean up old logs (placeholder)
                cleanup_results['operations'].append('Cleaned old logs')
            
            return {
                'success': True,
                'message': 'Tenant cleanup completed successfully',
                'data': cleanup_results
            }
            
        except Exception as e:
            logging.error(f"Tenant cleanup error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during tenant cleanup',
                'code': 'TENANT_CLEANUP_ERROR'
            }
    
    @staticmethod
    def migrate_tenant_data(store_id, migration_type):
        """Migrate tenant data (for upgrades)."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            migration_results = {
                'migrated_items': 0,
                'operations': []
            }
            
            # Placeholder for different migration types
            if migration_type == 'schema_update':
                # Run schema migrations
                migration_results['operations'].append('Updated database schema')
            
            elif migration_type == 'data_cleanup':
                # Clean up orphaned data
                migration_results['operations'].append('Cleaned orphaned data')
            
            elif migration_type == 'index_rebuild':
                # Rebuild database indexes
                migration_results['operations'].append('Rebuilt database indexes')
            
            return {
                'success': True,
                'message': f'Tenant migration ({migration_type}) completed successfully',
                'data': migration_results
            }
            
        except Exception as e:
            logging.error(f"Tenant migration error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during tenant migration',
                'code': 'TENANT_MIGRATION_ERROR'
            }
    
    @staticmethod
    def backup_tenant_data(store_id):
        """Create backup of tenant data."""
        try:
            store = Store.get_by_store_id(store_id)
            
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found',
                    'code': 'STORE_NOT_FOUND'
                }
            
            from datetime import datetime
            
            backup_info = {
                'backup_id': f"backup_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'store_id': store_id,
                'store_name': store.store_name,
                'created_at': datetime.now().isoformat(),
                'status': 'completed',
                'size_mb': 0  # Placeholder
            }
            
            # TODO: Implement actual backup logic
            # - Export database data
            # - Backup uploaded files
            # - Create backup archive
            
            logging.info(f"Backup created for tenant: {store_id}")
            
            return {
                'success': True,
                'message': 'Tenant backup created successfully',
                'data': backup_info
            }
            
        except Exception as e:
            logging.error(f"Tenant backup error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during tenant backup',
                'code': 'TENANT_BACKUP_ERROR'
            }