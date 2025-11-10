from app.db import db
from datetime import datetime

class Placeholder(db.Model):
    """Placeholder model for document templates."""
    __tablename__ = 'placeholders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    value = db.Column(db.Text)
    type = db.Column(db.String(50))  # e.g., 'text', 'date', 'number'
    is_required = db.Column(db.Boolean, default=True)
    validation_rules = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional relationship to document
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    document = db.relationship('Document', backref='document_placeholders', lazy=True)
    
    def __repr__(self):
        return f'<Placeholder {self.name}>' 