app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── routes.py      # REST API endpoints
│   └── models.py     # API data models
├── web/
│   ├── __init__.py
│   ├── routes.py      # Web interface routes
│   └── templates/     # HTML templates
│       └── index.html
├── README.md
├── .env
├── parser.py          # Shared parsing logic
└── config.py          # Configuration
└── extensions.py    

I am working on a pdf/pptx parser using flask - i have a web and api interface... I want you to sacn to the project files, check for errors and if they are communicating correctly, before production.... Here is the file structure --- 
app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── routes.py
├── web/
│   ├── __init__.py
│   └── models.py
│   ├── routes.py
│   └── templates/
│       └── index.html
├── tasks/           
│   ├── __init__.py
│   └── celery.py
├── services/        
│   ├── __init__.py
│   ├── file_service.py
│   └── queue_service.py
├── parser.py
├── config.py
├── extensions.py
├── requirements.txt 
├── Dockerfile         
├── docker-compose.yml 
├── .env.example       
└── README.md



Backend: 
● API Design: Design and implement a REST API endpoint using a Python framework 
(Please use Flask for this assessment) that accepts file uploads (PDF or PowerPoint) 
and securely saves them to a designated storage location (use the local filesystem 
for this assessment). 
● Data Parsing: Develop a module that utilizes libraries like Apache POI (for PPTX) or 
PyPDF2 (for PDF) to parse the uploaded documents. 
Extract relevant information like 
slide titles, text content, and any embedded metadata. 

● Data Storage: Implement a database schema or data model (e.g., using a relational 
database like PostgreSQL or a NoSQL database like MongoDB) to store the 
extracted information for future retrieval and analysis.

● Error Handling: Ensure robust error handling and validation to address scenarios 
such as: 
○ Unsupported file formats 
○ Corrupted files 
○ Exceeding file size limits 
○ Database connection issues 
● Deployment File: Build a deployment file using docker compose, with at least an API 
Gateway or Broker service, a Parsing service and a database Service. 
Demonstrating your knowledge of a cache service and a queuing service will be a 
plus.


Title 

Description: 

Installation 

pip install flask
pip install Werkzeug
pip install python-decouple
pip install psycopg2
pip install flask-sqlalchemy 
pip install python-pptx
pip install PyPDF2
pip install flask-restx

relevant info like:
--- slide titles, text content, and any embedded metadata. 





I am working on a pdf/pptx parser using flask - I have a web and api interface... I want you to scan through the project files, check for errors and if they are communicating and connected correctly, before production.... It handles queueing, caching operations.. Here is the file structure --- 
app/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── routes.py
├── web/
│   ├── __init__.py
│   └── models.py
│   ├── routes.py
│   └── templates/
│       └── index.html
├── tasks/           
│   ├── __init__.py
│   └── celery.py
├── services/        
│   ├── __init__.py
│   ├── file_service.py
│   └── queue_service.py
├── parser.py
├── config.py
├── extensions.py
├── requirements.txt 
├── Dockerfile         
├── docker-compose.yml 
├── .env
├── run.py
config.py --# config.py
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

RABBITMQ_URL = decouple.config('RABBITMQ_URL')
REDIS_URL = decouple.config('REDIS_URL')
# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CACHE_DEFAULT_TIMEOUT = 60
CACHE_KEY_PREFIX = 'fileparser_'
extensions.py -- from flask_sqlalchemy import SQLAlchemy
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
parser.py --- import pptx
from PyPDF2 import PdfReader
# Extract pdf data 
def extract_pdf_data(file_path):
    content = [] # to store extracted text
    try:
        with open(file_path, 'rb') as file: # read in binary mode
            reader = PdfReader(file)
            for page in reader.pages:
                content.append(page.extract_text())
        # return content
    except Exception as e:
        return None, f"PDF parsing failed: {str(e)}"
    return "\n".join(content), None


# Extract pptx data
def extract_pptx_data(file_path):
    content = [] # to store extracted text
    try:
        presentation = pptx.Presentation(file_path)
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    content.append(shape.text)
        # return content
    except Exception as e:
        return None, f"PPTx parsing failed: {str(e)}"

    return "\n".join(content), None
run.py -- from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from extensions import db
        db.create_all()
    app.run(debug=True)
