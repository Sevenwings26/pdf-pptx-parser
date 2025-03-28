from celery import Celery
from extensions import db, celery
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
