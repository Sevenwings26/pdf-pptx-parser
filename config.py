# config.py
import os
import decouple
import psycopg2


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = decouple.config("MAX_FILE_SIZE")
ALLOWED_EXTENSIONS = {'pdf', 'pptx'}

# Database configuration
DATABASE_URL = decouple.config('DATABASE_URL')
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'par.db')
# Convert postgres:// to postgresql:// for SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace('postgres://', 'postgresql://')

SECRET_KEY = decouple.config('SECRET_KEY')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 10,
    "max_overflow": 5
}

RABBITMQ_URL = decouple.config('RABBITMQ_URL')
REDIS_URL = decouple.config('REDIS_URL')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


CACHE_DEFAULT_TIMEOUT = 60
CACHE_KEY_PREFIX = 'fileparser_'
