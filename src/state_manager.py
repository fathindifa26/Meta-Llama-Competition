from datetime import datetime
from .database import FaceDatabase  
import json
import os

class StateManager:
    def __init__(self):
        self.current_id_ts = None      # ID wajah yang sedang terdeteksi
        self.first_visit_time = None   # Waktu pertama kali wajah terdeteksi
        self.last_face_time = None     # Waktu terakhir wajah terdeteksi
        self.face_in_frame = False     # Status wajah dalam frame
        self.buffer_stable = False     # Status buffer stabil
        self.db = FaceDatabase()

    def reset_state(self):
        """Reset state ketika wajah hilang terlalu lama."""
        self.current_id_ts = None
        self.first_visit_time = None
        self.last_face_time = None
        self.face_in_frame = False
        self.buffer_stable = False
        
    def update_face_time(self):
        """Update waktu terakhir wajah terdeteksi."""
        self.last_face_time = datetime.now()
        
    def set_current_visit(self, ts, is_new=False):
        """Set informasi kunjungan saat ini."""
        self.current_id_ts = ts
        if is_new or not self.first_visit_time:
            self.first_visit_time = ts
        self.update_face_time()
        
    def get_last_purchase(self, customer_id):
        """Ambil pembelian terakhir dari database.""" # <-- Update method
        purchases = self.db.get_customer_purchases(customer_id)
        return purchases[0] if purchases else None
    
    def get_last_visit_time(self):
        """Get formatted last visit time."""
        if self.last_face_time:
            return self.last_face_time.strftime("%d-%m-%Y %H:%M:%S")
        return None 