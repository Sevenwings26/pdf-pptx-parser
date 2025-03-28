from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from celery import Celery
from flask_caching import Cache
from config import REDIS_URL

db = SQLAlchemy()

api = Api(
    version='1.0',
    title='PDF/PPTx File Parser API',
    description='API Documentation and endpoints for PDF/PPTx File Parser',
    doc='/api/docs/'  # 127:0.1:5000/api/docs/ 
)

celery = Celery()

cache = Cache(config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_URL': REDIS_URL})
