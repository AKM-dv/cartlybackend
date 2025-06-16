"""
Policy routes for legal pages management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.policy import Policy
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

policies_bp = Blueprint('policies', __name__, url_prefix='/api/policies')

@policies_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_policies():
    """List store policies."""
    try:
        store_id = get_current_store_id()
        
        policies = Policy.query.filter_by(
            store_id=store_id
        ).order_by(Policy.display_order).all()
        
        return jsonify({
            'message': 'Policies retrieved successfully',
            'data': {
                'policies': [policy.to_dict() for policy in policies]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List policies route error: {str(e)}")
        return jsonify({
            'error': 'Policy listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('', methods=['POST'])
@require_auth
@require_store_access
def create_policy():
    """Create new policy."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['title', 'policy_type', 'content']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Create policy
        policy = Policy(
            store_id=store_id,
            title=data['title'],
            policy_type=data['policy_type'],
            content=data['content'],
            excerpt=data.get('excerpt'),
            is_published=data.get('is_published', False),
            is_required=data.get('is_required', False),
            show_in_footer=data.get('show_in_footer', True),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description'),
            meta_keywords=data.get('meta_keywords'),
            version=data.get('version', '1.0'),
            display_order=data.get('display_order', 0),
            template=data.get('template', 'default'),
            requires_acceptance=data.get('requires_acceptance', False)
        )
        
        # Handle optional fields
        if data.get('auto_sections'):
            policy.auto_sections = data['auto_sections']
        
        if data.get('custom_fields'):
            policy.custom_fields = data['custom_fields']
        
        # Set effective date
        if data.get('effective_date'):
            from datetime import datetime
            policy.effective_date = datetime.fromisoformat(data['effective_date'])
        else:
            from datetime import datetime
            policy.effective_date = datetime.utcnow()
        
        db.session.add(policy)
        db.session.commit()
        
        return jsonify({
            'message': 'Policy created successfully',
            'data': {
                'policy': policy.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create policy route error: {str(e)}")
        return jsonify({
            'error': 'Policy creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/<int:policy_id>', methods=['GET'])
@require_auth
@require_store_access
def get_policy(policy_id):
    """Get specific policy."""
    try:
        store_id = get_current_store_id()
        
        policy = Policy.query.filter_by(
            id=policy_id,
            store_id=store_id
        ).first()
        
        if not policy:
            return jsonify({
                'error': 'Policy not found',
                'message': 'The requested policy was not found'
            }), 404
        
        return jsonify({
            'message': 'Policy retrieved successfully',
            'data': {
                'policy': policy.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get policy route error: {str(e)}")
        return jsonify({
            'error': 'Policy retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/<int:policy_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_policy(policy_id):
    """Update policy."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        policy = Policy.query.filter_by(
            id=policy_id,
            store_id=store_id
        ).first()
        
        if not policy:
            return jsonify({
                'error': 'Policy not found',
                'message': 'The requested policy was not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'title', 'content', 'excerpt', 'is_published', 'is_required',
            'show_in_footer', 'meta_title', 'meta_description', 'meta_keywords',
            'version', 'display_order', 'template', 'requires_acceptance',
            'auto_sections', 'custom_fields'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(policy, field, data[field])
        
        # Update last modified date
        from datetime import datetime
        policy.last_modified_date = datetime.utcnow()
        
        # Update effective date if provided
        if data.get('effective_date'):
            policy.effective_date = datetime.fromisoformat(data['effective_date'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Policy updated successfully',
            'data': {
                'policy': policy.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update policy route error: {str(e)}")
        return jsonify({
            'error': 'Policy update failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/<int:policy_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_policy(policy_id):
    """Delete policy."""
    try:
        store_id = get_current_store_id()
        
        policy = Policy.query.filter_by(
            id=policy_id,
            store_id=store_id
        ).first()
        
        if not policy:
            return jsonify({
                'error': 'Policy not found',
                'message': 'The requested policy was not found'
            }), 404
        
        db.session.delete(policy)
        db.session.commit()
        
        return jsonify({
            'message': 'Policy deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete policy route error: {str(e)}")
        return jsonify({
            'error': 'Policy deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/create-defaults', methods=['POST'])
@require_auth
@require_store_access
def create_default_policies():
    """Create default policies for store."""
    try:
        store_id = get_current_store_id()
        
        policies = Policy.create_default_policies(store_id)
        
        return jsonify({
            'message': 'Default policies created successfully',
            'data': {
                'policies': [policy.to_dict() for policy in policies]
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create default policies route error: {str(e)}")
        return jsonify({
            'error': 'Default policy creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/by-type/<policy_type>', methods=['GET'])
@require_auth
@require_store_access
def get_policy_by_type(policy_type):
    """Get policy by type."""
    try:
        store_id = get_current_store_id()
        
        policy = Policy.query.filter_by(
            store_id=store_id,
            policy_type=policy_type
        ).first()
        
        if not policy:
            return jsonify({
                'error': 'Policy not found',
                'message': f'No {policy_type} policy found'
            }), 404
        
        return jsonify({
            'message': 'Policy retrieved successfully',
            'data': {
                'policy': policy.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get policy by type route error: {str(e)}")
        return jsonify({
            'error': 'Policy retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/footer', methods=['GET'])
@require_auth
@require_store_access
def get_footer_policies():
    """Get policies for footer display."""
    try:
        store_id = get_current_store_id()
        
        policies = Policy.get_footer_policies(store_id)
        
        return jsonify({
            'message': 'Footer policies retrieved successfully',
            'data': {
                'policies': [policy.to_public_dict() for policy in policies]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get footer policies route error: {str(e)}")
        return jsonify({
            'error': 'Footer policies retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/required', methods=['GET'])
@require_auth
@require_store_access
def get_required_policies():
    """Get policies required for checkout."""
    try:
        store_id = get_current_store_id()
        
        policies = Policy.get_required_policies(store_id)
        
        return jsonify({
            'message': 'Required policies retrieved successfully',
            'data': {
                'policies': [policy.to_public_dict() for policy in policies]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get required policies route error: {str(e)}")
        return jsonify({
            'error': 'Required policies retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@policies_bp.route('/review-due', methods=['GET'])
@require_auth
@require_store_access
def get_policies_due_for_review():
    """Get policies due for review."""
    try:
        store_id = get_current_store_id()
        
        policies = Policy.get_policies_due_for_review(store_id)
        
        return jsonify({
            'message': 'Policies due for review retrieved successfully',
            'data': {
                'policies': [policy.to_dict() for policy in policies],
                'count': len(policies)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get policies due for review route error: {str(e)}")
        return jsonify({
            'error': 'Policies review retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@policies_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@policies_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested policy was not found'
    }), 404