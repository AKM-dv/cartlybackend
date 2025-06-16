import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import logging

class FileUploadService:
    """Service for handling file uploads and management."""
    
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    
    @staticmethod
    def is_allowed_file(filename, file_type='image'):
        """Check if file extension is allowed."""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        if file_type == 'image':
            return extension in FileUploadService.ALLOWED_IMAGE_EXTENSIONS
        elif file_type == 'document':
            return extension in FileUploadService.ALLOWED_DOCUMENT_EXTENSIONS
        else:
            return extension in (FileUploadService.ALLOWED_IMAGE_EXTENSIONS | 
                               FileUploadService.ALLOWED_DOCUMENT_EXTENSIONS)
    
    @staticmethod
    def generate_filename(original_filename, prefix=""):
        """Generate unique filename."""
        if not original_filename or '.' not in original_filename:
            return None
        
        extension = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        if prefix:
            return f"{prefix}_{timestamp}_{unique_id}.{extension}"
        else:
            return f"{timestamp}_{unique_id}.{extension}"
    
    @staticmethod
    def get_upload_path(store_id, upload_type):
        """Get upload directory path for specific store and type."""
        base_path = current_app.config['UPLOAD_FOLDER']
        
        upload_paths = {
            'hero': 'hero_images',
            'product': 'product_images', 
            'blog': 'blog_images',
            'general': 'general'
        }
        
        upload_dir = upload_paths.get(upload_type, 'general')
        full_path = os.path.join(base_path, upload_dir, store_id)
        
        # Create directory if it doesn't exist
        os.makedirs(full_path, exist_ok=True)
        
        return full_path
    
    @staticmethod
    def upload_hero_image(store_id, file):
        """Upload hero section image."""
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    'success': False,
                    'message': 'No file provided',
                    'code': 'NO_FILE'
                }
            
            if not FileUploadService.is_allowed_file(file.filename, 'image'):
                return {
                    'success': False,
                    'message': 'Invalid file type. Only images are allowed.',
                    'code': 'INVALID_FILE_TYPE'
                }
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            if file_size > max_size:
                return {
                    'success': False,
                    'message': 'File size too large',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Generate filename and save
            filename = FileUploadService.generate_filename(file.filename, 'hero')
            upload_path = FileUploadService.get_upload_path(store_id, 'hero')
            file_path = os.path.join(upload_path, filename)
            
            # Save original file
            file.save(file_path)
            
            # Create optimized versions
            optimized_paths = FileUploadService._create_image_variants(file_path, store_id, 'hero')
            
            # Generate URLs
            base_url = '/uploads/hero_images'
            file_url = f"{base_url}/{store_id}/{filename}"
            
            return {
                'success': True,
                'message': 'Hero image uploaded successfully',
                'data': {
                    'url': file_url,
                    'filename': filename,
                    'original_size': file_size,
                    'variants': optimized_paths
                }
            }
            
        except Exception as e:
            logging.error(f"Hero image upload error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while uploading the image',
                'code': 'UPLOAD_ERROR'
            }
    
    @staticmethod
    def upload_product_image(store_id, file):
        """Upload product image."""
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    'success': False,
                    'message': 'No file provided',
                    'code': 'NO_FILE'
                }
            
            if not FileUploadService.is_allowed_file(file.filename, 'image'):
                return {
                    'success': False,
                    'message': 'Invalid file type. Only images are allowed.',
                    'code': 'INVALID_FILE_TYPE'
                }
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            if file_size > max_size:
                return {
                    'success': False,
                    'message': 'File size too large',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Generate filename and save
            filename = FileUploadService.generate_filename(file.filename, 'product')
            upload_path = FileUploadService.get_upload_path(store_id, 'product')
            file_path = os.path.join(upload_path, filename)
            
            # Save original file
            file.save(file_path)
            
            # Create optimized versions
            optimized_paths = FileUploadService._create_image_variants(file_path, store_id, 'product')
            
            # Generate URLs
            base_url = '/uploads/product_images'
            file_url = f"{base_url}/{store_id}/{filename}"
            
            return {
                'success': True,
                'message': 'Product image uploaded successfully',
                'data': {
                    'url': file_url,
                    'filename': filename,
                    'original_size': file_size,
                    'variants': optimized_paths
                }
            }
            
        except Exception as e:
            logging.error(f"Product image upload error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while uploading the image',
                'code': 'UPLOAD_ERROR'
            }
    
    @staticmethod
    def upload_blog_image(store_id, file):
        """Upload blog image."""
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    'success': False,
                    'message': 'No file provided',
                    'code': 'NO_FILE'
                }
            
            if not FileUploadService.is_allowed_file(file.filename, 'image'):
                return {
                    'success': False,
                    'message': 'Invalid file type. Only images are allowed.',
                    'code': 'INVALID_FILE_TYPE'
                }
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
            if file_size > max_size:
                return {
                    'success': False,
                    'message': 'File size too large',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Generate filename and save
            filename = FileUploadService.generate_filename(file.filename, 'blog')
            upload_path = FileUploadService.get_upload_path(store_id, 'blog')
            file_path = os.path.join(upload_path, filename)
            
            # Save original file
            file.save(file_path)
            
            # Create optimized versions
            optimized_paths = FileUploadService._create_image_variants(file_path, store_id, 'blog')
            
            # Generate URLs
            base_url = '/uploads/blog_images'
            file_url = f"{base_url}/{store_id}/{filename}"
            
            return {
                'success': True,
                'message': 'Blog image uploaded successfully',
                'data': {
                    'url': file_url,
                    'filename': filename,
                    'original_size': file_size,
                    'variants': optimized_paths
                }
            }
            
        except Exception as e:
            logging.error(f"Blog image upload error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while uploading the image',
                'code': 'UPLOAD_ERROR'
            }
    
    @staticmethod
    def delete_file(store_id, file_path, upload_type):
        """Delete uploaded file and its variants."""
        try:
            upload_dir = FileUploadService.get_upload_path(store_id, upload_type)
            full_path = os.path.join(upload_dir, file_path)
            
            # Delete original file
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # Delete variants
            base_name = os.path.splitext(file_path)[0]
            extension = os.path.splitext(file_path)[1]
            
            variants = ['_thumb', '_medium', '_large']
            for variant in variants:
                variant_path = os.path.join(upload_dir, f"{base_name}{variant}{extension}")
                if os.path.exists(variant_path):
                    os.remove(variant_path)
            
            return {
                'success': True,
                'message': 'File deleted successfully'
            }
            
        except Exception as e:
            logging.error(f"File deletion error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while deleting the file',
                'code': 'DELETE_ERROR'
            }
    
    @staticmethod
    def _create_image_variants(original_path, store_id, upload_type):
        """Create optimized image variants (thumbnail, medium, large)."""
        try:
            variants = {}
            
            # Open original image
            with Image.open(original_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Define sizes
                sizes = {
                    'thumb': (150, 150),
                    'medium': (400, 400),
                    'large': (800, 800)
                }
                
                base_name = os.path.splitext(os.path.basename(original_path))[0]
                extension = os.path.splitext(original_path)[1]
                upload_dir = FileUploadService.get_upload_path(store_id, upload_type)
                
                for variant_name, size in sizes.items():
                    # Create resized image
                    resized_img = img.copy()
                    resized_img.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Save variant
                    variant_filename = f"{base_name}_{variant_name}{extension}"
                    variant_path = os.path.join(upload_dir, variant_filename)
                    resized_img.save(variant_path, optimize=True, quality=85)
                    
                    # Generate URL
                    base_url = f'/uploads/{upload_type}_images'
                    variant_url = f"{base_url}/{store_id}/{variant_filename}"
                    variants[variant_name] = variant_url
            
            return variants
            
        except Exception as e:
            logging.error(f"Create image variants error: {str(e)}")
            return {}
    
    @staticmethod
    def get_file_info(store_id, filename, upload_type):
        """Get file information."""
        try:
            upload_path = FileUploadService.get_upload_path(store_id, upload_type)
            file_path = os.path.join(upload_path, filename)
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': 'File not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            # Get file stats
            stat = os.stat(file_path)
            
            file_info = {
                'filename': filename,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': upload_type
            }
            
            # Add image-specific info
            if FileUploadService.is_allowed_file(filename, 'image'):
                try:
                    with Image.open(file_path) as img:
                        file_info.update({
                            'width': img.width,
                            'height': img.height,
                            'format': img.format
                        })
                except Exception:
                    pass
            
            return {
                'success': True,
                'message': 'File information retrieved successfully',
                'data': file_info
            }
            
        except Exception as e:
            logging.error(f"Get file info error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving file information',
                'code': 'FILE_INFO_ERROR'
            }
    
    @staticmethod
    def list_files(store_id, upload_type, page=1, per_page=20):
        """List uploaded files for a store."""
        try:
            upload_path = FileUploadService.get_upload_path(store_id, upload_type)
            
            if not os.path.exists(upload_path):
                return {
                    'success': True,
                    'message': 'No files found',
                    'data': {
                        'files': [],
                        'pagination': {
                            'page': page,
                            'per_page': per_page,
                            'total': 0,
                            'pages': 0
                        }
                    }
                }
            
            # Get all files
            all_files = []
            for filename in os.listdir(upload_path):
                file_path = os.path.join(upload_path, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    # Skip variant files
                    if not any(variant in filename for variant in ['_thumb', '_medium', '_large']):
                        all_files.append(filename)
            
            # Sort by modification time (newest first)
            all_files.sort(key=lambda f: os.path.getmtime(os.path.join(upload_path, f)), reverse=True)
            
            # Pagination
            total = len(all_files)
            start = (page - 1) * per_page
            end = start + per_page
            files = all_files[start:end]
            
            # Get file info for each file
            file_list = []
            for filename in files:
                info_result = FileUploadService.get_file_info(store_id, filename, upload_type)
                if info_result['success']:
                    file_info = info_result['data']
                    # Add URL
                    base_url = f'/uploads/{upload_type}_images'
                    file_info['url'] = f"{base_url}/{store_id}/{filename}"
                    file_list.append(file_info)
            
            return {
                'success': True,
                'message': 'Files retrieved successfully',
                'data': {
                    'files': file_list,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"List files error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while listing files',
                'code': 'LIST_FILES_ERROR'
            }
    
    @staticmethod
    def cleanup_old_files(store_id, upload_type, days_old=30):
        """Clean up old uploaded files."""
        try:
            upload_path = FileUploadService.get_upload_path(store_id, upload_type)
            
            if not os.path.exists(upload_path):
                return {
                    'success': True,
                    'message': 'No files to clean up',
                    'data': {'deleted_count': 0}
                }
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(upload_path):
                file_path = os.path.join(upload_path, filename)
                
                if os.path.isfile(file_path):
                    # Check if file is older than cutoff
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            logging.warning(f"Failed to delete old file {filename}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Cleanup completed. Deleted {deleted_count} old files.',
                'data': {'deleted_count': deleted_count}
            }
            
        except Exception as e:
            logging.error(f"File cleanup error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during file cleanup',
                'code': 'CLEANUP_ERROR'
            }