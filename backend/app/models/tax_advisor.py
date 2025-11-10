from app.db import db
from datetime import datetime

class TaxAdvisor(db.Model):
    """Tax Advisor (Steuerberater) model."""
    __tablename__ = 'tax_advisors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    tax_number = db.Column(db.String(50), unique=True)
    specialization = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = db.relationship('Document', backref='tax_advisor', lazy=True)
    work_orders = db.relationship('WorkOrder', backref='tax_advisor', lazy=True)

    def __repr__(self):
        return f'<TaxAdvisor {self.name}>' 