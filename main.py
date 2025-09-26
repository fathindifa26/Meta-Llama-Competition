import argparse
from src.app import app
from src.config import Config

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=Config.HOST,
                       help='Host for Flask server')
    parser.add_argument('--port', type=int, default=Config.PORT,
                       help='Port for Flask server')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, threaded=True) 