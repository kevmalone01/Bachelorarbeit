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
    is_template = db.Column(db.Boolean, default=False)  # True if this is a template
    linked_client_group_ids = db.Column(db.JSON)  # Array of client group IDs that can use this template

    # Foreign Keys - made nullable
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    tax_advisor_id = db.Column(db.Integer, db.ForeignKey('tax_advisors.id'), nullable=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=True)
    
    def __repr__(self):
        return f'<Document {self.title}>'

    def to_dict(self):
        """Convert document object to dictionary with client and tax advisor data."""
        from app.models.client import Client, Salutation, LegalForm
        from app.models.tax_advisor import TaxAdvisor
        from sqlalchemy import text
        
        client = None
        tax_advisor = None
        
        # Get client if client_id exists - use raw SQL to avoid enum issues
        if self.client_id:
            try:
                # Try raw SQL first to avoid enum conversion issues
                query = text("SELECT * FROM clients WHERE id = :client_id")
                result = db.session.execute(query, {'client_id': self.client_id})
                row = result.fetchone()
                if row:
                    client_dict = dict(row._mapping)
                    # Create a minimal client object-like structure
                    client = type('Client', (), {
                        'client_type': client_dict.get('client_type'),
                        'mandate_manager': client_dict.get('mandate_manager'),
                        'mandate_responsible': client_dict.get('mandate_responsible'),
                        'email': client_dict.get('email'),
                        'tax_number': client_dict.get('tax_number'),
                        'tax_office': client_dict.get('tax_office'),
                        'tax_court': client_dict.get('tax_court'),
                        'address_zip': client_dict.get('address_zip'),
                        'address_city': client_dict.get('address_city'),
                        'address_street': client_dict.get('address_street'),
                        'address_number': client_dict.get('address_number'),
                        'tax_office_zip': client_dict.get('tax_office_zip'),
                        'tax_office_city': client_dict.get('tax_office_city'),
                        'tax_office_street': client_dict.get('tax_office_street'),
                        'tax_office_number': client_dict.get('tax_office_number'),
                        'tax_office_email': client_dict.get('tax_office_email'),
                        'tax_office_fax': client_dict.get('tax_office_fax'),
                        'salutation': None,
                        'title': client_dict.get('title'),
                        'first_name': client_dict.get('first_name'),
                        'last_name': client_dict.get('last_name'),
                        'birth_date': client_dict.get('birth_date'),
                        'tax_id': client_dict.get('tax_id'),
                        'company_name': client_dict.get('company_name'),
                        'legal_form': None,
                        'vat_id': client_dict.get('vat_id'),
                        'contact_salutation': None,
                        'contact_last_name': client_dict.get('contact_last_name'),
                        'contact_phone': client_dict.get('contact_phone'),
                        'contact_email': client_dict.get('contact_email'),
                        'contact_fax': client_dict.get('contact_fax'),
                    })()
                    
                    # Safely convert enum values
                    salutation_val = client_dict.get('salutation')
                    if salutation_val and salutation_val != '':
                        try:
                            if salutation_val in ['HERR', 'FRAU']:
                                client.salutation = Salutation[salutation_val]
                            elif salutation_val in ['Herr', 'Frau']:
                                # Find matching enum
                                for enum_val in Salutation:
                                    if enum_val.value == salutation_val:
                                        client.salutation = enum_val
                                        break
                        except (KeyError, AttributeError):
                            client.salutation = None
                    
                    legal_form_val = client_dict.get('legal_form')
                    if legal_form_val and legal_form_val != '':
                        try:
                            if legal_form_val in ['GMBH', 'AG', 'OHG', 'UG', 'KG', 'GBR', 'EINZELFIRMA']:
                                client.legal_form = LegalForm[legal_form_val]
                            elif legal_form_val in ['GmbH', 'AG', 'OHG', 'UG', 'KG', 'GbR', 'Einzelfirma']:
                                # Find matching enum
                                for enum_val in LegalForm:
                                    if enum_val.value == legal_form_val:
                                        client.legal_form = enum_val
                                        break
                        except (KeyError, AttributeError):
                            client.legal_form = None
                    
                    contact_salutation_val = client_dict.get('contact_salutation')
                    if contact_salutation_val and contact_salutation_val != '':
                        try:
                            if contact_salutation_val in ['HERR', 'FRAU']:
                                client.contact_salutation = Salutation[contact_salutation_val]
                            elif contact_salutation_val in ['Herr', 'Frau']:
                                # Find matching enum
                                for enum_val in Salutation:
                                    if enum_val.value == contact_salutation_val:
                                        client.contact_salutation = enum_val
                                        break
                        except (KeyError, AttributeError):
                            client.contact_salutation = None
            except Exception as e:
                # Fallback to ORM if raw SQL fails
                try:
                    client = Client.query.get(self.client_id)
                except Exception:
                    client = None
        
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
            'clientId': str(self.client_id) if self.client_id else None,  # Also include as clientId for frontend compatibility
            'tax_advisor_id': self.tax_advisor_id,
            'work_order_id': self.work_order_id,
            'placeholders': self.placeholders if self.placeholders else [],
            'linkedClientGroupIds': self.linked_client_group_ids if self.linked_client_group_ids else [],
            'is_template': self.is_template,
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
                # Handle birth_date - it might be a string (from raw SQL) or a date object
                birth_date_value = None
                if client.birth_date:
                    if isinstance(client.birth_date, str):
                        birth_date_value = client.birth_date
                    else:
                        try:
                            birth_date_value = client.birth_date.isoformat()
                        except AttributeError:
                            birth_date_value = str(client.birth_date)
                
                client_data['client'].update({
                    'salutation': client.salutation.value if client.salutation else None,
                    'title': client.title,
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'birth_date': birth_date_value,
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