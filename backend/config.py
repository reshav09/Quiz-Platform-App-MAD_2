"""
Configuration settings for the Quiz Master application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///quiz_master.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours by default
    
    # Redis and Celery settings (local development defaults)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Email settings (file-based simulation for development)
    EMAIL_SIMULATION_MODE = os.environ.get('EMAIL_SIMULATION_MODE', 'true').lower() == 'true'
    EMAIL_SIMULATION_DIR = os.environ.get('EMAIL_SIMULATION_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_simulation'))
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Application settings
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 10))
    QUIZ_TIME_LIMIT_DEFAULT = int(os.environ.get('QUIZ_TIME_LIMIT_DEFAULT', 30))  # minutes
    
    # Security settings
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Override for development
    EMAIL_SIMULATION_MODE = True
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    EMAIL_SIMULATION_MODE = True
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    EMAIL_SIMULATION_MODE = False
    SQLALCHEMY_ECHO = False

# Configuration dictionary for different environments
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig
}

# Default configuration
def get_config():
    """Get the current configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'dev')
    return config_by_name.get(env, DevelopmentConfig)
