"""
Customer service for customer operations and management.
"""

from datetime import datetime, timedelta
from app.config.database import db
from app.models.customer import Customer
from app.models.order import Order
from app.services.email_service import EmailService
from app.utils.validators import validate_email
import logging

class CustomerService:
    """Service for handling customer operations."""
    
    @staticmethod
    def create_customer(store_id, customer_data):
        """Create new customer with validation."""
        try:
            # Validate required fields
            required_fields = ['email', 'first_name', 'last_name']
            for field in required_fields:
                if not customer_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }
            
            # Validate email format
            if not validate_email(customer_data['email']):
                return {
                    'success': False,
                    'message': 'Invalid email format',
                    'code': 'INVALID_EMAIL'
                }
            
            # Check if customer already exists
            existing_customer = Customer.get_by_email(store_id, customer_data['email'])
            if existing_customer:
                return {
                    'success': False,
                    'message': 'Customer with this email already exists',
                    'code': 'CUSTOMER_EXISTS'
                }
            
            # Create customer
            customer = Customer(
                store_id=store_id,
                email=customer_data['email'].lower(),
                first_name=customer_data['first_name'],
                last_name=customer_data['last_name'],
                phone=customer_data.get('phone'),
                date_of_birth=customer_data.get('date_of_birth'),
                gender=customer_data.get('gender'),
                customer_group=customer_data.get('customer_group', 'regular'),
                language=customer_data.get('language', 'en'),
                accepts_marketing=customer_data.get('accepts_marketing', False),
                admin_notes=customer_data.get('admin_notes')
            )
            
            # Set password if provided
            if customer_data.get('password'):
                customer.set_password(customer_data['password'])
            
            # Handle addresses
            if customer_data.get('billing_address'):
                customer.billing_address = customer_data['billing_address']
            
            if customer_data.get('shipping_address'):
                customer.shipping_address = customer_data['shipping_address']
            
            # Handle tags
            if customer_data.get('tags'):
                customer.tags = customer_data['tags']
            
            db.session.add(customer)
            db.session.commit()
            
            # Send welcome email if requested
            if customer_data.get('send_welcome_email', False):
                EmailService.send_customer_welcome(customer)
            
            logging.info(f"Customer created: {customer.email} for store {store_id}")
            
            return {
                'success': True,
                'message': 'Customer created successfully',
                'data': {
                    'customer': customer.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Customer creation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating the customer',
                'code': 'CUSTOMER_CREATE_ERROR'
            }
    
    @staticmethod
    def update_customer(store_id, customer_id, customer_data):
        """Update customer information."""
        try:
            customer = Customer.query.filter_by(
                id=customer_id,
                store_id=store_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'message': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Validate email if being changed
            if 'email' in customer_data and customer_data['email'] != customer.email:
                if not validate_email(customer_data['email']):
                    return {
                        'success': False,
                        'message': 'Invalid email format',
                        'code': 'INVALID_EMAIL'
                    }
                
                # Check if new email already exists
                existing = Customer.get_by_email(store_id, customer_data['email'])
                if existing and existing.id != customer_id:
                    return {
                        'success': False,
                        'message': 'Email already in use by another customer',
                        'code': 'EMAIL_EXISTS'
                    }
            
            # Update allowed fields
            allowed_fields = [
                'email', 'first_name', 'last_name', 'phone', 'date_of_birth',
                'gender', 'customer_group', 'language', 'accepts_marketing',
                'is_active', 'admin_notes', 'billing_address', 'shipping_address',
                'tags', 'custom_fields'
            ]
            
            for field in allowed_fields:
                if field in customer_data:
                    if field == 'email':
                        setattr(customer, field, customer_data[field].lower())
                    else:
                        setattr(customer, field, customer_data[field])
            
            # Update password if provided
            if customer_data.get('password'):
                customer.set_password(customer_data['password'])
            
            db.session.commit()
            
            logging.info(f"Customer updated: {customer.email} for store {store_id}")
            
            return {
                'success': True,
                'message': 'Customer updated successfully',
                'data': {
                    'customer': customer.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Customer update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating the customer',
                'code': 'CUSTOMER_UPDATE_ERROR'
            }
    
    @staticmethod
    def delete_customer(store_id, customer_id):
        """Delete customer (soft delete)."""
        try:
            customer = Customer.query.filter_by(
                id=customer_id,
                store_id=store_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'message': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Check if customer has orders
            order_count = Order.query.filter_by(
                store_id=store_id,
                customer_id=customer_id
            ).count()
            
            if order_count > 0:
                # Soft delete - deactivate instead of deleting
                customer.is_active = False
                customer.deactivated_at = datetime.utcnow()
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Customer deactivated (has order history)',
                    'data': {
                        'customer': customer.to_dict()
                    }
                }
            else:
                # Hard delete if no orders
                db.session.delete(customer)
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Customer deleted successfully'
                }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Customer deletion error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while deleting the customer',
                'code': 'CUSTOMER_DELETE_ERROR'
            }
    
    @staticmethod
    def add_customer_note(store_id, customer_id, note):
        """Add note to customer."""
        try:
            customer = Customer.query.filter_by(
                id=customer_id,
                store_id=store_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'message': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Add timestamp to note
            timestamped_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {note}"
            
            if customer.admin_notes:
                customer.admin_notes += f"\n{timestamped_note}"
            else:
                customer.admin_notes = timestamped_note
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Note added successfully',
                'data': {
                    'customer': customer.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Add customer note error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while adding the note',
                'code': 'NOTE_ADD_ERROR'
            }
    
    @staticmethod
    def get_customer_analytics(store_id, customer_id):
        """Get customer analytics and insights."""
        try:
            customer = Customer.query.filter_by(
                id=customer_id,
                store_id=store_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'message': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Get customer orders
            orders = Order.query.filter_by(
                store_id=store_id,
                customer_id=customer_id
            ).order_by(Order.created_at.desc()).all()
            
            # Calculate analytics
            total_orders = len(orders)
            paid_orders = [order for order in orders if order.payment_status == 'paid']
            total_revenue = sum(float(order.total_amount) for order in paid_orders)
            average_order_value = total_revenue / len(paid_orders) if paid_orders else 0
            
            # Get recent orders
            recent_orders = orders[:5]
            
            # Calculate customer lifetime value
            registration_days = (datetime.utcnow() - customer.created_at).days if customer.created_at else 0
            clv = total_revenue
            
            # Customer segment
            if total_orders == 0:
                segment = 'new'
            elif total_orders == 1:
                segment = 'one_time'
            elif total_revenue > 1000:
                segment = 'vip'
            elif total_orders >= 5:
                segment = 'loyal'
            else:
                segment = 'regular'
            
            analytics_data = {
                'customer': customer.to_dict(),
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'average_order_value': average_order_value,
                    'customer_lifetime_value': clv,
                    'registration_days': registration_days,
                    'segment': segment
                },
                'recent_orders': [order.to_dict() for order in recent_orders],
                'order_frequency': {
                    'monthly': len([o for o in orders if o.created_at >= datetime.utcnow() - timedelta(days=30)]),
                    'quarterly': len([o for o in orders if o.created_at >= datetime.utcnow() - timedelta(days=90)]),
                    'yearly': len([o for o in orders if o.created_at >= datetime.utcnow() - timedelta(days=365)])
                }
            }
            
            return {
                'success': True,
                'message': 'Customer analytics retrieved successfully',
                'data': analytics_data
            }
            
        except Exception as e:
            logging.error(f"Customer analytics error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving customer analytics',
                'code': 'ANALYTICS_ERROR'
            }
    
    @staticmethod
    def bulk_update_customers(store_id, customer_ids, update_data):
        """Bulk update multiple customers."""
        try:
            if not customer_ids:
                return {
                    'success': False,
                    'message': 'No customers selected',
                    'code': 'NO_CUSTOMERS_SELECTED'
                }
            
            customers = Customer.query.filter(
                Customer.store_id == store_id,
                Customer.id.in_(customer_ids)
            ).all()
            
            if not customers:
                return {
                    'success': False,
                    'message': 'No customers found',
                    'code': 'CUSTOMERS_NOT_FOUND'
                }
            
            # Update allowed fields only
            allowed_bulk_fields = ['customer_group', 'is_active', 'accepts_marketing', 'tags']
            
            updated_count = 0
            for customer in customers:
                for field in allowed_bulk_fields:
                    if field in update_data:
                        if field == 'tags' and update_data[field]:
                            # Add tags instead of replacing
                            existing_tags = customer.tags or []
                            new_tags = update_data[field] if isinstance(update_data[field], list) else [update_data[field]]
                            customer.tags = list(set(existing_tags + new_tags))
                        else:
                            setattr(customer, field, update_data[field])
                updated_count += 1
            
            db.session.commit()
            
            logging.info(f"Bulk updated {updated_count} customers for store {store_id}")
            
            return {
                'success': True,
                'message': f'Successfully updated {updated_count} customers',
                'data': {
                    'updated_count': updated_count,
                    'customers': [customer.to_dict() for customer in customers]
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Bulk customer update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during bulk update',
                'code': 'BULK_UPDATE_ERROR'
            }