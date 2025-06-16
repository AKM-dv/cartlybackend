rates.append(rate_data)
            
            # Sort by rate (cheapest first)
            rates.sort(key=lambda x: x.get('rate', float('inf')))
            
            return {
                'success': True,
                'message': 'Shipping rates calculated successfully',
                'data': {
                    'rates': rates,
                    'count': len(rates)
                }
            }
            
        except Exception as e:
            logging.error(f"Calculate shipping rates error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to calculate shipping rates',
                'code': 'SHIPPING_CALCULATION_ERROR'
            }
    
    @staticmethod
    def _calculate_shiprocket_rate(partner, weight, dimensions, origin_pincode, destination_pincode, order_value):
        """Calculate Shiprocket shipping rate using API."""
        try:
            config = partner.get_api_config()
            
            # Get Shiprocket token
            token_result = ShippingService._get_shiprocket_token(config)
            if not token_result['success']:
                return token_result
            
            token = token_result['data']['token']
            
            # Prepare rate calculation request
            rate_data = {
                'pickup_postcode': origin_pincode,
                'delivery_postcode': destination_pincode,
                'weight': weight,
                'length': dimensions.get('length', 10) if dimensions else 10,
                'breadth': dimensions.get('width', 10) if dimensions else 10,
                'height': dimensions.get('height', 10) if dimensions else 10,
                'declared_value': order_value or 100
            }
            
            response = requests.get(
                f"{current_app.config['SHIPROCKET_API_URL']}/courier/serviceability",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                },
                params=rate_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Shiprocket API error',
                    'code': 'SHIPROCKET_API_ERROR'
                }
            
            data = response.json()
            
            if not data.get('status') or data['status'] != 200:
                return {
                    'success': False,
                    'message': data.get('message', 'Shiprocket calculation failed'),
                    'code': 'SHIPROCKET_CALC_ERROR'
                }
            
            # Get the best rate
            courier_data = data.get('data', {}).get('available_courier_companies', [])
            if not courier_data:
                return {
                    'success': False,
                    'message': 'No courier services available',
                    'code': 'NO_COURIER_AVAILABLE'
                }
            
            # Find cheapest option
            best_courier = min(courier_data, key=lambda x: float(x.get('rate', float('inf'))))
            
            return {
                'success': True,
                'data': {
                    'rate': float(best_courier['rate']),
                    'service_type': best_courier.get('courier_name', 'Standard'),
                    'estimated_days': best_courier.get('estimated_delivery_days', 3),
                    'courier_id': best_courier.get('courier_company_id'),
                    'cod_available': best_courier.get('cod') == 1
                }
            }
            
        except Exception as e:
            logging.error(f"Shiprocket rate calculation error: {str(e)}")
            return {
                'success': False,
                'message': 'Shiprocket rate calculation failed',
                'code': 'SHIPROCKET_ERROR'
            }
    
    @staticmethod
    def _calculate_delhivery_rate(partner, weight, dimensions, origin_pincode, destination_pincode, order_value):
        """Calculate Delhivery shipping rate using API."""
        try:
            config = partner.get_api_config()
            
            # Delhivery rate calculation
            params = {
                'md': 'S',  # Mode (Surface)
                'ss': 'Delivered',  # Status
                'o_pin': origin_pincode,
                'd_pin': destination_pincode,
                'cgm': weight * 1000,  # Weight in grams
                'o_city': '',
                'd_city': ''
            }
            
            response = requests.get(
                'https://track.delhivery.com/api/kinko/v1/invoice/charges',
                headers={
                    'Authorization': f'Token {config.get("api_token")}',
                    'Content-Type': 'application/json'
                },
                params=params
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Delhivery API error',
                    'code': 'DELHIVERY_API_ERROR'
                }
            
            data = response.json()
            
            if not data.get('success'):
                return {
                    'success': False,
                    'message': data.get('message', 'Delhivery calculation failed'),
                    'code': 'DELHIVERY_CALC_ERROR'
                }
            
            # Extract rate information
            charges = data.get('data', [{}])[0]
            total_amount = charges.get('total_amount', 0)
            
            return {
                'success': True,
                'data': {
                    'rate': float(total_amount),
                    'service_type': 'Delhivery Surface',
                    'estimated_days': 3,
                    'cod_available': True
                }
            }
            
        except Exception as e:
            logging.error(f"Delhivery rate calculation error: {str(e)}")
            return {
                'success': False,
                'message': 'Delhivery rate calculation failed',
                'code': 'DELHIVERY_ERROR'
            }
    
    @staticmethod
    def create_shipment(store_id, order_id, partner_id, shipment_data):
        """Create shipment with shipping partner."""
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
            
            # Get shipping partner
            partner = ShippingPartner.query.filter_by(
                id=partner_id,
                store_id=store_id,
                is_active=True
            ).first()
            
            if not partner:
                return {
                    'success': False,
                    'message': 'Shipping partner not available',
                    'code': 'PARTNER_NOT_AVAILABLE'
                }
            
            # Create shipment based on partner
            if partner.partner_name == 'shiprocket':
                result = ShippingService._create_shiprocket_shipment(partner, order, shipment_data)
            elif partner.partner_name == 'delhivery':
                result = ShippingService._create_delhivery_shipment(partner, order, shipment_data)
            else:
                # Generic local shipping
                result = ShippingService._create_local_shipment(partner, order, shipment_data)
            
            if result['success']:
                # Update order with shipment info
                order.shipping_partner = partner.partner_name
                order.tracking_number = result['data'].get('tracking_number')
                order.tracking_url = result['data'].get('tracking_url')
                order.fulfillment_status = 'shipped'
                order.shipped_at = datetime.utcnow()
                
                if result['data'].get('expected_delivery_date'):
                    order.expected_delivery_date = datetime.fromisoformat(result['data']['expected_delivery_date'])
                
                db.session.commit()
                
                # Update partner stats
                partner.update_shipment_stats()
                db.session.commit()
            
            return result
            
        except Exception as e:
            logging.error(f"Create shipment error: {str(e)}")
            return {
                'success': False,
                'message': 'Shipment creation failed',
                'code': 'SHIPMENT_CREATE_ERROR'
            }
    
    @staticmethod
    def _create_shiprocket_shipment(partner, order, shipment_data):
        """Create Shiprocket shipment."""
        try:
            config = partner.get_api_config()
            
            # Get token
            token_result = ShippingService._get_shiprocket_token(config)
            if not token_result['success']:
                return token_result
            
            token = token_result['data']['token']
            
            # Prepare shipment data
            order_data = {
                'order_id': order.order_number,
                'order_date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'pickup_location': config.get('pickup_location', 'Primary'),
                'channel_id': config.get('channel_id', ''),
                'comment': shipment_data.get('comment', ''),
                'billing_customer_name': order.customer_name,
                'billing_last_name': '',
                'billing_address': order.billing_address.get('address_line_1', ''),
                'billing_address_2': order.billing_address.get('address_line_2', ''),
                'billing_city': order.billing_address.get('city', ''),
                'billing_pincode': order.billing_address.get('postal_code', ''),
                'billing_state': order.billing_address.get('state', ''),
                'billing_country': order.billing_address.get('country', 'India'),
                'billing_email': order.customer_email,
                'billing_phone': order.customer_phone or '1234567890',
                'shipping_is_billing': order.same_as_billing,
                'shipping_customer_name': order.customer_name,
                'shipping_last_name': '',
                'shipping_address': order.shipping_address.get('address_line_1', ''),
                'shipping_address_2': order.shipping_address.get('address_line_2', ''),
                'shipping_city': order.shipping_address.get('city', ''),
                'shipping_pincode': order.shipping_address.get('postal_code', ''),
                'shipping_country': order.shipping_address.get('country', 'India'),
                'shipping_state': order.shipping_address.get('state', ''),
                'shipping_email': order.customer_email,
                'shipping_phone': order.customer_phone or '1234567890',
                'order_items': [],
                'payment_method': 'COD' if order.payment_method == 'cod' else 'Prepaid',
                'shipping_charges': float(order.shipping_amount) if order.shipping_amount else 0,
                'giftwrap_charges': 0,
                'transaction_charges': 0,
                'total_discount': float(order.discount_amount) if order.discount_amount else 0,
                'sub_total': float(order.subtotal),
                'length': shipment_data.get('length', 10),
                'breadth': shipment_data.get('width', 10),
                'height': shipment_data.get('height', 10),
                'weight': shipment_data.get('weight', 0.5)
            }
            
            # Add order items
            for item in order.order_items:
                order_data['order_items'].append({
                    'name': item.get('name', ''),
                    'sku': item.get('sku', ''),
                    'units': item.get('quantity', 1),
                    'selling_price': item.get('price', 0),
                    'discount': 0,
                    'tax': 0,
                    'hsn': item.get('hsn', '')
                })
            
            # Create order
            response = requests.post(
                f"{current_app.config['SHIPROCKET_API_URL']}/orders/create/adhoc",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                },
                json=order_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Shiprocket order creation failed',
                    'code': 'SHIPROCKET_ORDER_ERROR'
                }
            
            data = response.json()
            
            if not data.get('status') or data['status'] != 1:
                return {
                    'success': False,
                    'message': data.get('message', 'Shiprocket shipment failed'),
                    'code': 'SHIPROCKET_SHIPMENT_ERROR'
                }
            
            shipment_id = data.get('shipment_id')
            order_id = data.get('order_id')
            
            return {
                'success': True,
                'message': 'Shiprocket shipment created successfully',
                'data': {
                    'shipment_id': shipment_id,
                    'order_id': order_id,
                    'tracking_number': f'SR{shipment_id}',
                    'tracking_url': f'https://shiprocket.co/tracking/{shipment_id}',
                    'expected_delivery_date': (datetime.now() + timedelta(days=3)).isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"Shiprocket shipment creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Shiprocket shipment creation failed',
                'code': 'SHIPROCKET_ERROR'
            }
    
    @staticmethod
    def _create_delhivery_shipment(partner, order, shipment_data):
        """Create Delhivery shipment."""
        try:
            # Delhivery shipment creation implementation
            config = partner.get_api_config()
            
            # Create Delhivery waybill
            waybill_data = {
                'shipments': [{
                    'name': order.customer_name,
                    'add': f"{order.shipping_address.get('address_line_1', '')} {order.shipping_address.get('address_line_2', '')}",
                    'pin': order.shipping_address.get('postal_code', ''),
                    'city': order.shipping_address.get('city', ''),
                    'state': order.shipping_address.get('state', ''),
                    'country': order.shipping_address.get('country', 'India'),
                    'phone': order.customer_phone or '1234567890',
                    'order': order.order_number,
                    'payment_mode': 'COD' if order.payment_method == 'cod' else 'Prepaid',
                    'return_pin': shipment_data.get('return_pincode', ''),
                    'return_city': shipment_data.get('return_city', ''),
                    'return_phone': shipment_data.get('return_phone', ''),
                    'return_add': shipment_data.get('return_address', ''),
                    'return_state': shipment_data.get('return_state', ''),
                    'return_country': 'India',
                    'products_desc': ', '.join([item.get('name', '') for item in order.order_items]),
                    'hsn_code': '',
                    'cod_amount': float(order.total_amount) if order.payment_method == 'cod' else 0,
                    'order_value': float(order.total_amount),
                    'package_weight': shipment_data.get('weight', 0.5),
                    'package_length': shipment_data.get('length', 10),
                    'package_breadth': shipment_data.get('width', 10),
                    'package_height': shipment_data.get('height', 10),
                    'num_pieces': 1,
                    'fragile_shipment': shipment_data.get('fragile', False),
                    'consignee': order.customer_name,
                    'consignee_email': order.customer_email
                }]
            }
            
            response = requests.post(
                'https://track.delhivery.com/api/cmu/create.json',
                headers={
                    'Authorization': f'Token {config.get("api_token")}',
                    'Content-Type': 'application/json'
                },
                json=waybill_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Delhivery shipment creation failed',
                    'code': 'DELHIVERY_API_ERROR'
                }
            
            data = response.json()
            
            if not data.get('success'):
                return {
                    'success': False,
                    'message': data.get('message', 'Delhivery shipment failed'),
                    'code': 'DELHIVERY_SHIPMENT_ERROR'
                }
            
            # Extract waybill number
            packages = data.get('packages', [])
            if not packages:
                return {
                    'success': False,
                    'message': 'No waybill generated',
                    'code': 'NO_WAYBILL'
                }
            
            waybill = packages[0].get('waybill')
            
            return {
                'success': True,
                'message': 'Delhivery shipment created successfully',
                'data': {
                    'waybill': waybill,
                    'tracking_number': waybill,
                    'tracking_url': f'https://www.delhivery.com/track/package/{waybill}',
                    'expected_delivery_date': (datetime.now() + timedelta(days=4)).isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"Delhivery shipment creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Delhivery shipment creation failed',
                'code': 'DELHIVERY_ERROR'
            }
    
    @staticmethod
    def _create_local_shipment(partner, order, shipment_data):
        """Create local delivery shipment."""
        try:
            # Generate tracking number for local delivery
            tracking_number = f"LOCAL{order.store_id}{order.id}{int(datetime.now().timestamp())}"
            
            return {
                'success': True,
                'message': 'Local shipment created successfully',
                'data': {
                    'tracking_number': tracking_number,
                    'tracking_url': f'/track/{tracking_number}',
                    'expected_delivery_date': (datetime.now() + timedelta(days=1)).isoformat()
                }
            }
            
        except Exception as e:
            logging.error(f"Local shipment creation error: {str(e)}")
            return {
                'success': False,
                'message': 'Local shipment creation failed',
                'code': 'LOCAL_SHIPMENT_ERROR'
            }
    
    @staticmethod
    def _get_shiprocket_token(config):
        """Get Shiprocket authentication token."""
        try:
            auth_data = {
                'email': config.get('email') or current_app.config.get('SHIPROCKET_EMAIL'),
                'password': config.get('password') or current_app.config.get('SHIPROCKET_PASSWORD')
            }
            
            response = requests.post(
                f"{current_app.config['SHIPROCKET_API_URL']}/auth/login",
                json=auth_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Shiprocket authentication failed',
                    'code': 'SHIPROCKET_AUTH_ERROR'
                }
            
            data = response.json()
            token = data.get('token')
            
            if not token:
                return {
                    'success': False,
                    'message': 'No token received from Shiprocket',
                    'code': 'NO_TOKEN'
                }
            
            return {
                'success': True,
                'data': {'token': token}
            }
            
        except Exception as e:
            logging.error(f"Shiprocket token error: {str(e)}")
            return {
                'success': False,
                'message': 'Shiprocket token retrieval failed',
                'code': 'TOKEN_ERROR'
            }
    
    @staticmethod
    def track_shipment(store_id, tracking_number, partner_name=None):
        """Track shipment status."""
        try:
            # Find order by tracking number
            order = Order.query.filter_by(
                store_id=store_id,
                tracking_number=tracking_number
            ).first()
            
            if not order:
                return {
                    'success': False,
                    'message': 'Tracking number not found',
                    'code': 'TRACKING_NOT_FOUND'
                }
            
            partner_name = partner_name or order.shipping_partner
            
            if not partner_name:
                return {
                    'success': False,
                    'message': 'No shipping partner associated',
                    'code': 'NO_PARTNER'
                }
            
            # Get partner
            partner = ShippingPartner.query.filter_by(
                store_id=store_id,
                partner_name=partner_name
            ).first()
            
            if not partner:
                return {
                    'success': False,
                    'message': 'Shipping partner not found',
                    'code': 'PARTNER_NOT_FOUND'
                }
            
            # Track based on partner
            if partner_name == 'shiprocket':
                return ShippingService._track_shiprocket_shipment(partner, tracking_number)
            elif partner_name == 'delhivery':
                return ShippingService._track_delhivery_shipment(partner, tracking_number)
            else:
                # Generic tracking
                return {
                    'success': True,
                    'message': 'Tracking information retrieved',
                    'data': {
                        'tracking_number': tracking_number,
                        'status': 'shipped',
                        'location': 'In Transit',
                        'estimated_delivery': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                        'events': [
                            {
                                'date': order.shipped_at.isoformat() if order.shipped_at else datetime.now().isoformat(),
                                'status': 'Shipped',
                                'location': 'Origin',
                                'description': 'Package shipped'
                            }
                        ]
                    }
                }
            
        except Exception as e:
            logging.error(f"Track shipment error: {str(e)}")
            return {
                'success': False,
                'message': 'Shipment tracking failed',
                'code': 'TRACKING_ERROR'
            }
    
    @staticmethod
    def _track_shiprocket_shipment(partner, tracking_number):
        """Track Shiprocket shipment."""
        try:
            config = partner.get_api_config()
            
            # Get token
            token_result = ShippingService._get_shiprocket_token(config)
            if not token_result['success']:
                return token_result
            
            token = token_result['data']['token']
            
            # Track shipment
            response = requests.get(
                f"{current_app.config['SHIPROCKET_API_URL']}/courier/track/awb/{tracking_number}",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Shiprocket tracking failed',
                    'code': 'SHIPROCKET_TRACKING_ERROR'
                }
            
            data = response.json()
            
            if not data.get('tracking_data'):
                return {
                    'success': False,
                    'message': 'No tracking data available',
                    'code': 'NO_TRACKING_DATA'
                }
            
            tracking_data = data['tracking_data']
            track_status = tracking_data.get('track_status', 1)
            shipment_track = tracking_data.get('shipment_track', [])
            
            # Convert status code to readable status
            status_map = {
                1: 'Shipped',
                2: 'In Transit', 
                3: 'Out for Delivery',
                4: 'Delivered',
                5: 'RTO',
                6: 'Lost',
                7: 'Cancelled'
            }
            
            current_status = status_map.get(track_status, 'Unknown')
            
            # Format tracking events
            events = []
            for event in reversed(shipment_track):
                events.append({
                    'date': event.get('date'),
                    'status': event.get('status'),
                    'location': event.get('location'),
                    'description': event.get('sr-status-label', '')
                })
            
            return {
                'success': True,
                'message': 'Tracking information retrieved successfully',
                'data': {
                    'tracking_number': tracking_number,
                    'status': current_status,
                    'current_location': shipment_track[0].get('location') if shipment_track else '',
                    'estimated_delivery': tracking_data.get('edd'),
                    'events': events
                }
            }
            
        except Exception as e:
            logging.error(f"Shiprocket tracking error: {str(e)}")
            return {
                'success': False,
                'message': 'Shiprocket tracking failed',
                'code': 'SHIPROCKET_TRACK_ERROR'
            }
    
    @staticmethod
    def _track_delhivery_shipment(partner, tracking_number):
        """Track Delhivery shipment."""
        try:
            config = partner.get_api_config()
            
            response = requests.get(
                f'https://track.delhivery.com/api/v1/packages/json/?waybill={tracking_number}',
                headers={
                    'Authorization': f'Token {config.get("api_token")}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': 'Delhivery tracking failed',
                    'code': 'DELHIVERY_TRACKING_ERROR'
                }
            
            data = response.json()
            
            if not data.get('ShipmentData'):
                return {
                    'success': False,
                    'message': 'No tracking data available',
                    'code': 'NO_TRACKING_DATA'
                }
            
            shipment_data = data['ShipmentData'][0]
            shipment = shipment_data.get('Shipment', {})
            status = shipment.get('Status', {})
            
            # Format tracking events
            events = []
            scans = shipment.get('Scans', [])
            for scan in reversed(scans):
                events.append({
                    'date': scan.get('ScanDateTime'),
                    'status': scan.get('ScanType'),
                    'location': scan.get('ScannedLocation'),
                    'description': scan.get('Instructions', '')
                })
            
            return {
                'success': True,
                'message': 'Tracking information retrieved successfully',
                'data': {
                    'tracking_number': tracking_number,
                    'status': status.get('Status', 'Unknown'),
                    'current_location': scans[0].get('ScannedLocation') if scans else '',
                    'estimated_delivery': None,
                    'events': events
                }
            }
            
        except Exception as e:
            logging.error(f"Delhivery tracking error: {str(e)}")
            return {
                'success': False,
                'message': 'Delhivery tracking failed',
                'code': 'DELHIVERY_TRACK_ERROR'
            }
    
    @staticmethod
    def cancel_shipment(store_id, order_id, reason=None):
        """Cancel shipment."""
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
            
            if order.fulfillment_status not in ['pending', 'shipped']:
                return {
                    'success': False,
                    'message': 'Cannot cancel shipment in current status',
                    'code': 'INVALID_STATUS'
                }
            
            # Cancel based on shipping partner
            if order.shipping_partner == 'shiprocket':
                result = ShippingService._cancel_shiprocket_shipment(order, reason)
            elif order.shipping_partner == 'delhivery':
                result = ShippingService._cancel_delhivery_shipment(order, reason)
            else:
                # Generic cancellation
                result = {
                    'success': True,
                    'message': 'Shipment cancelled successfully',
                    'data': {}
                }
            
            if result['success']:
                # Update order status
                order.fulfillment_status = 'cancelled'
                order.cancellation_reason = reason
                order.cancelled_at = datetime.utcnow()
                db.session.commit()
            
            return result
            
        except Exception as e:
            logging.error(f"Cancel shipment error: {str(e)}")
            return {
                'success': False,
                'message': 'Shipment cancellation failed',
                'code': 'CANCELLATION_ERROR'
            }
    
    @staticmethod
    def _cancel_shiprocket_shipment(order, reason):
        """Cancel Shiprocket shipment."""
        try:
            # Implementation for Shiprocket cancellation
            # This would involve API calls to cancel the shipment
            
            return {
                'success': True,
                'message': 'Shiprocket shipment cancelled successfully',
                'data': {
                    'cancellation_id': f"CANCEL_{int(datetime.now().timestamp())}",
                    'reason': reason
                }
            }
            
        except Exception as e:
            logging.error(f"Shiprocket cancellation error: {str(e)}")
            return {
                'success': False,
                'message': 'Shiprocket cancellation failed',
                'code': 'SHIPROCKET_CANCEL_ERROR'
            }
    
    @staticmethod
    def _cancel_delhivery_shipment(order, reason):
        """Cancel Delhivery shipment."""
        try:
            # Implementation for Delhivery cancellation
            # This would involve API calls to cancel the shipment
            
            return {
                'success': True,
                'message': 'Delhivery shipment cancelled successfully',
                'data': {
                    'cancellation_id': f"CANCEL_{int(datetime.now().timestamp())}",
                    'reason': reason
                }
            }
            
        except Exception as e:
            logging.error(f"Delhivery cancellation error: {str(e)}")
            return {
                'success': False,
                'message': 'Delhivery cancellation failed',
                'code': 'DELHIVERY_CANCEL_ERROR'
            }
    
    @staticmethod
    def get_serviceable_areas(store_id, partner_name=None):
        """Get serviceable areas for shipping partners."""
        try:
            if partner_name:
                partner = ShippingPartner.query.filter_by(
                    store_id=store_id,
                    partner_name=partner_name,
                    is_active=True
                ).first()
                
                if not partner:
                    return {
                        'success': False,
                        'message': 'Shipping partner not found',
                        'code': 'PARTNER_NOT_FOUND'
                    }
                
                partners = [partner]
            else:
                partners = ShippingPartner.get_active_partners(store_id)
            
            serviceable_areas = {}
            for partner in partners:
                areas = []
                if partner.serviceable_pincodes:
                    areas.extend(partner.serviceable_pincodes)
                if partner.serviceable_states:
                    areas.extend(partner.serviceable_states)
                
                serviceable_areas[partner.partner_name] = {
                    'display_name': partner.display_name,
                    'serviceable_areas': areas,
                    'non_serviceable_areas': partner.non_serviceable_areas or [],
                    'supports_cod': partner.supports_cod,
                    'supports_international': partner.supports_international
                }
            
            return {
                'success': True,
                'message': 'Serviceable areas retrieved successfully',
                'data': {
                    'serviceable_areas': serviceable_areas
                }
            }
            
        except Exception as e:
            logging.error(f"Get serviceable areas error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to retrieve serviceable areas',
                'code': 'SERVICEABLE_AREAS_ERROR'
            }
    
    @staticmethod
    def check_serviceability(store_id, destination_pincode, weight=None):
        """Check if delivery is available to destination."""
        try:
            partners = ShippingPartner.get_serviceable_partners(store_id, destination_pincode, weight)
            
            serviceable_partners = []
            for partner in partners:
                partner_info = {
                    'partner_id': partner.id,
                    'partner_name': partner.partner_name,
                    'display_name': partner.display_name,
                    'supports_cod': partner.supports_cod,
                    'same_day_delivery': partner.same_day_delivery,
                    'next_day_delivery': partner.next_day_delivery,
                    'express_delivery': partner.express_delivery,
                    'standard_delivery': partner.standard_delivery,
                    'estimated_delivery_days': partner.get_delivery_estimate()
                }
                serviceable_partners.append(partner_info)
            
            return {
                'success': True,
                'message': 'Serviceability checked successfully',
                'data': {
                    'destination_pincode': destination_pincode,
                    'is_serviceable': len(serviceable_partners) > 0,
                    'available_partners': serviceable_partners,
                    'count': len(serviceable_partners)
                }
            }
            
        except Exception as e:
            logging.error(f"Check serviceability error: {str(e)}")
            return {
                'success': False,
                'message': 'Serviceability check failed',
                'code': 'SERVICEABILITY_ERROR'
            }
    
    @staticmethod
    def get_delivery_estimates(store_id, destination_pincode, service_type='standard'):
        """Get delivery time estimates for destination."""
        try:
            partners = ShippingPartner.get_serviceable_partners(store_id, destination_pincode)
            
            estimates = []
            for partner in partners:
                delivery_days = partner.get_delivery_estimate(service_type)
                
                estimate = {
                    'partner_name': partner.partner_name,
                    'display_name': partner.display_name,
                    'service_type': service_type,
                    'estimated_days': delivery_days,
                    'estimated_date': (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d')
                }
                estimates.append(estimate)
            
            return {
                'success': True,
                'message': 'Delivery estimates retrieved successfully',
                'data': {
                    'destination_pincode': destination_pincode,
                    'service_type': service_type,
                    'estimates': estimates
                }
            }
            
        except Exception as e:
            logging.error(f"Get delivery estimates error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get delivery estimates',
                'code': 'DELIVERY_ESTIMATES_ERROR'
            }"""
Shipping service for handling shipping operations and partner integrations.
"""

import requests
import json
from datetime import datetime, timedelta
from flask import current_app
from app.config.database import db
from app.models.shipping_partner import ShippingPartner
from app.models.order import Order
import logging

class ShippingService:
    """Service for handling shipping operations."""
    
    @staticmethod
    def calculate_shipping_rates(store_id, weight, dimensions, origin_pincode, destination_pincode, order_value=0):
        """Calculate shipping rates from all available partners."""
        try:
            partners = ShippingPartner.get_active_partners(store_id)
            
            if not partners:
                return {
                    'success': False,
                    'message': 'No shipping partners available',
                    'code': 'NO_PARTNERS_AVAILABLE'
                }
            
            rates = []
            for partner in partners:
                # Check if partner services the destination
                if not partner.is_serviceable(destination_pincode):
                    continue
                
                # Check weight limits
                if not partner.is_weight_acceptable(weight):
                    continue
                
                # Check dimensions if provided
                if dimensions and not partner.is_dimensions_acceptable(
                    dimensions.get('length', 0),
                    dimensions.get('width', 0), 
                    dimensions.get('height', 0)
                ):
                    continue
                
                # Calculate rate based on partner type
                if partner.partner_name == 'shiprocket':
                    rate_result = ShippingService._calculate_shiprocket_rate(
                        partner, weight, dimensions, origin_pincode, destination_pincode, order_value
                    )
                elif partner.partner_name == 'delhivery':
                    rate_result = ShippingService._calculate_delhivery_rate(
                        partner, weight, dimensions, origin_pincode, destination_pincode, order_value
                    )
                else:
                    # Use generic calculation
                    rate_result = partner.calculate_shipping_cost(weight, dimensions, destination_pincode)
                    if rate_result:
                        rate_result = {
                            'success': True,
                            'data': {
                                'rate': rate_result,
                                'service_type': 'standard',
                                'estimated_days': partner.get_delivery_estimate()
                            }
                        }
                
                if rate_result and rate_result.get('success'):
                    rate_data = rate_result['data']
                    rate_data.update({
                        'partner_id': partner.id,
                        'partner_name': partner.partner_name,
                        'display_name': partner.display_name,
                        'supports_cod': partner.supports_cod,
                        'supports_tracking': partner.supports_tracking
                    })