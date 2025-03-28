from . import api_ns
from flask_restx import fields, Resource
from flask import request, current_app
from extensions import db, cache
from web.models import FileUploaded, ParsedData
from services.queue_services import QueueService
from services.file_service import FileService
import os
from datetime import datetime
import uuid
from ..config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

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
        }