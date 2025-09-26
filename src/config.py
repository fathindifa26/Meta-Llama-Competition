import os
import cv2
import platform

class Config:
    # Model paths
    YOLO_MODEL_PATH = "yolov8n-face.pt"
    ARCFACE_MODEL_PATH = "iresnet100.onnx"
    
    # Database
    DATABASE_PATH = "data/face_recognition.db"
    
    # Storage paths
    FACES_DIR = "data/faces"
    EMBEDDINGS_DIR = "data/embeddings"
    BACKUP_DIR = "data/backups"
    
    # Create directories
    for directory in [FACES_DIR, EMBEDDINGS_DIR, BACKUP_DIR, "data"]:
        os.makedirs(directory, exist_ok=True)
    # Camera settings
    CAMERA_INDEX = 1  # 1 = external USB webcam, 0 = built-in MacBook camera

    # Auto-detect camera backend based on OS
    system = platform.system().lower()
    if system == "darwin":  # macOS
        CAMERA_API = cv2.CAP_AVFOUNDATION
    elif system == "windows":  # Windows
        CAMERA_API = cv2.CAP_DSHOW  # DirectShow untuk Windows
    elif system == "linux":  # Linux
        CAMERA_API = cv2.CAP_V4L2   # Video4Linux untuk Linux
    else:
        CAMERA_API = cv2.CAP_ANY    # Fallback

    FPS = 15  # Target FPS untuk capture
    BUFFER_SIZE = FPS  # Buffer size untuk face recognition (dalam frame)
    
    # Face detection settings
    MIN_FACE_AREA = 25000     # Minimal area wajah (pixel^2) - ditingkatkan untuk memastikan wajah lebih dekat
    MIN_CONFIDENCE = 0.5      # Minimal confidence score
    MAX_ERRORS = 5           # Maksimal error sebelum dianggap wajah berbeda
    
    # Full face requirements
    MIN_FACE_WIDTH = 150      # Minimal lebar wajah dalam pixel - ditingkatkan
    MIN_FACE_HEIGHT = 150     # Minimal tinggi wajah dalam pixel - ditingkatkan
    MIN_ASPECT_RATIO = 0.5    # Minimal rasio width/height (lebih toleran)
    MAX_ASPECT_RATIO = 1.5    # Maksimal rasio width/height (lebih toleran)
    MIN_CENTER_DIST = 0.15    # Minimal jarak pusat wajah dari tepi frame (15%)
    
    # Face recognition settings
    SIM_THRESHOLD = 0.400  # Threshold untuk similarity wajah (lebih besar = lebih toleran terhadap ekspresi)
    FACE_MEMORY_SECONDS = 1.0  # Berapa detik wajah diingat setelah hilang
    
    # Storage settings
    OUTPUT_DIR = "saved_faces"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Server settings
    HOST = "0.0.0.0"
    PORT = 5001
    
    # UI settings
    MAX_LOGS = 20 