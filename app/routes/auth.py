from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.services.auth_service import AuthService
from app.middleware import (
    require_auth, 
    get_current_user, 
    get_current_store_id,
    rate_limit,
    log_security_event
)
from app.utils.validators import validate_email, validate_required_fields
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=5, window=300)  # 5 attempts per 5 minutes
def login():
    """Authenticate user and return JWT tokens."""
    try:
        data = request.get_json()
        
        # Validate required fields
        validation_result = validate_required_fields(data, ['email', 'password'])
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Get store context if provided
        store_id = get_current_store_id() or data.get('store_id')
        
        # Attempt login
        result = AuthService.login(
            email=data['email'],
            password=data['password'],
            store_id=store_id
        )
        
        if result['success']:
            # Log successful login
            log_security_event('login_success', {
                'email': data['email'],
                'store_id': store_id
            })
            
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            # Log failed login
            log_security_event('login_failed', {
                'email': data['email'],
                'reason': result.get('code'),
                'store_id': store_id
            })
            
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 401
            
    except Exception as e:
        logging.error(f"Login route error: {str(e)}")
        return jsonify({
            'error': 'Login failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/register', methods=['POST'])
@rate_limit(max_requests=3, window=600)  # 3 attempts per 10 minutes
def register():
    """Register new admin user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        # Get store context
        store_id = get_current_store_id() or data.get('store_id')
        
        # Attempt registration
        result = AuthService.register(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            store_id=store_id,
            role=data.get('role', 'store_admin')
        )
        
        if result['success']:
            # Log successful registration
            log_security_event('registration_success', {
                'email': data['email'],
                'store_id': store_id
            })
            
            return jsonify({
                'message': result['message'],
                'data': {
                    'user': result['data']['user']
                    # Don't return verification token in production
                }
            }), 201
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
            
    except Exception as e:
        logging.error(f"Registration route error: {str(e)}")
        return jsonify({
            'error': 'Registration failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    try:
        current_user_id = get_jwt_identity()
        
        result = AuthService.refresh_token(current_user_id)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 401
            
    except Exception as e:
        logging.error(f"Token refresh route error: {str(e)}")
        return jsonify({
            'error': 'Token refresh failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with verification token."""
    try:
        data = request.get_json()
        
        if not data.get('token'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Verification token is required'
            }), 400
        
        result = AuthService.verify_email(data['token'])
        
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
        logging.error(f"Email verification route error: {str(e)}")
        return jsonify({
            'error': 'Email verification failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit(max_requests=3, window=600)  # 3 attempts per 10 minutes
def forgot_password():
    """Initiate password reset process."""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'error': 'Validation failed',
                'message': 'Email is required'
            }), 400
        
        if not validate_email(data['email']):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400
        
        result = AuthService.forgot_password(data['email'])
        
        # Always return success for security (don't reveal if email exists)
        return jsonify({
            'message': 'If an account exists, a password reset email will be sent'
        }), 200
        
    except Exception as e:
        logging.error(f"Forgot password route error: {str(e)}")
        return jsonify({
            'error': 'Password reset failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with reset token."""
    try:
        data = request.get_json()
        
        # Validate required fields
        validation_result = validate_required_fields(data, ['token', 'password'])
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        result = AuthService.reset_password(
            reset_token=data['token'],
            new_password=data['password']
        )
        
        if result['success']:
            # Log password reset
            log_security_event('password_reset_success', {
                'user_data': result['data']['user']
            })
            
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
        logging.error(f"Reset password route error: {str(e)}")
        return jsonify({
            'error': 'Password reset failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        
        # Validate required fields
        validation_result = validate_required_fields(data, ['current_password', 'new_password'])
        if not validation_result['valid']:
            return jsonify({
                'error': 'Validation failed',
                'message': validation_result['message']
            }), 400
        
        current_user = get_current_user()
        
        result = AuthService.change_password(
            user_id=current_user.user_id,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if result['success']:
            # Log password change
            log_security_event('password_change_success', {
                'user_id': current_user.user_id
            })
            
            return jsonify({
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
            
    except Exception as e:
        logging.error(f"Change password route error: {str(e)}")
        return jsonify({
            'error': 'Password change failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user."""
    try:
        current_user = get_current_user()
        
        result = AuthService.logout(current_user.user_id)
        
        if result['success']:
            # Log logout
            log_security_event('logout_success', {
                'user_id': current_user.user_id
            })
            
            return jsonify({
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'error': result['message'],
                'code': result.get('code')
            }), 400
            
    except Exception as e:
        logging.error(f"Logout route error: {str(e)}")
        return jsonify({
            'error': 'Logout failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile."""
    try:
        current_user = get_current_user()
        
        result = AuthService.get_profile(current_user.user_id)
        
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
        logging.error(f"Get profile route error: {str(e)}")
        return jsonify({
            'error': 'Profile retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update current user profile."""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        result = AuthService.update_profile(
            user_id=current_user.user_id,
            profile_data=data
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
        logging.error(f"Update profile route error: {str(e)}")
        return jsonify({
            'error': 'Profile update failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information."""
    try:
        current_user = get_current_user()
        store_id = get_current_store_id()
        
        user_data = current_user.to_dict()
        
        # Add store context if available
        if store_id:
            from app.models.store import Store
            store = Store.get_by_store_id(store_id)
            if store:
                user_data['current_store'] = {
                    'store_id': store.store_id,
                    'store_name': store.store_name,
                    'domain': store.domain
                }
        
        return jsonify({
            'message': 'User information retrieved successfully',
            'data': {
                'user': user_data
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get current user route error: {str(e)}")
        return jsonify({
            'error': 'User information retrieval failed',
            'message': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/check-token', methods=['POST'])
@require_auth
def check_token():
    """Check if current token is valid."""
    try:
        current_user = get_current_user()
        
        return jsonify({
            'message': 'Token is valid',
            'data': {
                'valid': True,
                'user': current_user.to_public_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Check token route error: {str(e)}")
        return jsonify({
            'error': 'Token validation failed',
            'message': 'An unexpected error occurred'
        }), 500

# Error handlers for this blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request data is invalid'
    }), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication is required'
    }), 401

@auth_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many authentication attempts. Please try again later.'
    }), 429