# from celery import Celery
# from extensions import db, celery
# from config import RABBITMQ_URL, REDIS_URL
# from parser import extract_pdf_data, extract_pptx_data
# from web.models import ParsedData


# celery = Celery(__name__)
# celery.conf.broker_url = RABBITMQ_URL
# celery.conf.result_backend = REDIS_URL

# @celery.task(bind=True)
# def process_file(self, file_path, file_ext, file_id):
#     try:
#         if file_ext == "pdf":
#             content = extract_pdf_data(file_path)
#         elif file_ext == "pptx":
#             content = extract_pptx_data(file_path)
        
#         with db.app.app_context():
#             parsed_data = ParsedData(file_id=file_id, content=content)
#             db.session.add(parsed_data)
#             db.session.commit()
#         return True
#     except Exception as e:
#         self.retry(exc=e, countdown=60)


from __init__ import create_app
from extensions import celery

app = create_app()

@celery.task(bind=True)
def process_file(self, file_path, file_ext, file_id):
    with app.app_context():  # <-- Add application context
        from parser import extract_pdf_data, extract_pptx_data
        from web.models import ParsedData
        from extensions import db
        
        try:
            if file_ext == "pdf":
                content, error = extract_pdf_data(file_path)
            elif file_ext == "pptx":
                content, error = extract_pptx_data(file_path)
            
            if error:
                raise ValueError(error)
                
            parsed_data = ParsedData(
                file_id=file_id,
                content=content
            )
            db.session.add(parsed_data)
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            raise self.retry(exc=e)