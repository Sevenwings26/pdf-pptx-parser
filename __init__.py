import os
from flask import Flask
from extensions import db, api, celery
from config import SQLALCHEMY_DATABASE_URI, UPLOAD_FOLDER, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, SECRET_KEY

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_FILE_SIZE'] = MAX_FILE_SIZE
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    celery.conf.update(app.config)

    # Register blueprints
    from api.routes import api_ns
    from web.routes import web_bp
    
    app.register_blueprint(web_bp)
    api.init_app(app)
    api.add_namespace(api_ns)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app
