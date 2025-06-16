from flask import current_app, render_template_string
from flask_mail import Mail, Message
from app.models.store import Store
from app.models.store_settings import StoreSettings
from app.models.contact_details import ContactDetails
import logging

mail = Mail()

class EmailService:
    """Service for handling email operations."""
    
    @staticmethod
    def init_app(app):
        """Initialize email service with Flask app."""
        mail.init_app(app)
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email."""
        try:
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            settings = StoreSettings.get_by_store_id(order.store_id)
            if not settings or not settings.order_confirmation_email:
                return False
            
            contact = ContactDetails.get_by_store_id(order.store_id)
            
            # Email content
            subject = f"Order Confirmation - {order.order_number}"
            
            html_content = EmailService._get_order_confirmation_template(order, store, contact)
            
            # Send email
            return EmailService._send_email(
                to=order.customer_email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send order confirmation error: {str(e)}")
            return False
    
    @staticmethod
    def send_order_status_update(order, old_status, new_status):
        """Send order status update email."""
        try:
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            settings = StoreSettings.get_by_store_id(order.store_id)
            if not settings:
                return False
            
            # Only send for certain status changes
            if new_status not in ['shipped', 'delivered']:
                return False
            
            if new_status == 'shipped' and not settings.order_shipped_email:
                return False
            
            contact = ContactDetails.get_by_store_id(order.store_id)
            
            # Email content
            subject = f"Order Update - {order.order_number}"
            
            html_content = EmailService._get_order_status_template(
                order, store, contact, old_status, new_status
            )
            
            # Send email
            return EmailService._send_email(
                to=order.customer_email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send order status update error: {str(e)}")
            return False
    
    @staticmethod
    def send_tracking_info(order):
        """Send tracking information email."""
        try:
            if not order.tracking_number:
                return False
            
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            contact = ContactDetails.get_by_store_id(order.store_id)
            
            # Email content
            subject = f"Your Order is on the Way - {order.order_number}"
            
            html_content = EmailService._get_tracking_info_template(order, store, contact)
            
            # Send email
            return EmailService._send_email(
                to=order.customer_email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send tracking info error: {str(e)}")
            return False
    
    @staticmethod
    def send_order_cancellation(order, reason=None):
        """Send order cancellation email."""
        try:
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            contact = ContactDetails.get_by_store_id(order.store_id)
            
            # Email content
            subject = f"Order Cancelled - {order.order_number}"
            
            html_content = EmailService._get_order_cancellation_template(
                order, store, contact, reason
            )
            
            # Send email
            return EmailService._send_email(
                to=order.customer_email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send order cancellation error: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(email, reset_token):
        """Send password reset email."""
        try:
            # Email content
            subject = "Password Reset Request"
            
            html_content = EmailService._get_password_reset_template(reset_token)
            
            # Send email
            return EmailService._send_email(
                to=email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logging.error(f"Send password reset error: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user, store=None):
        """Send welcome email to new user."""
        try:
            # Email content
            subject = "Welcome to the Admin Panel"
            
            html_content = EmailService._get_welcome_template(user, store)
            
            # Send email
            return EmailService._send_email(
                to=user.email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send welcome email error: {str(e)}")
            return False
    
    @staticmethod
    def send_low_stock_alert(store_id, low_stock_products):
        """Send low stock alert to store admins."""
        try:
            store = Store.get_by_store_id(store_id)
            if not store:
                return False
            
            settings = StoreSettings.get_by_store_id(store_id)
            if not settings or not settings.low_stock_email:
                return False
            
            # Get store admins
            from app.models.admin_user import AdminUser
            admins = AdminUser.get_store_admins(store_id)
            
            if not admins:
                return False
            
            # Email content
            subject = f"Low Stock Alert - {store.store_name}"
            
            html_content = EmailService._get_low_stock_template(
                store, low_stock_products
            )
            
            # Send to all admins
            success_count = 0
            for admin in admins:
                if EmailService._send_email(
                    to=admin.email,
                    subject=subject,
                    html_content=html_content,
                    store=store
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Send low stock alert error: {str(e)}")
            return False
    
    @staticmethod
    def send_new_order_notification(order):
        """Send new order notification to store admins."""
        try:
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            settings = StoreSettings.get_by_store_id(order.store_id)
            if not settings or not settings.admin_email_notifications:
                return False
            
            # Get store admins
            from app.models.admin_user import AdminUser
            admins = AdminUser.get_store_admins(order.store_id)
            
            if not admins:
                return False
            
            # Email content
            subject = f"New Order Received - {order.order_number}"
            
            html_content = EmailService._get_new_order_notification_template(order, store)
            
            # Send to all admins
            success_count = 0
            for admin in admins:
                if EmailService._send_email(
                    to=admin.email,
                    subject=subject,
                    html_content=html_content,
                    store=store
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Send new order notification error: {str(e)}")
            return False
    
    @staticmethod
    def send_email_verification(user, verification_token):
        """Send email verification to new user."""
        try:
            subject = "Verify Your Email Address"
            
            html_content = EmailService._get_email_verification_template(user, verification_token)
            
            return EmailService._send_email(
                to=user.email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logging.error(f"Send email verification error: {str(e)}")
            return False
    
    @staticmethod
    def send_store_setup_complete(store, owner):
        """Send store setup completion notification."""
        try:
            subject = f"Store Setup Complete - {store.store_name}"
            
            html_content = EmailService._get_store_setup_template(store, owner)
            
            return EmailService._send_email(
                to=owner.email,
                subject=subject,
                html_content=html_content,
                store=store
            )
            
        except Exception as e:
            logging.error(f"Send store setup complete error: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_expiry_warning(store, days_left):
        """Send subscription expiry warning."""
        try:
            from app.models.admin_user import AdminUser
            
            admins = AdminUser.get_store_admins(store.store_id)
            if not admins:
                return False
            
            subject = f"Subscription Expiring Soon - {store.store_name}"
            
            html_content = EmailService._get_subscription_warning_template(store, days_left)
            
            success_count = 0
            for admin in admins:
                if EmailService._send_email(
                    to=admin.email,
                    subject=subject,
                    html_content=html_content,
                    store=store
                ):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Send subscription expiry warning error: {str(e)}")
            return False
    
    @staticmethod
    def send_security_alert(user, event_type, details):
        """Send security alert email."""
        try:
            subject = "Security Alert - Unusual Activity Detected"
            
            html_content = EmailService._get_security_alert_template(user, event_type, details)
            
            return EmailService._send_email(
                to=user.email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logging.error(f"Send security alert error: {str(e)}")
            return False
    
    @staticmethod
    def send_bulk_email(store_id, recipients, subject, content, email_type='newsletter'):
        """Send bulk email to multiple recipients."""
        try:
            store = Store.get_by_store_id(store_id)
            if not store:
                return {
                    'success': False,
                    'message': 'Store not found'
                }
            
            sent_count = 0
            failed_count = 0
            
            for recipient in recipients:
                try:
                    html_content = EmailService._get_bulk_email_template(
                        content, store, email_type
                    )
                    
                    if EmailService._send_email(
                        to=recipient,
                        subject=subject,
                        html_content=html_content,
                        store=store
                    ):
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logging.error(f"Bulk email send error for {recipient}: {str(e)}")
                    failed_count += 1
            
            return {
                'success': True,
                'message': f'Bulk email completed. Sent: {sent_count}, Failed: {failed_count}',
                'data': {
                    'sent_count': sent_count,
                    'failed_count': failed_count,
                    'total_recipients': len(recipients)
                }
            }
            
        except Exception as e:
            logging.error(f"Bulk email error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while sending bulk email'
            }
    
    @staticmethod
    def send_invoice_email(order, invoice_pdf=None):
        """Send invoice email with PDF attachment."""
        try:
            store = Store.get_by_store_id(order.store_id)
            if not store:
                return False
            
            contact = ContactDetails.get_by_store_id(order.store_id)
            
            subject = f"Invoice - {order.order_number}"
            
            html_content = EmailService._get_invoice_template(order, store, contact)
            
            # Create message with attachment
            msg = EmailService._create_message_with_attachment(
                to=order.customer_email,
                subject=subject,
                html_content=html_content,
                attachment_data=invoice_pdf,
                attachment_filename=f"invoice_{order.order_number}.pdf",
                store=store
            )
            
            if msg:
                mail.send(msg)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Send invoice email error: {str(e)}")
            return False
    
    @staticmethod
    def _send_email(to, subject, html_content, store=None):
        """Send email using Flask-Mail."""
        try:
            # Determine sender
            if store:
                contact = ContactDetails.get_by_store_id(store.store_id)
                sender = contact.primary_email if contact else current_app.config['MAIL_DEFAULT_SENDER']
            else:
                sender = current_app.config['MAIL_DEFAULT_SENDER']
            
            # Create message
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[to],
                html=html_content
            )
            
            # Send email
            mail.send(msg)
            
            logging.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logging.error(f"Send email error: {str(e)}")
            return False
    
    @staticmethod
    def _create_message_with_attachment(to, subject, html_content, attachment_data=None, 
                                      attachment_filename=None, store=None):
        """Create email message with optional attachment."""
        try:
            # Determine sender
            if store:
                contact = ContactDetails.get_by_store_id(store.store_id)
                sender = contact.primary_email if contact else current_app.config['MAIL_DEFAULT_SENDER']
            else:
                sender = current_app.config['MAIL_DEFAULT_SENDER']
            
            # Create message
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[to],
                html=html_content
            )
            
            # Add attachment if provided
            if attachment_data and attachment_filename:
                msg.attach(
                    attachment_filename,
                    "application/pdf",
                    attachment_data
                )
            
            return msg
            
        except Exception as e:
            logging.error(f"Create message with attachment error: {str(e)}")
            return None
    
    # Template methods
    @staticmethod
    def _get_order_confirmation_template(order, store, contact):
        """Get order confirmation email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Order Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #28a745;">Order Confirmation</h1>
                
                <p>Dear {{ order.customer_name }},</p>
                
                <p>Thank you for your order! We've received your order and will process it shortly.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Order Details</h3>
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>Order Date:</strong> {{ order.created_at.strftime('%B %d, %Y') }}</p>
                    <p><strong>Total Amount:</strong> ${{ "%.2f"|format(order.total_amount) }}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Order Items</h3>
                    {% for item in order.order_items %}
                    <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                        <p><strong>{{ item.product_name }}</strong></p>
                        <p>Quantity: {{ item.quantity }} × ${{ "%.2f"|format(item.unit_price) }} = ${{ "%.2f"|format(item.total_price) }}</p>
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Billing Address</h3>
                    <p>
                        {{ order.billing_address.first_name }} {{ order.billing_address.last_name }}<br>
                        {{ order.billing_address.address_line_1 }}<br>
                        {% if order.billing_address.address_line_2 %}{{ order.billing_address.address_line_2 }}<br>{% endif %}
                        {{ order.billing_address.city }}, {{ order.billing_address.state }} {{ order.billing_address.postal_code }}<br>
                        {{ order.billing_address.country }}
                    </p>
                </div>
                
                <p>If you have any questions, please contact us at {{ contact.primary_email if contact else store.owner_email }}.</p>
                
                <p>Thank you for shopping with {{ store.store_name }}!</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, order=order, store=store, contact=contact)
    
    @staticmethod
    def _get_order_status_template(order, store, contact, old_status, new_status):
        """Get order status update email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Order Status Update</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Order Status Update</h1>
                
                <p>Dear {{ order.customer_name }},</p>
                
                <p>Your order status has been updated:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>New Status:</strong> <span style="color: #28a745;">{{ new_status.title() }}</span></p>
                    {% if order.tracking_number %}
                    <p><strong>Tracking Number:</strong> {{ order.tracking_number }}</p>
                    {% endif %}
                </div>
                
                {% if new_status == 'shipped' %}
                <p>Your order has been shipped and is on its way to you!</p>
                {% elif new_status == 'delivered' %}
                <p>Your order has been delivered. We hope you enjoy your purchase!</p>
                {% endif %}
                
                <p>Thank you for shopping with {{ store.store_name }}!</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(
            template, 
            order=order, 
            store=store, 
            contact=contact, 
            old_status=old_status, 
            new_status=new_status
        )
    
    @staticmethod
    def _get_tracking_info_template(order, store, contact):
        """Get tracking information email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tracking Information</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Your Order is on the Way!</h1>
                
                <p>Dear {{ order.customer_name }},</p>
                
                <p>Great news! Your order has been shipped and is on its way to you.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>Tracking Number:</strong> {{ order.tracking_number }}</p>
                    {% if order.tracking_url %}
                    <p><strong>Track Your Package:</strong> <a href="{{ order.tracking_url }}">{{ order.tracking_url }}</a></p>
                    {% endif %}
                    {% if order.shipping_partner %}
                    <p><strong>Shipping Partner:</strong> {{ order.shipping_partner }}</p>
                    {% endif %}
                </div>
                
                <p>You can use the tracking number to monitor your package's progress.</p>
                
                <p>Thank you for shopping with {{ store.store_name }}!</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, order=order, store=store, contact=contact)
    
    @staticmethod
    def _get_order_cancellation_template(order, store, contact, reason):
        """Get order cancellation email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Order Cancelled</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #e74c3c;">Order Cancelled</h1>
                
                <p>Dear {{ order.customer_name }},</p>
                
                <p>We regret to inform you that your order has been cancelled.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>Cancellation Date:</strong> {{ order.cancelled_at.strftime('%B %d, %Y') if order.cancelled_at else 'N/A' }}</p>
                    <p><strong>Order Total:</strong> ${{ "%.2f"|format(order.total_amount) }}</p>
                    {% if reason %}
                    <p><strong>Reason:</strong> {{ reason }}</p>
                    {% endif %}
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Cancelled Items</h3>
                    {% for item in order.order_items %}
                    <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                        <p><strong>{{ item.product_name }}</strong></p>
                        <p>Quantity: {{ item.quantity }} × ${{ "%.2f"|format(item.unit_price) }} = ${{ "%.2f"|format(item.total_price) }}</p>
                    </div>
                    {% endfor %}
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #155724; margin-top: 0;">Refund Information</h3>
                    <p style="color: #155724;">
                        {% if order.payment_status == 'paid' %}
                        Your payment has been processed for refund. You can expect to see the refund in your account within 5-7 business days.
                        {% else %}
                        Since no payment was processed, no refund is necessary.
                        {% endif %}
                    </p>
                </div>
                
                <p>We apologize for any inconvenience this may have caused. If you have any questions about this cancellation, please don't hesitate to contact us.</p>
                
                <div style="margin: 30px 0;">
                    <p><strong>Contact Information:</strong></p>
                    <p>Email: {{ contact.primary_email if contact else store.owner_email }}</p>
                    {% if contact and contact.primary_phone %}
                    <p>Phone: {{ contact.primary_phone }}</p>
                    {% endif %}
                </div>
                
                <p>Thank you for your understanding.</p>
                
                <p>Best regards,<br>{{ store.store_name }} Team</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, order=order, store=store, contact=contact, reason=reason)
    
    @staticmethod
    def _get_password_reset_template(reset_token):
        """Get password reset email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Password Reset</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Password Reset Request</h1>
                
                <p>You have requested to reset your password.</p>
                
                <p>Use the following token to reset your password:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; font-family: monospace;">
                    {{ reset_token }}
                </div>
                
                <p>This token will expire in 1 hour.</p>
                
                <p>If you did not request this password reset, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, reset_token=reset_token)
    
    @staticmethod
    def _get_welcome_template(user, store):
        """Get welcome email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Welcome to the Admin Panel!</h1>
                
                <p>Dear {{ user.get_full_name() }},</p>
                
                <p>Welcome to the admin panel{% if store %} for {{ store.store_name }}{% endif %}!</p>
                
                <p>Your account has been created with the following details:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Email:</strong> {{ user.email }}</p>
                    <p><strong>Role:</strong> {{ user.role }}</p>
                    {% if store %}
                    <p><strong>Store:</strong> {{ store.store_name }}</p>
                    {% endif %}
                </div>
                
                <p>You can now log in to the admin panel and start managing your store.</p>
                
                <p>If you have any questions, please don't hesitate to reach out.</p>
                
                <p>Best regards,<br>The Admin Team</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, user=user, store=store)
    
    @staticmethod
    def _get_low_stock_template(store, low_stock_products):
        """Get low stock alert email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Low Stock Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f39c12;">Low Stock Alert</h1>
                
                <p>The following products in {{ store.store_name }} are running low on stock:</p>
                
                <div style="margin: 20px 0;">
                    {% for product in low_stock_products %}
                    <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                        <p><strong>{{ product.name }}</strong></p>
                        <p>SKU: {{ product.sku }}</p>
                        <p>Current Stock: {{ product.inventory_quantity }}</p>
                        <p>Low Stock Threshold: {{ product.low_stock_threshold }}</p>
                    </div>
                    {% endfor %}
                </div>
                
                <p>Please restock these items to avoid going out of stock.</p>
                
                <p>{{ store.store_name }} Admin Panel</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, store=store, low_stock_products=low_stock_products)
    
    @staticmethod
    def _get_new_order_notification_template(order, store):
        """Get new order notification email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>New Order Received</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #28a745;">New Order Received!</h1>
                
                <p>A new order has been placed in {{ store.store_name }}.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Order Details</h3>
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>Customer:</strong> {{ order.customer_name }}</p>
                    <p><strong>Email:</strong> {{ order.customer_email }}</p>
                    <p><strong>Total Amount:</strong> ${{ "%.2f"|format(order.total_amount) }}</p>
                    <p><strong>Payment Method:</strong> {{ order.payment_method or 'Not specified' }}</p>
                    <p><strong>Order Date:</strong> {{ order.created_at.strftime('%B %d, %Y at %I:%M %p') }}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Order Items</h3>
                    {% for item in order.order_items %}
                    <div style="border-bottom: 1px solid #eee; padding: 5px 0;">
                        <p>{{ item.product_name }} × {{ item.quantity }} = ${{ "%.2f"|format(item.total_price) }}</p>
                    </div>
                    {% endfor %}
                </div>
                
                <p>Please log in to the admin panel to process this order.</p>
                
                <p>{{ store.store_name }} Admin Panel</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, order=order, store=store)
    
    @staticmethod
    def _get_email_verification_template(user, verification_token):
        """Get email verification template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Verify Your Email Address</h1>
                
                <p>Dear {{ user.get_full_name() }},</p>
                
                <p>Thank you for creating an account. To complete your registration, please verify your email address.</p>
                
                <p>Use the following verification code:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; font-family: monospace; font-size: 18px; text-align: center;">
                    {{ verification_token }}
                </div>
                
                <p>This verification code will expire in 24 hours.</p>
                
                <p>If you did not create this account, please ignore this email.</p>
                
                <p>Best regards,<br>The Admin Team</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, user=user, verification_token=verification_token)
    
    @staticmethod
    def _get_store_setup_template(store, owner):
        """Get store setup completion template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Store Setup Complete</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #28a745;">🎉 Your Store is Ready!</h1>
                
                <p>Dear {{ owner.get_full_name() }},</p>
                
                <p>Congratulations! Your store <strong>{{ store.store_name }}</strong> has been successfully set up and is ready to go live.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Store Details</h3>
                    <p><strong>Store Name:</strong> {{ store.store_name }}</p>
                    {% if store.get_store_url %}
                    <p><strong>Store URL:</strong> <a href="{{ store.get_store_url() }}">{{ store.get_store_url() }}</a></p>
                    {% endif %}
                    {% if store.domain %}
                    <p><strong>Admin Panel:</strong> <a href="https://admin.{{ store.domain }}">Admin Dashboard</a></p>
                    {% endif %}
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>What's Next?</h3>
                    <ul>
                        <li>Add your first products</li>
                        <li>Configure payment gateways</li>
                        <li>Set up shipping options</li>
                        <li>Customize your store theme</li>
                        <li>Create your first blog post</li>
                    </ul>
                </div>
                
                {% if store.plan_type %}
                <p>Your store is currently in <strong>{{ store.plan_type }}</strong> plan. You can upgrade anytime from the admin panel.</p>
                {% endif %}
                
                <p>If you need any help, our support team is here to assist you.</p>
                
                <p>Welcome to the platform!</p>
                
                <p>Best regards,<br>The Team</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, store=store, owner=owner)
    
    @staticmethod
    def _get_subscription_warning_template(store, days_left):
        """Get subscription expiry warning template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Subscription Expiring Soon</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f39c12;">⚠️ Subscription Expiring Soon</h1>
                
                <p>Your subscription for <strong>{{ store.store_name }}</strong> is expiring in <strong>{{ days_left }} days</strong>.</p>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    {% if store.plan_type %}
                    <p><strong>Current Plan:</strong> {{ store.plan_type.title() }}</p>
                    {% endif %}
                    {% if store.subscription_end %}
                    <p><strong>Expiry Date:</strong> {{ store.subscription_end.strftime('%B %d, %Y') }}</p>
                    {% endif %}
                </div>
                
                <p>To avoid any interruption to your service, please renew your subscription before it expires.</p>
                
                {% if store.domain %}
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://admin.{{ store.domain }}/billing" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Renew Subscription</a>
                </div>
                {% endif %}
                
                <p>After expiry, your store will be suspended until you renew your subscription.</p>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Thank you for choosing our platform!</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, store=store, days_left=days_left)
    
    @staticmethod
    def _get_security_alert_template(user, event_type, details):
        """Get security alert template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #dc3545;">🔒 Security Alert</h1>
                
                <p>Dear {{ user.get_full_name() }},</p>
                
                <p>We detected unusual activity on your account that requires your attention.</p>
                
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Event:</strong> {{ event_type }}</p>
                    <p><strong>Time:</strong> {{ details.get('timestamp', 'Unknown') }}</p>
                    <p><strong>IP Address:</strong> {{ details.get('ip_address', 'Unknown') }}</p>
                    <p><strong>Location:</strong> {{ details.get('location', 'Unknown') }}</p>
                </div>
                
                <p><strong>What should you do?</strong></p>
                <ul>
                    <li>If this was you, no action is needed</li>
                    <li>If this wasn't you, please change your password immediately</li>
                    <li>Consider enabling two-factor authentication</li>
                    <li>Contact support if you need assistance</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Change Password</a>
                </div>
                
                <p>Your account security is important to us. If you have any concerns, please contact our support team immediately.</p>
                
                <p>Stay safe!</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, user=user, event_type=event_type, details=details)
    
    @staticmethod
    def _get_bulk_email_template(content, store, email_type):
        """Get bulk email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ email_type.title() }}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50;">{{ store.store_name }}</h1>
                </div>
                
                <div style="margin: 20px 0;">
                    {{ content | safe }}
                </div>
                
                <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 40px; font-size: 12px; color: #666;">
                    <p>You received this email because you are subscribed to {{ email_type }} from {{ store.store_name }}.</p>
                    <p>If you no longer wish to receive these emails, you can <a href="#">unsubscribe</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, content=content, store=store, email_type=email_type)
    
    @staticmethod
    def _get_invoice_template(order, store, contact):
        """Get invoice email template."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invoice</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Invoice</h1>
                
                <p>Dear {{ order.customer_name }},</p>
                
                <p>Please find attached your invoice for order {{ order.order_number }}.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
                    <p><strong>Invoice Date:</strong> {{ order.created_at.strftime('%B %d, %Y') }}</p>
                    <p><strong>Total Amount:</strong> ${{ "%.2f"|format(order.total_amount) }}</p>
                </div>
                
                <p>If you have any questions about this invoice, please contact us at {{ contact.primary_email if contact else store.owner_email }}.</p>
                
                <p>Thank you for your business!</p>
                
                <p>{{ store.store_name }}</p>
            </div>
        </body>
        </html>
        """
        
        return render_template_string(template, order=order, store=store, contact=contact)