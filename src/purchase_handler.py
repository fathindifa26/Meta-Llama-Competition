from flask import jsonify

class PurchaseHandler:
    @staticmethod
    def process_purchase(current_session, db, logger, state, request):
        """Process purchase order."""
        if not current_session.get('customer_id'):
            return jsonify({'error': 'No customer session'}), 400
        
        data = request.get_json() or {}
        orders = data.get('orders', [])
        
        if not orders:
            return jsonify({'error': 'No items in order'}), 400
        
        try:
            total_amount = 0
            for order in orders:
                menu_id = order.get('menu_id')
                quantity = order.get('quantity', 1)
                
                success = db.add_purchase(current_session['customer_id'], menu_id, quantity)
                if success:
                    # Get menu item for logging
                    menu_items = db.get_menu()
                    menu_item = next((item for item in menu_items if item['id'] == menu_id), None)
                    if menu_item:
                        item_total = menu_item['price'] * quantity
                        total_amount += item_total
                        logger.log(f"Order: {quantity}x {menu_item['name']} = Rp {item_total:,}")
            
            logger.log(f"Total pesanan: Rp {total_amount:,}")
            logger.log("Terima kasih atas kunjungan Anda!")
            
            # Reset session after successful purchase
            current_session.update({
                'customer_id': None, 
                'session_id': None, 
                'status': 'waiting'
            })
            state.reset_state()
            
            return jsonify({
                'status': 'success', 
                'message': 'Order berhasil diproses!',
                'total': total_amount
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500