"""
Blog routes for content management.
"""

from flask import Blueprint, request, jsonify
from app.config.database import db
from app.models.blog import Blog
from app.services.file_upload_service import FileUploadService
from app.middleware import (
    require_auth,
    require_store_access,
    get_current_store_id
)
from app.utils.validators import validate_required_fields
import logging

blogs_bp = Blueprint('blogs', __name__, url_prefix='/api/blogs')

@blogs_bp.route('', methods=['GET'])
@require_auth
@require_store_access
def list_blogs():
    """List blogs with pagination and filters."""
    try:
        store_id = get_current_store_id()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search')
        status = request.args.get('status')
        category = request.args.get('category')
        author_id = request.args.get('author_id')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Blog.query.filter_by(store_id=store_id)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Blog.title.like(search_term),
                    Blog.content.like(search_term),
                    Blog.excerpt.like(search_term)
                )
            )
        
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(blog_category=category)
        
        if author_id:
            query = query.filter_by(author_id=author_id)
        
        # Apply sorting
        if hasattr(Blog, sort_by):
            order_column = getattr(Blog, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        blogs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'message': 'Blogs retrieved successfully',
            'data': {
                'blogs': [blog.to_dict() for blog in blogs],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        }), 200
        
    except Exception as e:
        logging.error(f"List blogs route error: {str(e)}")
        return jsonify({
            'error': 'Blog listing failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('', methods=['POST'])
@require_auth
@require_store_access
def create_blog():
    """Create new blog post."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        # Validate required fields
        required_fields = ['title', 'content']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Create blog
        blog = Blog(
            store_id=store_id,
            title=data['title'],
            content=data['content'],
            excerpt=data.get('excerpt'),
            author_id=data.get('author_id'),
            author_name=data.get('author_name'),
            featured_image=data.get('featured_image'),
            featured_image_alt=data.get('featured_image_alt'),
            blog_category=data.get('blog_category'),
            status=data.get('status', 'draft'),
            is_featured=data.get('is_featured', False),
            allow_comments=data.get('allow_comments', True),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description'),
            meta_keywords=data.get('meta_keywords'),
            focus_keyword=data.get('focus_keyword'),
            social_title=data.get('social_title'),
            social_description=data.get('social_description'),
            social_image=data.get('social_image'),
            content_type=data.get('content_type', 'article'),
            language=data.get('language', 'en')
        )
        
        # Handle optional fields
        if data.get('tags'):
            blog.tags = data['tags']
        
        if data.get('related_products'):
            blog.related_products = data['related_products']
        
        if data.get('related_posts'):
            blog.related_posts = data['related_posts']
        
        if data.get('custom_fields'):
            blog.custom_fields = data['custom_fields']
        
        # Generate table of contents
        blog.generate_table_of_contents()
        
        # Set published date if publishing
        if blog.status == 'published':
            from datetime import datetime
            blog.published_at = datetime.utcnow()
        
        db.session.add(blog)
        db.session.commit()
        
        return jsonify({
            'message': 'Blog created successfully',
            'data': {
                'blog': blog.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Create blog route error: {str(e)}")
        return jsonify({
            'error': 'Blog creation failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/<int:blog_id>', methods=['GET'])
@require_auth
@require_store_access
def get_blog(blog_id):
    """Get specific blog post."""
    try:
        store_id = get_current_store_id()
        
        blog = Blog.query.filter_by(
            id=blog_id,
            store_id=store_id
        ).first()
        
        if not blog:
            return jsonify({
                'error': 'Blog not found',
                'message': 'The requested blog post was not found'
            }), 404
        
        return jsonify({
            'message': 'Blog retrieved successfully',
            'data': {
                'blog': blog.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get blog route error: {str(e)}")
        return jsonify({
            'error': 'Blog retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/<int:blog_id>', methods=['PUT'])
@require_auth
@require_store_access
def update_blog(blog_id):
    """Update blog post."""
    try:
        data = request.get_json()
        store_id = get_current_store_id()
        
        blog = Blog.query.filter_by(
            id=blog_id,
            store_id=store_id
        ).first()
        
        if not blog:
            return jsonify({
                'error': 'Blog not found',
                'message': 'The requested blog post was not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = [
            'title', 'content', 'excerpt', 'author_id', 'author_name',
            'featured_image', 'featured_image_alt', 'blog_category', 'tags',
            'status', 'is_featured', 'allow_comments', 'meta_title',
            'meta_description', 'meta_keywords', 'focus_keyword',
            'social_title', 'social_description', 'social_image',
            'related_products', 'related_posts', 'content_type',
            'language', 'custom_fields'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(blog, field, data[field])
        
        # Regenerate reading time if content changed
        if 'content' in data:
            blog.reading_time = blog.calculate_reading_time()
            blog.generate_table_of_contents()
        
        # Update published date if status changed to published
        if data.get('status') == 'published' and blog.status != 'published':
            from datetime import datetime
            blog.published_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Blog updated successfully',
            'data': {
                'blog': blog.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update blog route error: {str(e)}")
        return jsonify({
            'error': 'Blog update failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/<int:blog_id>', methods=['DELETE'])
@require_auth
@require_store_access
def delete_blog(blog_id):
    """Delete blog post."""
    try:
        store_id = get_current_store_id()
        
        blog = Blog.query.filter_by(
            id=blog_id,
            store_id=store_id
        ).first()
        
        if not blog:
            return jsonify({
                'error': 'Blog not found',
                'message': 'The requested blog post was not found'
            }), 404
        
        db.session.delete(blog)
        db.session.commit()
        
        return jsonify({
            'message': 'Blog deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete blog route error: {str(e)}")
        return jsonify({
            'error': 'Blog deletion failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/upload-image', methods=['POST'])
@require_auth
@require_store_access
def upload_blog_image():
    """Upload image for blog post."""
    try:
        store_id = get_current_store_id()
        
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please select a file to upload'
            }), 400
        
        file = request.files['file']
        
        result = FileUploadService.upload_blog_image(store_id, file)
        
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
        logging.error(f"Upload blog image route error: {str(e)}")
        return jsonify({
            'error': 'Image upload failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/featured', methods=['GET'])
@require_auth
@require_store_access
def get_featured_blogs():
    """Get featured blog posts."""
    try:
        store_id = get_current_store_id()
        limit = min(int(request.args.get('limit', 5)), 20)
        
        blogs = Blog.query.filter_by(
            store_id=store_id,
            status='published',
            is_featured=True
        ).order_by(Blog.published_at.desc()).limit(limit).all()
        
        return jsonify({
            'message': 'Featured blogs retrieved successfully',
            'data': {
                'blogs': [blog.to_dict() for blog in blogs]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get featured blogs route error: {str(e)}")
        return jsonify({
            'error': 'Featured blogs retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@blogs_bp.route('/categories', methods=['GET'])
@require_auth
@require_store_access
def get_blog_categories():
    """Get all blog categories."""
    try:
        store_id = get_current_store_id()
        
        from sqlalchemy import func
        categories = db.session.query(
            Blog.blog_category,
            func.count(Blog.id).label('count')
        ).filter_by(
            store_id=store_id,
            status='published'
        ).group_by(Blog.blog_category).all()
        
        category_data = [
            {
                'name': category,
                'count': count
            }
            for category, count in categories if category
        ]
        
        return jsonify({
            'message': 'Blog categories retrieved successfully',
            'data': {
                'categories': category_data
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get blog categories route error: {str(e)}")
        return jsonify({
            'error': 'Blog categories retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@blogs_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@blogs_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested blog post was not found'
    }), 404