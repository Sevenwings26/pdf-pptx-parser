from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
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


# from flask import Blueprint, render_template, request, flash, redirect, url_for
# from extensions import db
# from .models import FileUploaded, ParsedData
# from parser import extract_pdf_data, extract_pptx_data
# from config import UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
# import os
# import uuid
# from datetime import datetime


# web_bp = Blueprint('web', __name__)

# @web_bp.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         if 'file' not in request.files:
#             flash('No file part', 'error')
#             return redirect(url_for('web.index'))

#         file = request.files['file']

#         if file.filename == '':
#             flash('No selected file', 'error')
#             return redirect(url_for('web.index'))

#         # Check file extension first
#         if not ('.' in file.filename and 
#                file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
#             flash('Unsupported file extension. Only PDF or PPTX are allowed', 'error')
#             return redirect(url_for('web.index'))

#         # Generate secure filename
#         file_ext = file.filename.rsplit('.', 1)[1].lower()
#         unique_filename = f"{datetime.now().strftime('%Y%m%d_%I-%M%p')}_{uuid.uuid4().hex}.{file_ext}"

#         # Ensure directory exists
#         os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#         file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
#         try:
#             # Save file first, then check size
#             file.save(file_path)
#             actual_size = os.path.getsize(file_path)
#             # os.chmod(file_path, 0o640)

#             if actual_size == 0:
#                 os.remove(file_path)  # Clean up empty file
#                 flash('Uploaded file is empty', 'error')
#                 return redirect(url_for('web.index'))
                
#             if actual_size > MAX_FILE_SIZE:
#                 os.remove(file_path)  # Clean up oversized file
#                 flash('File too large. Max file size is 12MB', 'error')
#                 return redirect(url_for('web.index'))

#             os.chmod(file_path, 0o640)

#             # Save file to db
#             uploaded_file = FileUploaded(filename=unique_filename, file_type=file_ext)
#             db.session.add(uploaded_file)
#             db.session.commit()

#             # Parse operation 
#             parsed_content, error = None, None
#             if file_ext == "pdf":
#                 parsed_content, error = extract_pdf_data(file_path)
#             elif file_ext == "pptx":
#                 parsed_content, error = extract_pptx_data(file_path)
                
#             if error:
#                 flash(f"Error parsing file: {error}", 'error')
#                 return redirect(url_for('web.index'))

#             # save parsed file      
#             parsed_data = ParsedData(file_id=uploaded_file.id, content=parsed_content)
#             db.session.add(parsed_data)
#             db.session.commit()

#             flash('File uploaded and processed successfully!', 'success')
#             # return render_template("results.html", 
#             #                     filename=unique_filename,
#             #                     content=parsed_content,
#             #                     file_type=file_ext.capitalize())
            
#         except Exception as e:
#             if os.path.exists(file_path):
#                 os.remove(file_path)
#             db.session.rollback()
#             flash(f'Error processing file: {str(e)}', 'error')
#             return redirect(url_for('web.index'))
    
#     # # Get some file
#     # uploaded_files = FileUploaded.query.order_by(FileUploaded.upload_date.desc()).limit(10).all()

#     # Get all files
#     uploaded_files = FileUploaded.query.order_by(FileUploaded.upload_date.desc()).all()
#     return render_template("index.html", recent_files=uploaded_files)


# @web_bp.route('/files')
# def list_files():
#     files = FileUploaded.query.order_by(FileUploaded.upload_date.desc()).all()
#     return render_template("files.html", files=files)


# @web_bp.route('/files/<int:file_id>')
# def view_file(file_id):
#     file_data = ParsedData.query.filter_by(file_id=file_id).first()
#     if not file_data:
#         flash('File not found', 'error')
#         return redirect(url_for('web.list_files'))
    
#     original_file = FileUploaded.query.get(file_id)
#     return render_template("file_detail.html", 
#                          content=file_data.content,
#                          filename=original_file.filename,
#                          upload_date=original_file.upload_date)