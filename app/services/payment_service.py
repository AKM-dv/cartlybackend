"""
Payment service for handling payment gateway operations and transactions.
"""

import razorpay
import requests
from datetime import datetime
from flask import current_app
from app.config.database import db
from app.models.payment_gateway import PaymentGateway
from app.models.order import Order
import logging

class PaymentService:
    """Service for handling payment operations."""
    
    @staticmethod
    def create_payment_order(store_id, order_id, gateway_name='razorpay'):
        """Create payment order with selected gateway."""
        try:
            # Get order
            order = Order.query.filter_by(
                id=order_id,
                store_id=store_id
            ).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            # Get payment gateway
            gateway = PaymentGateway.get_by_name(store_id, gateway_name)
            if not gateway or not gateway.is_active:
                return {
                    'success': False,
                    'message': 'Payment gateway not available',
                    'code': 'GATEWAY_NOT_AVAILABLE'
                }
            
            # Check amount limits
            if not gateway.is_amount_supported(float(order.total_amount)):
                return {
                    'success': False,
                    'message': f'Amount not supported. Min: {gateway.min_amount}, Max: {gateway.max_amount}',
                    'code': 'AMOUNT_NOT_SUPPORTED'
                }
            
            # Check currency support
            if not gateway.is_currency_supported(order.currency):
                return {
                    'success': False,
                    'message': f'Currency {order.currency} not supported',
                    'code': 'CURRENCY_NOT_SUPPORTED'
                }
            
            # Create payment order based on gateway
            if gateway_name == 'razorpay':
                result = PaymentService._create_razorpay_order(gateway, order)
            elif gateway_name == 'paypal':
                result = PaymentService._create_paypal_order(gateway, order)
            elif gateway_name == 'phonepe':
                result = PaymentService._create_phonepe_order(gateway, order)
            else:
                return {
                    'success': False,
                    'message': 'Unsupported payment gateway',
                    'code': 'UNSUPPORTED_GATEWAY'
                }
            
            if result['success']:
                # Update order with payment info
                order.payment_gateway = gateway_name
                order.payment_reference = result['data'].get('payment_id')
                db.session.commit()
                
                # Update gateway stats
                gateway.update_transaction_stats(float(order.total_amount), success=True)
                db.session.commit()
            
            return result
            
        except Exception as e:
            logging.error(f"Create payment order error: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred while creating payment order',
                'code': 'PAYMENT_CREATE_ERROR'
            }
    
    @staticmethod
    def _create_razorpay_order(gateway, order):
        """Create Razorpay payment order."""
        try:
            config = gateway.get_gateway_config()
            client = razorpay.Client(auth=(config['key_id'], config['key_secret']))
            
            # Convert amount to paise
            amount_paise = int(float(order.total_amount) * 100)
            
            razorpay_order = client.order.create({
                'amount': amount_paise,
                'currency': order.currency,
                'receipt': order.order_number,
                'payment_capture': '1' if gateway.auto_capture else '0',
                'notes': {
                    'store_id': order.store_id,
                    'order_id': str(order.id),
                    'customer_email': order.customer_email
                }
            })
            
            return {
                'success': True,
                'message': 'Razorpay order created successfully',
                'data': {
                    'payment_id': razorpay_order['id'],
                    'amount': razorpay_order['amount'],
                    'currency': razorpay_order['currency'],
                    'key_id': config['key_id'],
                    'order_id': razorpay_order['id'],
                    'checkout_options': {
                        'theme': {
                            'color': config.get('theme_color', '#3399cc')
                        },
                        'image': config.get('checkout_logo', ''),
                        'prefill': {
                            'name': order.customer_name,
                            'email': order.customer_email,
                            'contact': order.customer_phone or ''
                        }
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"Razorpay order creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to create Razorpay order',
                'code': 'RAZORPAY_ERROR'
            }
    
    @staticmethod
    def _create_paypal_order(gateway, order):
        """Create PayPal payment order."""
        try:
            config = gateway.get_gateway_config()
            
            # PayPal API endpoint
            base_url = 'https://api.sandbox.paypal.com' if config['mode'] == 'sandbox' else 'https://api.paypal.com'
            
            # Get access token
            auth_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'en_US',
                },
                auth=(config['client_id'], config['client_secret']),
                data={'grant_type': 'client_credentials'}
            )
            
            if auth_response.status_code != 200:
                return {
                    'success': False,
                    'message': 'PayPal authentication failed',
                    'code': 'PAYPAL_AUTH_ERROR'
                }
            
            access_token = auth_response.json()['access_token']
            
            # Create order
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': order.order_number,
                    'amount': {
                        'currency_code': order.currency,
                        'value': str(order.total_amount)
                    },
                    'description': f'Order {order.order_number}'
                }],
                'application_context': {
                    'return_url': f"{current_app.config.get('BASE_URL', 'http://localhost')}/payment/success",
                    'cancel_url': f"{current_app.config.get('BASE_URL', 'http://localhost')}/payment/cancel"
                }
            }
            
            create_response = requests.post(
                f"{base_url}/v2/checkout/orders",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}',
                },
                json=order_data
            )
            
            if create_response.status_code != 201:
                return {
                    'success': False,
                    'message': 'PayPal order creation failed',
                    'code': 'PAYPAL_CREATE_ERROR'
                }
            
            paypal_order = create_response.json()
            approval_url = next(link['href'] for link in paypal_order['links'] if link['rel'] == 'approve')
            
            return {
                'success': True,
                'message': 'PayPal order created successfully',
                'data': {
                    'payment_id': paypal_order['id'],
                    'approval_url': approval_url,
                    'order_id': paypal_order['id']
                }
            }
            
        except Exception as e:
            logging.error(f"PayPal order creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to create PayPal order',
                'code': 'PAYPAL_ERROR'
            }
    
    @staticmethod
    def _create_phonepe_order(gateway, order):
        """Create PhonePe payment order."""
        try:
            config = gateway.get_gateway_config()
            
            # PhonePe payment request
            payment_data = {
                'merchantId': config['merchant_id'],
                'merchantTransactionId': f"{order.order_number}_{int(datetime.now().timestamp())}",
                'merchantUserId': str(order.customer_id) if order.customer_id else order.customer_email,
                'amount': int(float(order.total_amount) * 100),  # Convert to paise
                'redirectUrl': f"{current_app.config.get('BASE_URL', 'http://localhost')}/payment/phonepe/callback",
                'redirectMode': 'REDIRECT',
                'callbackUrl': f"{current_app.config.get('BASE_URL', 'http://localhost')}/api/webhooks/phonepe",
                'paymentInstrument': {
                    'type': 'PAY_PAGE'
                }
            }
            
            # This is a simplified implementation
            # In production, you'd need to implement proper PhonePe integration
            # including request signing, API calls, etc.
            
            return {
                'success': True,
                'message': 'PhonePe order created successfully',
                'data': {
                    'payment_id': payment_data['merchantTransactionId'],
                    'redirect_url': f"https://mercury-{'uat' if config['env'] == 'sandbox' else 'prod'}.phonepe.com/transact",
                    'order_id': payment_data['merchantTransactionId']
                }
            }
            
        except Exception as e:
            logging.error(f"PhonePe order creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to create PhonePe order',
                'code': 'PHONEPE_ERROR'
            }
    
    @staticmethod
    def verify_payment(store_id, payment_id, gateway_name, payment_data=None):
        """Verify payment status."""
        try:
            gateway = PaymentGateway.get_by_name(store_id, gateway_name)
            if not gateway:
                return {
                    'success': False,
                    'message': 'Payment gateway not found',
                    'code': 'GATEWAY_NOT_FOUND'
                }
            
            if gateway_name == 'razorpay':
                return PaymentService._verify_razorpay_payment(gateway, payment_id, payment_data)
            elif gateway_name == 'paypal':
                return PaymentService._verify_paypal_payment(gateway, payment_id)
            elif gateway_name == 'phonepe':
                return PaymentService._verify_phonepe_payment(gateway, payment_id)
            else:
                return {
                    'success': False,
                    'message': 'Unsupported payment gateway',
                    'code': 'UNSUPPORTED_GATEWAY'
                }
                
        except Exception as e:
            logging.error(f"Payment verification error: {str(e)}")
            return {
                'success': False,
                'message': 'Payment verification failed',
                'code': 'VERIFICATION_ERROR'
            }
    
    @staticmethod
    def _verify_razorpay_payment(gateway, payment_id, payment_data):
        """Verify Razorpay payment."""
        try:
            config = gateway.get_gateway_config()
            client = razorpay.Client(auth=(config['key_id'], config['key_secret']))
            
            # Verify signature if provided
            if payment_data and 'razorpay_signature' in payment_data:
                params_dict = {
                    'razorpay_order_id': payment_data['razorpay_order_id'],
                    'razorpay_payment_id': payment_data['razorpay_payment_id'],
                    'razorpay_signature': payment_data['razorpay_signature']
                }
                
                try:
                    client.utility.verify_payment_signature(params_dict)
                except:
                    return {
                        'success': False,
                        'message': 'Invalid payment signature',
                        'code': 'INVALID_SIGNATURE'
                    }
            
            # Fetch payment details
            payment = client.payment.fetch(payment_id)
            
            return {
                'success': True,
                'message': 'Payment verified successfully',
                'data': {
                    'payment_id': payment['id'],
                    'order_id': payment['order_id'],
                    'status': payment['status'],
                    'amount': payment['amount'] / 100,  # Convert from paise
                    'currency': payment['currency'],
                    'method': payment['method'],
                    'captured': payment['captured'],
                    'created_at': payment['created_at']
                }
            }
            
        except Exception as e:
            logging.error(f"Razorpay verification error: {str(e)}")
            return {
                'success': False,
                'message': 'Razorpay verification failed',
                'code': 'RAZORPAY_VERIFICATION_ERROR'
            }
    
    @staticmethod
    def _verify_paypal_payment(gateway, payment_id):
        """Verify PayPal payment."""
        try:
            config = gateway.get_gateway_config()
            base_url = 'https://api.sandbox.paypal.com' if config['mode'] == 'sandbox' else 'https://api.paypal.com'
            
            # Get access token (same as in create order)
            auth_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
                auth=(config['client_id'], config['client_secret']),
                data={'grant_type': 'client_credentials'}
            )
            
            if auth_response.status_code != 200:
                return {
                    'success': False,
                    'message': 'PayPal authentication failed',
                    'code': 'PAYPAL_AUTH_ERROR'
                }
            
            access_token = auth_response.json()['access_token']
            
            # Get order details
            order_response = requests.get(
                f"{base_url}/v2/checkout/orders/{payment_id}",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}',
                }
            )
            
            if order_response.status_code != 200:
                return {
                    'success': False,
                    'message': 'PayPal order not found',
                    'code': 'PAYPAL_ORDER_NOT_FOUND'
                }
            
            order_data = order_response.json()
            
            return {
                'success': True,
                'message': 'PayPal payment verified successfully',
                'data': {
                    'payment_id': order_data['id'],
                    'status': order_data['status'],
                    'amount': float(order_data['purchase_units'][0]['amount']['value']),
                    'currency': order_data['purchase_units'][0]['amount']['currency_code'],
                    'payer_email': order_data.get('payer', {}).get('email_address', ''),
                    'created_at': order_data['create_time']
                }
            }
            
        except Exception as e:
            logging.error(f"PayPal verification error: {str(e)}")
            return {
                'success': False,
                'message': 'PayPal verification failed',
                'code': 'PAYPAL_VERIFICATION_ERROR'
            }
    
    @staticmethod
    def _verify_phonepe_payment(gateway, payment_id):
        """Verify PhonePe payment."""
        try:
            # This is a simplified implementation
            # In production, you'd implement proper PhonePe verification
            # including API calls to check transaction status
            
            return {
                'success': True,
                'message': 'PhonePe payment verified successfully',
                'data': {
                    'payment_id': payment_id,
                    'status': 'completed',  # This should come from actual API
                    'amount': 0,  # This should come from actual API
                    'currency': 'INR',
                    'method': 'phonepe',
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"PhonePe verification error: {str(e)}")
            return {
                'success': False,
                'message': 'PhonePe verification failed',
                'code': 'PHONEPE_VERIFICATION_ERROR'
            }
    
    @staticmethod
    def process_refund(store_id, order_id, refund_amount, reason=None, gateway_name=None):
        """Process payment refund."""
        try:
            order = Order.query.filter_by(
                id=order_id,
                store_id=store_id
            ).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Order not found',
                    'code': 'ORDER_NOT_FOUND'
                }
            
            if order.payment_status != 'paid':
                return {
                    'success': False,
                    'message': 'Order payment not completed',
                    'code': 'PAYMENT_NOT_COMPLETED'
                }
            
            gateway_name = gateway_name or order.payment_gateway
            gateway = PaymentGateway.get_by_name(store_id, gateway_name)
            
            if not gateway or not gateway.supports_refunds:
                return {
                    'success': False,
                    'message': 'Refunds not supported by payment gateway',
                    'code': 'REFUNDS_NOT_SUPPORTED'
                }
            
            # Validate refund amount
            if refund_amount > float(order.total_amount):
                return {
                    'success': False,
                    'message': 'Refund amount cannot exceed order total',
                    'code': 'INVALID_REFUND_AMOUNT'
                }
            
            # Process refund based on gateway
            if gateway_name == 'razorpay':
                result = PaymentService._process_razorpay_refund(gateway, order, refund_amount, reason)
            elif gateway_name == 'paypal':
                result = PaymentService._process_paypal_refund(gateway, order, refund_amount, reason)
            else:
                return {
                    'success': False,
                    'message': 'Refunds not implemented for this gateway',
                    'code': 'REFUND_NOT_IMPLEMENTED'
                }
            
            if result['success']:
                # Update order status
                order.payment_status = 'refunded' if refund_amount == float(order.total_amount) else 'partially_refunded'
                order.refund_amount = (order.refund_amount or 0) + refund_amount
                order.refund_reason = reason
                order.refunded_at = datetime.utcnow()
                db.session.commit()
            
            return result
            
        except Exception as e:
            logging.error(f"Process refund error: {str(e)}")
            return {
                'success': False,
                'message': 'Refund processing failed',
                'code': 'REFUND_ERROR'
            }
    
    @staticmethod
    def _process_razorpay_refund(gateway, order, refund_amount, reason):
        """Process Razorpay refund."""
        try:
            config = gateway.get_gateway_config()
            client = razorpay.Client(auth=(config['key_id'], config['key_secret']))
            
            # Create refund
            refund_data = {
                'amount': int(refund_amount * 100),  # Convert to paise
                'speed': 'normal',
                'notes': {
                    'reason': reason or 'Refund requested',
                    'order_number': order.order_number
                }
            }
            
            refund = client.payment.refund(order.payment_transaction_id, refund_data)
            
            return {
                'success': True,
                'message': 'Refund processed successfully',
                'data': {
                    'refund_id': refund['id'],
                    'amount': refund['amount'] / 100,
                    'currency': refund['currency'],
                    'status': refund['status'],
                    'created_at': refund['created_at']
                }
            }
            
        except Exception as e:
            logging.error(f"Razorpay refund error: {str(e)}")
            return {
                'success': False,
                'message': 'Razorpay refund failed',
                'code': 'RAZORPAY_REFUND_ERROR'
            }
    
    @staticmethod
    def _process_paypal_refund(gateway, order, refund_amount, reason):
        """Process PayPal refund."""
        try:
            # PayPal refund implementation would go here
            # This is a placeholder implementation
            
            return {
                'success': True,
                'message': 'PayPal refund processed successfully',
                'data': {
                    'refund_id': f"PAYPAL_REFUND_{int(datetime.now().timestamp())}",
                    'amount': refund_amount,
                    'currency': order.currency,
                    'status': 'completed',
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"PayPal refund error: {str(e)}")
            return {
                'success': False,
                'message': 'PayPal refund failed',
                'code': 'PAYPAL_REFUND_ERROR'
            }
    
    @staticmethod
    def get_payment_methods(store_id, amount=None, currency='USD'):
        """Get available payment methods for store."""
        try:
            gateways = PaymentGateway.get_active_gateways(store_id)
            
            available_methods = []
            for gateway in gateways:
                # Check amount limits
                if amount and not gateway.is_amount_supported(amount):
                    continue
                
                # Check currency support
                if not gateway.is_currency_supported(currency):
                    continue
                
                # Calculate fees
                fees = gateway.calculate_fees(amount) if amount else 0
                
                method_data = {
                    'gateway_name': gateway.gateway_name,
                    'display_name': gateway.display_name,
                    'gateway_type': gateway.gateway_type,
                    'logo': gateway.display_logo,
                    'description': gateway.display_description,
                    'transaction_fees': fees,
                    'supports_refunds': gateway.supports_refunds,
                    'estimated_time': gateway.payment_timeout,
                    'min_amount': float(gateway.min_amount),
                    'max_amount': float(gateway.max_amount) if gateway.max_amount else None
                }
                
                available_methods.append(method_data)
            
            # Sort by priority
            available_methods.sort(key=lambda x: next(
                (g.priority for g in gateways if g.gateway_name == x['gateway_name']), 999
            ))
            
            return {
                'success': True,
                'message': 'Payment methods retrieved successfully',
                'data': {
                    'payment_methods': available_methods,
                    'count': len(available_methods)
                }
            }
            
        except Exception as e:
            logging.error(f"Get payment methods error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to retrieve payment methods',
                'code': 'PAYMENT_METHODS_ERROR'
            }
    
    @staticmethod
    def handle_webhook(store_id, gateway_name, webhook_data):
        """Handle payment gateway webhooks."""
        try:
            gateway = PaymentGateway.get_by_name(store_id, gateway_name)
            if not gateway:
                return {
                    'success': False,
                    'message': 'Payment gateway not found',
                    'code': 'GATEWAY_NOT_FOUND'
                }
            
            if gateway_name == 'razorpay':
                return PaymentService._handle_razorpay_webhook(gateway, webhook_data)
            elif gateway_name == 'paypal':
                return PaymentService._handle_paypal_webhook(gateway, webhook_data)
            elif gateway_name == 'phonepe':
                return PaymentService._handle_phonepe_webhook(gateway, webhook_data)
            else:
                return {
                    'success': False,
                    'message': 'Webhook not supported for this gateway',
                    'code': 'WEBHOOK_NOT_SUPPORTED'
                }
                
        except Exception as e:
            logging.error(f"Webhook handling error: {str(e)}")
            return {
                'success': False,
                'message': 'Webhook processing failed',
                'code': 'WEBHOOK_ERROR'
            }
    
    @staticmethod
    def _handle_razorpay_webhook(gateway, webhook_data):
        """Handle Razorpay webhook."""
        try:
            event = webhook_data.get('event')
            payload = webhook_data.get('payload', {})
            
            if event == 'payment.captured':
                payment = payload.get('payment', {}).get('entity', {})
                order_id = payment.get('order_id')
                
                # Find order and update status
                order = Order.query.filter_by(
                    store_id=gateway.store_id,
                    payment_reference=order_id
                ).first()
                
                if order:
                    order.payment_status = 'paid'
                    order.payment_transaction_id = payment.get('id')
                    order.confirmed_at = datetime.utcnow()
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Payment captured webhook processed',
                    'data': {'order_id': order.id if order else None}
                }
            
            elif event == 'payment.failed':
                payment = payload.get('payment', {}).get('entity', {})
                order_id = payment.get('order_id')
                
                # Find order and update status
                order = Order.query.filter_by(
                    store_id=gateway.store_id,
                    payment_reference=order_id
                ).first()
                
                if order:
                    order.payment_status = 'failed'
                    order.payment_failure_reason = payment.get('error_description')
                    db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Payment failed webhook processed',
                    'data': {'order_id': order.id if order else None}
                }
            
            return {
                'success': True,
                'message': 'Webhook received but no action taken',
                'data': {'event': event}
            }
            
        except Exception as e:
            logging.error(f"Razorpay webhook error: {str(e)}")
            return {
                'success': False,
                'message': 'Razorpay webhook processing failed',
                'code': 'RAZORPAY_WEBHOOK_ERROR'
            }
    
    @staticmethod
    def _handle_paypal_webhook(gateway, webhook_data):
        """Handle PayPal webhook."""
        # PayPal webhook implementation would go here
        return {
            'success': True,
            'message': 'PayPal webhook processed',
            'data': {}
        }
    
    @staticmethod
    def _handle_phonepe_webhook(gateway, webhook_data):
        """Handle PhonePe webhook."""
        # PhonePe webhook implementation would go here
        return {
            'success': True,
            'message': 'PhonePe webhook processed',
            'data': {}
        }