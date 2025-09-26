import cv2
from flask import Flask, Response, request, jsonify, render_template, redirect, url_for
from datetime import datetime
import time
import os

from .config import Config
from .face_processor import FaceProcessor
from .logger import Logger
from .state_manager import StateManager
from .database import FaceDatabase
from .camera_handler import CameraHandler  # Import baru
from .recognition_handler import RecognitionHandler  # Import baru
from .purchase_handler import PurchaseHandler  # Import baru
from .mood_api import create_mood_api # Import baru

# Tentukan path untuk templates dan static folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'face_recognition_cafe_secret_key'

# Inisialisasi komponen-komponen utama
face_processor = FaceProcessor()  # Menangani deteksi dan pengenalan wajah
logger = Logger()                # Menangani logging pesan
state = StateManager()           # Mengelola state program
db = FaceDatabase()              # Database

# Initialize handlers
camera_handler = CameraHandler(logger)
recognition_handler = RecognitionHandler(face_processor, state, db, logger)

# Register mood API blueprint
mood_bp = create_mood_api(db)
app.register_blueprint(mood_bp)


# Global variable untuk session management
current_session = {
    'customer_id': None,
    'session_id': None,
    'status': 'waiting'
}

@app.route('/')
def index():
    """Main route - Face Recognition page."""
    return render_template('face_recognition.html')

@app.route('/menu')
def menu():
    """Menu selection page."""
    if not current_session.get('customer_id'):
        return redirect(url_for('index'))
    return render_template('menu_selection.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_frames():
    """Generate video frames - now much cleaner!"""
    global current_session
    
    try:
        # Initialize camera
        if not camera_handler.initialize_camera():
            return
        
        while True:
            # Read frame
            ret, frame = camera_handler.read_frame()
            if not ret or frame is None:
                break
            
            # Process face detection and recognition
            current_session, bbox, face_found = recognition_handler.process_face_detection(
                frame, current_session
            )
            
            # Draw face rectangle if detected
            if face_found and bbox:
                camera_handler.draw_face_rectangle(frame, bbox, state.buffer_stable)
            
            # Encode and yield frame
            frame_bytes = camera_handler.encode_frame(frame)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        camera_handler.release()
        
    except Exception as e:
        logger.log(f"❌ Error: {e}")
        camera_handler.release()

@app.route('/api/recognition_status')
def get_recognition_status():
    """Get current recognition status."""
    return jsonify(current_session)

@app.route('/api/menu')
def get_menu():
    """Get menu items with recommendations."""
    try:
        customer_id = current_session.get('customer_id')
        
        # Always get all menu items
        all_menu = db.get_menu()
        most_popular = db.get_most_popular_item()
        
        # ✅ Check if menu has mood tags (indicating mood features available)
        has_mood_features = any(item.get('mood_tags') for item in all_menu)

        if customer_id:
            # Logged-in customer - get personalized recommendations
            last_purchase = db.get_last_purchase_item(customer_id)
            
            return jsonify({
                'last_purchase': last_purchase,
                'most_popular': most_popular,
                'has_mood_features': has_mood_features, # ✅ Indicate if mood features are available
                'all_menu': all_menu, # ✅ Always include all_menu
                'customer_id': customer_id
            })
        else:
            # Guest user - only recommendations without last_purchase
            return jsonify({
                'last_purchase': None,
                'most_popular': most_popular,
                'all_menu': all_menu,  # ✅ Always include all_menu
                'has_mood_features': has_mood_features,
                'customer_id': None
            })
            
    except Exception as e:
        print(f"❌ Menu API Error: {e}")  # Debug print
        # Fallback - at least return basic menu
        try:
            return jsonify({
                'last_purchase': None,
                'most_popular': None,
                'all_menu': db.get_menu(),
                'has_mood_features': False,
                'error': str(e)
            })
        except:
            return jsonify({'error': str(e)}), 500

@app.route('/api/purchase', methods=['POST'])
def make_purchase():
    """Handle purchase order."""
    return PurchaseHandler.process_purchase(current_session, db, logger, state, request)

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    """Reset current session."""
    global current_session
    current_session = {'customer_id': None, 'session_id': None, 'status': 'waiting'}
    state.reset_state()
    return jsonify({'status': 'reset'})

@app.route('/logs')
def get_logs():
    """Get current logs."""
    return jsonify(logger.get_logs())

# Reset database route (for development)
@app.route('/reset_db')
def reset_database():
    """Reset database and populate with menu items."""
    db.reset_database()
    return jsonify({'status': 'Database reset successfully!'})

@app.route('/mood-menu')
def mood_menu():
    """Mood-based menu selection page."""
    return render_template('mood_menu.html')