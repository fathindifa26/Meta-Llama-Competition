from datetime import datetime

class RecognitionHandler:
    def __init__(self, face_processor, state_manager, database, logger):
        self.face_processor = face_processor
        self.state = state_manager
        self.db = database
        self.logger = logger
        
    def process_face_detection(self, frame, current_session):
        """Process face detection and recognition logic."""
        face_found, confidence, bbox = self.face_processor.detect_faces(frame)
        x1, y1, x2, y2 = bbox
        
        if face_found:
            return self._handle_face_found(frame, bbox, current_session)
        else:
            return self._handle_no_face(current_session), bbox, False
            
    def _handle_face_found(self, frame, bbox, current_session):
        """Handle when face is detected."""
        x1, y1, x2, y2 = bbox
        face_img = frame[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return current_session, bbox, False
            
        current_emb = self.face_processor.process_face(frame, bbox)
        buffer_full = self.face_processor.update_buffer(current_emb)
        
        if not self.state.face_in_frame:
            self.state.face_in_frame = True
            
        if buffer_full and not self.state.buffer_stable:
            self.state.buffer_stable = True
            return self._process_recognition(current_emb, face_img, current_session)
            
        return current_session, bbox, True
        
    def _handle_no_face(self, current_session):
        """Handle when no face is detected."""
        if self.state.face_in_frame:
            self.logger.log("Wajah tidak terdeteksi")
            self.state.face_in_frame = False
            self.state.buffer_stable = False
        
        if self.face_processor.update_buffer(None):
            if current_session['customer_id']:
                self.logger.log("Face recognition session timeout")
                
        return current_session
        
    def _process_recognition(self, current_emb, face_img, current_session):
        """Process face recognition logic."""
        visited, customer_id, similarity = self.face_processor.find_visit(current_emb)
        
        if visited:
            return self._handle_existing_customer(customer_id, current_session)
        else:
            return self._handle_new_customer(current_emb, face_img, current_session)
            
    def _handle_existing_customer(self, customer_id, current_session):
        """Handle existing customer recognition."""
        customer = self.db.get_customer(customer_id)
        if customer:
            current_session['customer_id'] = customer_id
            current_session['status'] = 'recognized'
            self.state.set_current_visit(customer_id)
            
            first_visit = datetime.fromisoformat(customer['first_seen']).strftime("%d-%m-%Y %H:%M:%S")
            last_purchases = self.db.get_customer_purchases_with_menu(customer_id)
            
            msg = f"Selamat datang kembali! Member sejak {first_visit}"
            if last_purchases:
                last_item = last_purchases[0]['menu_name']
                msg += f"\nTerakhir pesan: {last_item}"
            self.logger.log(msg)
            
        return current_session, None, True
        
    def _handle_new_customer(self, current_emb, face_img, current_session):
        """Handle new customer registration."""
        customer_id = self.face_processor.save_face(current_emb, face_img)
        if customer_id:
            current_session['customer_id'] = customer_id
            current_session['status'] = 'new_customer'
            self.state.set_current_visit(customer_id, is_new=True)
            self.logger.log("Selamat datang! Anda customer baru. Silakan pilih menu favorit Anda!")
            
        return current_session, None, True