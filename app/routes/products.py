from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.product import Product
from app.models.category import Category
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id,
    validate_store_limits
)
from app.utils.validators import validate_required_fields
import logging

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

@products_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_products():
    """List products with pagination and filters."""
    try:
        store_id = get_current_store_id()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search')
        category_id = request.args.get('category_id')
        status = request.args.get('status')
        is_featured = request.args.get('is_featured')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Product.query.filter_by(store_id=store_id)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.like(search_term),
                    Product.sku.like(search_term),
                    Product.description.like(search_term)
                )
            )
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if is_featured is not None:
            query = query.filter_by(is_featured=is_featured.lower() == 'true')
        
        # Apply sorting
        if hasattr(Product, sort_by):
            order_column = getattr(Product, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'message': 'Products retrieved successfully',
            'data': {
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
        logging.error(f"List products route error: {str(e)}")
        return jsonify({
            'error': 'Product listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('', methods=['POST'])
@require_auth
@require_store_access
@validate_store_limits
def create_product():
    """Create new product."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['name', 'price']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Create product
        product = Product(
            store_id=store_id,
            name=data['name'],
            description=data.get('description'),
            short_description=data.get('short_description'),
            price=data['price'],
            compare_price=data.get('compare_price'),
            cost_price=data.get('cost_price'),
            sku=data.get('sku'),
            barcode=data.get('barcode'),
            category_id=data.get('category_id'),
            brand=data.get('brand'),
            weight=data.get('weight'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            track_inventory=data.get('track_inventory', True),
            inventory_quantity=data.get('inventory_quantity', 0),
            low_stock_threshold=data.get('low_stock_threshold', 5),
            allow_backorders=data.get('allow_backorders', False),
            is_featured=data.get('is_featured', False),
            is_digital=data.get('is_digital', False),
            requires_shipping=data.get('requires_shipping', True),
            tax_class=data.get('tax_class', 'standard'),
            status=data.get('status', 'draft')
        )
        
        # Handle optional fields
        if 'tags' in data:
            product.tags = data['tags']
        
        if 'specifications' in data:
            product.specifications = data['specifications']
        
        if 'features' in data:
            product.features = data['features']
        
        if 'meta_title' in data:
            product.meta_title = data['meta_title']
        
        if 'meta_description' in data:
            product.meta_description = data['meta_description']
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create product route error: {str(e)}")
        return jsonify({
            'error': 'Product creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>', methods=['GET'])
@require_auth
@require_store_access
def get_product(product_id):
    """Get specific product."""
    try:
        store_id = get_current_store_id()
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        return jsonify({
            'message': 'Product retrieved successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get product route error: {str(e)}")
        return jsonify({
            'error': 'Product retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_product(product_id):
    """Update product."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'short_description', 'price', 'compare_price',
            'cost_price', 'sku', 'barcode', 'category_id', 'brand', 'tags',
            'specifications', 'features', 'weight', 'length', 'width', 'height',
            'track_inventory', 'inventory_quantity', 'low_stock_threshold',
            'allow_backorders', 'is_featured', 'is_digital', 'requires_shipping',
            'tax_class', 'meta_title', 'meta_description', 'meta_keywords',
            'status'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(product, field, data[field])
        
        # Recalculate reading time if content changed
        if 'description' in data:
            product.reading_time = product.calculate_reading_time()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update product route error: {str(e)}")
        return jsonify({
            'error': 'Product update failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_product(product_id):
    """Delete product."""
    try:
        store_id = get_current_store_id()
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete product route error: {str(e)}")
        return jsonify({
            'error': 'Product deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>/publish', methods=['POST'])
@require_auth
@require_store_access
def publish_product(product_id):
    """Publish product."""
    try:
        store_id = get_current_store_id()
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        product.publish()
        db.session.commit()
        
        return jsonify({
            'message': 'Product published successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Publish product route error: {str(e)}")
        return jsonify({
            'error': 'Product publishing failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>/unpublish', methods=['POST'])
@require_auth
@require_store_access
def unpublish_product(product_id):
    """Unpublish product."""
    try:
        store_id = get_current_store_id()
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        product.unpublish()
        db.session.commit()
        
        return jsonify({
            'message': 'Product unpublished successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unpublish product route error: {str(e)}")
        return jsonify({
            'error': 'Product unpublishing failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>/images', methods=['POST'])
@require_auth
@require_store_access
def add_product_image(product_id):
    """Add image to product."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('image_url'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Image URL is required'
            }), 400
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        product.add_image(
            image_url=data['image_url'],
            alt_text=data.get('alt_text', ''),
            is_featured=data.get('is_featured', False)
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Image added successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add product image route error: {str(e)}")
        return jsonify({
            'error': 'Image addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>/images', methods=['DELETE'])
@require_auth
@require_store_access
def remove_product_image(product_id):
    """Remove image from product."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        if not data.get('image_url'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Image URL is required'
            }), 400
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        success = product.remove_image(data['image_url'])
        
        if not success:
            return jsonify({
                'error': 'Image not found',
                'message': 'The specified image was not found'
            }), 404
        
        db.session.commit()
        
        return jsonify({
            'message': 'Image removed successfully',
            'data': {
                'product': product.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Remove product image route error: {str(e)}")
        return jsonify({
            'error': 'Image removal failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/<int:product_id>/variants', methods=['POST'])
@require_auth
@require_store_access
def add_product_variant(product_id):
    """Add variant to product."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['sku', 'options']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        product = Product.query.filter_by(
            id=product_id,
            store_id=store_id
        ).first()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'message': 'The requested product was not found'
            }), 404
        
        variant_data = {
            'sku': data['sku'],
            'options': data['options'],
            'price': data.get('price', product.price),
            'inventory': data.get('inventory', 0),
            'image': data.get('image')
        }
        
        variant_id = product.add_variant(variant_data)
        db.session.commit()
        
        return jsonify({
            'message': 'Variant added successfully',
            'data': {
                'variant_id': variant_id,
                'product': product.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Add product variant route error: {str(e)}")
        return jsonify({
            'error': 'Variant addition failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/featured', methods=['GET'])
@require_auth
@require_store_access
def get_featured_products():
    """Get featured products."""
    try:
        store_id = get_current_store_id()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        products = Product.get_featured_products(store_id, limit)
        
        return jsonify({
            'message': 'Featured products retrieved successfully',
            'data': {
                'products': [product.to_dict() for product in products]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get featured products route error: {str(e)}")
        return jsonify({
            'error': 'Featured products retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/low-stock', methods=['GET'])
@require_auth
@require_store_access
def get_low_stock_products():
    """Get products with low stock."""
    try:
        store_id = get_current_store_id()
        
        products = Product.get_low_stock_products(store_id)
        
        return jsonify({
            'message': 'Low stock products retrieved successfully',
            'data': {
                'products': [product.to_dict() for product in products],
                'count': len(products)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get low stock products route error: {str(e)}")
        return jsonify({
            'error': 'Low stock products retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@products_bp.route('/search', methods=['GET'])
@require_auth
@require_store_access
def search_products():
    """Search products."""
    try:
        store_id = get_current_store_id()
        search_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if not search_term:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Search term is required'
            }), 400
        
        products = Product.search_products(store_id, search_term, limit)
        
        return jsonify({
            'message': 'Search completed successfully',
            'data': {
                'products': [product.to_dict() for product in products],
                'search_term': search_term,
                'count': len(products)
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Search products route error: {str(e)}")
        return jsonify({
            'error': 'Product search failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@products_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@products_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested product was not found'
    }), 404