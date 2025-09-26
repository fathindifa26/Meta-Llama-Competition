import cv2
import numpy as np
from ultralytics import YOLO
from openvino import Core
from scipy.spatial.distance import cosine
from datetime import datetime
import os
from .config import Config
from .database import FaceDatabase
import mediapipe as mp
import numpy as np
import cv2

class FaceProcessor:
    def __init__(self):
        # Initialize YOLO model
        self.model_yolo = YOLO(Config.YOLO_MODEL_PATH, verbose=False)
        
        # Initialize ArcFace model
        ie = Core()
        ov_model = ie.read_model(model=Config.ARCFACE_MODEL_PATH)
        self.compiled_model = ie.compile_model(model=ov_model, device_name="CPU")
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        
        # Initialize database instead of file system
        self.db = FaceDatabase()

        # Initialize buffers and state
        self.embedding_buffer = []
        self.current_face_id = None  # ID wajah yang sedang ditrack
        self.reference_embedding = None  # Embedding referensi untuk wajah yang sedang ditrack
        self.no_face_counter = 0
        self.error_count = 0
        self.face_changed = False  # Flag untuk menandai pergantian wajah
        self.saved_records = self.load_saved_records()
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def load_saved_records(self):
        """Load saved face embeddings from database."""
        return self.db.get_all_embeddings()  # Returns [(customer_id, embedding), ...]
    
    def is_full_face(self, frame, x1, y1, x2, y2):
        """Check if detected face meets full face requirements."""
        frame_h, frame_w = frame.shape[:2]
        face_w = x2 - x1
        face_h = y2 - y1
        
        # Check minimum dimensions
        if face_w < Config.MIN_FACE_WIDTH or face_h < Config.MIN_FACE_HEIGHT:
            return False
            
        # Check aspect ratio (width/height should be close to 1 for a full face)
        aspect_ratio = face_w / face_h
        if aspect_ratio < Config.MIN_ASPECT_RATIO or aspect_ratio > Config.MAX_ASPECT_RATIO:
            return False
            
        # Check if face is centered enough in frame
        face_center_x = (x1 + x2) / 2 / frame_w
        face_center_y = (y1 + y2) / 2 / frame_h
        
        min_dist = Config.MIN_CENTER_DIST
        if (face_center_x < min_dist or face_center_x > (1 - min_dist) or
            face_center_y < min_dist or face_center_y > (1 - min_dist)):
            return False
            
        return True
    
    def detect_faces(self, frame):
        """Detect faces and return the best one based on confidence and size."""
        results = self.model_yolo(frame, verbose=False)
        best_det = None
        max_score = -1
        
        for res in results:
            for b in res.boxes:
                cls = int(b.cls[0])
                if self.model_yolo.names[cls].lower() not in ("face","person"):
                    continue
                    
                conf = float(b.conf[0])
                x1,y1,x2,y2 = map(int, b.xyxy[0])
                area = (x2-x1)*(y2-y1)
                
                # Hanya proses wajah yang memenuhi semua kriteria
                if (area >= Config.MIN_FACE_AREA and 
                    conf >= Config.MIN_CONFIDENCE and 
                    self.is_full_face(frame, x1, y1, x2, y2)):
                    
                    score = conf * (area / Config.MIN_FACE_AREA)  # Weight by area
                    if score > max_score:
                        max_score = score
                        best_det = (conf, (x1,y1,x2,y2))
        
        return (True, *best_det) if best_det else (False, None, (0,0,0,0))
    
    def preprocess_face(self, img):
        """Preprocess face image for the model."""
        face = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face = cv2.resize(face, (112,112))
        face = face.astype(np.float32) / 255.0
        face = (face - 0.5)/0.5
        return np.transpose(face, (2,0,1))[None,:,:,:]
    
    def align_face(self, frame, bbox):
        try:
            # ArcFace 5-point template
            arcface_template = np.array([
                [38.2946, 51.6963],
                [73.5318, 51.5014],
                [56.0252, 71.7366],
                [41.5493, 92.3655],
                [70.7299, 92.2041]
            ], dtype=np.float32)

            x1, y1, x2, y2 = bbox
            face_img = frame[y1:y2, x1:x2]
            
            # Check if face crop is valid
            if face_img.size == 0 or face_img.shape[0] == 0 or face_img.shape[1] == 0:
                return cv2.resize(frame[max(0,y1):min(frame.shape[0],y2), 
                                      max(0,x1):min(frame.shape[1],x2)], (112, 112))
            
            h, w = face_img.shape[:2]

            results = self.face_mesh.process(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
            if not results.multi_face_landmarks:
                return cv2.resize(face_img, (112, 112))
                
            landmarks = results.multi_face_landmarks[0].landmark

            # 5 landmark points
            idx = [33, 263, 1, 61, 291]
            src_points = np.array([
                [landmarks[i].x * w, landmarks[i].y * h] for i in idx
            ], dtype=np.float32)

            # Check if landmarks are valid
            if np.any(np.isnan(src_points)):
                return cv2.resize(face_img, (112, 112))

            M = cv2.estimateAffinePartial2D(src_points, arcface_template)[0]
            if M is None:
                return cv2.resize(face_img, (112, 112))
                
            aligned = cv2.warpAffine(face_img, M, (112, 112), borderValue=0.0)
            return aligned
                
        except Exception as e:
            print(f"Face alignment failed: {str(e)}")
            return cv2.resize(face_img, (112, 112))
    
    def process_face(self, frame, bbox):
        """Extract embedding from face image with alignment."""
        # Align face first
        aligned_face = self.align_face(frame, bbox)
        # Then preprocess
        inp = self.preprocess_face(aligned_face)
        # Get embedding
        out = self.compiled_model({self.input_layer: inp})
        return out[self.output_layer][0]
    
    def find_visit(self, emb):
        """Find if embedding matches any saved records."""
        best_match = (False, None, 1.0)  # (found, customer_id, similarity)
        for customer_id, s in self.saved_records:
            similarity = cosine(emb, s)
            if similarity < Config.SIM_THRESHOLD and similarity < best_match[2]:
                best_match = (True, customer_id, similarity)
        return best_match
    
    def update_buffer(self, current_emb=None):
        """Update embedding buffer and check stability."""
        if current_emb is None:
            # No face detected
            self.no_face_counter += 1
            if self.no_face_counter >= Config.BUFFER_SIZE:
                # Reset everything if no face for full buffer duration
                self.embedding_buffer.clear()
                self.error_count = 0
                self.no_face_counter = 0
                self.current_face_id = None
                self.reference_embedding = None
                self.face_changed = False
                return True  # Signal to reset state
            return False
            
        self.no_face_counter = 0  # Reset no-face counter
        
        # Jika buffer kosong, mulai buffer baru
        if not self.embedding_buffer:
            self.embedding_buffer.append(current_emb)
            return False
            
        # Cek similarity dengan reference embedding jika ada
        if self.reference_embedding is not None:
            ref_similarity = cosine(current_emb, self.reference_embedding)
            if ref_similarity > Config.SIM_THRESHOLD:
                self.error_count += 1
                if self.error_count >= Config.MAX_ERRORS:
                    # Wajah sudah berbeda dengan referensi
                    self.embedding_buffer = [current_emb]
                    self.error_count = 0
                    self.current_face_id = None
                    self.reference_embedding = None
                    self.face_changed = True
                    return False
        
        # Update buffer
        self.embedding_buffer.append(current_emb)
        if len(self.embedding_buffer) > Config.BUFFER_SIZE:
            self.embedding_buffer.pop(0)
            
        # Cek stabilitas buffer
        buffer_stable = len(self.embedding_buffer) >= Config.BUFFER_SIZE
        
        # Jika buffer penuh dan belum ada reference embedding, set reference
        if buffer_stable and self.reference_embedding is None and self.error_count == 0:
            # Gunakan rata-rata embedding dalam buffer sebagai referensi
            self.reference_embedding = np.mean(self.embedding_buffer, axis=0)
            self.reference_embedding /= np.linalg.norm(self.reference_embedding)
            
        return buffer_stable and self.error_count == 0
    
    def save_face(self, embedding, face_img):
        """Save new face embedding and image to database."""
        customer_id = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        # Calculate quality scores
        quality_score = self.calculate_quality_score(face_img)
        confidence_score = 0.9  # Default high confidence for saved faces
        
        # Save to database
        success = self.db.add_customer(customer_id, face_img, embedding, confidence_score)
        
        if success:
            # Update in-memory records
            self.saved_records.append((customer_id, embedding))
            return customer_id
        return None
    
    def calculate_quality_score(self, face_img):
        """Calculate face quality score.""" # <-- Add this method
        if face_img is None or face_img.size == 0:
            return 0.0
        
        # Simple quality assessment based on image properties
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        # Blur detection using Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_factor = min(blur_score / 100, 1.0)
        
        # Brightness assessment
        brightness = np.mean(gray)
        if 50 <= brightness <= 200:
            brightness_factor = 1.0
        else:
            brightness_factor = max(0.3, 1.0 - abs(brightness - 125) / 125)
        
        # Size factor
        h, w = face_img.shape[:2]
        size_factor = min(w * h / (150 * 150), 1.0)
        
        return np.mean([blur_factor, brightness_factor, size_factor])
    