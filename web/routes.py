from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file
from extensions import db, cache  
from web.models import FileUploaded, ParsedData 
from config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS 
from services.file_service import FileService 
import os
import uuid
from datetime import datetime
from time import time


web_bp = Blueprint('web', __name__, template_folder='templates')

# Lazy loader for QueueService to break circular imports
def get_queue_service():
    from services.queue_services import QueueService  # Local import
    return QueueService()

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
            get_queue_service().enqueue_file_processing(  # Using the lazy loader
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
    status = get_queue_service().get_processing_status(file_id)  # Using the lazy loader
    
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
    status = get_queue_service().get_processing_status(file_id)  # Using the lazy loader
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
        download_name=file.filename,
        mimetype='application/octet-stream'  # Added MIME type
    )