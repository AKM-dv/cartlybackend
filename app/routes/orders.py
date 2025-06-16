from flask import Blueprint, request, jsonify
from app.services.order_service import OrderService
from app.config.database import db
from app.models.order import Order
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@orders_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_orders():
    """List orders with filters and pagination."""
    try:
        store_id = get_current_store_id()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build filters
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('payment_status'):
            filters['payment_status'] = request.args.get('payment_status')
        
        if request.args.get('customer_email'):
            filters['customer_email'] = request.args.get('customer_email')
        
        if request.args.get('order_number'):
            filters['order_number'] = request.args.get('order_number')
        
        if request.args.get('date_from'):
            try:
                from datetime import datetime
                filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
            except ValueError:
                pass
        
        if request.args.get('date_to'):
            try:
                from datetime import datetime
                filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
            except ValueError:
                pass
        
        if request.args.get('min_amount'):
            try:
                filters['min_amount'] = float(request.args.get('min_amount'))
            except ValueError:
                pass
        
        if request.args.get('max_amount'):
            try:
                filters['max_amount'] = float(request.args.get('max_amount'))
            except ValueError:
                pass
        
        result = OrderService.get_orders_list(
            store_id=store_id,
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"List orders route error: {str(e)}")
        return jsonify({
            'error': 'Order listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('', methods=['POST'])
@require_auth
@require_store_access
def create_order():
    """Create new order."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['customer_email', 'customer_name', 'billing_address', 'order_items']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Add source as admin
        data['source'] = 'admin'
        
        result = OrderService.create_order(store_id, data)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 201
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Create order route error: {str(e)}")
        return jsonify({
            'error': 'Order creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>', methods=['GET'])
@require_auth
@require_store_access
def get_order(order_id):
    """Get specific order."""
    try:
        store_id = get_current_store_id()
        
        result = OrderService.get_order(store_id, order_id=order_id)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 404
        
    except Exception as e:
        logging.error(f"Get order route error: {str(e)}")
        return jsonify({
            'error': 'Order retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/by-number/<order_number>', methods=['GET'])
@require_auth
@require_store_access
def get_order_by_number(order_number):
    """Get order by order number."""
    try:
        store_id = get_current_store_id()
        
        result = OrderService.get_order(store_id, order_number=order_number)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 404
        
    except Exception as e:
        logging.error(f"Get order by number route error: {str(e)}")
        return jsonify({
            'error': 'Order retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@require_auth
@require_store_access
def update_order_status(order_id):
    """Update order status."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('status'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Status is required'
            }), 400
        
        result = OrderService.update_order_status(
            store_id=store_id,
            order_id=order_id,
            new_status=data['status'],
            notes=data.get('notes')
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Update order status route error: {str(e)}")
        return jsonify({
            'error': 'Order status update failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/payment-status', methods=['PUT'])
@require_auth
@require_store_access
def update_payment_status(order_id):
    """Update order payment status."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('payment_status'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Payment status is required'
            }), 400
        
        result = OrderService.update_payment_status(
            store_id=store_id,
            order_id=order_id,
            payment_status=data['payment_status'],
            transaction_id=data.get('transaction_id')
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Update payment status route error: {str(e)}")
        return jsonify({
            'error': 'Payment status update failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/tracking', methods=['POST'])
@require_auth
@require_store_access
def add_tracking_info(order_id):
    """Add tracking information to order."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('tracking_number'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Tracking number is required'
            }), 400
        
        result = OrderService.add_tracking_info(
            store_id=store_id,
            order_id=order_id,
            tracking_number=data['tracking_number'],
            tracking_url=data.get('tracking_url'),
            shipping_partner=data.get('shipping_partner')
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Add tracking info route error: {str(e)}")
        return jsonify({
            'error': 'Tracking info addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@require_auth
@require_store_access
def cancel_order(order_id):
    """Cancel order."""
    try:
        data = request.get_json() or {}
        store_id = get_current_store_id()
        
        result = OrderService.cancel_order(
            store_id=store_id,
            order_id=order_id,
            reason=data.get('reason'),
            restore_inventory=data.get('restore_inventory', True)
        )
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Cancel order route error: {str(e)}")
        return jsonify({
            'error': 'Order cancellation failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/analytics', methods=['GET'])
@require_auth
@require_store_access
def get_order_analytics():
    """Get order analytics."""
    try:
        store_id = get_current_store_id()
        
        # Get date range from query parameters
        date_range = None
        if request.args.get('start_date') or request.args.get('end_date'):
            from datetime import datetime
            date_range = {}
            
            if request.args.get('start_date'):
                try:
                    date_range['start_date'] = datetime.fromisoformat(request.args.get('start_date'))
                except ValueError:
                    pass
            
            if request.args.get('end_date'):
                try:
                    date_range['end_date'] = datetime.fromisoformat(request.args.get('end_date'))
                except ValueError:
                    pass
        
        result = OrderService.get_order_analytics(store_id, date_range)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
    except Exception as e:
        logging.error(f"Get order analytics route error: {str(e)}")
        return jsonify({
            'error': 'Order analytics retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/pending', methods=['GET'])
@require_auth
@require_store_access
def get_pending_orders():
    """Get pending orders that need attention."""
    try:
        store_id = get_current_store_id()
        
        orders = Order.get_pending_orders(store_id)
        
        return jsonify({
            'message': 'Pending orders retrieved successfully',
            'data': {
                'orders': [order.to_dict() for order in orders],
                'count': len(orders)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get pending orders route error: {str(e)}")
        return jsonify({
            'error': 'Pending orders retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/recent', methods=['GET'])
@require_auth
@require_store_access
def get_recent_orders():
    """Get recent orders."""
    try:
        store_id = get_current_store_id()
        
        days = int(request.args.get('days', 7))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        orders = Order.get_recent_orders(store_id, days, limit)
        
        return jsonify({
            'message': 'Recent orders retrieved successfully',
            'data': {
                'orders': [order.to_dict() for order in orders],
                'count': len(orders)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get recent orders route error: {str(e)}")
        return jsonify({
            'error': 'Recent orders retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/by-status/<status>', methods=['GET'])
@require_auth
@require_store_access
def get_orders_by_status(status):
    """Get orders by specific status."""
    try:
        store_id = get_current_store_id()
        limit = min(int(request.args.get('limit', 50)), 100)
        
        orders = Order.get_orders_by_status(store_id, status, limit)
        
        return jsonify({
            'message': f'Orders with status "{status}" retrieved successfully',
            'data': {
                'orders': [order.to_dict() for order in orders],
                'count': len(orders),
                'status': status
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get orders by status route error: {str(e)}")
        return jsonify({
            'error': 'Orders retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/notes', methods=['PUT'])
@require_auth
@require_store_access
def update_order_notes(order_id):
    """Update order admin notes."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        order = Order.query.filter_by(
            id=order_id,
            store_id=store_id
        ).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found',
                'message': 'The requested order was not found'
            }), 404
        
        notes = data.get('notes', '')
        order.admin_notes = notes
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order notes updated successfully',
            'data': {
                'order': order.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update order notes route error: {str(e)}")
        return jsonify({
            'error': 'Order notes update failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/tags', methods=['POST'])
@require_auth
@require_store_access
def add_order_tag(order_id):
    """Add tag to order."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('tag'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Tag is required'
            }), 400
        
        order = Order.query.filter_by(
            id=order_id,
            store_id=store_id
        ).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found',
                'message': 'The requested order was not found'
            }), 404
        
        order.add_tag(data['tag'])
        db.session.commit()
        
        return jsonify({
            'message': 'Tag added successfully',
            'data': {
                'order': order.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add order tag route error: {str(e)}")
        return jsonify({
            'error': 'Tag addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/<int:order_id>/tags', methods=['DELETE'])
@require_auth
@require_store_access
def remove_order_tag(order_id):
    """Remove tag from order."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('tag'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Tag is required'
            }), 400
        
        order = Order.query.filter_by(
            id=order_id,
            store_id=store_id
        ).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found',
                'message': 'The requested order was not found'
            }), 404
        
        order.remove_tag(data['tag'])
        db.session.commit()
        
        return jsonify({
            'message': 'Tag removed successfully',
            'data': {
                'order': order.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Remove order tag route error: {str(e)}")
        return jsonify({
            'error': 'Tag removal failed',
            'message': 'An unexpected error occurred'
        }), 500

@orders_bp.route('/export', methods=['GET'])
@require_auth
@require_store_access
def export_orders():
    """Export orders to CSV."""
    try:
        store_id = get_current_store_id()
        
        # Get filters (same as list_orders)
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('payment_status'):
            filters['payment_status'] = request.args.get('payment_status')
        
        if request.args.get('date_from'):
            try:
                from datetime import datetime
                filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
            except ValueError:
                pass
        
        if request.args.get('date_to'):
            try:
                from datetime import datetime
                filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
            except ValueError:
                pass
        
        # Get all orders (no pagination for export)
        result = OrderService.get_orders_list(
            store_id=store_id,
            filters=filters,
            page=1,
            per_page=10000  # Large number to get all orders
        )
        
        if not result['success']:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
        
        orders = result['data']['orders']
        
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order Number', 'Customer Name', 'Customer Email', 'Status',
            'Payment Status', 'Total Amount', 'Currency', 'Created At',
            'Items Count', 'Shipping Method'
        ])
        
        # Write data
        for order in orders:
            writer.writerow([
                order['order_number'],
                order['customer_name'],
                order['customer_email'],
                order['status'],
                order['payment_status'],
                order['total_amount'],
                order['currency'],
                order['created_at'],
                len(order['order_items']),
                order.get('shipping_method', '')
            ])
        
        # Create response
        from flask import Response
        
        csv_content = output.getvalue()
        output.close()
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=orders_export.csv'
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Export orders route error: {str(e)}")
        return jsonify({
            'error': 'Orders export failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@orders_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@orders_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested order was not found'
    }), 404 