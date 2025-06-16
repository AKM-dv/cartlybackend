from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.category import Category
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@categories_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_categories():
    """List categories with optional hierarchy."""
    try:
        store_id = get_current_store_id()
        
        # Get query parameters
        parent_id = request.args.get('parent_id')
        include_children = request.args.get('include_children', 'false').lower() == 'true'
        flat = request.args.get('flat', 'false').lower() == 'true'
        
        if flat:
            # Get all categories in flat list
            categories = Category.query.filter_by(
                store_id=store_id,
                is_active=True
            ).order_by(Category.level, Category.sort_order).all()
        elif parent_id:
            # Get categories with specific parent
            if parent_id == 'root':
                categories = Category.get_root_categories(store_id)
            else:
                categories = Category.query.filter_by(
                    store_id=store_id,
                    parent_id=parent_id,
                    is_active=True
                ).order_by(Category.sort_order).all()
        else:
            # Get root categories by default
            categories = Category.get_root_categories(store_id)
        
        # Convert to dict and include children if requested
        category_data = []
        for category in categories:
            cat_dict = category.to_dict()
            if include_children and not flat:
                cat_dict['children'] = [
                    child.to_dict() for child in category.get_active_children()
                ]
            category_data.append(cat_dict)
        
        return jsonify({
            'message': 'Categories retrieved successfully',
            'data': {
                'categories': category_data,
                'count': len(category_data)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List categories route error: {str(e)}")
        return jsonify({
            'error': 'Category listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('', methods=['POST'])
@require_auth
@require_store_access
def create_category():
    """Create new category."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        validation_result = validate_required_fields(data, ['name'])
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Validate parent category if provided
        parent_id = data.get('parent_id')
        if parent_id:
            parent = Category.query.filter_by(
                id=parent_id,
                store_id=store_id
            ).first()
            
            if not parent:
                return jsonify({
                    'error': 'Invalid parent category',
                    'message': 'Parent category not found'
                }), 400
        
        # Create category
        category = Category(
            store_id=store_id,
            name=data['name'],
            description=data.get('description'),
            parent_id=parent_id,
            sort_order=data.get('sort_order', 0),
            image=data.get('image'),
            icon=data.get('icon'),
            banner_image=data.get('banner_image'),
            is_featured=data.get('is_featured', False),
            show_in_menu=data.get('show_in_menu', True),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description'),
            meta_keywords=data.get('meta_keywords'),
            display_type=data.get('display_type', 'grid'),
            products_per_page=data.get('products_per_page', 12),
            show_subcategories=data.get('show_subcategories', True)
        )
        
        # Handle category attributes
        if 'category_attributes' in data:
            category.category_attributes = data['category_attributes']
        
        if 'available_filters' in data:
            category.available_filters = data['available_filters']
        
        if 'auto_add_rules' in data:
            category.auto_add_rules = data['auto_add_rules']
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'data': {
                'category': category.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create category route error: {str(e)}")
        return jsonify({
            'error': 'Category creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/<int:category_id>', methods=['GET'])
@require_auth
@require_store_access
def get_category(category_id):
    """Get specific category."""
    try:
        store_id = get_current_store_id()
        
        category = Category.query.filter_by(
            id=category_id,
            store_id=store_id
        ).first()
        
        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': 'The requested category was not found'
            }), 404
        
        # Include additional data
        category_dict = category.to_dict()
        category_dict['breadcrumb'] = category.get_breadcrumb()
        category_dict['children'] = [child.to_dict() for child in category.get_active_children()]
        
        return jsonify({
            'message': 'Category retrieved successfully',
            'data': {
                'category': category_dict
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get category route error: {str(e)}")
        return jsonify({
            'error': 'Category retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_category(category_id):
    """Update category."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        category = Category.query.filter_by(
            id=category_id,
            store_id=store_id
        ).first()
        
        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': 'The requested category was not found'
            }), 404
        
        # Validate parent category if being changed
        if 'parent_id' in data and data['parent_id'] != category.parent_id:
            new_parent_id = data['parent_id']
            
            if new_parent_id:
                parent = Category.query.filter_by(
                    id=new_parent_id,
                    store_id=store_id
                ).first()
                
                if not parent:
                    return jsonify({
                        'error': 'Invalid parent category',
                        'message': 'Parent category not found'
                    }), 400
                
                # Check for circular reference
                if new_parent_id == category_id:
                    return jsonify({
                        'error': 'Invalid parent',
                        'message': 'Category cannot be its own parent'
                    }), 400
                
                # Check if new parent is not a descendant
                descendant_ids = category.get_child_ids()
                if new_parent_id in descendant_ids:
                    return jsonify({
                        'error': 'Invalid parent',
                        'message': 'Cannot move category to its descendant'
                    }), 400
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'parent_id', 'sort_order', 'image', 'icon',
            'banner_image', 'is_active', 'is_featured', 'show_in_menu',
            'meta_title', 'meta_description', 'meta_keywords', 'display_type',
            'products_per_page', 'show_subcategories', 'category_attributes',
            'available_filters', 'auto_add_rules'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(category, field, data[field])
        
        # Update level if parent changed
        if 'parent_id' in data:
            if data['parent_id']:
                parent = Category.query.get(data['parent_id'])
                category.level = parent.level + 1 if parent else 0
            else:
                category.level = 0
            
            # Update children levels
            category._update_children_levels()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Category updated successfully',
            'data': {
                'category': category.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update category route error: {str(e)}")
        return jsonify({
            'error': 'Category update failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_category(category_id):
    """Delete category."""
    try:
        store_id = get_current_store_id()
        
        category = Category.query.filter_by(
            id=category_id,
            store_id=store_id
        ).first()
        
        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': 'The requested category was not found'
            }), 404
        
        # Check if category can be deleted
        can_delete, message = category.can_delete()
        if not can_delete:
            return jsonify({
                'error': 'Cannot delete category',
                'message': message
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete category route error: {str(e)}")
        return jsonify({
            'error': 'Category deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/<int:category_id>/move', methods=['POST'])
@require_auth
@require_store_access
def move_category(category_id):
    """Move category to new parent."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        category = Category.query.filter_by(
            id=category_id,
            store_id=store_id
        ).first()
        
        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': 'The requested category was not found'
            }), 404
        
        new_parent_id = data.get('parent_id')
        
        success, message = category.move_to_parent(new_parent_id)
        
        if not success:
            return jsonify({
                'error': 'Move failed',
                'message': message
            }), 400
        
        db.session.commit()
        
        return jsonify({
            'message': message,
            'data': {
                'category': category.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Move category route error: {str(e)}")
        return jsonify({
            'error': 'Category move failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/<int:category_id>/products', methods=['GET'])
@require_auth
@require_store_access
def get_category_products(category_id):
    """Get products in category."""
    try:
        store_id = get_current_store_id()
        
        category = Category.query.filter_by(
            id=category_id,
            store_id=store_id
        ).first()
        
        if not category:
            return jsonify({
                'error': 'Category not found',
                'message': 'The requested category was not found'
            }), 404
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', category.products_per_page)), 100)
        
        from app.models.product import Product
        
        # Get products in this category
        query = Product.query.filter_by(
            store_id=store_id,
            category_id=category_id,
            status='active'
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'message': 'Category products retrieved successfully',
            'data': {
                'category': category.to_dict(),
                'products': [product.to_dict() for product in products],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get category products route error: {str(e)}")
        return jsonify({
            'error': 'Category products retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/featured', methods=['GET'])
@require_auth
@require_store_access
def get_featured_categories():
    """Get featured categories."""
    try:
        store_id = get_current_store_id()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        categories = Category.get_featured_categories(store_id, limit)
        
        return jsonify({
            'message': 'Featured categories retrieved successfully',
            'data': {
                'categories': [category.to_dict() for category in categories]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get featured categories route error: {str(e)}")
        return jsonify({
            'error': 'Featured categories retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/menu', methods=['GET'])
@require_auth
@require_store_access
def get_menu_categories():
    """Get categories for menu display."""
    try:
        store_id = get_current_store_id()
        
        categories = Category.get_menu_categories(store_id)
        
        # Build hierarchical structure
        menu_structure = []
        root_categories = [cat for cat in categories if cat.parent_id is None]
        
        for root_cat in root_categories:
            cat_dict = root_cat.to_dict()
            cat_dict['children'] = [
                child.to_dict() for child in categories 
                if child.parent_id == root_cat.id
            ]
            menu_structure.append(cat_dict)
        
        return jsonify({
            'message': 'Menu categories retrieved successfully',
            'data': {
                'menu_structure': menu_structure
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get menu categories route error: {str(e)}")
        return jsonify({
            'error': 'Menu categories retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@categories_bp.route('/rebuild-stats', methods=['POST'])
@require_auth
@require_store_access
def rebuild_category_stats():
    """Rebuild category statistics."""
    try:
        store_id = get_current_store_id()
        
        Category.rebuild_tree_stats(store_id)
        
        return jsonify({
            'message': 'Category statistics rebuilt successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Rebuild category stats route error: {str(e)}")
        return jsonify({
            'error': 'Category stats rebuild failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@categories_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@categories_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested category was not found'
    }), 404