api/routes.py -- from . import api_ns
from flask_restx import fields, Resource
from flask import request, current_app
from extensions import db, cache
from web.models import FileUploaded, ParsedData
from services.queue_services import QueueService
from services.file_service import FileService
import os
from datetime import datetime
import uuid
from config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

# Response Models
upload_model = api_ns.model('UploadedFile', {
    'id': fields.Integer(description="File ID"),
    'filename': fields.String(required=True, description='Uploaded file name'),
    'file_type': fields.String(description="File type (PDF/PPTX)"),
    'upload_date': fields.DateTime(description="Upload timestamp"),
    'status': fields.String(description="Processing status")
})

parsed_model = api_ns.model('ParsedFile', {
    'parsed_id': fields.Integer(description="Parsed File ID"),
    'file_id': fields.Integer(description="ID of the uploaded file"),
    'content': fields.String(description="Extracted text content"),
    'processing_time': fields.Float(description="Processing duration in seconds")
})

status_model = api_ns.model('ProcessingStatus', {
    'file_id': fields.Integer,
    'status': fields.String,
    'queue_position': fields.Integer,
    'estimated_wait': fields.Float
})

@api_ns.route('/upload/')
class UploadFile(Resource):
    @api_ns.doc(description="Upload PDF or PPTX files")
    @api_ns.response(202, 'Accepted', upload_model)
    @api_ns.response(400, 'Bad Request')
    @api_ns.response(500, 'Internal Server Error')
    def post(self):
        """Queue file for processing"""
        if 'file' not in request.files:
            return {'error': 'No file part'}, 400
        
        file = request.files['file']
        if file.filename == "":
            return {'error': 'No selected file'}, 400
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return {'error': 'File too large. Max file size is 12MB'}, 400
        
        # Validate extension
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            return {'error': 'Unsupported file extension. Only PDF or PPTX are allowed'}, 400

        try:
            # Save file through service layer
            uploaded_file = FileService.save_file(file)
            
            # Queue processing
            task_id = QueueService.enqueue_file_processing(
                file_path=os.path.join(UPLOAD_FOLDER, uploaded_file.filename),
                file_ext=file_ext,
                file_id=uploaded_file.id
            )
            
            # Cache initial status
            cache.set(f"file_{uploaded_file.id}_status", "queued", timeout=3600)
            
            return {
                'id': uploaded_file.id,
                'filename': uploaded_file.filename,
                'file_type': file_ext,
                'upload_date': uploaded_file.upload_date.isoformat(),
                'status': 'queued',
                'task_id': task_id,
                'status_url': f'/api/files/{uploaded_file.id}/status'
            }, 202
            
        except Exception as e:
            current_app.logger.error(f"Upload failed: {str(e)}")
            return {'error': str(e)}, 500

@api_ns.route('/files/<int:file_id>/status')
class FileStatus(Resource):
    @api_ns.doc(description="Check processing status")
    @api_ns.marshal_with(status_model)
    @cache.cached(timeout=10, key_prefix='file_status_%s')
    def get(self, file_id):
        """Get processing status"""
        status = QueueService.get_processing_status(file_id)
        return {
            'file_id': file_id,
            'status': status.get('status', 'unknown'),
            'queue_position': status.get('position', 0),
            'estimated_wait': status.get('wait_time', 0)
        }

@api_ns.route('/files')
class FileList(Resource):
    @api_ns.doc(description="List all files")
    @api_ns.marshal_list_with(upload_model)
    @cache.cached(timeout=60)
    def get(self):
        """Get all uploaded files with status"""
        files = FileUploaded.query.order_by(FileUploaded.upload_date.desc()).all()
        return [{
            'id': f.id,
            'filename': f.filename,
            'file_type': f.file_type,
            'upload_date': f.upload_date,
            'status': cache.get(f"file_{f.id}_status") or "pending"
        } for f in files]

@api_ns.route('/parsed/<int:file_id>')
class ParsedContent(Resource):
    @api_ns.doc(description="Get parsed content")
    @api_ns.marshal_with(parsed_model)
    @cache.cached(timeout=300, key_prefix='parsed_content_%s')
    def get(self, file_id):
        """Get parsed file content"""
        parsed_data = ParsedData.query.filter_by(file_id=file_id).first_or_404()
        return {
            'parsed_id': parsed_data.id,
            'file_id': parsed_data.file_id,
            'content': parsed_data.content,
            'processing_time': parsed_data.processing_time
        } services/file_service.py -- import os
