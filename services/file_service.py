import os
from datetime import datetime
import uuid
from tasks.celery import process_file
from extensions import db
from web.models import FileUploaded
from flask import current_app

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
    