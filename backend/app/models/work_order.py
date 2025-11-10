from app.db import db
from datetime import datetime

class WorkOrder(db.Model):
    """Work Order (Arbeitsauftrag) model."""
    __tablename__ = 'work_orders'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # e.g., 'open', 'in_progress', 'completed'
    priority = db.Column(db.String(20), default='medium')  # e.g., 'low', 'medium', 'high'
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tax_advisor_id = db.Column(db.Integer, db.ForeignKey('tax_advisors.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('documents.id', name='fk_work_order_template'), nullable=True)  # Link to document template

    # Relationships
    documents = db.relationship('Document', backref='work_order', lazy=True, foreign_keys='Document.work_order_id')
    template = db.relationship('Document', foreign_keys=[template_id], lazy=True)

    def __repr__(self):
        return f'<WorkOrder {self.title}>' 