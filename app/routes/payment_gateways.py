"""
Payment gateway routes for payment method management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.payment_gateway import PaymentGateway
from app.middleware import (
    require_auth,
    require_store_access,
    require_store_owner,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

payment_gateways_bp = Blueprint('payment_gateways', __name__, url_prefix='/api/payment-gateways')

@payment_gateways_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_payment_gateways():
    """List all payment gateways for store."""
    try:
        store_id = get_current_store_id()
        
        gateways = PaymentGateway.query.filter_by(
            store_id=store_id
        ).order_by(PaymentGateway.display_order).all()
        
        return jsonify({
            'message': 'Payment gateways retrieved successfully',
            'data': {
                'gateways': [gateway.to_dict() for gateway in gateways]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List payment gateways route error: {str(e)}")
        return jsonify({
            'error': 'Payment gateways retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def create_payment_gateway():
    """Create new payment gateway."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['gateway_name', 'gateway_type']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Check if gateway already exists
        existing = PaymentGateway.query.filter_by(
            store_id=store_id,
            gateway_type=data['gateway_type']
        ).first()
        
        if existing:
            return jsonify({
                'error': 'Gateway exists',
                'message': f'{data["gateway_type"]} gateway already configured'
            }), 400
        
        # Create gateway
        gateway = PaymentGateway(
            store_id=store_id,
            gateway_name=data['gateway_name'],
            gateway_type=data['gateway_type'],
            is_active=data.get('is_active', True),
            is_sandbox=data.get('is_sandbox', True),
            display_order=data.get('display_order', 0),
            transaction_fee_type=data.get('transaction_fee_type', 'percentage'),
            transaction_fee_value=data.get('transaction_fee_value', 0),
            min_amount=data.get('min_amount'),
            max_amount=data.get('max_amount'),
            description=data.get('description'),
            instructions=data.get('instructions')
        )
        
        # Handle configuration
        if data.get('configuration'):
            gateway.configuration = data['configuration']
        
        # Handle supported currencies
        if data.get('supported_currencies'):
            gateway.supported_currencies = data['supported_currencies']
        
        # Handle supported countries
        if data.get('supported_countries'):
            gateway.supported_countries = data['supported_countries']
        
        db.session.add(gateway)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment gateway created successfully',
            'data': {
                'gateway': gateway.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create payment gateway route error: {str(e)}")
        return jsonify({
            'error': 'Payment gateway creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/<int:gateway_id>', methods=['GET'])
@require_auth
@require_store_access
def get_payment_gateway(gateway_id):
    """Get specific payment gateway."""
    try:
        store_id = get_current_store_id()
        
        gateway = PaymentGateway.query.filter_by(
            id=gateway_id,
            store_id=store_id
        ).first()
        
        if not gateway:
            return jsonify({
                'error': 'Gateway not found',
                'message': 'The requested payment gateway was not found'
            }), 404
        
        return jsonify({
            'message': 'Payment gateway retrieved successfully',
            'data': {
                'gateway': gateway.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get payment gateway route error: {str(e)}")
        return jsonify({
            'error': 'Payment gateway retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/<int:gateway_id>', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_payment_gateway(gateway_id):
    """Update payment gateway."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        gateway = PaymentGateway.query.filter_by(
            id=gateway_id,
            store_id=store_id
        ).first()
        
        if not gateway:
            return jsonify({
                'error': 'Gateway not found',
                'message': 'The requested payment gateway was not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'gateway_name', 'is_active', 'is_sandbox', 'display_order',
            'transaction_fee_type', 'transaction_fee_value', 'min_amount',
            'max_amount', 'description', 'instructions', 'configuration',
            'supported_currencies', 'supported_countries'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(gateway, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment gateway updated successfully',
            'data': {
                'gateway': gateway.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update payment gateway route error: {str(e)}")
        return jsonify({
            'error': 'Payment gateway update failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/<int:gateway_id>', methods=['DELETE'])
@require_auth
@require_store_access
@require_store_owner
def delete_payment_gateway(gateway_id):
    """Delete payment gateway."""
    try:
        store_id = get_current_store_id()
        
        gateway = PaymentGateway.query.filter_by(
            id=gateway_id,
            store_id=store_id
        ).first()
        
        if not gateway:
            return jsonify({
                'error': 'Gateway not found',
                'message': 'The requested payment gateway was not found'
            }), 404
        
        db.session.delete(gateway)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment gateway deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete payment gateway route error: {str(e)}")
        return jsonify({
            'error': 'Payment gateway deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/<int:gateway_id>/toggle', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def toggle_gateway_status(gateway_id):
    """Toggle payment gateway active status."""
    try:
        store_id = get_current_store_id()
        
        gateway = PaymentGateway.query.filter_by(
            id=gateway_id,
            store_id=store_id
        ).first()
        
        if not gateway:
            return jsonify({
                'error': 'Gateway not found',
                'message': 'The requested payment gateway was not found'
            }), 404
        
        gateway.is_active = not gateway.is_active
        db.session.commit()
        
        status = 'activated' if gateway.is_active else 'deactivated'
        
        return jsonify({
            'message': f'Payment gateway {status} successfully',
            'data': {
                'gateway': gateway.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Toggle gateway status route error: {str(e)}")
        return jsonify({
            'error': 'Gateway status toggle failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/active', methods=['GET'])
@require_auth
@require_store_access
def get_active_gateways():
    """Get active payment gateways."""
    try:
        store_id = get_current_store_id()
        
        gateways = PaymentGateway.get_active_gateways(store_id)
        
        return jsonify({
            'message': 'Active payment gateways retrieved successfully',
            'data': {
                'gateways': [gateway.to_dict() for gateway in gateways]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get active gateways route error: {str(e)}")
        return jsonify({
            'error': 'Active gateways retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/test-connection/<int:gateway_id>', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def test_gateway_connection(gateway_id):
    """Test payment gateway connection."""
    try:
        store_id = get_current_store_id()
        
        gateway = PaymentGateway.query.filter_by(
            id=gateway_id,
            store_id=store_id
        ).first()
        
        if not gateway:
            return jsonify({
                'error': 'Gateway not found',
                'message': 'The requested payment gateway was not found'
            }), 404
        
        # Test connection
        test_result = gateway.test_connection()
        
        return jsonify({
            'message': 'Gateway connection tested successfully',
            'data': {
                'test_result': test_result
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Test gateway connection route error: {str(e)}")
        return jsonify({
            'error': 'Gateway connection test failed',
            'message': 'An unexpected error occurred'
        }), 500

@payment_gateways_bp.route('/reorder', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def reorder_gateways():
    """Reorder payment gateways."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if 'gateway_orders' not in data:
            return jsonify({
                'error': 'Validation failed',
                'message': 'gateway_orders is required'
            }), 400
        
        gateway_orders = data['gateway_orders']
        
        # Update display order for each gateway
        for gateway_id, display_order in gateway_orders.items():
            gateway = PaymentGateway.query.filter_by(
                id=int(gateway_id),
                store_id=store_id
            ).first()
            
            if gateway:
                gateway.display_order = display_order
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment gateways reordered successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Reorder gateways route error: {str(e)}")
        return jsonify({
            'error': 'Gateway reordering failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@payment_gateways_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@payment_gateways_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested payment gateway was not found'
    }), 404