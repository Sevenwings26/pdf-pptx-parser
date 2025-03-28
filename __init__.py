import os
from flask import Flask
from extensions import db, api, celery  # Changed to absolute import
from config import (  # Changed to absolute import
    SQLALCHEMY_DATABASE_URI,
    UPLOAD_FOLDER,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    SECRET_KEY,
    SQLALCHEMY_ENGINE_OPTIONS  # Added for connection pooling
)

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'UPLLEM_FOLDER': UPLOAD_FOLDER,
        'MAX_FILE_SIZE': MAX_FILE_SIZE * 1024 * 1024,  # Convert MB to bytes
        'ALLOWED_EXTENSIONS': ALLOWED_EXTENSIONS,
        'SECRET_KEY': SECRET_KEY,
        'SQLALCHEMY_ENGINE_OPTIONS': SQLALCHEMY_ENGINE_OPTIONS  # Connection pooling
    })

    # Initialize extensions
    db.init_app(app)
    
    # Configure Celery
    celery.conf.update({
        'broker_url': app.config.get('RABBITMQ_URL'),
        'result_backend': app.config.get('REDIS_URL'),
        'task_serializer': 'json',
        'worker_max_tasks_per_child': 100  # Prevent memory leaks
    })

    # Register blueprints
    from api.routes import api_ns
    from web.routes import web_bp
    
    api.init_app(app)
    api.add_namespace(api_ns)
    app.register_blueprint(web_bp)

    # Create upload folder with secure permissions
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o750, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Failed to create upload folder: {str(e)}")

    # Health check route
    @app.route('/health')
    def health_check():
        return {"status": "healthy"}, 200

    return app



# import os
# from flask import Flask
# from extensions import db, api, celery
# from config import SQLALCHEMY_DATABASE_URI, UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, SECRET_KEY

# def create_app():
#     app = Flask(__name__)
    
#     # Configure app
#     app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#     app.config['MAX_FILE_SIZE'] = MAX_FILE_SIZE
#     app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
#     app.config['SECRET_KEY'] = SECRET_KEY
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#     # Initialize extensions
#     db.init_app(app)
#     celery.conf.update(app.config)

#     # Register blueprints
#     from api.routes import api_ns
#     from web.routes import web_bp
    
#     app.register_blueprint(web_bp)
#     api.init_app(app)
#     api.add_namespace(api_ns)
    
#     # Create upload folder
#     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#     return app
