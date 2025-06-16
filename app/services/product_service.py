from datetime import datetime
from app.config.database import db
from app.models.product import Product
from app.models.category import Category
from app.services.file_upload_service import FileUploadService
import logging

class ProductService:
    """Service for handling product operations."""
    
    @staticmethod
    def create_product(store_id, product_data):
        """Create new product with validation."""
        try:
            # Validate required fields
            required_fields = ['name', 'price']
            for field in required_fields:
                if not product_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }
            
            # Validate price
            try:
                price = float(product_data['price'])
                if price < 0:
                    return {
                        'success': False,
                        'message': 'Price must be positive',
                        'code': 'INVALID_PRICE'
                    }
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'message': 'Invalid price format',
                    'code': 'INVALID_PRICE'
                }
            
            # Validate category if provided
            if product_data.get('category_id'):
                category = Category.query.filter_by(
                    id=product_data['category_id'],
                    store_id=store_id
                ).first()
                
                if not category:
                    return {
                        'success': False,
                        'message': 'Invalid category',
                        'code': 'INVALID_CATEGORY'
                    }
            
            # Check SKU uniqueness if provided
            if product_data.get('sku'):
                existing_product = Product.get_by_sku(store_id, product_data['sku'])
                if existing_product:
                    return {
                        'success': False,
                        'message': 'SKU already exists',
                        'code': 'SKU_EXISTS'
                    }
            
            # Create product
            product = Product(
                store_id=store_id,
                name=product_data['name'],
                description=product_data.get('description'),
                short_description=product_data.get('short_description'),
                price=price,
                compare_price=product_data.get('compare_price'),
                cost_price=product_data.get('cost_price'),
                sku=product_data.get('sku'),
                barcode=product_data.get('barcode'),
                category_id=product_data.get('category_id'),
                brand=product_data.get('brand'),
                tags=product_data.get('tags', []),
                specifications=product_data.get('specifications', {}),
                features=product_data.get('features', []),
                weight=product_data.get('weight'),
                length=product_data.get('length'),
                width=product_data.get('width'),
                height=product_data.get('height'),
                track_inventory=product_data.get('track_inventory', True),
                inventory_quantity=product_data.get('inventory_quantity', 0),
                low_stock_threshold=product_data.get('low_stock_threshold', 5),
                allow_backorders=product_data.get('allow_backorders', False),
                is_featured=product_data.get('is_featured', False),
                is_digital=product_data.get('is_digital', False),
                requires_shipping=product_data.get('requires_shipping', True),
                tax_class=product_data.get('tax_class', 'standard'),
                meta_title=product_data.get('meta_title'),
                meta_description=product_data.get('meta_description'),
                meta_keywords=product_data.get('meta_keywords'),
                status=product_data.get('status', 'draft')
            )
            
            db.session.add(product)
            db.session.commit()
            
            logging.info(f"Product created: {product.name} ({product.id}) for store {store_id}")
            
            return {
                'success': True,
                'message': 'Product created successfully',
                'data': {
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Product creation error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating the product',
                'code': 'PRODUCT_CREATE_ERROR'
            }
    
    @staticmethod
    def get_product(store_id, product_id):
        """Get product by ID."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            return {
                'success': True,
                'message': 'Product retrieved successfully',
                'data': {
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            logging.error(f"Get product error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving the product',
                'code': 'PRODUCT_GET_ERROR'
            }
    
    @staticmethod
    def update_product(store_id, product_id, update_data):
        """Update product."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            # Validate price if provided
            if 'price' in update_data:
                try:
                    price = float(update_data['price'])
                    if price < 0:
                        return {
                            'success': False,
                            'message': 'Price must be positive',
                            'code': 'INVALID_PRICE'
                        }
                except (ValueError, TypeError):
                    return {
                        'success': False,
                        'message': 'Invalid price format',
                        'code': 'INVALID_PRICE'
                    }
            
            # Validate category if provided
            if 'category_id' in update_data and update_data['category_id']:
                category = Category.query.filter_by(
                    id=update_data['category_id'],
                    store_id=store_id
                ).first()
                
                if not category:
                    return {
                        'success': False,
                        'message': 'Invalid category',
                        'code': 'INVALID_CATEGORY'
                    }
            
            # Check SKU uniqueness if being updated
            if 'sku' in update_data and update_data['sku'] != product.sku:
                existing_product = Product.get_by_sku(store_id, update_data['sku'])
                if existing_product:
                    return {
                        'success': False,
                        'message': 'SKU already exists',
                        'code': 'SKU_EXISTS'
                    }
            
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
                if field in update_data:
                    setattr(product, field, update_data[field])
            
            db.session.commit()
            
            logging.info(f"Product updated: {product.name} ({product.id})")
            
            return {
                'success': True,
                'message': 'Product updated successfully',
                'data': {
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Product update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating the product',
                'code': 'PRODUCT_UPDATE_ERROR'
            }
    
    @staticmethod
    def delete_product(store_id, product_id):
        """Delete product."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            # Check if product has orders (optional - you might want to prevent deletion)
            # This would require Order model relationship
            
            db.session.delete(product)
            db.session.commit()
            
            logging.info(f"Product deleted: {product.name} ({product.id})")
            
            return {
                'success': True,
                'message': 'Product deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Product deletion error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while deleting the product',
                'code': 'PRODUCT_DELETE_ERROR'
            }
    
    @staticmethod
    def update_inventory(store_id, product_id, quantity_change, variant_id=None):
        """Update product inventory."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            if not product.track_inventory:
                return {
                    'success': False,
                    'message': 'Inventory tracking is disabled for this product',
                    'code': 'INVENTORY_NOT_TRACKED'
                }
            
            success = product.update_inventory(quantity_change, variant_id)
            
            if not success:
                return {
                    'success': False,
                    'message': 'Failed to update inventory',
                    'code': 'INVENTORY_UPDATE_FAILED'
                }
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Inventory updated successfully',
                'data': {
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Inventory update error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while updating inventory',
                'code': 'INVENTORY_UPDATE_ERROR'
            }
    
    @staticmethod
    def add_product_image(store_id, product_id, image_data):
        """Add image to product."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            # Upload image if file provided
            if 'file' in image_data:
                upload_result = FileUploadService.upload_product_image(
                    store_id, 
                    image_data['file']
                )
                
                if not upload_result['success']:
                    return upload_result
                
                image_url = upload_result['data']['url']
            else:
                image_url = image_data.get('image_url')
            
            if not image_url:
                return {
                    'success': False,
                    'message': 'Image URL or file is required',
                    'code': 'IMAGE_REQUIRED'
                }
            
            product.add_image(
                image_url=image_url,
                alt_text=image_data.get('alt_text', ''),
                is_featured=image_data.get('is_featured', False)
            )
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Image added successfully',
                'data': {
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Add product image error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while adding the image',
                'code': 'IMAGE_ADD_ERROR'
            }
    
    @staticmethod
    def add_product_variant(store_id, product_id, variant_data):
        """Add variant to product."""
        try:
            product = Product.query.filter_by(
                id=product_id,
                store_id=store_id
            ).first()
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found',
                    'code': 'PRODUCT_NOT_FOUND'
                }
            
            # Validate required fields
            required_fields = ['sku', 'options']
            for field in required_fields:
                if not variant_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required for variant',
                        'code': 'MISSING_REQUIRED_FIELD'
                    }
            
            # Check SKU uniqueness across all products
            existing_product = Product.get_by_sku(store_id, variant_data['sku'])
            if existing_product:
                return {
                    'success': False,
                    'message': 'Variant SKU already exists',
                    'code': 'SKU_EXISTS'
                }
            
            variant_id = product.add_variant({
                'sku': variant_data['sku'],
                'options': variant_data['options'],
                'price': variant_data.get('price', product.price),
                'inventory': variant_data.get('inventory', 0),
                'image': variant_data.get('image')
            })
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Variant added successfully',
                'data': {
                    'variant_id': variant_id,
                    'product': product.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Add product variant error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while adding the variant',
                'code': 'VARIANT_ADD_ERROR'
            }
    
    @staticmethod
    def bulk_update_products(store_id, updates):
        """Bulk update multiple products."""
        try:
            updated_products = []
            
            for update in updates:
                product_id = update.get('product_id')
                if not product_id:
                    continue
                
                product = Product.query.filter_by(
                    id=product_id,
                    store_id=store_id
                ).first()
                
                if not product:
                    continue
                
                # Update allowed fields
                allowed_fields = ['price', 'inventory_quantity', 'status', 'is_featured']
                
                for field in allowed_fields:
                    if field in update:
                        setattr(product, field, update[field])
                
                updated_products.append(product)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully updated {len(updated_products)} products',
                'data': {
                    'updated_count': len(updated_products),
                    'products': [p.to_dict() for p in updated_products]
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Bulk update products error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during bulk update',
                'code': 'BULK_UPDATE_ERROR'
            }
    
    @staticmethod
    def get_product_analytics(store_id, product_id=None, date_range=None):
        """Get product analytics."""
        try:
            analytics_data = {
                'products': {},
                'summary': {
                    'total_products': 0,
                    'active_products': 0,
                    'low_stock_products': 0,
                    'out_of_stock_products': 0
                }
            }
            
            # Get product counts
            if product_id:
                products = Product.query.filter_by(id=product_id, store_id=store_id).all()
            else:
                products = Product.query.filter_by(store_id=store_id).all()
            
            analytics_data['summary']['total_products'] = len(products)
            analytics_data['summary']['active_products'] = len([p for p in products if p.status == 'active'])
            
            # Get low stock and out of stock counts
            low_stock = Product.get_low_stock_products(store_id)
            out_of_stock = Product.get_out_of_stock_products(store_id)
            
            analytics_data['summary']['low_stock_products'] = len(low_stock)
            analytics_data['summary']['out_of_stock_products'] = len(out_of_stock)
            
            # TODO: Add sales analytics when Order model is available
            # - Top selling products
            # - Revenue by product
            # - Conversion rates
            
            return {
                'success': True,
                'message': 'Product analytics retrieved successfully',
                'data': analytics_data
            }
            
        except Exception as e:
            logging.error(f"Product analytics error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while retrieving analytics',
                'code': 'ANALYTICS_ERROR'
            }
    
    @staticmethod
    def import_products(store_id, products_data):
        """Import products from data array."""
        try:
            imported_products = []
            errors = []
            
            for i, product_data in enumerate(products_data):
                try:
                    result = ProductService.create_product(store_id, product_data)
                    
                    if result['success']:
                        imported_products.append(result['data']['product'])
                    else:
                        errors.append({
                            'row': i + 1,
                            'error': result['message'],
                            'code': result.get('code')
                        })
                        
                except Exception as e:
                    errors.append({
                        'row': i + 1,
                        'error': str(e),
                        'code': 'IMPORT_ROW_ERROR'
                    })
            
            return {
                'success': True,
                'message': f'Import completed. {len(imported_products)} products imported, {len(errors)} errors',
                'data': {
                    'imported_count': len(imported_products),
                    'error_count': len(errors),
                    'products': imported_products,
                    'errors': errors
                }
            }
            
        except Exception as e:
            logging.error(f"Product import error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during product import',
                'code': 'IMPORT_ERROR'
            }