import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # Upload settings  
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Database settings - absolute path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{os.path.join(INSTANCE_PATH, "app.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ollama LLM settings
    OLLAMA_API_BASE = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
    DEFAULT_LLM_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'qwen3:0.6b')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(Config):
    # Ensure secret key is set in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Use a production database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')

# Dictionary with available configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on environment variable."""
    config_name = os.getenv('FLASK_ENV', 'default')
    return config[config_name]