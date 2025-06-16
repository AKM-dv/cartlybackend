"""
Store settings routes for store configuration management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.store_settings import StoreSettings
from app.middleware import (
    require_auth,
    require_store_access,
    require_store_owner,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

store_settings_bp = Blueprint('store_settings', __name__, url_prefix='/api/store-settings')

@store_settings_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def get_store_settings():
    """Get store settings."""
    try:
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            # Create default settings if not exists
            settings = StoreSettings.create_default_settings(store_id)
        
        return jsonify({
            'message': 'Store settings retrieved successfully',
            'data': {
                'settings': settings.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get store settings route error: {str(e)}")
        return jsonify({
            'error': 'Store settings retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_store_settings():
    """Update store settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update allowed fields
        allowed_fields = [
            'timezone', 'currency', 'date_format', 'time_format', 'number_format',
            'weight_unit', 'dimension_unit', 'tax_calculation_method', 'prices_include_tax',
            'display_prices_with_tax', 'default_tax_rate', 'inventory_tracking',
            'low_stock_threshold', 'out_of_stock_visibility', 'backorder_policy',
            'customer_registration', 'guest_checkout', 'order_id_prefix',
            'order_id_suffix', 'invoice_prefix', 'invoice_suffix', 'auto_invoice_generation',
            'email_notifications', 'sms_notifications', 'notification_settings',
            'checkout_settings', 'shipping_settings', 'payment_settings',
            'seo_settings', 'social_media_settings', 'analytics_settings',
            'security_settings', 'api_settings', 'maintenance_settings',
            'backup_settings', 'custom_css', 'custom_js', 'theme_settings',
            'gdpr_settings', 'cookie_settings', 'terms_acceptance_required',
            'custom_fields'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Store settings updated successfully',
            'data': {
                'settings': settings.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update store settings route error: {str(e)}")
        return jsonify({
            'error': 'Store settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/general', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_general_settings():
    """Update general store settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update general fields
        general_fields = [
            'timezone', 'currency', 'date_format', 'time_format',
            'number_format', 'weight_unit', 'dimension_unit'
        ]
        
        for field in general_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'General settings updated successfully',
            'data': {
                'general_settings': {
                    field: getattr(settings, field) for field in general_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update general settings route error: {str(e)}")
        return jsonify({
            'error': 'General settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/tax', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_tax_settings():
    """Update tax settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update tax fields
        tax_fields = [
            'tax_calculation_method', 'prices_include_tax',
            'display_prices_with_tax', 'default_tax_rate'
        ]
        
        for field in tax_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tax settings updated successfully',
            'data': {
                'tax_settings': {
                    field: getattr(settings, field) for field in tax_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update tax settings route error: {str(e)}")
        return jsonify({
            'error': 'Tax settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/inventory', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_inventory_settings():
    """Update inventory settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update inventory fields
        inventory_fields = [
            'inventory_tracking', 'low_stock_threshold',
            'out_of_stock_visibility', 'backorder_policy'
        ]
        
        for field in inventory_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Inventory settings updated successfully',
            'data': {
                'inventory_settings': {
                    field: getattr(settings, field) for field in inventory_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update inventory settings route error: {str(e)}")
        return jsonify({
            'error': 'Inventory settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/checkout', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_checkout_settings():
    """Update checkout settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update checkout fields
        checkout_fields = [
            'customer_registration', 'guest_checkout', 'checkout_settings'
        ]
        
        for field in checkout_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Checkout settings updated successfully',
            'data': {
                'checkout_settings': {
                    field: getattr(settings, field) for field in checkout_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update checkout settings route error: {str(e)}")
        return jsonify({
            'error': 'Checkout settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/notifications', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_notification_settings():
    """Update notification settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update notification fields
        notification_fields = [
            'email_notifications', 'sms_notifications', 'notification_settings'
        ]
        
        for field in notification_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notification settings updated successfully',
            'data': {
                'notification_settings': {
                    field: getattr(settings, field) for field in notification_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update notification settings route error: {str(e)}")
        return jsonify({
            'error': 'Notification settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/seo', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_seo_settings():
    """Update SEO settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update SEO settings
        if 'seo_settings' in data:
            settings.seo_settings = data['seo_settings']
        
        db.session.commit()
        
        return jsonify({
            'message': 'SEO settings updated successfully',
            'data': {
                'seo_settings': settings.seo_settings
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update SEO settings route error: {str(e)}")
        return jsonify({
            'error': 'SEO settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/security', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_security_settings():
    """Update security settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update security settings
        if 'security_settings' in data:
            settings.security_settings = data['security_settings']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Security settings updated successfully',
            'data': {
                'security_settings': settings.security_settings
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update security settings route error: {str(e)}")
        return jsonify({
            'error': 'Security settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/theme', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_theme_settings():
    """Update theme settings."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        settings = StoreSettings.get_by_store_id(store_id)
        
        if not settings:
            settings = StoreSettings(store_id=store_id)
            db.session.add(settings)
        
        # Update theme fields
        theme_fields = ['custom_css', 'custom_js', 'theme_settings']
        
        for field in theme_fields:
            if field in data:
                setattr(settings, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Theme settings updated successfully',
            'data': {
                'theme_settings': {
                    field: getattr(settings, field) for field in theme_fields
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update theme settings route error: {str(e)}")
        return jsonify({
            'error': 'Theme settings update failed',
            'message': 'An unexpected error occurred'
        }), 500

@store_settings_bp.route('/reset-to-defaults', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def reset_to_defaults():
    """Reset store settings to defaults."""
    try:
        store_id = get_current_store_id()
        
        # Delete existing settings
        existing_settings = StoreSettings.get_by_store_id(store_id)
        if existing_settings:
            db.session.delete(existing_settings)
        
        # Create new default settings
        settings = StoreSettings.create_default_settings(store_id)
        
        return jsonify({
            'message': 'Store settings reset to defaults successfully',
            'data': {
                'settings': settings.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Reset settings route error: {str(e)}")
        return jsonify({
            'error': 'Settings reset failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@store_settings_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@store_settings_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested settings were not found'
    }), 404