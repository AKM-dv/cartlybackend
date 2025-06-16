from flask import Blueprint, request, jsonify
from app.services.store_service import StoreService
from app.middleware import (
    require_auth, 
    require_role,
    require_store_access,
    require_store_owner,
    get_current_store_id,
    get_current_user,
    validate_store_limits
)
from app.utils.validators import validate_required_fields, validate_email
import logging

store_bp = Blueprint('store', __name__, url_prefix='/api/stores')

@store_bp.route('', methods=['POST'])
@require_role('super_admin')
def create_store():
    """Create new store (Super admin only)."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['store_name', 'domain', 'subdomain', 'owner_email', 'owner_name']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Validate email format
        if not validate_email(data['owner_email']):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid owner email address'
            }), 400
        
        # Separate store and owner data
        store_data = {
            'store_name': data['store_name'],
            'store_description': data.get('store_description'),
            'domain': data['domain'],
            'subdomain': data['subdomain'],
            'custom_domain': data.get('custom_domain'),
            'business_name': data.get('business_name'),
            'business_type': data.get('business_type', 'retail'),
            'plan_type': data.get('plan_type', 'basic'),
            'address_line_1': data.get('address_line_1'),
            'city': data.get('city'),
            'state': data.get('state'),
            'postal_code': data.get('postal_code'),
            'country': data.get('country', 'India')
        }
        
        owner_data = {
            'owner_name': data['owner_name'],
            'owner_email': data['owner_email'],
            'owner_phone': data.get('owner_phone'),
            'first_name': data.get('first_name', data['owner_name'].split()[0]),
            'last_name': data.get('last_name', data['owner_name'].split()[-1]),
            'password': data.get('password')  # Optional - can be set later
        }
        
        result = StoreService.create_store(store_data, owner_data)
        
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
        logging.error(f"Create store route error: {str(e)}")
        return jsonify({
            'error': 'Store creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('', methods=['GET'])
@require_role('super_admin')
def list_stores():
    """List all stores (Super admin only)."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search')
        status = request.args.get('status')
        
        result = StoreService.list_stores(
            page=page,
            per_page=per_page,
            search=search,
            status=status
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
        logging.error(f"List stores route error: {str(e)}")
        return jsonify({
            'error': 'Store listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current', methods=['GET'])
@require_auth
@require_store_access
def get_current_store():
    """Get current store information."""
    try:
        store_id = get_current_store_id()
        
        result = StoreService.get_store(store_id)
        
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
        logging.error(f"Get current store route error: {str(e)}")
        return jsonify({
            'error': 'Store retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>', methods=['GET'])
@require_auth
def get_store(store_id):
    """Get specific store information."""
    try:
        current_user = get_current_user()
        
        # Check access permissions
        if not current_user.is_super_admin() and not current_user.can_access_store(store_id):
            return jsonify({
                'error': 'Access denied',
                'message': 'You do not have access to this store'
            }), 403
        
        result = StoreService.get_store(store_id)
        
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
        logging.error(f"Get store route error: {str(e)}")
        return jsonify({
            'error': 'Store retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_current_store():
    """Update current store information."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        result = StoreService.update_store(store_id, data)
        
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
        logging.error(f"Update store route error: {str(e)}")
        return jsonify({
            'error': 'Store update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>', methods=['PUT'])
@require_role('super_admin')
def update_store(store_id):
    """Update specific store (Super admin only)."""
    try:
        data = request.get_json()
        
        result = StoreService.update_store(store_id, data)
        
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
        logging.error(f"Update store route error: {str(e)}")
        return jsonify({
            'error': 'Store update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>', methods=['DELETE'])
@require_role('super_admin')
def delete_store(store_id):
    """Delete store (Super admin only)."""
    try:
        result = StoreService.delete_store(store_id)
        
        if result['success']:
            return jsonify({
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
            
    except Exception as e:
        logging.error(f"Delete store route error: {str(e)}")
        return jsonify({
            'error': 'Store deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current/settings', methods=['GET'])
@require_auth
@require_store_access
def get_store_settings():
    """Get current store settings."""
    try:
        store_id = get_current_store_id()
        
        result = StoreService.get_store_settings(store_id)
        
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
        logging.error(f"Get store settings route error: {str(e)}")
        return jsonify({
            'error': 'Store settings retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current/settings', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_store_settings():
    """Update current store settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        result = StoreService.update_store_settings(store_id, data)
        
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
        logging.error(f"Update store settings route error: {str(e)}")
        return jsonify({
            'error': 'Store settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current/stats', methods=['GET'])
@require_auth
@require_store_access
def get_store_stats():
    """Get current store statistics."""
    try:
        store_id = get_current_store_id()
        
        result = StoreService.get_store_stats(store_id)
        
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
        logging.error(f"Get store stats route error: {str(e)}")
        return jsonify({
            'error': 'Store statistics retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current/maintenance', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def toggle_maintenance_mode():
    """Toggle store maintenance mode."""
    try:
        data = request.get_json() or {}
        store_id = get_current_store_id()
        
        enabled = data.get('enabled')
        message = data.get('message')
        
        result = StoreService.toggle_maintenance_mode(
            store_id=store_id,
            enabled=enabled,
            message=message
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
        logging.error(f"Toggle maintenance route error: {str(e)}")
        return jsonify({
            'error': 'Maintenance mode toggle failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>/plan', methods=['PUT'])
@require_role('super_admin')
def change_store_plan(store_id):
    """Change store subscription plan (Super admin only)."""
    try:
        data = request.get_json()
        
        if not data.get('plan'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Plan type is required'
            }), 400
        
        result = StoreService.change_store_plan(store_id, data['plan'])
        
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
        logging.error(f"Change store plan route error: {str(e)}")
        return jsonify({
            'error': 'Plan change failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>/suspend', methods=['POST'])
@require_role('super_admin')
def suspend_store(store_id):
    """Suspend store (Super admin only)."""
    try:
        data = request.get_json() or {}
        reason = data.get('reason')
        
        result = StoreService.suspend_store(store_id, reason)
        
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
        logging.error(f"Suspend store route error: {str(e)}")
        return jsonify({
            'error': 'Store suspension failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/<store_id>/reactivate', methods=['POST'])
@require_role('super_admin')
def reactivate_store(store_id):
    """Reactivate suspended store (Super admin only)."""
    try:
        result = StoreService.reactivate_store(store_id)
        
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
        logging.error(f"Reactivate store route error: {str(e)}")
        return jsonify({
            'error': 'Store reactivation failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/validate-domain', methods=['POST'])
@require_auth
def validate_domain():
    """Validate if domain is available."""
    try:
        data = request.get_json()
        
        if not data.get('domain'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Domain is required'
            }), 400
        
        store_id = data.get('store_id')  # For updating existing store
        
        result = StoreService.validate_domain(data['domain'], store_id)
        
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
        logging.error(f"Validate domain route error: {str(e)}")
        return jsonify({
            'error': 'Domain validation failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_bp.route('/current/health', methods=['GET'])
@require_auth
@require_store_access
def get_store_health():
    """Get current store health status."""
    try:
        store_id = get_current_store_id()
        
        result = StoreService.get_store_health(store_id)
        
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
        logging.error(f"Get store health route error: {str(e)}")
        return jsonify({
            'error': 'Store health check failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@store_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@store_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@store_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested store was not found'
    }), 404