from app import create_app, db
from app.db import init_db, reset_db
from app.models import Client, Document, TaxAdvisor, WorkOrder, Placeholder, Salutation, LegalForm
import click
from datetime import datetime
import logging
import os
from app.config.logging_config import setup_logger, log_request_info

app = create_app()

# Logging setup - Set to INFO level for production
setup_logger(app, log_level=logging.INFO)
# Remove request logging middleware to reduce log noise
# log_request_info(app)

# Add a test log message
app.logger.info("Starting application")

# Flask CLI commands
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database tables."""
    init_db()
    app.logger.info("Database initialization completed")
    click.echo("Initialized the database.")
    
@app.cli.command("reset-db")
def reset_db_command():
    """Reset the database tables."""
    reset_db()
    app.logger.info("Database reset completed")
    click.echo("Reset the database.")

@app.cli.command("seed-db")
def seed_db_command():
    """Seed the database with sample data."""
    app.logger.info("Starting database seeding with sample data")
    try:
        # Create sample clients
        app.logger.debug("Creating sample clients")
        client1 = Client(
            client_type='natural',
            mandate_manager="Max Mustermann",
            mandate_responsible="Lisa Beispiel",
            salutation=Salutation.HERR,
            title="Dr.",
            first_name="Hans",
            last_name="Müller",
            birth_date=datetime.strptime("1992-01-01", "%Y-%m-%d").date(),
            address_zip="86150",
            address_city="Augsburg",
            address_street="Bahnhofstraße",
            address_number="12a",
            email="hans.mueller@example.com",
            tax_number="123/456/78900",
            tax_id="12345678901",
            tax_office="Finanzamt Augsburg Stadt",
            tax_office_zip="86150",
            tax_office_city="Augsburg",
            tax_office_street="Finanzamtstraße",
            tax_office_number="5",
            tax_office_email="kontakt@finanzamt.de",
            tax_office_fax="+49 821 1234567",
            tax_court="Finanzgericht München"
        )
        
        client2 = Client(
            client_type='company',
            mandate_manager="Max Mustermann",
            mandate_responsible="Lisa Beispiel",
            company_name="Stadtwerke Augsburg GmbH",
            legal_form=LegalForm.GMBH,
            address_zip="86150",
            address_city="Augsburg",
            address_street="Industriestraße",
            address_number="10",
            email="info@stadtwerke-augsburg.de",
            tax_number="123/456/78900",
            vat_id="DE123456789",
            tax_office="Finanzamt Augsburg Land",
            tax_court="Finanzgericht München",
            contact_salutation=Salutation.FRAU,
            contact_last_name="Meier",
            contact_phone="+49 821 7654321",
            contact_email="meier@stadtwerke-augsburg.de",
            contact_fax="+49 821 7654322"
        )
        
        # Create sample tax advisors
        app.logger.debug("Creating sample tax advisors")
        advisor1 = TaxAdvisor(
            name="Test Advisor 1",
            email="advisor1@example.com",
            phone="1112223333",
            address="Advisor Address 1",
            tax_number="111222333",
            specialization="Tax Law"
        )
        advisor2 = TaxAdvisor(
            name="Test Advisor 2",
            email="advisor2@example.com",
            phone="4445556666",
            address="Advisor Address 2",
            tax_number="444555666",
            specialization="Accounting"
        )
        
        db.session.add_all([client1, client2, advisor1, advisor2])
        db.session.commit()
        app.logger.debug("Clients and advisors saved to database")
        
        # Create sample work orders
        app.logger.debug("Creating sample work orders")
        work_order1 = WorkOrder(
            title="Tax Return 2023",
            description="Annual tax return preparation",
            status="open",
            priority="high",
            client_id=client1.id,
            tax_advisor_id=advisor1.id
        )
        work_order2 = WorkOrder(
            title="Financial Audit",
            description="Quarterly financial audit",
            status="in_progress",
            priority="medium",
            client_id=client2.id,
            tax_advisor_id=advisor2.id
        )
        
        db.session.add_all([work_order1, work_order2])
        db.session.commit()
        app.logger.debug("Work orders saved to database")
        
        # Create sample documents
        app.logger.debug("Creating sample documents")
        document1 = Document(
            title="Tax Return Document",
            content="Tax return content",
            document_type="tax_return",
            status="draft",
            file_path="documents/tax_return_2023.pdf",
            client_id=client1.id,
            tax_advisor_id=advisor1.id,
            work_order_id=work_order1.id
        )
        document2 = Document(
            title="Audit Report",
            content="Audit report content",
            document_type="audit_report",
            status="final",
            file_path="documents/audit_report_2023.pdf",
            client_id=client2.id,
            tax_advisor_id=advisor2.id,
            work_order_id=work_order2.id
        )
        
        db.session.add_all([document1, document2])
        db.session.commit()
        app.logger.debug("Documents saved to database")
        
        app.logger.info("Database seeded with sample data")
        click.echo("Database seeded with sample data.")
    except Exception as e:
        app.logger.error("Error seeding database: %s", str(e), exc_info=True)
        db.session.rollback()
        click.echo(f"Error seeding database: {str(e)}")

@app.cli.command("show-db")
def show_db_command():
    """Show all entries in the database."""
    click.echo("\n=== Clients ===")
    clients = Client.query.all()
    for client in clients:
        click.echo(f"ID: {client.id}")
        click.echo(f"Type: {client.client_type}")
        click.echo(f"Mandatsmanager: {client.mandate_manager}")
        click.echo(f"Mandatsverantwortlicher: {client.mandate_responsible}")
        
        if client.client_type == 'natural':
            click.echo(f"Name: {client.salutation.value if client.salutation else ''} {client.title or ''} {client.first_name} {client.last_name}")
            click.echo(f"Geburtsdatum: {client.birth_date}")
            click.echo(f"Steuer-ID: {client.tax_id}")
        else:
            click.echo(f"Firma: {client.company_name}")
            click.echo(f"Rechtsform: {client.legal_form.value if client.legal_form else ''}")
            click.echo(f"USt-ID: {client.vat_id}")
            click.echo(f"Ansprechpartner: {client.contact_salutation.value if client.contact_salutation else ''} {client.contact_last_name}")
            click.echo(f"Kontakt: {client.contact_phone} / {client.contact_email}")
        
        click.echo(f"Adresse: {client.address_street} {client.address_number}, {client.address_zip} {client.address_city}")
        click.echo(f"E-Mail: {client.email}")
        click.echo(f"Steuernummer: {client.tax_number}")
        click.echo(f"Finanzamt: {client.tax_office}")
        click.echo(f"Finanzamt Adresse: {client.tax_office_street} {client.tax_office_number}, {client.tax_office_zip} {client.tax_office_city}")
        click.echo(f"Finanzamt Kontakt: {client.tax_office_email} / {client.tax_office_fax}")
        click.echo(f"Finanzgericht: {client.tax_court}")
        click.echo("---")
    
    click.echo("\n=== Tax Advisors ===")
    advisors = TaxAdvisor.query.all()
    for advisor in advisors:
        click.echo(f"ID: {advisor.id}")
        click.echo(f"Name: {advisor.name}")
        click.echo(f"Email: {advisor.email}")
        click.echo(f"Specialization: {advisor.specialization}")
        click.echo("---")
    
    click.echo("\n=== Work Orders ===")
    orders = WorkOrder.query.all()
    for order in orders:
        click.echo(f"ID: {order.id}")
        click.echo(f"Title: {order.title}")
        click.echo(f"Status: {order.status}")
        click.echo(f"Client ID: {order.client_id}")
        click.echo(f"Tax Advisor ID: {order.tax_advisor_id}")
        click.echo("---")
    
    click.echo("\n=== Documents ===")
    documents = Document.query.all()
    for doc in documents:
        click.echo(f"ID: {doc.id}")
        click.echo(f"Title: {doc.title}")
        click.echo(f"Type: {doc.document_type}")
        click.echo(f"Status: {doc.status}")
        click.echo("---")
    
    click.echo("\n=== Placeholders ===")
    placeholders = Placeholder.query.all()
    for ph in placeholders:
        click.echo(f"ID: {ph.id}")
        click.echo(f"Name: {ph.name}")
        click.echo(f"Value: {ph.value}")
        click.echo(f"Document ID: {ph.document_id}")
        click.echo("---")

# Create shell context
@app.shell_context_processor
def make_shell_context():
    """Add database and models to flask shell context."""
    return {
        'db': db,
        'Client': Client,
        'Document': Document,
        'TaxAdvisor': TaxAdvisor,
        'WorkOrder': WorkOrder,
        'Placeholder': Placeholder
    }
    
@app.cli.command("delete-doc")
@click.argument("id")
def delete_doc_command(id):
    """Delete a document from the database."""
    click.echo("Deleting document...")
    Document.query.filter_by(id=id).delete()
    db.session.commit()
    click.echo("Document deleted.")

if __name__ == '__main__':
    app.logger.info('Application start')
    app.run(debug=True)
