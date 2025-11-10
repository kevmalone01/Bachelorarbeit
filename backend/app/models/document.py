from datetime import datetime
from app.db import db

class Document(db.Model):
    """Document model."""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    document_type = db.Column(db.String(50))  # z.B. 'tax_return', 'annual_report', etc.
    status = db.Column(db.String(20))  # z.B. 'draft', 'final', etc.
    file_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    placeholders = db.Column(db.JSON)

    # Foreign Keys - made nullable
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    tax_advisor_id = db.Column(db.Integer, db.ForeignKey('tax_advisors.id'), nullable=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=True)
    
    def __repr__(self):
        return f'<Document {self.title}>'

    def to_dict(self):
        """Convert document object to dictionary with client and tax advisor data."""
        from app.models.client import Client
        from app.models.tax_advisor import TaxAdvisor
        
        client = None
        tax_advisor = None
        
        # Get client if client_id exists
        if self.client_id:
            client = Client.query.get(self.client_id)
        
        # Get tax advisor if tax_advisor_id exists  
        if self.tax_advisor_id:
            tax_advisor = TaxAdvisor.query.get(self.tax_advisor_id)

        # Basis-Dokumentdaten
        doc_dict = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'document_type': self.document_type,
            'status': self.status,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client_id': self.client_id,
            'tax_advisor_id': self.tax_advisor_id,
            'work_order_id': self.work_order_id,
        }

        # Client-Daten (only if client exists)
        if client:
            client_data = {
                'client': {
                    'type': client.client_type,
                    'mandate_manager': client.mandate_manager,
                    'mandate_responsible': client.mandate_responsible,
                    'email': client.email,
                    'tax_number': client.tax_number,
                    'tax_office': client.tax_office,
                    'tax_court': client.tax_court,
                    'address': {
                        'zip': client.address_zip,
                        'city': client.address_city,
                        'street': client.address_street,
                        'number': client.address_number
                    },
                    'tax_office_address': {
                        'zip': client.tax_office_zip,
                        'city': client.tax_office_city,
                        'street': client.tax_office_street,
                        'number': client.tax_office_number,
                        'email': client.tax_office_email,
                        'fax': client.tax_office_fax
                    }
                }
            }

            # Typ-spezifische Client-Daten
            if client.client_type == 'natural':
                client_data['client'].update({
                    'salutation': client.salutation.value if client.salutation else None,
                    'title': client.title,
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'birth_date': client.birth_date.isoformat() if client.birth_date else None,
                    'tax_id': client.tax_id
                })
            else:  # company
                client_data['client'].update({
                    'company_name': client.company_name,
                    'legal_form': client.legal_form.value if client.legal_form else None,
                    'vat_id': client.vat_id,
                    'contact': {
                        'salutation': client.contact_salutation.value if client.contact_salutation else None,
                        'last_name': client.contact_last_name,
                        'phone': client.contact_phone,
                        'email': client.contact_email,
                        'fax': client.contact_fax
                    }
                })

            doc_dict.update(client_data)

        # Steuerberater-Daten (only if tax advisor exists)
        if tax_advisor:
            doc_dict['tax_advisor'] = {
                'name': tax_advisor.name,
                'email': tax_advisor.email,
                'phone': tax_advisor.phone,
                'address': tax_advisor.address,
                'tax_number': tax_advisor.tax_number,
                'specialization': tax_advisor.specialization
            }

        return doc_dict

    @classmethod
    def create_with_client_data(cls, **kwargs):
        """Create a new document and automatically include client and tax advisor data."""
        document = cls(**kwargs)
        db.session.add(document)
        db.session.commit()
        return document 