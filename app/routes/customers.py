from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.customer import Customer
from app.models.order import Order
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id
)
from app.utils.validators import validate_required_fields, validate_email
import logging

customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')

@customers_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_customers():
    """List customers with pagination and filters."""
    try:
        store_id = get_current_store_id()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search')
        customer_group = request.args.get('customer_group')
        is_active = request.args.get('is_active')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Customer.query.filter_by(store_id=store_id)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Customer.first_name.like(search_term),
                    Customer.last_name.like(search_term),
                    Customer.email.like(search_term),
                    Customer.phone.like(search_term)
                )
            )
        
        if customer_group:
            query = query.filter_by(customer_group=customer_group)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        # Apply sorting
        if hasattr(Customer, sort_by):
            order_column = getattr(Customer, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        customers = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'message': 'Customers retrieved successfully',
            'data': {
                'customers': [customer.to_dict() for customer in customers],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List customers route error: {str(e)}")
        return jsonify({
            'error': 'Customer listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('', methods=['POST'])
@require_auth
@require_store_access
def create_customer():
    """Create new customer."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['email', 'first_name', 'last_name']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Check if email already exists
        existing_customer = Customer.query.filter_by(
            store_id=store_id,
            email=data['email'].lower()
        ).first()
        
        if existing_customer:
            return jsonify({
                'error': 'Email already exists',
                'message': 'A customer with this email already exists'
            }), 400
        
        # Create customer
        customer = Customer(
            store_id=store_id,
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            customer_group=data.get('customer_group', 'regular'),
            accepts_marketing=data.get('accepts_marketing', True),
            preferred_language=data.get('preferred_language', 'en'),
            preferred_currency=data.get('preferred_currency', 'USD'),
            timezone=data.get('timezone', 'UTC'),
            registration_source=data.get('registration_source', 'admin'),
            utm_source=data.get('utm_source'),
            utm_medium=data.get('utm_medium'),
            utm_campaign=data.get('utm_campaign')
        )
        
        # Set password if provided
        if data.get('password'):
            customer.set_password(data['password'])
        
        # Handle custom fields
        if 'custom_fields' in data:
            customer.custom_fields = data['custom_fields']
        
        # Handle admin notes
        if 'admin_notes' in data:
            customer.admin_notes = data['admin_notes']
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'message': 'Customer created successfully',
            'data': {
                'customer': customer.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create customer route error: {str(e)}")
        return jsonify({
            'error': 'Customer creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['GET'])
@require_auth
@require_store_access
def get_customer(customer_id):
    """Get specific customer."""
    try:
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        # Get customer's orders
        orders = Order.get_customer_orders(store_id, customer_id, limit=10)
        
        customer_data = customer.to_dict()
        customer_data['recent_orders'] = [order.to_dict() for order in orders]
        
        return jsonify({
            'message': 'Customer retrieved successfully',
            'data': {
                'customer': customer_data
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get customer route error: {str(e)}")
        return jsonify({
            'error': 'Customer retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_customer(customer_id):
    """Update customer."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        # Validate email if being changed
        if 'email' in data and data['email'] != customer.email:
            if not validate_email(data['email']):
                return jsonify({
                    'error': 'Invalid email',
                    'message': 'Please provide a valid email address'
                }), 400
            
            # Check if new email already exists
            existing_customer = Customer.query.filter_by(
                store_id=store_id,
                email=data['email'].lower()
            ).first()
            
            if existing_customer:
                return jsonify({
                    'error': 'Email already exists',
                    'message': 'A customer with this email already exists'
                }), 400
        
        # Update allowed fields
        allowed_fields = [
            'email', 'first_name', 'last_name', 'phone', 'date_of_birth',
            'gender', 'is_active', 'accepts_marketing', 'customer_group',
            'preferred_language', 'preferred_currency', 'timezone',
            'custom_fields', 'admin_notes'
        ]
        
        for field in allowed_fields:
            if field in data:
                if field == 'email':
                    setattr(customer, field, data[field].lower())
                else:
                    setattr(customer, field, data[field])
        
        # Handle password update
        if data.get('password'):
            customer.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Customer updated successfully',
            'data': {
                'customer': customer.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update customer route error: {str(e)}")
        return jsonify({
            'error': 'Customer update failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_customer(customer_id):
    """Delete customer."""
    try:
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        # Check if customer has orders
        order_count = Order.query.filter_by(
            store_id=store_id,
            customer_id=customer_id
        ).count()
        
        if order_count > 0:
            return jsonify({
                'error': 'Cannot delete customer',
                'message': f'Customer has {order_count} orders. Consider deactivating instead.'
            }), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({
            'message': 'Customer deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete customer route error: {str(e)}")
        return jsonify({
            'error': 'Customer deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>/addresses', methods=['GET'])
@require_auth
@require_store_access
def get_customer_addresses(customer_id):
    """Get customer addresses."""
    try:
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        return jsonify({
            'message': 'Customer addresses retrieved successfully',
            'data': {
                'addresses': customer.addresses or []
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get customer addresses route error: {str(e)}")
        return jsonify({
            'error': 'Customer addresses retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>/addresses', methods=['POST'])
@require_auth
@require_store_access
def add_customer_address(customer_id):
    """Add address to customer."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        # Validate required address fields
        required_fields = ['first_name', 'last_name', 'address_line_1', 'city', 'state', 'postal_code', 'country']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        address_id = customer.add_address(data)
        db.session.commit()
        
        return jsonify({
            'message': 'Address added successfully',
            'data': {
                'address_id': address_id,
                'customer': customer.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add customer address route error: {str(e)}")
        return jsonify({
            'error': 'Address addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>/addresses/<int:address_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_customer_address(customer_id, address_id):
    """Update customer address."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        success = customer.update_address(address_id, data)
        
        if not success:
            return jsonify({
                'error': 'Address not found',
                'message': 'The requested address was not found'
            }), 404
        
        db.session.commit()
        
        return jsonify({
            'message': 'Address updated successfully',
            'data': {
                'customer': customer.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update customer address route error: {str(e)}")
        return jsonify({
            'error': 'Address update failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>/addresses/<int:address_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_customer_address(customer_id, address_id):
    """Delete customer address."""
    try:
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        success = customer.remove_address(address_id)
        
        if not success:
            return jsonify({
                'error': 'Address not found',
                'message': 'The requested address was not found'
            }), 404
        
        db.session.commit()
        
        return jsonify({
            'message': 'Address deleted successfully',
            'data': {
                'customer': customer.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete customer address route error: {str(e)}")
        return jsonify({
            'error': 'Address deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/<int:customer_id>/orders', methods=['GET'])
@require_auth
@require_store_access
def get_customer_orders(customer_id):
    """Get customer's orders."""
    try:
        store_id = get_current_store_id()
        
        customer = Customer.query.filter_by(
            id=customer_id,
            store_id=store_id
        ).first()
        
        if not customer:
            return jsonify({
                'error': 'Customer not found',
                'message': 'The requested customer was not found'
            }), 404
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Get orders with pagination
        query = Order.query.filter_by(
            store_id=store_id,
            customer_id=customer_id
        ).order_by(Order.created_at.desc())
        
        total = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'message': 'Customer orders retrieved successfully',
            'data': {
                'customer': customer.to_public_dict(),
                'orders': [order.to_dict() for order in orders],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get customer orders route error: {str(e)}")
        return jsonify({
            'error': 'Customer orders retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/search', methods=['GET'])
@require_auth
@require_store_access
def search_customers():
    """Search customers."""
    try:
        store_id = get_current_store_id()
        search_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not search_term:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Search term is required'
            }), 400
        
        search_pattern = f"%{search_term}%"
        
        customers = Customer.query.filter(
            Customer.store_id == store_id,
            db.or_(
                Customer.first_name.like(search_pattern),
                Customer.last_name.like(search_pattern),
                Customer.email.like(search_pattern),
                Customer.phone.like(search_pattern)
            )
        ).limit(limit).all()
        
        return jsonify({
            'message': 'Customer search completed successfully',
            'data': {
                'customers': [customer.to_dict() for customer in customers],
                'search_term': search_term,
                'count': len(customers)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Search customers route error: {str(e)}")
        return jsonify({
            'error': 'Customer search failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/export', methods=['GET'])
@require_auth
@require_store_access
def export_customers():
    """Export customers to CSV."""
    try:
        store_id = get_current_store_id()
        
        # Get filters
        customer_group = request.args.get('customer_group')
        is_active = request.args.get('is_active')
        
        query = Customer.query.filter_by(store_id=store_id)
        
        if customer_group:
            query = query.filter_by(customer_group=customer_group)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        customers = query.all()
        
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Customer ID', 'First Name', 'Last Name', 'Email', 'Phone',
            'Customer Group', 'Total Orders', 'Total Spent', 'Last Order Date',
            'Registration Date', 'Is Active', 'Accepts Marketing'
        ])
        
        # Write data
        for customer in customers:
            writer.writerow([
                customer.id,
                customer.first_name,
                customer.last_name,
                customer.email,
                customer.phone or '',
                customer.customer_group,
                customer.total_orders,
                float(customer.total_spent) if customer.total_spent else 0,
                customer.last_order_date.isoformat() if customer.last_order_date else '',
                customer.created_at.isoformat(),
                customer.is_active,
                customer.accepts_marketing
            ])
        
        # Create response
        from flask import Response
        
        csv_content = output.getvalue()
        output.close()
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=customers_export.csv'
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Export customers route error: {str(e)}")
        return jsonify({
            'error': 'Customer export failed',
            'message': 'An unexpected error occurred'
        }), 500

@customers_bp.route('/analytics', methods=['GET'])
@require_auth
@require_store_access
def get_customer_analytics():
    """Get customer analytics."""
    try:
        store_id = get_current_store_id()
        
        # Get total customers
        total_customers = Customer.query.filter_by(store_id=store_id).count()
        active_customers = Customer.query.filter_by(store_id=store_id, is_active=True).count()
        
        # Get customers by group
        from sqlalchemy import func
        group_stats = db.session.query(
            Customer.customer_group,
            func.count(Customer.id).label('count')
        ).filter_by(store_id=store_id).group_by(Customer.customer_group).all()
        
        # Get recent registrations (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = Customer.query.filter(
            Customer.store_id == store_id,
            Customer.created_at >= thirty_days_ago
        ).count()
        
        # Get top customers by spending
        top_customers = Customer.query.filter_by(
            store_id=store_id
        ).order_by(Customer.total_spent.desc()).limit(10).all()
        
        analytics_data = {
            'summary': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'inactive_customers': total_customers - active_customers,
                'recent_registrations': recent_registrations
            },
            'by_group': {group: count for group, count in group_stats},
            'top_customers': [
                {
                    'id': customer.id,
                    'name': customer.get_full_name(),
                    'email': customer.email,
                    'total_spent': float(customer.total_spent) if customer.total_spent else 0,
                    'total_orders': customer.total_orders
                }
                for customer in top_customers
            ]
        }
        
        return jsonify({
            'message': 'Customer analytics retrieved successfully',
            'data': analytics_data
        }), 200
        
    except Exception as e:
        logging.error(f"Customer analytics route error: {str(e)}")
        return jsonify({
            'error': 'Customer analytics retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@customers_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@customers_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested customer was not found'
    }), 404