#!/usr/bin/env python3
"""
Script to create 5 test clients (mixed natural persons and companies)
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Client, Salutation, LegalForm
from datetime import date

def create_test_clients():
    """Create 5 test clients - mixed natural persons and companies"""
    app = create_app()
    
    with app.app_context():
        # Count existing clients (without loading them to avoid enum issues)
        try:
            existing_count = db.session.query(Client.id).count()
            print(f"Found {existing_count} existing client(s). Will add new clients...")
        except Exception as e:
            print(f"Note: Could not check existing clients: {e}")
            existing_count = 0
        
        clients_data = [
            # 1. Natürliche Person
            {
                'client_type': 'natural',
                'salutation': Salutation.HERR,
                'title': 'Dr.',
                'first_name': 'Max',
                'last_name': 'Mustermann',
                'birth_date': date(1980, 5, 15),
                'email': 'max.mustermann@example.com',
                'tax_number': '12345/67890',
                'tax_id': 'DE123456789',
                'tax_office': 'Finanzamt München',
                'address_street': 'Musterstraße',
                'address_number': '42',
                'address_zip': '80331',
                'address_city': 'München',
                'tax_office_street': 'Maximilianstraße',
                'tax_office_number': '1',
                'tax_office_zip': '80539',
                'tax_office_city': 'München',
                'tax_office_email': 'info@finanzamt-muenchen.de'
            },
            # 2. Unternehmen (GmbH)
            {
                'client_type': 'company',
                'company_name': 'Musterfirma',
                'legal_form': LegalForm.GMBH,  # Note: Enum value is "GmbH"
                'vat_id': 'DE123456789',
                'email': 'info@musterfirma.de',
                'tax_number': '98765/43210',
                'tax_office': 'Finanzamt Berlin',
                'address_street': 'Unter den Linden',
                'address_number': '1',
                'address_zip': '10117',
                'address_city': 'Berlin',
                'contact_salutation': Salutation.FRAU,
                'contact_last_name': 'Schmidt',
                'contact_email': 'schmidt@musterfirma.de',
                'contact_phone': '+49 30 12345678',
                'tax_office_street': 'Friedrichstraße',
                'tax_office_number': '219',
                'tax_office_zip': '10969',
                'tax_office_city': 'Berlin',
                'tax_office_email': 'info@finanzamt-berlin.de'
            },
            # 3. Natürliche Person
            {
                'client_type': 'natural',
                'salutation': Salutation.FRAU,
                'first_name': 'Anna',
                'last_name': 'Schmidt',
                'birth_date': date(1990, 8, 22),
                'email': 'anna.schmidt@example.com',
                'tax_number': '11111/22222',
                'tax_id': 'DE987654321',
                'tax_office': 'Finanzamt Hamburg',
                'address_street': 'Reeperbahn',
                'address_number': '123',
                'address_zip': '20359',
                'address_city': 'Hamburg',
                'tax_office_street': 'Steinstraße',
                'tax_office_number': '1',
                'tax_office_zip': '20095',
                'tax_office_city': 'Hamburg',
                'tax_office_email': 'info@finanzamt-hamburg.de'
            },
            # 4. Unternehmen (AG)
            {
                'client_type': 'company',
                'company_name': 'Tech Solutions',
                'legal_form': LegalForm.AG,
                'vat_id': 'DE555666777',
                'email': 'kontakt@techsolutions.de',
                'tax_number': '33333/44444',
                'tax_office': 'Finanzamt Frankfurt',
                'address_street': 'Zeil',
                'address_number': '100',
                'address_zip': '60313',
                'address_city': 'Frankfurt am Main',
                'contact_salutation': Salutation.HERR,
                'contact_last_name': 'Weber',
                'contact_email': 'weber@techsolutions.de',
                'contact_phone': '+49 69 98765432',
                'tax_office_street': 'Gutleutstraße',
                'tax_office_number': '124',
                'tax_office_zip': '60329',
                'tax_office_city': 'Frankfurt am Main',
                'tax_office_email': 'info@finanzamt-frankfurt.de'
            },
            # 5. Natürliche Person
            {
                'client_type': 'natural',
                'salutation': Salutation.HERR,
                'first_name': 'Thomas',
                'last_name': 'Müller',
                'birth_date': date(1975, 12, 3),
                'email': 'thomas.mueller@example.com',
                'tax_number': '55555/66666',
                'tax_id': 'DE111222333',
                'tax_office': 'Finanzamt Köln',
                'address_street': 'Hohe Straße',
                'address_number': '99',
                'address_zip': '50667',
                'address_city': 'Köln',
                'tax_office_street': 'Appellhofplatz',
                'tax_office_number': '1',
                'tax_office_zip': '50667',
                'tax_office_city': 'Köln',
                'tax_office_email': 'info@finanzamt-koeln.de'
            }
        ]
        
        created_clients = []
        for client_data in clients_data:
            try:
                client = Client(**client_data)
                db.session.add(client)
                db.session.commit()
                created_clients.append(client)
                client_type = "Natürliche Person" if client.client_type == 'natural' else "Unternehmen"
                name = f"{client.first_name} {client.last_name}" if client.client_type == 'natural' else client.company_name
                print(f"✓ {client_type} erstellt: {name} (ID: {client.id})")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Fehler beim Erstellen: {str(e)}")
        
        print(f"\n{len(created_clients)} Mandanten erfolgreich erstellt!")

if __name__ == '__main__':
    create_test_clients()

