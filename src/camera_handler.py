import cv2
import time
from datetime import datetime
from .config import Config

class CameraHandler:
    def __init__(self, logger):
        self.logger = logger
        self.cap = None
        
    def initialize_camera(self):
        """Initialize camera with fallback."""
        self.cap = cv2.VideoCapture(Config.CAMERA_INDEX, Config.CAMERA_API)
        
        if not self.cap.isOpened():
            self.logger.log("⚠️ External webcam tidak terdeteksi, mencoba menggunakan built-in camera...")
            self.cap = cv2.VideoCapture(0, Config.CAMERA_API)
            
            if not self.cap.isOpened():
                self.logger.log("❌ Error: Tidak ada kamera yang terdeteksi!")
                return False
            else:
                self.logger.log("✅ Menggunakan built-in camera")
        else:
            self.logger.log("✅ Menggunakan external webcam")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FPS, Config.FPS)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        time.sleep(2)
        return True
        
    def read_frame(self):
        """Read frame from camera with error handling."""
        if not self.cap:
            return None, None
            
        ret, frame = self.cap.read()
        if not ret or frame is None or frame.size == 0:
            self.logger.log("❌ Error: Gagal membaca frame dari kamera")
            return None, None
            
        return ret, frame
    
    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            
    def draw_face_rectangle(self, frame, bbox, is_stable):
        """Draw face detection rectangle."""
        x1, y1, x2, y2 = bbox
        color = (0, 255, 0) if is_stable else (255, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
    def encode_frame(self, frame):
        """Encode frame to JPEG bytes."""
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            return buffer.tobytes()
        return None