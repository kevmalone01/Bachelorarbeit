from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from app.db import db
import os

# Create extensions instances
migrate = Migrate()

def create_app(config_object=None):
    """Application factory pattern to create Flask app instance"""
    app = Flask(__name__)
    
    # Enable CORS with more detailed configuration
    CORS(app, resources={r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    }})
    
    # Load configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        # Import and load the default configuration
        from config import get_config
        app.config.from_object(get_config())
    
    # Ensure instance folder exists
    instance_path = getattr(app.config, 'INSTANCE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance'))
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
    
    # Debug: Print database path
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Instance path: {instance_path}")
    print(f"App instance path: {app.instance_path}")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Add redirect for direct document routes (without /api prefix)
    @app.route('/documents/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def document_redirect(subpath):
        from flask import redirect, request
        # Redirect to the same route with /api prefix
        url = f"/api/documents/{subpath}"
        if request.query_string:
            url += f"?{request.query_string.decode('utf-8')}"
        return redirect(url, code=307)  # 307 preserves method and body
    
    @app.route('/documents/preview-temp', methods=['POST'])
    def document_preview_temp_redirect():
        from flask import redirect
        return redirect('/api/documents/preview-temp', code=307)  # 307 preserves method and body
    
    # Add redirect for client routes (without /api prefix)
    @app.route('/clients', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def clients_redirect():
        from flask import redirect, request
        url = "/api/clients"
        if request.query_string:
            url += f"?{request.query_string.decode('utf-8')}"
        return redirect(url, code=307)  # 307 preserves method and body
    
    @app.route('/clients/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def client_detail_redirect(subpath):
        from flask import redirect, request
        url = f"/api/clients/{subpath}"
        if request.query_string:
            url += f"?{request.query_string.decode('utf-8')}"
        return redirect(url, code=307)  # 307 preserves method and body
    
    @app.route('/')
    def index():
        return "Welcome to Flask API with SQLAlchemy"
    
    return app 