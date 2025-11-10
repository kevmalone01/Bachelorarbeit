from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app.db import db
from app.models.client import Client
from app.models.placeholder import Placeholder
from app.models.document import Document
from app.models.tax_advisor import TaxAdvisor
from app.models.work_order import WorkOrder

class DatabaseService:
    """Service class for handling database operations."""
    
    # Client (Mandant) Operations
    def create_client(self, client_data: Dict[str, Any]) -> Client:
        """Create a new client."""
        try:
            client = Client(**client_data)
            db.session.add(client)
            db.session.commit()
            return client
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to create client: {str(e)}")

    def get_client(self, client_id: int) -> Optional[Client]:
        """Get a client by ID."""
        return Client.query.get(client_id)

    def get_all_clients(self) -> List[Client]:
        """Get all clients."""
        return Client.query.all()

    def update_client(self, client_id: int, client_data: Dict[str, Any]) -> Client:
        """Update a client."""
        try:
            client = Client.query.get(client_id)
            if not client:
                raise Exception("Client not found")
            
            for key, value in client_data.items():
                setattr(client, key, value)
            
            db.session.commit()
            return client
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to update client: {str(e)}")

    def delete_client(self, client_id: int) -> bool:
        """Delete a client."""
        try:
            client = Client.query.get(client_id)
            if not client:
                raise Exception("Client not found")
            
            db.session.delete(client)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to delete client: {str(e)}")

    # Placeholder Operations
    def create_placeholder(self, placeholder_data: Dict[str, Any]) -> Placeholder:
        """Create a new placeholder."""
        try:
            placeholder = Placeholder(**placeholder_data)
            db.session.add(placeholder)
            db.session.commit()
            return placeholder
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to create placeholder: {str(e)}")

    def get_placeholder(self, placeholder_id: int) -> Optional[Placeholder]:
        """Get a placeholder by ID."""
        return Placeholder.query.get(placeholder_id)

    def get_all_placeholders(self) -> List[Placeholder]:
        """Get all placeholders."""
        return Placeholder.query.all()

    def update_placeholder(self, placeholder_id: int, placeholder_data: Dict[str, Any]) -> Placeholder:
        """Update a placeholder."""
        try:
            placeholder = Placeholder.query.get(placeholder_id)
            if not placeholder:
                raise Exception("Placeholder not found")
            
            for key, value in placeholder_data.items():
                setattr(placeholder, key, value)
            
            db.session.commit()
            return placeholder
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to update placeholder: {str(e)}")

    def delete_placeholder(self, placeholder_id: int) -> bool:
        """Delete a placeholder."""
        try:
            placeholder = Placeholder.query.get(placeholder_id)
            if not placeholder:
                raise Exception("Placeholder not found")
            
            db.session.delete(placeholder)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to delete placeholder: {str(e)}")

    # Document Operations
    def create_document(self, document_data: Dict[str, Any]) -> Document:
        """Create a new document."""
        try:
            document = Document(**document_data)
            db.session.add(document)
            db.session.commit()
            return document
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to create document: {str(e)}")

    def get_document(self, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        return Document.query.get(document_id)

    def get_all_documents(self) -> List[Document]:
        """Get all documents."""
        return Document.query.all()

    def update_document(self, document_id: int, document_data: Dict[str, Any]) -> Document:
        """Update a document."""
        try:
            document = Document.query.get(document_id)
            if not document:
                raise Exception("Document not found")
            
            for key, value in document_data.items():
                setattr(document, key, value)
            
            db.session.commit()
            return document
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to update document: {str(e)}")

    def delete_document(self, document_id: int) -> bool:
        """Delete a document."""
        try:
            document = Document.query.get(document_id)
            if not document:
                raise Exception("Document not found")
            
            db.session.delete(document)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to delete document: {str(e)}")

    # Tax Advisor Operations
    def create_tax_advisor(self, tax_advisor_data: Dict[str, Any]) -> TaxAdvisor:
        """Create a new tax advisor."""
        try:
            tax_advisor = TaxAdvisor(**tax_advisor_data)
            db.session.add(tax_advisor)
            db.session.commit()
            return tax_advisor
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to create tax advisor: {str(e)}")

    def get_tax_advisor(self, tax_advisor_id: int) -> Optional[TaxAdvisor]:
        """Get a tax advisor by ID."""
        return TaxAdvisor.query.get(tax_advisor_id)

    def get_all_tax_advisors(self) -> List[TaxAdvisor]:
        """Get all tax advisors."""
        return TaxAdvisor.query.all()

    def update_tax_advisor(self, tax_advisor_id: int, tax_advisor_data: Dict[str, Any]) -> TaxAdvisor:
        """Update a tax advisor."""
        try:
            tax_advisor = TaxAdvisor.query.get(tax_advisor_id)
            if not tax_advisor:
                raise Exception("Tax advisor not found")
            
            for key, value in tax_advisor_data.items():
                setattr(tax_advisor, key, value)
            
            db.session.commit()
            return tax_advisor
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to update tax advisor: {str(e)}")

    def delete_tax_advisor(self, tax_advisor_id: int) -> bool:
        """Delete a tax advisor."""
        try:
            tax_advisor = TaxAdvisor.query.get(tax_advisor_id)
            if not tax_advisor:
                raise Exception("Tax advisor not found")
            
            db.session.delete(tax_advisor)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to delete tax advisor: {str(e)}")

    # Work Order Operations
    def create_work_order(self, work_order_data: Dict[str, Any]) -> WorkOrder:
        """Create a new work order."""
        try:
            work_order = WorkOrder(**work_order_data)
            db.session.add(work_order)
            db.session.commit()
            return work_order
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to create work order: {str(e)}")

    def get_work_order(self, work_order_id: int) -> Optional[WorkOrder]:
        """Get a work order by ID."""
        return WorkOrder.query.get(work_order_id)

    def get_all_work_orders(self) -> List[WorkOrder]:
        """Get all work orders."""
        return WorkOrder.query.all()

    def update_work_order(self, work_order_id: int, work_order_data: Dict[str, Any]) -> WorkOrder:
        """Update a work order."""
        try:
            work_order = WorkOrder.query.get(work_order_id)
            if not work_order:
                raise Exception("Work order not found")
            
            for key, value in work_order_data.items():
                setattr(work_order, key, value)
            
            db.session.commit()
            return work_order
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to update work order: {str(e)}")

    def delete_work_order(self, work_order_id: int) -> bool:
        """Delete a work order."""
        try:
            work_order = WorkOrder.query.get(work_order_id)
            if not work_order:
                raise Exception("Work order not found")
            
            db.session.delete(work_order)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Failed to delete work order: {str(e)}")
