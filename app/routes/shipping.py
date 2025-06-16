"""
Shipping routes for shipping partners and methods management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.shipping_partner import ShippingPartner
from app.services.shipping_service import ShippingService
from app.middleware import (
    require_auth,
    require_store_access,
    require_store_owner,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

shipping_bp = Blueprint('shipping', __name__, url_prefix='/api/shipping')

@shipping_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_shipping_partners():
    """List all shipping partners for store."""
    try:
        store_id = get_current_store_id()
        
        partners = ShippingPartner.query.filter_by(
            store_id=store_id
        ).order_by(ShippingPartner.priority).all()
        
        return jsonify({
            'message': 'Shipping partners retrieved successfully',
            'data': {
                'partners': [partner.to_dict() for partner in partners]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List shipping partners route error: {str(e)}")
        return jsonify({
            'error': 'Shipping partners retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def create_shipping_partner():
    """Create new shipping partner."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['partner_name', 'partner_type']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Create shipping partner
        partner = ShippingPartner(
            store_id=store_id,
            partner_name=data['partner_name'],
            display_name=data.get('display_name', data['partner_name']),
            partner_type=data['partner_type'],
            is_active=data.get('is_active', True),
            is_test_mode=data.get('is_test_mode', True),
            priority=data.get('priority', 0),
            api_key=data.get('api_key'),
            api_secret=data.get('api_secret'),
            api_token=data.get('api_token'),
            merchant_id=data.get('merchant_id'),
            supports_cod=data.get('supports_cod', True),
            supports_prepaid=data.get('supports_prepaid', True),
            supports_international=data.get('supports_international', False),
            supports_reverse_pickup=data.get('supports_reverse_pickup', True),
            supports_tracking=data.get('supports_tracking', True),
            same_day_delivery=data.get('same_day_delivery', False),
            next_day_delivery=data.get('next_day_delivery', False),
            express_delivery=data.get('express_delivery', True),
            standard_delivery=data.get('standard_delivery', True),
            base_rate=data.get('base_rate', 0),
            per_kg_rate=data.get('per_kg_rate', 0),
            per_km_rate=data.get('per_km_rate', 0),
            fuel_surcharge=data.get('fuel_surcharge', 0),
            min_weight=data.get('min_weight', 0.1),
            max_weight=data.get('max_weight', 50),
            max_length=data.get('max_length', 100),
            max_width=data.get('max_width', 100),
            max_height=data.get('max_height', 100),
            standard_delivery_days=data.get('standard_delivery_days', 3),
            express_delivery_days=data.get('express_delivery_days', 1)
        )
        
        # Handle configuration
        if data.get('config_data'):
            partner.config_data = data['config_data']
        
        # Handle service areas
        if data.get('serviceable_pincodes'):
            partner.serviceable_pincodes = data['serviceable_pincodes']
        
        if data.get('serviceable_states'):
            partner.serviceable_states = data['serviceable_states']
        
        if data.get('non_serviceable_areas'):
            partner.non_serviceable_areas = data['non_serviceable_areas']
        
        db.session.add(partner)
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping partner created successfully',
            'data': {
                'partner': partner.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create shipping partner route error: {str(e)}")
        return jsonify({
            'error': 'Shipping partner creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/<int:partner_id>', methods=['GET'])
@require_auth
@require_store_access
def get_shipping_partner(partner_id):
    """Get specific shipping partner."""
    try:
        store_id = get_current_store_id()
        
        partner = ShippingPartner.query.filter_by(
            id=partner_id,
            store_id=store_id
        ).first()
        
        if not partner:
            return jsonify({
                'error': 'Partner not found',
                'message': 'The requested shipping partner was not found'
            }), 404
        
        return jsonify({
            'message': 'Shipping partner retrieved successfully',
            'data': {
                'partner': partner.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get shipping partner route error: {str(e)}")
        return jsonify({
            'error': 'Shipping partner retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/<int:partner_id>', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_shipping_partner(partner_id):
    """Update shipping partner."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        partner = ShippingPartner.query.filter_by(
            id=partner_id,
            store_id=store_id
        ).first()
        
        if not partner:
            return jsonify({
                'error': 'Partner not found',
                'message': 'The requested shipping partner was not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'display_name', 'is_active', 'is_test_mode', 'priority',
            'api_key', 'api_secret', 'api_token', 'merchant_id',
            'supports_cod', 'supports_prepaid', 'supports_international',
            'supports_reverse_pickup', 'supports_tracking', 'same_day_delivery',
            'next_day_delivery', 'express_delivery', 'standard_delivery',
            'base_rate', 'per_kg_rate', 'per_km_rate', 'fuel_surcharge',
            'min_weight', 'max_weight', 'max_length', 'max_width', 'max_height',
            'standard_delivery_days', 'express_delivery_days', 'config_data',
            'serviceable_pincodes', 'serviceable_states', 'non_serviceable_areas'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(partner, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping partner updated successfully',
            'data': {
                'partner': partner.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update shipping partner route error: {str(e)}")
        return jsonify({
            'error': 'Shipping partner update failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/<int:partner_id>', methods=['DELETE'])
@require_auth
@require_store_access
@require_store_owner
def delete_shipping_partner(partner_id):
    """Delete shipping partner."""
    try:
        store_id = get_current_store_id()
        
        partner = ShippingPartner.query.filter_by(
            id=partner_id,
            store_id=store_id
        ).first()
        
        if not partner:
            return jsonify({
                'error': 'Partner not found',
                'message': 'The requested shipping partner was not found'
            }), 404
        
        db.session.delete(partner)
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping partner deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete shipping partner route error: {str(e)}")
        return jsonify({
            'error': 'Shipping partner deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/<int:partner_id>/toggle', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def toggle_partner_status(partner_id):
    """Toggle shipping partner active status."""
    try:
        store_id = get_current_store_id()
        
        partner = ShippingPartner.query.filter_by(
            id=partner_id,
            store_id=store_id
        ).first()
        
        if not partner:
            return jsonify({
                'error': 'Partner not found',
                'message': 'The requested shipping partner was not found'
            }), 404
        
        partner.is_active = not partner.is_active
        db.session.commit()
        
        status = 'activated' if partner.is_active else 'deactivated'
        
        return jsonify({
            'message': f'Shipping partner {status} successfully',
            'data': {
                'partner': partner.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Toggle partner status route error: {str(e)}")
        return jsonify({
            'error': 'Partner status toggle failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/active', methods=['GET'])
@require_auth
@require_store_access
def get_active_partners():
    """Get active shipping partners."""
    try:
        store_id = get_current_store_id()
        
        partners = ShippingPartner.get_active_partners(store_id)
        
        return jsonify({
            'message': 'Active shipping partners retrieved successfully',
            'data': {
                'partners': [partner.to_dict() for partner in partners]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get active partners route error: {str(e)}")
        return jsonify({
            'error': 'Active partners retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/calculate-rates', methods=['POST'])
@require_auth
@require_store_access
def calculate_shipping_rates():
    """Calculate shipping rates from all partners."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['weight', 'origin_pincode', 'destination_pincode']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = ShippingService.calculate_shipping_rates(
            store_id=store_id,
            weight=data['weight'],
            dimensions=data.get('dimensions'),
            origin_pincode=data['origin_pincode'],
            destination_pincode=data['destination_pincode'],
            order_value=data.get('order_value', 0)
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
        logging.error(f"Calculate shipping rates route error: {str(e)}")
        return jsonify({
            'error': 'Shipping rate calculation failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/create-shipment', methods=['POST'])
@require_auth
@require_store_access
def create_shipment():
    """Create shipment for order."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['order_id', 'partner_id']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = ShippingService.create_shipment(
            store_id=store_id,
            order_id=data['order_id'],
            partner_id=data['partner_id'],
            shipment_data=data.get('shipment_data', {})
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
        logging.error(f"Create shipment route error: {str(e)}")
        return jsonify({
            'error': 'Shipment creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/track/<tracking_number>', methods=['GET'])
@require_auth
@require_store_access
def track_shipment(tracking_number):
    """Track shipment status."""
    try:
        store_id = get_current_store_id()
        partner_name = request.args.get('partner_name')
        
        result = ShippingService.track_shipment(
            store_id=store_id,
            tracking_number=tracking_number,
            partner_name=partner_name
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
        logging.error(f"Track shipment route error: {str(e)}")
        return jsonify({
            'error': 'Shipment tracking failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/cancel-shipment', methods=['POST'])
@require_auth
@require_store_access
def cancel_shipment():
    """Cancel shipment."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['order_id']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = ShippingService.cancel_shipment(
            store_id=store_id,
            order_id=data['order_id'],
            reason=data.get('reason')
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
        logging.error(f"Cancel shipment route error: {str(e)}")
        return jsonify({
            'error': 'Shipment cancellation failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/check-serviceability', methods=['POST'])
@require_auth
@require_store_access
def check_serviceability():
    """Check if delivery is available to destination."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['destination_pincode']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = ShippingService.check_serviceability(
            store_id=store_id,
            destination_pincode=data['destination_pincode'],
            weight=data.get('weight')
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
        logging.error(f"Check serviceability route error: {str(e)}")
        return jsonify({
            'error': 'Serviceability check failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/delivery-estimates', methods=['POST'])
@require_auth
@require_store_access
def get_delivery_estimates():
    """Get delivery time estimates for destination."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['destination_pincode']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = ShippingService.get_delivery_estimates(
            store_id=store_id,
            destination_pincode=data['destination_pincode'],
            service_type=data.get('service_type', 'standard')
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
        logging.error(f"Get delivery estimates route error: {str(e)}")
        return jsonify({
            'error': 'Delivery estimates retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/serviceable-areas', methods=['GET'])
@require_auth
@require_store_access
def get_serviceable_areas():
    """Get serviceable areas for shipping partners."""
    try:
        store_id = get_current_store_id()
        partner_name = request.args.get('partner_name')
        
        result = ShippingService.get_serviceable_areas(
            store_id=store_id,
            partner_name=partner_name
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
        logging.error(f"Get serviceable areas route error: {str(e)}")
        return jsonify({
            'error': 'Serviceable areas retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/test-connection/<int:partner_id>', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def test_partner_connection(partner_id):
    """Test shipping partner API connection."""
    try:
        store_id = get_current_store_id()
        
        partner = ShippingPartner.query.filter_by(
            id=partner_id,
            store_id=store_id
        ).first()
        
        if not partner:
            return jsonify({
                'error': 'Partner not found',
                'message': 'The requested shipping partner was not found'
            }), 404
        
        # Test connection
        test_result = partner.test_connection()
        
        return jsonify({
            'message': 'Partner connection tested successfully',
            'data': {
                'test_result': test_result
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Test partner connection route error: {str(e)}")
        return jsonify({
            'error': 'Partner connection test failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/reorder', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def reorder_partners():
    """Reorder shipping partners."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if 'partner_orders' not in data:
            return jsonify({
                'error': 'Validation failed',
                'message': 'partner_orders is required'
            }), 400
        
        partner_orders = data['partner_orders']
        
        # Update priority for each partner
        for partner_id, priority in partner_orders.items():
            partner = ShippingPartner.query.filter_by(
                id=int(partner_id),
                store_id=store_id
            ).first()
            
            if partner:
                partner.priority = priority
        
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping partners reordered successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Reorder partners route error: {str(e)}")
        return jsonify({
            'error': 'Partner reordering failed',
            'message': 'An unexpected error occurred'
        }), 500

@shipping_bp.route('/zones', methods=['GET'])
@require_auth
@require_store_access
def get_shipping_zones():
    """Get shipping zones for store."""
    try:
        store_id = get_current_store_id()
        
        # Get unique service areas from all partners
        partners = ShippingPartner.query.filter_by(
            store_id=store_id,
            is_active=True
        ).all()
        
        zones = set()
        for partner in partners:
            if partner.serviceable_states:
                zones.update(partner.serviceable_states)
        
        return jsonify({
            'message': 'Shipping zones retrieved successfully',
            'data': {
                'zones': list(zones)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get shipping zones route error: {str(e)}")
        return jsonify({
            'error': 'Shipping zones retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@shipping_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@shipping_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested shipping partner was not found'
    }), 404