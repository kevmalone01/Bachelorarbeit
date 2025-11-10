import pytest
from datetime import datetime
from app.services.database_service import DatabaseService
from app.models import Client, Placeholder, Document, TaxAdvisor, WorkOrder

@pytest.fixture
def db_service():
    """Create a database service instance."""
    return DatabaseService()

@pytest.fixture
def sample_client_data():
    """Sample client data for testing."""
    return {
        'name': 'Test Client',
        'email': 'test@client.com',
        'phone': '1234567890',
        'address': 'Test Address',
        'tax_number': '123456789'
    }

@pytest.fixture
def sample_tax_advisor_data():
    """Sample tax advisor data for testing."""
    return {
        'name': 'Test Advisor',
        'email': 'test@advisor.com',
        'phone': '0987654321',
        'address': 'Advisor Address',
        'tax_number': '987654321',
        'specialization': 'Tax Law'
    }

@pytest.fixture
def sample_work_order_data(sample_client_data, sample_tax_advisor_data):
    """Sample work order data for testing."""
    return {
        'title': 'Test Work Order',
        'description': 'Test Description',
        'status': 'open',
        'priority': 'high',
        'due_date': datetime.utcnow(),
        'client_id': 1,  # Will be updated in test
        'tax_advisor_id': 1  # Will be updated in test
    }

@pytest.fixture
def sample_document_data(sample_client_data, sample_tax_advisor_data, sample_work_order_data):
    """Sample document data for testing."""
    return {
        'title': 'Test Document',
        'content': 'Test Content',
        'document_type': 'invoice',
        'status': 'draft',
        'file_path': '/test/path',
        'client_id': 1,  # Will be updated in test
        'tax_advisor_id': 1,  # Will be updated in test
        'work_order_id': 1  # Will be updated in test
    }

@pytest.fixture
def sample_placeholder_data():
    """Sample placeholder data for testing."""
    return {
        'name': 'Test Placeholder',
        'description': 'Test Description',
        'value': 'Test Value',
        'type': 'text',
        'is_required': True,
        'document_id': 1  # Will be updated in test
    }

