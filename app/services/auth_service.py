from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.config.database import db
from app.models.admin_user import AdminUser
from app.middleware.auth_middleware import validate_password_strength, generate_secure_token
import logging

class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def login(email, password, store_id=None):
        """Authenticate user and return tokens."""
        try:
            # Find user by email
            user = AdminUser.get_by_email(email.lower())
            
            if not user:
                AuthService._log_failed_login(email, "User not found")
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }
            
            # Check if account is locked
            if user.is_locked:
                AuthService._log_failed_login(email, "Account locked")
                return {
                    'success': False,
                    'message': 'Account is locked. Please contact administrator.',
                    'code': 'ACCOUNT_LOCKED'
                }
            
            # Check if account is active
            if not user.is_active:
                AuthService._log_failed_login(email, "Account inactive")
                return {
                    'success': False,
                    'message': 'Account is disabled. Please contact administrator.',
                    'code': 'ACCOUNT_DISABLED'
                }
            
            # Verify password
            if not user.check_password(password):
                user.increment_failed_login()
                db.session.commit()
                
                AuthService._log_failed_login(email, "Invalid password")
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }
            
            # Check store access if specified
            if store_id and not user.can_access_store(store_id):
                AuthService._log_failed_login(email, f"No access to store {store_id}")
                return {
                    'success': False,
                    'message': 'You do not have access to this store',
                    'code': 'STORE_ACCESS_DENIED'
                }
            
            # Update login info
            user.update_last_login()
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(
                identity=user.user_id,
                expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            )
            
            refresh_token = create_refresh_token(
                identity=user.user_id,
                expires_delta=current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
            )
            
            # Log successful login
            logging.info(f"Successful login for user {user.email}")
            
            return {
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
                }
            }
            
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during login',
                'code': 'LOGIN_ERROR'
            }
    
    @staticmethod
    def register(email, password, first_name, last_name, store_id=None, role='store_admin'):
        """Register new admin user."""
        try:
            # Validate email uniqueness
            if AdminUser.get_by_email(email.lower()):
                return {
                    'success': False,
                    'message': 'An account with this email already exists',
                    'code': 'EMAIL_EXISTS'
                }
            
            # Validate password strength
            is_strong, message = validate_password_strength(password)
            if not is_strong:
                return {
                    'success': False,
                    'message': message,
                    'code': 'WEAK_PASSWORD'
                }
            
            # Create new user
            user = AdminUser(
                email=email.lower(),
                first_name=first_name,
                last_name=last_name,
                role=role,
                store_id=store_id,
                verification_token=generate_secure_token()
            )
            
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logging.info(f"New user registered: {user.email}")
            
            return {
                'success': True,
                'message': 'Account created successfully',
                'data': {
                    'user': user.to_dict(),
                    'verification_token': user.verification_token
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during registration',
                'code': 'REGISTRATION_ERROR'
            }
    
    @staticmethod
    def refresh_token(user_id):
        """Generate new access token from refresh token."""
        try:
            user = AdminUser.get_by_user_id(user_id)
            
            if not user or not user.is_active:
                return {
                    'success': False,
                    'message': 'Invalid user',
                    'code': 'INVALID_USER'
                }
            
            # Generate new access token
            access_token = create_access_token(
                identity=user.user_id,
                expires_delta=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            )
            
            return {
                'success': True,
                'message': 'Token refreshed successfully',
                'data': {
                    'access_token': access_token,
                    'token_type': 'Bearer',
                    'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
                }
            }
            
        except Exception as e:
            logging.error(f"Token refresh error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during token refresh',
                'code': 'TOKEN_REFRESH_ERROR'
            }
    
    @staticmethod
    def verify_email(verification_token):
        """Verify user email with token."""
        try:
            user = AdminUser.query.filter_by(verification_token=verification_token).first()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid verification token',
                    'code': 'INVALID_TOKEN'
                }
            
            user.is_verified = True
            user.verification_token = None
            db.session.commit()
            
            logging.info(f"Email verified for user: {user.email}")
            
            return {
                'success': True,
                'message': 'Email verified successfully',
                'data': {
                    'user': user.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Email verification error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during email verification',
                'code': 'VERIFICATION_ERROR'
            }
    
    @staticmethod
    def forgot_password(email):
        """Initiate password reset process."""
        try:
            user = AdminUser.get_by_email(email.lower())
            
            if not user:
                # Return success even if user doesn't exist for security
                return {
                    'success': True,
                    'message': 'If an account exists, a password reset email will be sent',
                    'code': 'RESET_EMAIL_SENT'
                }
            
            # Generate reset token
            reset_token = user.generate_reset_token()
            db.session.commit()
            
            # TODO: Send reset email
            # EmailService.send_password_reset_email(user.email, reset_token)
            
            logging.info(f"Password reset requested for: {user.email}")
            
            return {
                'success': True,
                'message': 'Password reset email sent',
                'data': {
                    'reset_token': reset_token  # Remove in production
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password reset error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during password reset',
                'code': 'RESET_ERROR'
            }
    
    @staticmethod
    def reset_password(reset_token, new_password):
        """Reset password with token."""
        try:
            user = AdminUser.query.filter_by(reset_token=reset_token).first()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid reset token',
                    'code': 'INVALID_TOKEN'
                }
            
            # Verify token hasn't expired
            if not user.verify_reset_token(reset_token):
                return {
                    'success': False,
                    'message': 'Reset token has expired',
                    'code': 'TOKEN_EXPIRED'
                }
            
            # Validate password strength
            is_strong, message = validate_password_strength(new_password)
            if not is_strong:
                return {
                    'success': False,
                    'message': message,
                    'code': 'WEAK_PASSWORD'
                }
            
            # Update password
            user.set_password(new_password)
            user.clear_reset_token()
            user.unlock_account()  # Unlock if locked
            db.session.commit()
            
            logging.info(f"Password reset completed for: {user.email}")
            
            return {
                'success': True,
                'message': 'Password reset successfully',
                'data': {
                    'user': user.to_public_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password reset completion error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during password reset',
                'code': 'RESET_COMPLETION_ERROR'
            }
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password."""
        try:
            user = AdminUser.get_by_user_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            # Verify current password
            if not user.check_password(current_password):
                return {
                    'success': False,
                    'message': 'Current password is incorrect',
                    'code': 'INVALID_CURRENT_PASSWORD'
                }
            
            # Validate new password strength
            is_strong, message = validate_password_strength(new_password)
            if not is_strong:
                return {
                    'success': False,
                    'message': message,
                    'code': 'WEAK_PASSWORD'
                }
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            logging.info(f"Password changed for user: {user.email}")
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password change error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during password change',
                'code': 'PASSWORD_CHANGE_ERROR'
            }
    
    @staticmethod
    def logout(user_id):
        """Handle user logout."""
        try:
            # In a real implementation, you might:
            # - Add token to blacklist
            # - Clear session data
            # - Log the logout event
            
            user = AdminUser.get_by_user_id(user_id)
            if user:
                logging.info(f"User logged out: {user.email}")
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
            
        except Exception as e:
            logging.error(f"Logout error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during logout',
                'code': 'LOGOUT_ERROR'
            }
    
    @staticmethod
    def get_profile(user_id):
        """Get user profile."""
        try:
            user = AdminUser.get_by_user_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            return {
                'success': True,
                'message': 'Profile retrieved successfully',
                'data': {
                    'user': user.to_dict()
                }
            }
            
        except Exception as e:
            logging.error(f"Get profile error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving profile',
                'code': 'PROFILE_ERROR'
            }
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile."""
        try:
            user = AdminUser.get_by_user_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'phone', 'avatar']
            
            for field in allowed_fields:
                if field in profile_data:
                    setattr(user, field, profile_data[field])
            
            db.session.commit()
            
            logging.info(f"Profile updated for user: {user.email}")
            
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'data': {
                    'user': user.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Profile update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating profile',
                'code': 'PROFILE_UPDATE_ERROR'
            }
    
    @staticmethod
    def _log_failed_login(email, reason):
        """Log failed login attempt."""
        logging.warning(f"Failed login attempt for {email}: {reason}")
        # In production, implement proper security logging