import os
import logging
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "komalmusic")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

# Import routes after app creation to avoid circular imports
from routes.api import api_bp
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

@app.errorhandler(404)
def not_found(error):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500
