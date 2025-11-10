from datetime import datetime
from app.db import db
import enum

class Salutation(enum.Enum):
    HERR = "Herr"
    FRAU = "Frau"

class LegalForm(enum.Enum):
    GMBH = "GmbH"
    AG = "AG"
    OHG = "OHG"
    UG = "UG"
    KG = "KG"
    GBR = "GbR"
    EINZELFIRMA = "Einzelfirma"

class Client(db.Model):
    """Client model that supports both natural persons and companies."""
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    client_type = db.Column(db.String(20), nullable=False)  # 'natural' or 'company'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Common fields for both types
    mandate_manager = db.Column(db.String(100))  # Mandatsmanager
    mandate_responsible = db.Column(db.String(100))  # Mandatsverantwortlicher
    email = db.Column(db.String(120))
    tax_number = db.Column(db.String(50))  # Steuernummer
    tax_office = db.Column(db.String(100))  # Finanzamt
    tax_court = db.Column(db.String(100))  # Finanzgericht

    # Address fields
    address_zip = db.Column(db.String(10))  # PLZ
    address_city = db.Column(db.String(100))  # Ort
    address_street = db.Column(db.String(100))  # Straße
    address_number = db.Column(db.String(10))  # Nr.

    # Fields for natural persons
    salutation = db.Column(db.Enum(Salutation))  # Anrede
    title = db.Column(db.String(50))  # Titel
    first_name = db.Column(db.String(100))  # Vorname
    last_name = db.Column(db.String(100))  # Nachname
    birth_date = db.Column(db.Date)  # Geburtsdatum
    tax_id = db.Column(db.String(50))  # Steuer-ID

    # Fields for companies
    company_name = db.Column(db.String(100))  # Firma
    legal_form = db.Column(db.Enum(LegalForm))  # Rechtsform
    vat_id = db.Column(db.String(50))  # USt-ID

    # Contact person fields (for companies)
    contact_salutation = db.Column(db.Enum(Salutation))  # Anrede Ansprechpartner
    contact_last_name = db.Column(db.String(100))  # Nachname Ansprechpartner
    contact_phone = db.Column(db.String(50))  # Telefon Ansprechpartner
    contact_email = db.Column(db.String(120))  # E-Mail Ansprechpartner
    contact_fax = db.Column(db.String(50))  # Fax

    # Tax office address fields
    tax_office_zip = db.Column(db.String(10))  # PLZ (Finanzamt)
    tax_office_city = db.Column(db.String(100))  # Ort (Finanzamt)
    tax_office_street = db.Column(db.String(100))  # Straße (Finanzamt)
    tax_office_number = db.Column(db.String(10))  # Nr. (Finanzamt)
    tax_office_email = db.Column(db.String(120))  # E-Mail (Finanzamt)
    tax_office_fax = db.Column(db.String(50))  # Fax (Finanzamt)

    def __repr__(self):
        if self.client_type == 'natural':
            return f'<Client {self.first_name} {self.last_name}>'
        else:
            return f'<Client {self.company_name}>'

    def to_dict(self):
        """Convert client object to dictionary."""
        base_dict = {
            'id': self.id,
            'client_type': self.client_type,
            'mandate_manager': self.mandate_manager,
            'mandate_responsible': self.mandate_responsible,
            'email': self.email,
            'tax_number': self.tax_number,
            'tax_office': self.tax_office,
            'tax_court': self.tax_court,
            'address_zip': self.address_zip,
            'address_city': self.address_city,
            'address_street': self.address_street,
            'address_number': self.address_number,
            'tax_office_zip': self.tax_office_zip,
            'tax_office_city': self.tax_office_city,
            'tax_office_street': self.tax_office_street,
            'tax_office_number': self.tax_office_number,
            'tax_office_email': self.tax_office_email,
            'tax_office_fax': self.tax_office_fax,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if self.client_type == 'natural':
            base_dict.update({
                'salutation': self.salutation.value if self.salutation else None,
                'title': self.title,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'birth_date': self.birth_date.isoformat() if self.birth_date else None,
                'tax_id': self.tax_id
            })
        else:
            base_dict.update({
                'company_name': self.company_name,
                'legal_form': self.legal_form.value if self.legal_form else None,
                'vat_id': self.vat_id,
                'contact_salutation': self.contact_salutation.value if self.contact_salutation else None,
                'contact_last_name': self.contact_last_name,
                'contact_phone': self.contact_phone,
                'contact_email': self.contact_email,
                'contact_fax': self.contact_fax
            })

        return base_dict 