from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import endpoints at the end to avoid circular imports
from app.routes import routes    