class TestDatabaseService:
    """Test suite for DatabaseService."""

    def test_client_crud(self, db_service, sample_client_data):
        """Test CRUD operations for Client model."""
        # Create
        client = db_service.create_client(sample_client_data)
        assert client.id is not None
        assert client.name == sample_client_data['name']
        assert client.email == sample_client_data['email']

        # Read
        retrieved_client = db_service.get_client(client.id)
        assert retrieved_client.id == client.id
        assert retrieved_client.name == client.name

        # Update
        update_data = {'name': 'Updated Client Name'}
        updated_client = db_service.update_client(client.id, update_data)
        assert updated_client.name == 'Updated Client Name'

        # Delete
        assert db_service.delete_client(client.id) is True
        assert db_service.get_client(client.id) is None

    def test_tax_advisor_crud(self, db_service, sample_tax_advisor_data):
        """Test CRUD operations for TaxAdvisor model."""
        # Create
        advisor = db_service.create_tax_advisor(sample_tax_advisor_data)
        assert advisor.id is not None
        assert advisor.name == sample_tax_advisor_data['name']
        assert advisor.email == sample_tax_advisor_data['email']

        # Read
        retrieved_advisor = db_service.get_tax_advisor(advisor.id)
        assert retrieved_advisor.id == advisor.id
        assert retrieved_advisor.name == advisor.name

        # Update
        update_data = {'name': 'Updated Advisor Name'}
        updated_advisor = db_service.update_tax_advisor(advisor.id, update_data)
        assert updated_advisor.name == 'Updated Advisor Name'

        # Delete
        assert db_service.delete_tax_advisor(advisor.id) is True
        assert db_service.get_tax_advisor(advisor.id) is None

    def test_work_order_crud(self, db_service, sample_work_order_data, sample_client_data, sample_tax_advisor_data):
        """Test CRUD operations for WorkOrder model."""
        # Create dependencies first
        client = db_service.create_client(sample_client_data)
        advisor = db_service.create_tax_advisor(sample_tax_advisor_data)
        
        # Update work order data with actual IDs
        sample_work_order_data['client_id'] = client.id
        sample_work_order_data['tax_advisor_id'] = advisor.id

        # Create
        work_order = db_service.create_work_order(sample_work_order_data)
        assert work_order.id is not None
        assert work_order.title == sample_work_order_data['title']

        # Read
        retrieved_work_order = db_service.get_work_order(work_order.id)
        assert retrieved_work_order.id == work_order.id
        assert retrieved_work_order.title == work_order.title

        # Update
        update_data = {'title': 'Updated Work Order'}
        updated_work_order = db_service.update_work_order(work_order.id, update_data)
        assert updated_work_order.title == 'Updated Work Order'

        # Delete
        assert db_service.delete_work_order(work_order.id) is True
        assert db_service.get_work_order(work_order.id) is None

        # Clean up dependencies
        db_service.delete_client(client.id)
        db_service.delete_tax_advisor(advisor.id)

    def test_document_crud(self, db_service, sample_document_data, sample_client_data, 
                         sample_tax_advisor_data, sample_work_order_data):
        """Test CRUD operations for Document model."""
        # Create dependencies first
        client = db_service.create_client(sample_client_data)
        advisor = db_service.create_tax_advisor(sample_tax_advisor_data)
        work_order = db_service.create_work_order({
            **sample_work_order_data,
            'client_id': client.id,
            'tax_advisor_id': advisor.id
        })
        
        # Update document data with actual IDs
        sample_document_data['client_id'] = client.id
        sample_document_data['tax_advisor_id'] = advisor.id
        sample_document_data['work_order_id'] = work_order.id

        # Create
        document = db_service.create_document(sample_document_data)
        assert document.id is not None
        assert document.title == sample_document_data['title']

        # Read
        retrieved_document = db_service.get_document(document.id)
        assert retrieved_document.id == document.id
        assert retrieved_document.title == document.title

        # Update
        update_data = {'title': 'Updated Document'}
        updated_document = db_service.update_document(document.id, update_data)
        assert updated_document.title == 'Updated Document'

        # Delete
        assert db_service.delete_document(document.id) is True
        assert db_service.get_document(document.id) is None

        # Clean up dependencies
        db_service.delete_work_order(work_order.id)
        db_service.delete_client(client.id)
        db_service.delete_tax_advisor(advisor.id)

    def test_placeholder_crud(self, db_service, sample_placeholder_data, sample_document_data,
                            sample_client_data, sample_tax_advisor_data, sample_work_order_data):
        """Test CRUD operations for Placeholder model."""
        # Create dependencies first
        client = db_service.create_client(sample_client_data)
        advisor = db_service.create_tax_advisor(sample_tax_advisor_data)
        work_order = db_service.create_work_order({
            **sample_work_order_data,
            'client_id': client.id,
            'tax_advisor_id': advisor.id
        })
        document = db_service.create_document({
            **sample_document_data,
            'client_id': client.id,
            'tax_advisor_id': advisor.id,
            'work_order_id': work_order.id
        })
        
        # Update placeholder data with actual document ID
        sample_placeholder_data['document_id'] = document.id

        # Create
        placeholder = db_service.create_placeholder(sample_placeholder_data)
        assert placeholder.id is not None
        assert placeholder.name == sample_placeholder_data['name']

        # Read
        retrieved_placeholder = db_service.get_placeholder(placeholder.id)
        assert retrieved_placeholder.id == placeholder.id
        assert retrieved_placeholder.name == placeholder.name

        # Update
        update_data = {'name': 'Updated Placeholder'}
        updated_placeholder = db_service.update_placeholder(placeholder.id, update_data)
        assert updated_placeholder.name == 'Updated Placeholder'

        # Delete
        assert db_service.delete_placeholder(placeholder.id) is True
        assert db_service.get_placeholder(placeholder.id) is None

        # Clean up dependencies
        db_service.delete_document(document.id)
        db_service.delete_work_order(work_order.id)
        db_service.delete_client(client.id)
        db_service.delete_tax_advisor(advisor.id) 