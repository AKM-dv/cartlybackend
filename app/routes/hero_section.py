from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.hero_section import HeroSection
from app.services.file_upload_service import FileUploadService
from app.middleware import (
    require_auth,
    require_store_access,
    require_store_owner,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

hero_section_bp = Blueprint('hero_section', __name__, url_prefix='/api/hero-section')

@hero_section_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def get_hero_section():
    """Get hero section configuration."""
    try:
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            # Create default hero section if not exists
            hero_section = HeroSection.create_default(store_id)
        
        return jsonify({
            'message': 'Hero section retrieved successfully',
            'data': {
                'hero_section': hero_section.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get hero section route error: {str(e)}")
        return jsonify({
            'error': 'Hero section retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_hero_section():
    """Update hero section configuration."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            hero_section = HeroSection(store_id=store_id)
            db.session.add(hero_section)
        
        # Update allowed fields
        allowed_fields = [
            'enable_top_bar', 'top_bar_text', 'top_bar_link', 'top_bar_link_text',
            'top_bar_bg_color', 'top_bar_text_color', 'top_bar_position',
            'hero_type', 'hero_height', 'hero_overlay_opacity',
            'auto_play', 'slide_duration', 'show_navigation', 'show_pagination',
            'slide_animation', 'single_image_url', 'single_mobile_image_url',
            'single_title', 'single_subtitle', 'single_description',
            'single_button_text', 'single_button_link', 'single_text_position',
            'single_text_color', 'video_url', 'video_poster', 'video_autoplay',
            'video_muted', 'video_loop', 'enable_popup', 'popup_type',
            'popup_title', 'popup_content', 'popup_image', 'popup_button_text',
            'popup_button_link', 'popup_delay', 'popup_frequency', 'popup_position',
            'popup_size', 'popup_bg_color', 'popup_text_color', 'popup_overlay_color',
            'popup_overlay_opacity', 'enable_exit_intent', 'exit_intent_title',
            'exit_intent_content', 'exit_intent_discount_code', 'hide_on_mobile',
            'mobile_hero_height', 'mobile_text_size', 'lazy_load_images',
            'preload_next_slide', 'track_clicks'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(hero_section, field, data[field])
        
        # Handle hero slides separately
        if 'hero_slides' in data:
            hero_section.hero_slides = data['hero_slides']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Hero section updated successfully',
            'data': {
                'hero_section': hero_section.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update hero section route error: {str(e)}")
        return jsonify({
            'error': 'Hero section update failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/top-bar', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_top_bar():
    """Update top bar configuration."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            hero_section = HeroSection(store_id=store_id)
            db.session.add(hero_section)
        
        # Update top bar fields
        top_bar_fields = [
            'enable_top_bar', 'top_bar_text', 'top_bar_link', 'top_bar_link_text',
            'top_bar_bg_color', 'top_bar_text_color', 'top_bar_position'
        ]
        
        for field in top_bar_fields:
            if field in data:
                setattr(hero_section, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Top bar updated successfully',
            'data': {
                'top_bar_config': hero_section.get_top_bar_config()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update top bar route error: {str(e)}")
        return jsonify({
            'error': 'Top bar update failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/slides', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def add_slide():
    """Add new slide to hero section."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['image_url', 'title']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            hero_section = HeroSection(store_id=store_id)
            db.session.add(hero_section)
            db.session.flush()
        
        # Prepare slide data
        slide_data = {
            'image_url': data['image_url'],
            'mobile_image_url': data.get('mobile_image_url'),
            'title': data['title'],
            'subtitle': data.get('subtitle'),
            'description': data.get('description'),
            'button_text': data.get('button_text'),
            'button_link': data.get('button_link'),
            'text_position': data.get('text_position', 'center'),
            'text_color': data.get('text_color', '#ffffff'),
            'overlay_color': data.get('overlay_color', '#000000'),
            'overlay_opacity': data.get('overlay_opacity', 30),
            'animation': data.get('animation', 'fade'),
            'duration': data.get('duration', 5000),
            'active': data.get('active', True),
            'order': data.get('order')
        }
        
        slide_id = hero_section.add_slide(slide_data)
        db.session.commit()
        
        return jsonify({
            'message': 'Slide added successfully',
            'data': {
                'slide_id': slide_id,
                'hero_section': hero_section.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add slide route error: {str(e)}")
        return jsonify({
            'error': 'Slide addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/slides/<int:slide_id>', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_slide(slide_id):
    """Update existing slide."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            return jsonify({
                'error': 'Hero section not found',
                'message': 'Hero section configuration not found'
            }), 404
        
        success = hero_section.update_slide(slide_id, data)
        
        if not success:
            return jsonify({
                'error': 'Slide not found',
                'message': 'The requested slide was not found'
            }), 404
        
        db.session.commit()
        
        return jsonify({
            'message': 'Slide updated successfully',
            'data': {
                'hero_section': hero_section.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update slide route error: {str(e)}")
        return jsonify({
            'error': 'Slide update failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/slides/<int:slide_id>', methods=['DELETE'])
@require_auth
@require_store_access
@require_store_owner
def delete_slide(slide_id):
    """Delete slide from hero section."""
    try:
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            return jsonify({
                'error': 'Hero section not found',
                'message': 'Hero section configuration not found'
            }), 404
        
        success = hero_section.delete_slide(slide_id)
        
        if not success:
            return jsonify({
                'error': 'Slide not found',
                'message': 'The requested slide was not found'
            }), 404
        
        db.session.commit()
        
        return jsonify({
            'message': 'Slide deleted successfully',
            'data': {
                'hero_section': hero_section.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete slide route error: {str(e)}")
        return jsonify({
            'error': 'Slide deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/slides/reorder', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def reorder_slides():
    """Reorder slides."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if 'slide_orders' not in data:
            return jsonify({
                'error': 'Validation failed',
                'message': 'slide_orders is required'
            }), 400
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            return jsonify({
                'error': 'Hero section not found',
                'message': 'Hero section configuration not found'
            }), 404
        
        hero_section.reorder_slides(data['slide_orders'])
        db.session.commit()
        
        return jsonify({
            'message': 'Slides reordered successfully',
            'data': {
                'hero_section': hero_section.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Reorder slides route error: {str(e)}")
        return jsonify({
            'error': 'Slide reordering failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/popup', methods=['PUT'])
@require_auth
@require_store_access
@require_store_owner
def update_popup():
    """Update popup configuration."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            hero_section = HeroSection(store_id=store_id)
            db.session.add(hero_section)
        
        # Update popup fields
        popup_fields = [
            'enable_popup', 'popup_type', 'popup_title', 'popup_content',
            'popup_image', 'popup_button_text', 'popup_button_link',
            'popup_delay', 'popup_frequency', 'popup_position', 'popup_size',
            'popup_bg_color', 'popup_text_color', 'popup_overlay_color',
            'popup_overlay_opacity', 'enable_exit_intent', 'exit_intent_title',
            'exit_intent_content', 'exit_intent_discount_code'
        ]
        
        for field in popup_fields:
            if field in data:
                setattr(hero_section, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Popup configuration updated successfully',
            'data': {
                'popup_config': hero_section.get_popup_config()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update popup route error: {str(e)}")
        return jsonify({
            'error': 'Popup update failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/upload-image', methods=['POST'])
@require_auth
@require_store_access
@require_store_owner
def upload_hero_image():
    """Upload hero image."""
    try:
        store_id = get_current_store_id()
        
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please select a file to upload'
            }), 400
        
        file = request.files['file']
        
        result = FileUploadService.upload_hero_image(store_id, file)
        
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
        logging.error(f"Upload hero image route error: {str(e)}")
        return jsonify({
            'error': 'Image upload failed',
            'message': 'An unexpected error occurred'
        }), 500

@hero_section_bp.route('/preview', methods=['GET'])
@require_auth
@require_store_access
def get_hero_preview():
    """Get hero section preview configuration."""
    try:
        store_id = get_current_store_id()
        
        hero_section = HeroSection.get_by_store_id(store_id)
        
        if not hero_section:
            return jsonify({
                'error': 'Hero section not found',
                'message': 'Hero section configuration not found'
            }), 404
        
        preview_config = {
            'top_bar': hero_section.get_top_bar_config(),
            'hero': hero_section.get_hero_config(),
            'popup': hero_section.get_popup_config()
        }
        
        return jsonify({
            'message': 'Hero section preview retrieved successfully',
            'data': preview_config
        }), 200
        
    except Exception as e:
        logging.error(f"Get hero preview route error: {str(e)}")
        return jsonify({
            'error': 'Hero section preview failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@hero_section_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@hero_section_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404