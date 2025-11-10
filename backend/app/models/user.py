from datetime import datetime
from app.db import db

class User(db.Model):
    """User model for authentication and settings"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(100), default='user')
    language = db.Column(db.String(10), default='de')
    
    # Model preferences
    preferred_text_model = db.Column(db.String(100), default='llama3')
    preferred_image_model = db.Column(db.String(100), default='llava')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'language': self.language,
            'preferred_text_model': self.preferred_text_model,
            'preferred_image_model': self.preferred_image_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_preferences(self, **kwargs):
        """Update user preferences"""
        allowed_fields = [
            'name', 'role', 'language', 
            'preferred_text_model', 'preferred_image_model'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(self, field):
                setattr(self, field, value)
        
        self.updated_at = datetime.utcnow() 