from app.models.client import Client, Salutation, LegalForm
from app.models.document import Document
from app.models.tax_advisor import TaxAdvisor
from app.models.work_order import WorkOrder
from app.models.placeholder import Placeholder
from app.models.user import User

# This helps to expose the models at the package level
__all__ = [
    'Client',
    'Document',
    'TaxAdvisor',
    'WorkOrder',
    'Placeholder',
    'Salutation',
    'LegalForm',
    'User'
] 