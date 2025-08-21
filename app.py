import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize in-memory storage
from models import init_storage
init_storage()

# Import routes
from routes.main_routes import main_bp
from routes.api_routes import api_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/healthz')
def health_check():
    return {'status': 'healthy'}, 200
