import sys
import os

# Add current directory and backend to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now import the Flask app
try:
    from app import app
    print(f"Successfully imported Flask app from {backend_dir}")
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: create a basic Flask app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return {"message": "Plan Concierge API - Fallback Mode", "status": "running"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)