from datetime import datetime
import uuid
from tasks.celery import process_file
from extensions import db
from web.models import FileUploaded

class FileService:
    @staticmethod
    def save_and_process(file):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%I-%M%p')}_{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        # Save to DB
        uploaded_file = FileUploaded(filename=unique_filename, file_type=file_ext)
        db.session.add(uploaded_file)
        db.session.commit()
        
        # Queue processing
        process_file.delay(file_path, file_ext, uploaded_file.id)
        
        return uploaded_file
    services/queue_service.py --- import os
from datetime import datetime
import uuid
from extensions import db, celery
from web.models import FileUploaded, ParsedData
from parser import extract_pdf_data, extract_pptx_data
from flask import current_app
from time import sleep
import redis
from functools import wraps

# Initialize Redis connection pool
redis_pool = redis.ConnectionPool.from_url(current_app.config['REDIS_URL'])
redis_client = redis.Redis(connection_pool=redis_pool)

def rate_limited(max_per_minute):
    """Decorator to limit task execution rate"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"rate_limit:{func.__name__}"
            current = redis_client.get(key)
            
            if current and int(current) >= max_per_minute:
                sleep(60)  # Wait a minute if limit reached
                redis_client.delete(key)
            
            with redis_client.pipeline() as pipe:
                pipe.incr(key)
                pipe.expire(key, 60)
                pipe.execute()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class QueueService:
    @staticmethod
    def enqueue_file_processing(file_path, file_ext, file_id):
        """
        Enqueue file for processing with retry and priority handling
        """
        try:
            # Cache the file metadata before processing
            cache_key = f"file:{file_id}:meta"
            redis_client.hset(
                cache_key,
                mapping={
                    'path': file_path,
                    'ext': file_ext,
                    'status': 'queued'
                }
            )
            redis_client.expire(cache_key, 3600)  # Expire in 1 hour
            
            # Enqueue the processing task with priority
            priority = 1 if file_ext == 'pdf' else 2  # Higher priority for PDFs
            task = process_file.apply_async(
                args=(file_path, file_ext, file_id),
                queue='parsing',
                priority=priority,
                retry=True,
                retry_policy={
                    'max_retries': 3,
                    'interval_start': 10,
                    'interval_step': 30,
                    'interval_max': 300,
                }
            )
            
            return task.id
        
        except Exception as e:
            current_app.logger.error(f"Failed to enqueue file: {str(e)}")
            raise

    @staticmethod
    @celery.task(bind=True, base=celery.Task)
    @rate_limited(max_per_minute=30)  # Limit to 30 tasks per minute
    def process_file(self, file_path, file_ext, file_id):
        """
        Process file content and save to database
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Parse based on file type
            if file_ext == "pdf":
                content = extract_pdf_data(file_path)
            elif file_ext == "pptx":
                content = extract_pptx_data(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Save parsed content
            with db.session.begin():
                parsed_data = ParsedData(
                    file_id=file_id,
                    content=content,
                    status='completed'
                )
                db.session.add(parsed_data)
            
            # Update cache
            cache_key = f"file:{file_id}:meta"
            redis_client.hset(cache_key, 'status', 'completed')
            
            return {
                'file_id': file_id,
                'status': 'completed',
                'content_length': len(content)
            }
            
        except Exception as e:
            # Update cache with error
            cache_key = f"file:{file_id}:meta"
            redis_client.hset(cache_key, 'status', 'failed')
            redis_client.hset(cache_key, 'error', str(e))
            
            current_app.logger.error(f"Failed to process file {file_id}: {str(e)}")
            raise self.retry(exc=e)

    @staticmethod
    def get_processing_status(file_id):
        """
        Check processing status from Redis cache
        """
        cache_key = f"file:{file_id}:meta"
        status = redis_client.hgetall(cache_key)
        
        if not status:
            return {'status': 'not_found'}
        
        return {
            'status': status.get(b'status', b'unknown').decode(),
            'error': status.get(b'error', b'').decode(),
            'path': status.get(b'path', b'').decode(),
            'ext': status.get(b'ext', b'').decode()
        }

    @staticmethod
    def cleanup_file(file_id):
        """
        Clean up file and cache after processing
        """
        cache_key = f"file:{file_id}:meta"
        file_info = redis_client.hgetall(cache_key)
        
        if file_info and b'path' in file_info:
            try:
                os.remove(file_info[b'path'].decode())
            except OSError:
                pass
        
        redis_client.delete(cache_key)
        tasks/celery.py --- from celery import Celery
from extensions import db
from . import config
from parser import extract_pdf_data, extract_pptx_data
from web.models import ParsedData


celery = Celery(__name__)
celery.conf.broker_url = config.RABBITMQ_URL
celery.conf.result_backend = config.REDIS_URL

@celery.task(bind=True)
def process_file(self, file_path, file_ext, file_id):
    try:
        if file_ext == "pdf":
            content = extract_pdf_data(file_path)
        elif file_ext == "pptx":
            content = extract_pptx_data(file_path)
        
        with db.app.app_context():
            parsed_data = ParsedData(file_id=file_id, content=content)
            db.session.add(parsed_data)
            db.session.commit()
        return True
    except Exception as e:
        self.retry(exc=e, countdown=60)
web/models.py --- # from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extensions import db
# db = SQLAlchemy()

class FileUploaded(db.Model):
    """Uploaded File"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class ParsedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_uploaded.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file = db.relationship("FileUploaded", backref=db.backref('parsed_data', lazy=True))
web/routes.py --- from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from extensions import db, cache
from .models import FileUploaded, ParsedData
from services.queue_services import QueueService
from services.file_service import FileService
from config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
import os
import uuid
from datetime import datetime
from time import time


web_bp = Blueprint('web', __name__, template_folder='templates')

@web_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('web.index'))

        file = request.files['file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('web.index'))

        try:
            # Validate file size before saving
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash(f'File too large. Maximum size is {MAX_FILE_SIZE//(1024*1024)}MB', 'error')
                return redirect(url_for('web.index'))
                
            if file_size == 0:
                flash('File is empty', 'error')
                return redirect(url_for('web.index'))

            # Validate extension
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in ALLOWED_EXTENSIONS:
                flash('Only PDF and PowerPoint files are allowed', 'error')
                return redirect(url_for('web.index'))

            # Process file through services
            uploaded_file = FileService.save_file(file)
            QueueService.enqueue_file_processing(
                file_path=os.path.join(UPLOAD_FOLDER, uploaded_file.filename),
                file_ext=file_ext,
                file_id=uploaded_file.id
            )

            flash('File uploaded and queued for processing!', 'success')
            return redirect(url_for('web.view_file', file_id=uploaded_file.id))
            
        except Exception as e:
            current_app.logger.error(f"Upload error: {str(e)}")
            flash('An error occurred during upload. Please try again.', 'error')
            return redirect(url_for('web.index'))
    
    # Get recent files with caching
    @cache.memoize(timeout=60)
    def get_recent_files():
        return FileUploaded.query.order_by(FileUploaded.upload_date.desc()).limit(5).all()
        
    return render_template("index.html", recent_files=get_recent_files())

@web_bp.route('/files')
def list_files():
    """List all files with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get paginated files with caching
    cache_key = f"files_page_{page}"
    files = cache.get(cache_key)
    
    if files is None:
        files = FileUploaded.query.order_by(FileUploaded.upload_date.desc()).paginate(page=page, per_page=per_page)
        cache.set(cache_key, files, timeout=60)
    
    return render_template("files.html", files=files)

@web_bp.route('/files/<int:file_id>')
def view_file(file_id):
    """View file details and processing status"""
    # Get file or 404
    file = FileUploaded.query.get_or_404(file_id)
    
    # Get processing status from queue service
    status = QueueService.get_processing_status(file_id)
    
    # Get parsed content if available
    parsed_content = None
    if status.get('status') == 'completed':
        parsed_data = ParsedData.query.filter_by(file_id=file_id).first()
        if parsed_data:
            parsed_content = parsed_data.content
    
    return render_template(
        "file_detail.html",
        file=file,
        status=status,
        content=parsed_content,
        show_refresh=status.get('status') not in ['completed', 'failed']
    )

@web_bp.route('/files/<int:file_id>/status')
def file_status(file_id):
    """JSON endpoint for status updates (used by AJAX)"""
    status = QueueService.get_processing_status(file_id)
    return {
        'status': status.get('status'),
        'progress': status.get('progress', 0),
        'estimated_time': status.get('estimated_time')
    }

@web_bp.route('/files/<int:file_id>/download')
def download_file(file_id):
    """Download original file"""
    file = FileUploaded.query.get_or_404(file_id)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    if not os.path.exists(file_path):
        flash('Original file no longer available', 'error')
        return redirect(url_for('web.view_file', file_id=file_id))
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.filename
    )

