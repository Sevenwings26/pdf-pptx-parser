# from flask_sqlalchemy import SQLAlchemy
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
