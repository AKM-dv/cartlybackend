from datetime import datetime, timedelta
from app.config.database import db
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import Product
from app.services.email_service import EmailService
import logging

class OrderService:
    """Service for handling order operations."""
    
    @staticmethod
    def create_order(store_id, order_data):
        """Create new order."""
        try:
            # Validate required fields
            required_fields = ['customer_email', 'customer_name', 'billing_address', 'order_items']
            for field in required_fields:
                if not order_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }
            
            # Validate order items
            if not order_data['order_items'] or len(order_data['order_items']) == 0:
                return {
                    'success': False,
                    'message': 'Order must contain at least one item',
                    'code': 'EMPTY_ORDER'
                }
            
            # Validate and calculate totals
            calculation_result = OrderService._calculate_order_totals(store_id, order_data['order_items'])
            if not calculation_result['success']:
                return calculation_result
            
            totals = calculation_result['data']
            
            # Get or create customer
            customer = None
            if not order_data.get('is_guest_order', False):
                customer = Customer.get_by_email(store_id, order_data['customer_email'])
            
            # Create order
            order = Order(
                store_id=store_id,
                customer_id=customer.id if customer else None,
                is_guest_order=order_data.get('is_guest_order', False),
                customer_email=order_data['customer_email'],
                customer_phone=order_data.get('customer_phone'),
                customer_name=order_data['customer_name'],
                billing_address=order_data['billing_address'],
                shipping_address=order_data.get('shipping_address', order_data['billing_address']),
                same_as_billing=order_data.get('same_as_billing', True),
                order_items=order_data['order_items'],
                subtotal=totals['subtotal'],
                tax_amount=totals['tax_amount'],
                shipping_amount=totals['shipping_amount'],
                discount_amount=totals['discount_amount'],
                total_amount=totals['total_amount'],
                currency=order_data.get('currency', 'USD'),
                payment_method=order_data.get('payment_method'),
                payment_gateway=order_data.get('payment_gateway'),
                shipping_method=order_data.get('shipping_method'),
                customer_notes=order_data.get('customer_notes'),
                source=order_data.get('source', 'admin'),
                ip_address=order_data.get('ip_address'),
                user_agent=order_data.get('user_agent')
            )
            
            db.session.add(order)
            db.session.commit()
            
            # Update product inventory
            OrderService._update_inventory_for_order(order)
            
            # Send order confirmation email
            if order_data.get('send_confirmation_email', True):
                EmailService.send_order_confirmation(order)
            
            logging.info(f"Order created: {order.order_number} for store {store_id}")
            
            return {
                'success': True,
                'message': 'Order created successfully',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Order creation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating the order',
                'code': 'ORDER_CREATE_ERROR'
            }
    
    @staticmethod
    def get_order(store_id, order_id=None, order_number=None):
        """Get order by ID or order number."""
        try:
            if order_id:
                order = Order.query.filter_by(id=order_id, store_id=store_id).first()
            elif order_number:
                order = Order.get_by_order_number(store_id, order_number)
            else:
                return {
                    'success': False,
                    'message': 'Order ID or order number is required',
                    'code': 'MISSING_IDENTIFIER'
                }
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            return {
                'success': True,
                'message': 'Order retrieved successfully',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            logging.error(f"Get order error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving the order',
                'code': 'ORDER_GET_ERROR'
            }
    
    @staticmethod
    def update_order_status(store_id, order_id, new_status, notes=None):
        """Update order status."""
        try:
            order = Order.query.filter_by(id=order_id, store_id=store_id).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
            
            if new_status not in valid_statuses:
                return {
                    'success': False,
                    'message': 'Invalid order status',
                    'code': 'INVALID_STATUS'
                }
            
            old_status = order.status
            
            # Update status based on type
            if new_status == 'confirmed':
                if not order.confirm():
                    return {
                        'success': False,
                        'message': 'Cannot confirm order in current state',
                        'code': 'INVALID_STATUS_TRANSITION'
                    }
            elif new_status == 'shipped':
                if not order.ship():
                    return {
                        'success': False,
                        'message': 'Cannot ship order in current state',
                        'code': 'INVALID_STATUS_TRANSITION'
                    }
            elif new_status == 'delivered':
                if not order.deliver():
                    return {
                        'success': False,
                        'message': 'Cannot mark order as delivered in current state',
                        'code': 'INVALID_STATUS_TRANSITION'
                    }
            elif new_status == 'cancelled':
                if not order.cancel(notes):
                    return {
                        'success': False,
                        'message': 'Cannot cancel order in current state',
                        'code': 'INVALID_STATUS_TRANSITION'
                    }
            else:
                order.status = new_status
            
            # Add admin notes if provided
            if notes:
                if order.admin_notes:
                    order.admin_notes += f"\n[{datetime.now()}] Status changed from {old_status} to {new_status}: {notes}"
                else:
                    order.admin_notes = f"Status changed from {old_status} to {new_status}: {notes}"
            
            db.session.commit()
            
            # Send status update email
            EmailService.send_order_status_update(order, old_status, new_status)
            
            logging.info(f"Order status updated: {order.order_number} from {old_status} to {new_status}")
            
            return {
                'success': True,
                'message': f'Order status updated to {new_status}',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Order status update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating order status',
                'code': 'ORDER_STATUS_UPDATE_ERROR'
            }
    
    @staticmethod
    def update_payment_status(store_id, order_id, payment_status, transaction_id=None):
        """Update order payment status."""
        try:
            order = Order.query.filter_by(id=order_id, store_id=store_id).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            valid_statuses = ['pending', 'paid', 'partially_paid', 'failed', 'refunded', 'partially_refunded']
            
            if payment_status not in valid_statuses:
                return {
                    'success': False,
                    'message': 'Invalid payment status',
                    'code': 'INVALID_PAYMENT_STATUS'
                }
            
            order.update_payment_status(payment_status, transaction_id)
            db.session.commit()
            
            logging.info(f"Payment status updated: {order.order_number} to {payment_status}")
            
            return {
                'success': True,
                'message': f'Payment status updated to {payment_status}',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Payment status update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating payment status',
                'code': 'PAYMENT_STATUS_UPDATE_ERROR'
            }
    
    @staticmethod
    def add_tracking_info(store_id, order_id, tracking_number, tracking_url=None, shipping_partner=None):
        """Add tracking information to order."""
        try:
            order = Order.query.filter_by(id=order_id, store_id=store_id).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            order.tracking_number = tracking_number
            order.tracking_url = tracking_url
            order.shipping_partner = shipping_partner
            
            # Update status to shipped if not already
            if order.status not in ['shipped', 'delivered']:
                order.ship(tracking_number, shipping_partner)
            
            db.session.commit()
            
            # Send tracking email
            EmailService.send_tracking_info(order)
            
            logging.info(f"Tracking info added: {order.order_number} - {tracking_number}")
            
            return {
                'success': True,
                'message': 'Tracking information added successfully',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Add tracking info error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while adding tracking information',
                'code': 'TRACKING_ADD_ERROR'
            }
    
    @staticmethod
    def get_orders_list(store_id, filters=None, page=1, per_page=20):
        """Get orders list with filters and pagination."""
        try:
            query = Order.query.filter_by(store_id=store_id)
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.filter_by(status=filters['status'])
                
                if filters.get('payment_status'):
                    query = query.filter_by(payment_status=filters['payment_status'])
                
                if filters.get('customer_email'):
                    query = query.filter(Order.customer_email.like(f"%{filters['customer_email']}%"))
                
                if filters.get('order_number'):
                    query = query.filter(Order.order_number.like(f"%{filters['order_number']}%"))
                
                if filters.get('date_from'):
                    query = query.filter(Order.created_at >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(Order.created_at <= filters['date_to'])
                
                if filters.get('min_amount'):
                    query = query.filter(Order.total_amount >= filters['min_amount'])
                
                if filters.get('max_amount'):
                    query = query.filter(Order.total_amount <= filters['max_amount'])
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            orders = query.order_by(Order.created_at.desc()).offset(
                (page - 1) * per_page
            ).limit(per_page).all()
            
            return {
                'success': True,
                'message': 'Orders retrieved successfully',
                'data': {
                    'orders': [order.to_dict() for order in orders],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"Get orders list error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving orders',
                'code': 'ORDERS_LIST_ERROR'
            }
    
    @staticmethod
    def get_order_analytics(store_id, date_range=None):
        """Get order analytics and statistics."""
        try:
            # Set default date range to last 30 days
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = date_range.get('start_date')
                end_date = date_range.get('end_date')
            
            # Base query
            query = Order.query.filter_by(store_id=store_id)
            
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            if end_date:
                query = query.filter(Order.created_at <= end_date)
            
            orders = query.all()
            
            # Calculate analytics
            analytics = {
                'summary': {
                    'total_orders': len(orders),
                    'total_revenue': sum(float(order.total_amount) for order in orders if order.payment_status == 'paid'),
                    'average_order_value': 0,
                    'pending_orders': len([o for o in orders if o.status == 'pending']),
                    'completed_orders': len([o for o in orders if o.status == 'delivered']),
                    'cancelled_orders': len([o for o in orders if o.status == 'cancelled'])
                },
                'by_status': {},
                'by_payment_status': {},
                'daily_sales': [],
                'top_customers': []
            }
            
            # Calculate average order value
            paid_orders = [o for o in orders if o.payment_status == 'paid']
            if paid_orders:
                analytics['summary']['average_order_value'] = analytics['summary']['total_revenue'] / len(paid_orders)
            
            # Group by status
            status_counts = {}
            payment_status_counts = {}
            
            for order in orders:
                status_counts[order.status] = status_counts.get(order.status, 0) + 1
                payment_status_counts[order.payment_status] = payment_status_counts.get(order.payment_status, 0) + 1
            
            analytics['by_status'] = status_counts
            analytics['by_payment_status'] = payment_status_counts
            
            # Daily sales (last 7 days)
            daily_sales = {}
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).date()
                daily_sales[date.isoformat()] = {
                    'date': date.isoformat(),
                    'orders': 0,
                    'revenue': 0
                }
            
            for order in orders:
                order_date = order.created_at.date().isoformat()
                if order_date in daily_sales:
                    daily_sales[order_date]['orders'] += 1
                    if order.payment_status == 'paid':
                        daily_sales[order_date]['revenue'] += float(order.total_amount)
            
            analytics['daily_sales'] = list(daily_sales.values())
            
            # Top customers (by order value)
            customer_stats = {}
            for order in paid_orders:
                email = order.customer_email
                if email not in customer_stats:
                    customer_stats[email] = {
                        'email': email,
                        'name': order.customer_name,
                        'total_orders': 0,
                        'total_spent': 0
                    }
                
                customer_stats[email]['total_orders'] += 1
                customer_stats[email]['total_spent'] += float(order.total_amount)
            
            # Sort by total spent and get top 10
            top_customers = sorted(
                customer_stats.values(),
                key=lambda x: x['total_spent'],
                reverse=True
            )[:10]
            
            analytics['top_customers'] = top_customers
            
            return {
                'success': True,
                'message': 'Order analytics retrieved successfully',
                'data': analytics
            }
            
        except Exception as e:
            logging.error(f"Order analytics error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving order analytics',
                'code': 'ORDER_ANALYTICS_ERROR'
            }
    
    @staticmethod
    def _calculate_order_totals(store_id, order_items):
        """Calculate order totals including tax and shipping."""
        try:
            subtotal = 0
            
            # Validate and calculate subtotal
            for item in order_items:
                if not all(key in item for key in ['product_id', 'quantity', 'unit_price']):
                    return {
                        'success': False,
                        'message': 'Invalid order item data',
                        'code': 'INVALID_ORDER_ITEM'
                    }
                
                # Verify product exists and is available
                product = Product.query.filter_by(
                    id=item['product_id'],
                    store_id=store_id
                ).first()
                
                if not product:
                    return {
                        'success': False,
                        'message': f"Product {item['product_id']} not found",
                        'code': 'PRODUCT_NOT_FOUND'
                    }
                
                if product.status != 'active':
                    return {
                        'success': False,
                        'message': f"Product {product.name} is not available",
                        'code': 'PRODUCT_NOT_AVAILABLE'
                    }
                
                # Check inventory
                if product.track_inventory and not product.is_in_stock():
                    return {
                        'success': False,
                        'message': f"Product {product.name} is out of stock",
                        'code': 'PRODUCT_OUT_OF_STOCK'
                    }
                
                # Calculate item total
                item_total = float(item['unit_price']) * int(item['quantity'])
                item['total_price'] = item_total
                subtotal += item_total
            
            # Calculate tax (placeholder - implement based on store settings)
            tax_amount = 0  # TODO: Implement tax calculation
            
            # Calculate shipping (placeholder - implement based on shipping method)
            shipping_amount = 0  # TODO: Implement shipping calculation
            
            # Calculate discount (placeholder - implement coupon logic)
            discount_amount = 0  # TODO: Implement discount calculation
            
            # Calculate total
            total_amount = subtotal + tax_amount + shipping_amount - discount_amount
            
            return {
                'success': True,
                'data': {
                    'subtotal': subtotal,
                    'tax_amount': tax_amount,
                    'shipping_amount': shipping_amount,
                    'discount_amount': discount_amount,
                    'total_amount': total_amount
                }
            }
            
        except Exception as e:
            logging.error(f"Calculate order totals error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while calculating order totals',
                'code': 'CALCULATION_ERROR'
            }
    
    @staticmethod
    def _update_inventory_for_order(order):
        """Update product inventory after order creation."""
        try:
            for item in order.order_items:
                product = Product.query.filter_by(
                    id=item['product_id'],
                    store_id=order.store_id
                ).first()
                
                if product and product.track_inventory:
                    # Reduce inventory by quantity ordered
                    product.update_inventory(-item['quantity'], item.get('variant_id'))
                    
                    # Record sale for analytics
                    product.record_sale(item['quantity'], item['total_price'])
            
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Update inventory for order error: {str(e)}")
            # Don't fail the order creation, just log the error
    
    @staticmethod
    def cancel_order(store_id, order_id, reason=None, restore_inventory=True):
        """Cancel order and optionally restore inventory."""
        try:
            order = Order.query.filter_by(id=order_id, store_id=store_id).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            if not order.can_cancel():
                return {
                    'success': False,
                    'message': 'Order cannot be cancelled in current state',
                    'code': 'CANNOT_CANCEL'
                }
            
            # Cancel the order
            order.cancel(reason)
            
            # Restore inventory if requested
            if restore_inventory:
                for item in order.order_items:
                    product = Product.query.filter_by(
                        id=item['product_id'],
                        store_id=order.store_id
                    ).first()
                    
                    if product and product.track_inventory:
                        product.update_inventory(item['quantity'], item.get('variant_id'))
            
            db.session.commit()
            
            # Send cancellation email
            EmailService.send_order_cancellation(order, reason)
            
            logging.info(f"Order cancelled: {order.order_number} - {reason}")
            
            return {
                'success': True,
                'message': 'Order cancelled successfully',
                'data': {
                    'order': order.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Cancel order error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while cancelling the order',
                'code': 'ORDER_CANCEL_ERROR'
            }