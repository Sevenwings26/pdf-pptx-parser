import os
from datetime import datetime
import uuid
from extensions import db, celery, cache
from web.models import FileUploaded, ParsedData
from parser import extract_pdf_data, extract_pptx_data
from flask import current_app
from tasks.celery import process_file
# from celery import current_app as celery_app

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
            
            # task = celery_app.send_task(
            #     'tasks.celery.process_file',  # Full task path
            #     args=(file_path, file_ext, file_id),
            #     queue='parsing',
            #     priority=priority,
            #     retry=True,
            #     retry_policy={
            #         'max_retries': 3,
            #         'interval_start': 10,
            #         'interval_step': 30,
            #         'interval_max': 300,
            #     }
            # )
            
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
        