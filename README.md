# ☕ Face Recognition Cafe System

A modern AI-powered cafe system with face recognition, purchase tracking, and mood-based recommendations.
![Face Recognition Cafe Demo](.docs/images/kasir_face_demo_small.gif)
## Features

- 🎭 **AI Mood-Based Recommendations** - Tell us your mood, get perfect drink suggestions
- 👤 **Face Recognition** - Automatic customer identification and personalized experience
- 📊 **Purchase History** - Track customer preferences and buying patterns
- 🛒 **Smart Cart System** - Intuitive menu selection and checkout process
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile

## Prerequisites

### System Requirements
- Python 3.8+
- Webcam (for face recognition)
- Internet connection (for AI recommendations)

### Required AI Models

The system will automatically download required models on first run, but you can also download manually:

1. **YOLOv8n-face.pt** (Face Detection)
   - Auto-downloads from Ultralytics
   - Manual: [YOLOv8 Face Model](https://github.com/ultralytics/ultralytics)

2. **resnet100.onnx** (Face Recognition)
   - Download: You can find for yourself
   - Place in root project directory

### OpenAI API (for Mood Recommendations)
- Get API key from [OpenAI](https://platform.openai.com/api-keys)
- Set environment variable: `OPENAI_API_KEY=your_api_key_here`

## Quick Start

### 1. Clone and Install

```bash
git clone https://gitlab.com/asal-bapak-senang/kasir-face.git
cd kasir-face
pip install -r requirements.txt
```

### 2. Initialize Database (REQUIRED)

**⚠️ Run this FIRST before starting the application:**

```bash
python init_database.py
```

This will:
- ✅ Create database schema
- ✅ Setup enhanced menu with AI-ready descriptions
- ✅ Add sample customers and purchase history
- ✅ Initialize mood-based recommendation system

### 3. Start Application

```bash
python main.py
```

### 4. Access the System

Open your browser and go to: `http://localhost:5001`

## Usage Guide

### For First-Time Users

1. **Initialize Database**: Run `python init_database.py`
2. **Start Server**: Run `python main.py`
3. **Face Recognition**: Navigate to the camera page and let system recognize you
4. **Menu Selection**: Choose from personalized recommendations or browse all items
5. **Mood Recommendations**: Try the AI mood feature - describe how you feel!
6. **Checkout**: Review cart and complete your order

### For Development

```bash
# Reset database (if needed)
python init_database.py

# Check API endpoints
curl http://localhost:5001/api/menu
curl http://localhost:5001/api/mood-presets
```

## API Endpoints

### Core Endpoints
- `GET /` - Main face recognition page
- `GET /menu` - Menu selection page
- `GET /api/menu` - Get menu items with recommendations
- `POST /api/purchase` - Process order

### Mood-Based AI
- `GET /api/mood-presets` - Get quick mood options
- `POST /api/mood-recommendation` - Custom mood analysis
- `POST /api/mood-recommendation/preset/<mood>` - Preset mood recommendation

## Configuration

### Environment Variables

```bash
# OpenAI API for mood recommendations
OPENAI_API_KEY=your_openai_api_key

# Camera settings (optional)
CAMERA_INDEX=0

# Server settings (optional)  
FLASK_PORT=5001
DEBUG=True
```

### Camera Setup

The system uses your default camera (index 0). If you have multiple cameras:

```python
# In src/config.py
CAMERA_INDEX = 1  # Change to your preferred camera
```

## Troubleshooting

### Common Issues

**Database Error**: Run `python init_database.py` first

**Camera Not Working**: Check camera permissions and ensure no other apps are using it

**AI Recommendations Not Working**: Verify OpenAI API key is set correctly

**404 Image Errors**: Normal - system uses placeholder images for menu items

### Reset Everything

```bash
# Complete reset
python init_database.py
# Select 'y' when prompted to reset existing database
```

## Project Structure

```
kasir-face/
├── src/                    # Core application code
│   ├── database.py        # Database operations
│   ├── mood_matcher.py    # AI mood analysis
│   ├── mood_api.py       # Mood API endpoints
│   └── ...               # Other modules
├── templates/             # HTML templates
├── static/               # CSS, JS, images
├── data/                 # Database and face data
├── init_database.py      # Database initialization (RUN FIRST)
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## Features in Detail

### 🎭 AI Mood Recommendations

The system uses OpenAI's GPT to analyze your mood and recommend the perfect drink:

- **Custom Input**: Describe your feelings in natural language
- **Quick Moods**: Pre-defined mood buttons (tired, stressed, creative, etc.)
- **Smart Matching**: AI considers menu descriptions, your history, and current mood
- **Confidence Scoring**: Shows how confident the AI is in its recommendation

### 👤 Face Recognition

- **Automatic Detection**: Recognizes returning customers instantly
- **Privacy First**: Face data stored locally, no cloud uploads
- **Purchase History**: Remembers your favorite orders
- **Personalized Experience**: Tailored recommendations based on past purchases

### 📊 Analytics & Insights

- **Popular Items**: See what other customers love
- **Personal Stats**: Track your own ordering patterns
- **Recommendation Engine**: Smart suggestions based on behavior

## Contributing

This is a private project. For access or contributions, contact the development team.

## License

Proprietary and confidential. All rights reserved.



**🚀 Ready to get started? Run `python init_database.py` then `python main.py`**


