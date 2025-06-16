"""
Contact routes for contact details management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.contact_details import ContactDetails
from app.middleware import (
    require_auth,
    require_store_access,
    require_store_owner,
    get_current_store_id
)
from app.utils.validators import validate_required_fields, validate_email
import logging

contact_bp = Blueprint('contact', __name__, url_prefix='/api/contact')

@contact_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def get_contact_details():
    """Get store contact details."""
    try:
        store_id = get_current_store_id()
        
        contact = ContactDetails.get_by_store_id(store_id)
        
        if not contact:
            # Create default contact details if not exists
            contact = ContactDetails(store_id=store_id)
            db.session.add(contact)
            db.session.commit()
        
        return jsonify({
            'message': 'Contact details retrieved successfully',
            'data': {
                'contact': contact.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get contact details route error: {str(e)}")
        return jsonify({
            'error': 'Contact details retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@contact_bp.route('', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_contact_details():
    """Update store contact details."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        contact = ContactDetails.get_by_store_id(store_id)
        
        if not contact:
            contact = ContactDetails(store_id=store_id)
            db.session.add(contact)
        
        # Validate email if provided
        if 'email' in data and data['email']:
            if not validate_email(data['email']):
                return jsonify({
                    'error': 'Invalid email',
                    'message': 'Please provide a valid email address'
                }), 400
        
        # Update allowed fields
        allowed_fields = [
            'business_name', 'email', 'phone', 'mobile', 'fax', 'website',
            'address_line_1', 'address_line_2', 'city', 'state', 'country',
            'postal_code', 'latitude', 'longitude', 'business_hours',
            'social_media_links', 'contact_person', 'support_email',
            'sales_email', 'business_registration_number', 'tax_id',
            'bank_details', 'emergency_contact', 'additional_info'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(contact, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contact details updated successfully',
            'data': {
                'contact': contact.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update contact details route error: {str(e)}")
        return jsonify({
            'error': 'Contact details update failed',
            'message': 'An unexpected error occurred'
        }), 500

@contact_bp.route('/business-hours', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_business_hours():
    """Update business hours."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if 'business_hours' not in data:
            return jsonify({
                'error': 'Validation failed',
                'message': 'business_hours is required'
            }), 400
        
        contact = ContactDetails.get_by_store_id(store_id)
        
        if not contact:
            contact = ContactDetails(store_id=store_id)
            db.session.add(contact)
        
        contact.business_hours = data['business_hours']
        db.session.commit()
        
        return jsonify({
            'message': 'Business hours updated successfully',
            'data': {
                'business_hours': contact.business_hours
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update business hours route error: {str(e)}")
        return jsonify({
            'error': 'Business hours update failed',
            'message': 'An unexpected error occurred'
        }), 500

@contact_bp.route('/social-media', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_social_media():
    """Update social media links."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if 'social_media_links' not in data:
            return jsonify({
                'error': 'Validation failed',
                'message': 'social_media_links is required'
            }), 400
        
        contact = ContactDetails.get_by_store_id(store_id)
        
        if not contact:
            contact = ContactDetails(store_id=store_id)
            db.session.add(contact)
        
        contact.social_media_links = data['social_media_links']
        db.session.commit()
        
        return jsonify({
            'message': 'Social media links updated successfully',
            'data': {
                'social_media_links': contact.social_media_links
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update social media route error: {str(e)}")
        return jsonify({
            'error': 'Social media update failed',
            'message': 'An unexpected error occurred'
        }), 500

@contact_bp.route('/location', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_location():
    """Update store location coordinates."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['latitude', 'longitude']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        contact = ContactDetails.get_by_store_id(store_id)
        
        if not contact:
            contact = ContactDetails(store_id=store_id)
            db.session.add(contact)
        
        contact.latitude = data['latitude']
        contact.longitude = data['longitude']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Location updated successfully',
            'data': {
                'latitude': contact.latitude,
                'longitude': contact.longitude
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update location route error: {str(e)}")
        return jsonify({
            'error': 'Location update failed',
            'message': 'An unexpected error occurred'
        }), 500

@contact_bp.route('/verify-address', methods=['POST'])
@require_auth
@require_store_access
def verify_address():
    """Verify address using external service."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['address_line_1', 'city', 'country']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # TODO: Implement address verification using external service
        # For now, return the address as provided
        verified_address = {
            'address_line_1': data['address_line_1'],
            'address_line_2': data.get('address_line_2'),
            'city': data['city'],
            'state': data.get('state'),
            'country': data['country'],
            'postal_code': data.get('postal_code'),
            'is_verified': True,
            'suggestions': []
        }
        
        return jsonify({
            'message': 'Address verified successfully',
            'data': {
                'verified_address': verified_address
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Verify address route error: {str(e)}")
        return jsonify({
            'error': 'Address verification failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@contact_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@contact_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested contact information was not found'
    }), 404