templates/index.html -- {% extends "base.html" %}

{% block content %}

<div class="card">
    <div class="card-body">
        <h5 class="card-title">Upload Document</h5>
        <form method="POST" enctype="multipart/form-data">
            <div class="mb-3">
                <input class="form-control" type="file" name="file" accept=".pdf,.pptx" required>
                <div class="form-text">Only PDF and PowerPoint files (max 12MB)</div>
            </div>
            <button type="submit" class="btn btn-primary">Upload & Parse</button>
        </form>
    </div>
</div>

{% if recent_files %}
<div class="mt-4">
    <h5>Recently Uploaded Files</h5>
    <ul class="list-group">
        {% for file in recent_files %}
        <li class="list-group-item d-flex justify-content-between align-items-center">
            <a href="{{ url_for('web.view_file', file_id=file.id) }}">{{ file.filename }}</a>
            <span class="badge bg-{{ 'info' if file.file_type == 'pdf' else 'warning' }} rounded-pill">
                {{ file.file_type|upper }}
            </span>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
{% endblock %} ---- file_details.html -- {% extends "base.html" %}

{% block content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5>{{ filename }}</h5>
        <div>
            <span class="badge bg-secondary me-2">
                Uploaded: {{ upload_date.strftime('%Y-%m-%d %H:%M') }}
            </span>
            <a href="{{ url_for('web.list_files') }}" class="btn btn-sm btn-outline-secondary">Back to List</a>
        </div>
    </div>
    <div class="card-body">
        <div class="border p-3 bg-light">
            <pre>{{ content }}</pre>
        </div>
    </div>
</div>
{% endblock %}   - files.html -- {% extends "base.html" %}

{% block content %}
<h1 class="mb-4">Uploaded Files</h1>
<a href="{{ url_for('web.index') }}" class="btn btn-primary mb-3">Upload New File</a>

<div class="list-group">
    {% for file in files %}
    <a href="{{ url_for('web.view_file', file_id=file.id) }}" 
       class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
        <div>
            <h6 class="mb-1">{{ file.filename }}</h6>
            <small class="text-muted">Uploaded: {{ file.upload_date.strftime('%Y-%m-%d %H:%M') }}</small>
        </div>
        <span class="badge bg-{{ 'info' if file.file_type == 'pdf' else 'warning' }} rounded-pill">
            {{ file.file_type|upper }}
        </span>
    </a>
    {% endfor %}
</div>
{% endblock %} ---- results.html --- {% extends "base.html" %}

{% block content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5>Parsing Results: {{ filename }}</h5>
        <span class="badge bg-{{ 'info' if file_type == 'Pdf' else 'warning' }}">
            {{ file_type }}
        </span>
    </div>
    <div class="card-body">
        <div class="mb-3">
            <a href="{{ url_for('web.index') }}" class="btn btn-outline-secondary">Upload Another</a>
            <a href="{{ url_for('web.list_files') }}" class="btn btn-outline-primary">View All Files</a>
        </div>
        
        <div class="border p-3 bg-light">
            <pre>{{ content }}</pre>
        </div>
    </div>
</div>
{% endblock %} ................ docker-compose.yml --  version: '3.8'

services:
  # API Gateway Service
  api_gateway:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://fileuser:filepass@db/filedb
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    depends_on:
      - db
      - redis
      - rabbitmq
      - parser_worker

  # Database Service (PostgreSQL)
  db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=fileuser
      - POSTGRES_PASSWORD=filepass
      - POSTGRES_DB=filedb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fileuser -d filedb"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Parser Worker Service
  parser_worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://fileuser:filepass@db/filedb
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
    depends_on:
      - db
      - redis
      - rabbitmq

  # Redis Cache Service
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # RabbitMQ Queue Service
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"  # AMQP
      - "15672:15672"  # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data: and Dockerfile.py - FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

ENV FLASK_APP=app
ENV FLASK_ENV=production

EXPOSE 5000