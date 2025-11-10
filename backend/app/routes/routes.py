from flask import jsonify, request, send_file, current_app
from app import db
from app.models import Client, Document, TaxAdvisor, WorkOrder, Placeholder, Salutation, LegalForm, User
from app.routes import api_bp
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.services.llm_service import ollama_service
from app.services.document_service import document_service
from app.services.user_service import UserService
import base64
import os
import tempfile
import logging
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

# Document
@api_bp.route('/documents/preview/<int:document_id>', methods=['POST'])
def preview_document(document_id):
    """Generate a preview of a document with placeholders filled in.
    
    Request body should contain placeholder values as JSON.
    """
    logger.info("Received request to preview document with ID: %d", document_id)
    try:
        placeholder_values = request.get_json()
        if not placeholder_values:
            logger.warning("No placeholder values provided for document with ID: %d", document_id)
            return jsonify({'error': 'No placeholder values provided'}), 400
            
        logger.debug("Placeholder values: %s", placeholder_values)
        preview_data = document_service.create_document_preview(document_id, placeholder_values)
        logger.info("Successfully created preview for document with ID: %d", document_id)
        return jsonify(preview_data), 200
    except ValueError as e:
        logger.error("Error value when creating preview for document %d: %s", document_id, str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Исключение при создании предпросмотра для документа %d: %s", document_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500

@api_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    """Upload a document template and save it.
    
    Form data should include:
    - file: The document file
    - name: Template name
    - description: Template description (optional)
    - placeholders: JSON string of placeholder definitions (optional)
    """
    logger.info("Received request to upload document")
    try:
        # Check if file is present
        if 'file' not in request.files:
            logger.warning("File not provided in upload request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("File with empty name in upload request")
            return jsonify({'error': 'No file selected'}), 400
            
        logger.debug("Uploading file: %s", file.filename)
        
        # Get document metadata
        name = request.form.get('name', file.filename)
        description = request.form.get('description', '')
        
        # Save file
        file_path = document_service.save_document(file, file.filename)
        logger.debug("File saved at path: %s", file_path)
        
        # Process placeholders if provided
        placeholders = []
        if 'placeholders' in request.form:
            import json
            try:
                placeholders = json.loads(request.form['placeholders'])
                logger.debug("Received placeholders: %d", len(placeholders))
            except json.JSONDecodeError:
                logger.error("Invalid placeholders JSON")
                return jsonify({'error': 'Invalid placeholders JSON'}), 400
        
        # Save document with placeholders
        file_data = {
            'name': name,
            'description': description,
            'file_path': file_path,
            'file_type': file.content_type,
            'created_by': request.form.get('created_by')
        }
        
        document = document_service.save_document_with_placeholders(file_data, placeholders)
        logger.info("Document successfully saved with ID: %d", document.id)
        
        return jsonify({
            'id': document.id,
            'name': document.title,
            'description': document.content,
            'file_type': document.document_type,
            'created_at': document.created_at.isoformat() if document.created_at else None
        }), 201
    except ValueError as e:
        logger.error("Error value when uploading document: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when uploading document: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to upload document: {str(e)}'}), 500

@api_bp.route('/documents/download/<int:document_id>', methods=['POST'])
def download_document_with_placeholders(document_id):
    """Generate and download a document with placeholders filled in.
    
    Request body should contain placeholder values as JSON.
    """
    logger.info("Received request to download document with ID: %d", document_id)
    try:
        placeholder_values = request.get_json()
        if not placeholder_values:
            logger.warning("No placeholder values provided for document with ID: %d", document_id)
            return jsonify({'error': 'No placeholder values provided'}), 400
            
        logger.debug("Placeholder values: %s", placeholder_values)
        
        # Generate preview
        preview_data = document_service.create_document_preview(document_id, placeholder_values)
        
        # Decode base64 data
        file_data = base64.b64decode(preview_data['preview_data'])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + preview_data['filename'].split('.')[-1]) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
            logger.debug("Temporary file created at path: %s", tmp_path)
        
        # Send file
        logger.info("Sending filled document: %s", preview_data['filename'])
        response = send_file(
            tmp_path,
            mimetype=preview_data['mime_type'],
            as_attachment=False,
            download_name=preview_data['filename']
        )
        
        # Clean up temp file after sending
        @response.call_on_close
        def cleanup():
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.debug("Temporary file deleted: %s", tmp_path)
                
        return response
    except ValueError as e:
        logger.error("Error value when downloading document %d: %s", document_id, str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when downloading document %d: %s", document_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to generate document: {str(e)}'}), 500

@api_bp.route('/documents/preview-temp', methods=['POST'])
def preview_uploaded_document():
    """Generate a preview of an uploaded document with placeholders filled in without saving to database.
    
    Expected multipart/form-data with:
    - file: The document file
    - placeholders: JSON string of placeholder values
    """
    logger.info("Received request to preview temporary document")
    try:
        # Check if file is present
        if 'file' not in request.files:
            logger.warning("File not provided in preview request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("File with empty name in preview request")
            return jsonify({'error': 'No file selected'}), 400
            
        logger.debug("Uploading temporary file: %s", file.filename)
        
        # Get placeholder values
        placeholder_values = {}
        if 'placeholders' in request.form:
            import json
            try:
                placeholder_values = json.loads(request.form['placeholders'])
                logger.debug("Received placeholder values: %d", len(placeholder_values))
            except json.JSONDecodeError:
                logger.error("Invalid placeholders JSON")
                return jsonify({'error': 'Invalid placeholders JSON'}), 400
                
        # Generate preview
        preview_data = document_service.create_preview_from_uploaded_file(file, placeholder_values)
        logger.info("Successfully created preview for temporary document: %s", file.filename)
        
        return jsonify(preview_data), 200
    except ValueError as e:
        logger.error("Error value when creating preview for temporary document: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when creating preview for temporary document: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500

@api_bp.route('/documents/placeholders/rename-temp', methods=['POST'])
def update_placeholder_name_in_temp():
    """Update a placeholder name in a temporary document file.
    
    Expected multipart/form-data with:
    - file: The document file
    - oldName: Current placeholder name
    - newName: New placeholder name to replace it with
    
    Returns the updated document with placeholders replaced.
    """
    logger.info("Received request to update placeholder name in temporary document")
    try:
        # Check if file is present
        if 'file' not in request.files:
            logger.warning("File not provided in rename-temp request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("File with empty name in rename-temp request")
            return jsonify({'error': 'No file selected'}), 400
            
        old_name = request.form.get('oldName')
        new_name = request.form.get('newName')
        
        if not old_name or not new_name:
            logger.warning("Missing oldName or newName in request")
            return jsonify({'error': 'Missing required fields: oldName and newName'}), 400
        
        logger.debug("Updating placeholder from '%s' to '%s' in temporary file", old_name, new_name)
        
        # Update placeholder in the file
        result = document_service.update_placeholder_in_temp_file(file, old_name, new_name)
        
        logger.info("Successfully processed placeholder update in temporary document")
        return jsonify(result), 200
    except ValueError as e:
        logger.error("Value error when updating placeholder in temp file: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when updating placeholder in temp file: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to update placeholder: {str(e)}'}), 500

# Dashboard

# Client routes
@api_bp.route('/clients', methods=['GET'])
def get_clients():
    """Get all clients."""
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])

@api_bp.route('/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Get a specific client."""
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict())

@api_bp.route('/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete a specific client."""
    try:
        # Get the client record
        client = Client.query.get_or_404(client_id)
        logger.info("Found client with ID: %d for deletion", client_id)
        
        # Simply delete the client and let the database handle cascades
        # or if no relationships exist, this will just delete the client
        db.session.delete(client)
        db.session.commit()
        
        logger.info("Client deleted successfully with ID: %d", client_id)
        return jsonify({"success": True, "message": "Client deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting client with ID %d: %s", client_id, str(e), exc_info=True)
        return jsonify({"error": f"Failed to delete client: {str(e)}"}), 500

@api_bp.route('/clients', methods=['POST'])
def create_client():
    """Create a new client."""
    try:
        data = request.get_json()
        logger.debug("Received client data: %s", data)
        
        # Convert string values of Enum to objects of Enum
        if data.get('client_type') == 'natural' and data.get('salutation'):
            try:
                data['salutation'] = Salutation[data['salutation']]
            except KeyError:
                logger.error("Invalid salutation value: %s", data['salutation'])
                return jsonify({'error': f'Invalid salutation value: {data["salutation"]}'}), 400
        
        if data.get('client_type') == 'company' and data.get('legal_form'):
            try:
                data['legal_form'] = LegalForm[data['legal_form']]
            except KeyError:
                logger.error("Invalid legal form value: %s", data['legal_form'])
                return jsonify({'error': f'Invalid legal form value: {data["legal_form"]}'}), 400
        
        if data.get('contact_salutation'):
            try:
                data['contact_salutation'] = Salutation[data['contact_salutation']]
            except KeyError:
                logger.error("Invalid contact salutation value: %s", data['contact_salutation'])
                return jsonify({'error': f'Invalid contact salutation value: {data["contact_salutation"]}'}), 400
        
        # Convert string date representation to date object if it exists
        if data.get('birth_date'):
            try:
                data['birth_date'] = datetime.strptime(data['birth_date'], "%Y-%m-%d").date()
            except ValueError:
                logger.error("Invalid date format for birth_date: %s", data['birth_date'])
                return jsonify({'error': f'Invalid date format for birth_date: {data["birth_date"]}. Use YYYY-MM-DD format.'}), 400
        
        client = Client(**data)
        db.session.add(client)
        try:
            db.session.commit()
            logger.info("Client created successfully with ID: %d", client.id)
            return jsonify(client.to_dict()), 201
        except IntegrityError as e:
            db.session.rollback()
            logger.error("IntegrityError during client creation: %s", str(e))
            return jsonify({'error': 'Client with this email or tax number already exists'}), 400
    except Exception as e:
        logger.error("Unexpected error during client creation: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to create client: {str(e)}'}), 500

# Tax Advisor routes
@api_bp.route('/tax-advisors', methods=['GET'])
def get_tax_advisors():
    """Get all tax advisors."""
    advisors = TaxAdvisor.query.all()
    return jsonify([{
        'id': advisor.id,
        'name': advisor.name,
        'email': advisor.email,
        'phone': advisor.phone,
        'address': advisor.address,
        'tax_number': advisor.tax_number,
        'specialization': advisor.specialization
    } for advisor in advisors])

@api_bp.route('/tax-advisors/<int:advisor_id>', methods=['GET'])
def get_tax_advisor(advisor_id):
    """Get a specific tax advisor."""
    advisor = TaxAdvisor.query.get_or_404(advisor_id)
    return jsonify({
        'id': advisor.id,
        'name': advisor.name,
        'email': advisor.email,
        'phone': advisor.phone,
        'address': advisor.address,
        'tax_number': advisor.tax_number,
        'specialization': advisor.specialization
    })

# Document routes
@api_bp.route('/documents', methods=['GET'])
def get_documents():
    """Get all documents."""
    documents = Document.query.all()
    return jsonify([doc.to_dict() for doc in documents])

@api_bp.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific document."""
    document = Document.query.get_or_404(document_id)
    return jsonify(document.to_dict())

@api_bp.route('/documents/<int:document_id>/file', methods=['GET'])
def get_document_file(document_id):
    """Get the original file of a specific document."""
    logger.info("Received request to get file for document with ID: %d", document_id)
    try:
        # Get the document record
        document = Document.query.get_or_404(document_id)
        
        # Check if file exists
        if not document.file_path or not os.path.exists(document.file_path):
            logger.error("Document file not found for ID %d at path: %s", document_id, document.file_path)
            return jsonify({"error": "Document file not found"}), 404
        
        # Determine MIME type
        mime_type = document.document_type or 'application/octet-stream'
        
        # Get original filename
        filename = os.path.basename(document.file_path)
        
        logger.info("Sending document file: %s", filename)
        return send_file(
            document.file_path,
            mimetype=mime_type,
            as_attachment=False,
            download_name=filename
        )
        
    except Exception as e:
        logger.error("Error getting document file with ID %d: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Failed to get document file: {str(e)}"}), 500

@api_bp.route('/documents/<int:document_id>/text', methods=['GET'])
def get_document_text(document_id):
    """Get the text content of a specific document."""
    logger.info("Received request to get text content for document with ID: %d", document_id)
    try:
        # Get the document record
        document = Document.query.get_or_404(document_id)
        
        # Check if file exists
        if not document.file_path or not os.path.exists(document.file_path):
            logger.error("Document file not found for ID %d at path: %s", document_id, document.file_path)
            return jsonify({"error": "Document file not found"}), 404
        
        # Extract text using document service
        text_content = document_service.extract_text_from_file(document.file_path)
        
        logger.info("Successfully extracted text content for document ID: %d", document_id)
        return jsonify({"text": text_content}), 200
        
    except Exception as e:
        logger.error("Error getting document text with ID %d: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Failed to get document text: {str(e)}"}), 500

@api_bp.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a specific document."""
    logger.info("Received request to delete document with ID: %d", document_id)
    try:
        # Get the document record
        document = Document.query.get_or_404(document_id)
        logger.info("Found document with ID: %d for deletion", document_id)
        
        # Delete the document file if it exists
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                logger.info("Deleted document file: %s", document.file_path)
            except OSError as e:
                logger.warning("Could not delete document file %s: %s", document.file_path, str(e))
        
        # Delete the document from database
        db.session.delete(document)
        db.session.commit()
        
        logger.info("Document deleted successfully with ID: %d", document_id)
        return jsonify({"success": True, "message": "Document deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting document with ID %d: %s", document_id, str(e), exc_info=True)
        return jsonify({"error": f"Failed to delete document: {str(e)}"}), 500

@api_bp.route('/documents/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """Update an existing document template.
    
    Form data can include:
    - file: The new document file (optional)
    - name: Template name
    - description: Template description (optional)
    - placeholders: JSON string of placeholder definitions (optional)
    """
    logger.info("Received request to update document with ID: %d", document_id)
    try:
        # Get the document record
        document = Document.query.get_or_404(document_id)
        logger.info("Found document with ID: %d for update", document_id)
        
        # Update document metadata
        if 'name' in request.form:
            document.title = request.form['name']
            logger.debug("Updated document name to: %s", document.title)
            
        if 'description' in request.form:
            document.content = request.form['description']
            logger.debug("Updated document description")
        
        # Update file if provided
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                logger.debug("Updating document file: %s", file.filename)
                
                # Delete old file if it exists
                if document.file_path and os.path.exists(document.file_path):
                    try:
                        os.remove(document.file_path)
                        logger.info("Deleted old document file: %s", document.file_path)
                    except OSError as e:
                        logger.warning("Could not delete old document file %s: %s", document.file_path, str(e))
                
                # Save new file
                new_file_path = document_service.save_document(file, file.filename)
                document.file_path = new_file_path
                document.document_type = file.content_type
                logger.debug("New file saved at path: %s", new_file_path)
        
        # Update placeholders if provided
        if 'placeholders' in request.form:
            import json
            try:
                placeholders = json.loads(request.form['placeholders'])
                document.placeholders = placeholders
                logger.debug("Updated placeholders: %d", len(placeholders))
            except json.JSONDecodeError:
                logger.error("Invalid placeholders JSON")
                return jsonify({'error': 'Invalid placeholders JSON'}), 400
        
        # Save changes to database
        db.session.commit()
        logger.info("Document updated successfully with ID: %d", document.id)
        
        return jsonify({
            'id': document.id,
            'name': document.title,
            'description': document.content,
            'file_type': document.document_type,
            'created_at': document.created_at.isoformat() if document.created_at else None,
            'updated_at': document.updated_at.isoformat() if document.updated_at else None
        }), 200
    except ValueError as e:
        db.session.rollback()
        logger.error("Error value when updating document %d: %s", document_id, str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error("Exception when updating document %d: %s", document_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to update document: {str(e)}'}), 500

@api_bp.route('/documents', methods=['POST'])
def create_document():
    """Create a new document."""
    data = request.get_json()
    document = Document(**data)
    db.session.add(document)
    try:
        db.session.commit()
        return jsonify(document.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Invalid data provided'}), 400

# Work Order routes
@api_bp.route('/work-orders', methods=['GET'])
def get_work_orders():
    """Get all work orders."""
    work_orders = WorkOrder.query.all()
    return jsonify([{
        'id': order.id,
        'title': order.title,
        'description': order.description,
        'status': order.status,
        'priority': order.priority,
        'due_date': order.due_date.isoformat() if order.due_date else None,
        'client_id': order.client_id,
        'tax_advisor_id': order.tax_advisor_id,
        'template_id': order.template_id
    } for order in work_orders])

@api_bp.route('/work-orders/<int:order_id>', methods=['GET'])
def get_work_order(order_id):
    """Get a specific work order."""
    order = WorkOrder.query.get_or_404(order_id)
    return jsonify({
        'id': order.id,
        'title': order.title,
        'description': order.description,
        'status': order.status,
        'priority': order.priority,
        'due_date': order.due_date.isoformat() if order.due_date else None,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
        'client_id': order.client_id,
        'tax_advisor_id': order.tax_advisor_id,
        'template_id': order.template_id
    })

@api_bp.route('/work-orders/<int:order_id>', methods=['PUT'])
def update_work_order(order_id):
    """Update a specific work order."""
    logger.info("Received request to update work order with ID: %d", order_id)
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get the work order
        work_order = WorkOrder.query.get_or_404(order_id)
        logger.info("Found work order with ID: %d for update", order_id)
        
        # Update fields if provided
        if 'title' in data:
            work_order.title = data['title']
        if 'description' in data:
            work_order.description = data['description']
        if 'status' in data:
            work_order.status = data['status']
        if 'priority' in data:
            work_order.priority = data['priority']
        if 'client_id' in data:
            # Validate client exists
            client = Client.query.get(data['client_id'])
            if not client:
                return jsonify({'error': f'Client with ID {data["client_id"]} not found'}), 404
            work_order.client_id = data['client_id']
        if 'tax_advisor_id' in data:
            # Validate tax advisor exists
            tax_advisor = TaxAdvisor.query.get(data['tax_advisor_id'])
            if not tax_advisor:
                return jsonify({'error': f'Tax advisor with ID {data["tax_advisor_id"]} not found'}), 404
            work_order.tax_advisor_id = data['tax_advisor_id']
        if 'template_id' in data:
            work_order.template_id = data['template_id']
        if 'due_date' in data:
            if data['due_date']:
                try:
                    from datetime import datetime
                    work_order.due_date = datetime.fromisoformat(data['due_date'])
                except ValueError:
                    logger.error("Invalid due_date format: %s", data['due_date'])
                    return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
            else:
                work_order.due_date = None
        
        # Update timestamp
        work_order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info("Work order updated successfully with ID: %d", work_order.id)
        
        return jsonify({
            'id': work_order.id,
            'title': work_order.title,
            'description': work_order.description,
            'status': work_order.status,
            'priority': work_order.priority,
            'due_date': work_order.due_date.isoformat() if work_order.due_date else None,
            'created_at': work_order.created_at.isoformat() if work_order.created_at else None,
            'updated_at': work_order.updated_at.isoformat() if work_order.updated_at else None,
            'client_id': work_order.client_id,
            'tax_advisor_id': work_order.tax_advisor_id,
            'template_id': work_order.template_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating work order with ID %d: %s", order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to update work order: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>', methods=['DELETE'])
def delete_work_order(order_id):
    """Delete a specific work order."""
    logger.info("Received request to delete work order with ID: %d", order_id)
    try:
        # Get the work order record
        work_order = WorkOrder.query.get_or_404(order_id)
        logger.info("Found work order with ID: %d for deletion", order_id)
        
        # Delete the work order from database
        db.session.delete(work_order)
        db.session.commit()
        
        logger.info("Work order deleted successfully with ID: %d", order_id)
        return jsonify({"success": True, "message": "Work order deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting work order with ID %d: %s", order_id, str(e), exc_info=True)
        return jsonify({"error": f"Failed to delete work order: {str(e)}"}), 500

@api_bp.route('/work-orders', methods=['POST'])
def create_work_order():
    """Create a new work order/workflow."""
    logger.info("Received request to create a new work order")
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logger.debug("Creating work order with data: %s", data)
        
        # Validate required fields
        required_fields = ['name', 'client_id']
        for field in required_fields:
            if not data.get(field):
                logger.error("Missing required field: %s", field)
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if client exists
        client = Client.query.get(data['client_id'])
        if not client:
            logger.error("Client not found with ID: %d", data['client_id'])
            return jsonify({'error': f'Client with ID {data["client_id"]} not found'}), 404
        
        # Get tax advisor (use first available if not specified)
        tax_advisor_id = data.get('tax_advisor_id')
        if not tax_advisor_id:
            first_advisor = TaxAdvisor.query.first()
            if first_advisor:
                tax_advisor_id = first_advisor.id
            else:
                logger.error("No tax advisor available")
                return jsonify({'error': 'No tax advisor available'}), 400
        
        # Check if tax advisor exists
        tax_advisor = TaxAdvisor.query.get(tax_advisor_id)
        if not tax_advisor:
            logger.error("Tax advisor not found with ID: %d", tax_advisor_id)
            return jsonify({'error': f'Tax advisor with ID {tax_advisor_id} not found'}), 404
        
        # Create work order
        work_order = WorkOrder(
            title=data['name'],
            description=data.get('description', ''),
            status='open',  # Default status
            priority=data.get('priority', 'medium'),
            client_id=data['client_id'],
            tax_advisor_id=tax_advisor_id,
            template_id=data.get('template_id')  # Add template_id support
        )
        
        # Handle due date if provided
        if data.get('due_date'):
            try:
                from datetime import datetime
                work_order.due_date = datetime.fromisoformat(data['due_date'])
            except ValueError:
                logger.error("Invalid due_date format: %s", data['due_date'])
                return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
        
        db.session.add(work_order)
        db.session.commit()
        
        logger.info("Work order created successfully with ID: %d", work_order.id)
        
        return jsonify({
            'id': work_order.id,
            'title': work_order.title,
            'description': work_order.description,
            'status': work_order.status,
            'priority': work_order.priority,
            'due_date': work_order.due_date.isoformat() if work_order.due_date else None,
            'created_at': work_order.created_at.isoformat() if work_order.created_at else None,
            'updated_at': work_order.updated_at.isoformat() if work_order.updated_at else None,
            'client_id': work_order.client_id,
            'tax_advisor_id': work_order.tax_advisor_id,
            'template_id': work_order.template_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error creating work order: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to create work order: {str(e)}'}), 500

@api_bp.route('/work-orders/with-documents', methods=['POST'])
def create_work_order_with_documents():
    """Create a new work order/workflow with document uploads."""
    logger.info("Received request to create a new work order with documents")
    try:
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        priority = request.form.get('priority', 'medium')
        client_id = request.form.get('client_id', type=int)
        template_id = request.form.get('template_id', type=int)
        due_date = request.form.get('due_date')
        assigned_to = request.form.get('assigned_to')
        recipient_id = request.form.get('recipient_id', type=int)
        
        logger.debug("Creating work order with form data: name=%s, client_id=%s", name, client_id)
        
        # Validate required fields
        if not name or not client_id:
            logger.error("Missing required fields: name or client_id")
            return jsonify({'error': 'Missing required fields: name and client_id are required'}), 400
        
        # Check if client exists
        client = Client.query.get(client_id)
        if not client:
            logger.error("Client not found with ID: %d", client_id)
            return jsonify({'error': f'Client with ID {client_id} not found'}), 404
        
        # Get tax advisor (use first available if not specified)
        tax_advisor_id = request.form.get('tax_advisor_id', type=int)
        if not tax_advisor_id:
            first_advisor = TaxAdvisor.query.first()
            if first_advisor:
                tax_advisor_id = first_advisor.id
            else:
                logger.error("No tax advisor available")
                return jsonify({'error': 'No tax advisor available'}), 400
        
        # Check if tax advisor exists
        tax_advisor = TaxAdvisor.query.get(tax_advisor_id)
        if not tax_advisor:
            logger.error("Tax advisor not found with ID: %d", tax_advisor_id)
            return jsonify({'error': f'Tax advisor with ID {tax_advisor_id} not found'}), 404
        
        # Create work order
        work_order = WorkOrder(
            title=name,
            description=description,
            status='open',  # Default status
            priority=priority,
            client_id=client_id,
            tax_advisor_id=tax_advisor_id,
            template_id=template_id
        )
        
        # Handle due date if provided
        if due_date:
            try:
                from datetime import datetime
                work_order.due_date = datetime.fromisoformat(due_date)
            except ValueError:
                logger.error("Invalid due_date format: %s", due_date)
                return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
        
        db.session.add(work_order)
        db.session.flush()  # To get the work_order.id
        
        # Handle file uploads with PDF conversion
        uploaded_files = request.files.getlist('documents')
        document_count = 0
        
        if uploaded_files:
            import os
            from werkzeug.utils import secure_filename
            
            for file in uploaded_files:
                if file and file.filename:
                    original_filename = secure_filename(file.filename)
                    
                    try:
                        # Convert file to PDF and get the path and new filename
                        pdf_file_path, pdf_filename = document_service.convert_file_to_pdf(
                            file, original_filename, file.content_type
                        )
                        
                        # Create document record with PDF information
                        document = Document(
                            title=pdf_filename,  # Use PDF filename
                            document_type='application/pdf',  # Always PDF now
                            status='uploaded',
                            file_path=os.path.relpath(pdf_file_path, current_app.config['UPLOAD_FOLDER']),
                            client_id=client_id,
                            tax_advisor_id=tax_advisor_id,
                            work_order_id=work_order.id
                        )
                        
                        db.session.add(document)
                        document_count += 1
                        
                        logger.info("Document converted to PDF and uploaded: %s -> %s for work order: %d", 
                                   original_filename, pdf_filename, work_order.id)
                                   
                    except Exception as e:
                        logger.error("Failed to convert and upload document %s: %s", 
                                   original_filename, str(e))
                        # Skip this file but continue with others
                        continue
        
        db.session.commit()
        
        logger.info("Work order created successfully with ID: %d and %d documents", work_order.id, document_count)
        
        return jsonify({
            'id': work_order.id,
            'title': work_order.title,
            'description': work_order.description,
            'status': work_order.status,
            'priority': work_order.priority,
            'due_date': work_order.due_date.isoformat() if work_order.due_date else None,
            'created_at': work_order.created_at.isoformat() if work_order.created_at else None,
            'client_id': work_order.client_id,
            'tax_advisor_id': work_order.tax_advisor_id,
            'template_id': work_order.template_id,
            'document_count': document_count
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error creating work order with documents: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to create work order with documents: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/documents', methods=['GET'])
def get_work_order_documents(order_id):
    """Get all documents for a specific work order."""
    logger.info("Received request to get documents for work order ID: %d", order_id)
    try:
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
                        
        # Get all documents for this work order
        documents = Document.query.filter_by(work_order_id=order_id).all()
        
        import os
        return jsonify([{
            'id': doc.id,
            'name': doc.title,
            'file_name': doc.title,
            'file_type': get_file_mime_type(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)) if doc.file_path else 'application/octet-stream',
            'file_size': get_file_size(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)) if doc.file_path else 0,
            'document_type': doc.document_type,
            'status': doc.status,
            'created_at': doc.created_at.isoformat() if doc.created_at else None,
            'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
        } for doc in documents])
        
    except Exception as e:
        logger.error("Error getting documents for work order %d: %s", order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to get documents: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/documents', methods=['POST'])
def upload_work_order_documents(order_id):
    """Upload additional documents to an existing work order."""
    logger.info("Received request to upload documents to work order ID: %d", order_id)
    try:
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
        
        # Handle file uploads
        uploaded_files = request.files.getlist('documents')
        
        if not uploaded_files:
            return jsonify({'error': 'No files provided'}), 400
        
        document_count = 0
        uploaded_documents = []
        
        import os
        from werkzeug.utils import secure_filename
        
        for file in uploaded_files:
            if file and file.filename:
                original_filename = secure_filename(file.filename)
                
                try:
                    # Convert file to PDF and get the path and new filename
                    pdf_file_path, pdf_filename = document_service.convert_file_to_pdf(
                        file, original_filename, file.content_type
                    )
                    
                    # Create document record with PDF information
                    document = Document(
                        title=pdf_filename,  # Use PDF filename
                        document_type='application/pdf',  # Always PDF now
                        status='uploaded',
                        file_path=os.path.relpath(pdf_file_path, current_app.config['UPLOAD_FOLDER']),
                        client_id=work_order.client_id,
                        tax_advisor_id=work_order.tax_advisor_id,
                        work_order_id=work_order.id
                    )
                    
                    db.session.add(document)
                    document_count += 1
                    
                    uploaded_documents.append({
                        'name': pdf_filename,
                        'file_type': 'application/pdf',
                        'file_size': get_file_size(pdf_file_path)
                    })
                    
                    logger.info("Document converted to PDF and uploaded: %s -> %s for work order: %d", 
                               original_filename, pdf_filename, work_order.id)
                               
                except Exception as e:
                    logger.error("Failed to convert and upload document %s: %s", 
                               original_filename, str(e))
                    # Skip this file but continue with others
                    continue
        
        db.session.commit()
        
        logger.info("Successfully uploaded %d documents to work order: %d", document_count, work_order.id)
        
        return jsonify({
            'message': f'Successfully uploaded {document_count} document(s)',
            'document_count': document_count,
            'documents': uploaded_documents
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error uploading documents to work order %d: %s", order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to upload documents: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/documents/<int:document_id>/file', methods=['GET'])
def get_work_order_document_file(order_id, document_id):
    """Get document file for viewing/download from a work order."""
    logger.info("Received request to get document file: %d from work order: %d", document_id, order_id)
    try:
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
        
        # Get document and verify it belongs to this work order
        document = Document.query.filter_by(id=document_id, work_order_id=order_id).first()
        if not document:
            return jsonify({'error': 'Document not found or does not belong to this work order'}), 404
        
        if not document.file_path:
            return jsonify({'error': 'Document file not found'}), 404
        
        import os
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.file_path)
        
        if not os.path.exists(file_path):
            logger.error("Document file not found on disk: %s", file_path)
            return jsonify({'error': 'Document file not found on disk'}), 404
        
        return send_file(
            file_path,
            as_attachment=False,
            download_name=document.title
        )
        
    except Exception as e:
        logger.error("Error getting document file %d from work order %d: %s", document_id, order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to get document file: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/documents/<int:document_id>', methods=['DELETE'])
def delete_work_order_document(order_id, document_id):
    """Delete a document from a work order."""
    logger.info("Received request to delete document: %d from work order: %d", document_id, order_id)
    try:
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
        
        # Get document and verify it belongs to this work order
        document = Document.query.filter_by(id=document_id, work_order_id=order_id).first()
        if not document:
            return jsonify({'error': 'Document not found or does not belong to this work order'}), 404
        
        # Delete file from disk if it exists
        if document.file_path:
            import os
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info("Document file deleted from disk: %s", file_path)
                except OSError as e:
                    logger.warning("Could not delete document file from disk: %s - %s", file_path, str(e))
        
        # Delete document record from database
        db.session.delete(document)
        db.session.commit()
        
        logger.info("Document deleted successfully: %d from work order: %d", document_id, order_id)
        
        return jsonify({
            'message': 'Document deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting document %d from work order %d: %s", document_id, order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to delete document: {str(e)}'}), 500

# Helper functions for file operations
def get_file_mime_type(file_path):
    """Get MIME type of a file."""
    import mimetypes
    import os
    
    if not file_path or not os.path.exists(file_path):
        return 'application/octet-stream'
    
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def get_file_size(file_path):
    """Get size of a file in bytes."""
    import os
    
    if not file_path or not os.path.exists(file_path):
        return 0
    
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

# Placeholder routes
@api_bp.route('/placeholders', methods=['GET'])
def get_placeholders():
    """Get all placeholders."""
    placeholders = Placeholder.query.all()
    return jsonify([{
        'id': ph.id,
        'name': ph.name,
        'description': ph.description,
        'value': ph.value,
        'type': ph.type,
        'is_required': ph.is_required,
        'document_id': ph.document_id
    } for ph in placeholders])

@api_bp.route('/placeholders/<int:placeholder_id>', methods=['GET'])
def get_placeholder(placeholder_id):
    """Get a specific placeholder."""
    placeholder = Placeholder.query.get_or_404(placeholder_id)
    return jsonify({
        'id': placeholder.id,
        'name': placeholder.name,
        'description': placeholder.description,
        'value': placeholder.value,
        'type': placeholder.type,
        'is_required': placeholder.is_required,
        'document_id': placeholder.document_id
    })

@api_bp.route('/documents/<int:document_id>/placeholders/rename', methods=['PUT'])
def update_placeholder_name(document_id):
    """Update a placeholder name within a document.
    
    Request body should contain:
    - oldName: Current placeholder name
    - newName: New placeholder name to replace it with
    """
    logger.info("Received request to update placeholder name for document with ID: %d", document_id)
    try:
        data = request.get_json()
        if not data or 'oldName' not in data or 'newName' not in data:
            logger.warning("Missing required fields for placeholder rename")
            return jsonify({'error': 'Missing required fields: oldName and newName'}), 400
            
        old_name = data['oldName']
        new_name = data['newName']
        
        logger.debug("Updating placeholder from '%s' to '%s'", old_name, new_name)
        
        # Update placeholder in the document
        result = document_service.update_placeholder_name(document_id, old_name, new_name)
        
        if result:
            logger.info("Successfully updated placeholder name in document %d", document_id)
            return jsonify({'success': True, 'message': 'Placeholder updated successfully'}), 200
        else:
            logger.warning("Placeholder '%s' not found in document %d", old_name, document_id)
            return jsonify({'error': 'Placeholder not found'}), 404
    except ValueError as e:
        logger.error("Value error when updating placeholder: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when updating placeholder: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to update placeholder: {str(e)}'}), 500

@api_bp.route('/documents/templates', methods=['GET'])
def get_document_templates():
    """Get all document templates with their placeholders.
    
    Returns a list of templates that can be used to create new documents.
    """
    logger.info("Received request to get all document templates")
    try:
        # Get all documents
        documents = Document.query.all()
        
        # Format document data with placeholders
        result = []
        for doc in documents:
            # Get placeholders from JSON field instead of querying the Placeholder table
            placeholders_data = doc.placeholders or []
            
            if doc.content is None:
                continue
            
            doc_dict = {
                'id': doc.id,
                'name': doc.title,  # Use title as name for frontend consistency
                'description': doc.content,  # Use content as description
                'file_type': doc.document_type,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'placeholders': placeholders_data
            }
            
            result.append(doc_dict)
        
        logger.info("Successfully retrieved %d document templates", len(result))
        return jsonify(result), 200
    except Exception as e:
        logger.error("Error retrieving document templates: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to retrieve templates: {str(e)}'}), 500

@api_bp.route('/documents/create-from-template/<int:template_id>', methods=['POST'])
def create_from_template(template_id):
    """Create a document from a template with placeholders filled in.
    
    Request body should contain placeholder values as JSON.
    Returns the generated document data.
    """
    logger.info("Received request to create document from template with ID: %d", template_id)
    try:
        placeholder_values = request.get_json()
        if not placeholder_values:
            logger.warning("No placeholder values provided for template with ID: %d", template_id)
            return jsonify({'error': 'No placeholder values provided'}), 400
            
        logger.debug("Placeholder values: %s", placeholder_values)
        
        # Find the template
        document = Document.query.get(template_id)
        if not document:
            logger.error("Template with ID %d not found", template_id)
            return jsonify({'error': f'Template with ID {template_id} not found'}), 404
        
        # Get associated placeholders from JSON field
        placeholders = document.placeholders or []
        logger.debug("Found %d placeholders for template", len(placeholders))
        
        # Validate required placeholders are provided
        missing_required = []
        for placeholder in placeholders:
            if placeholder.get('required', False) and placeholder.get('name') not in placeholder_values:
                missing_required.append(placeholder.get('name'))
        
        if missing_required:
            logger.error("Missing required placeholders: %s", ", ".join(missing_required))
            return jsonify({'error': f'Missing required placeholders: {", ".join(missing_required)}'}), 400
        
        # Generate document
        preview_data = document_service.create_document_preview(template_id, placeholder_values)
        logger.info("Successfully created document from template with ID: %d", template_id)
        
        return jsonify(preview_data), 200
    except ValueError as e:
        logger.error("Error creating document from template %d: %s", template_id, str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception creating document from template %d: %s", template_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to create document: {str(e)}'}), 500

# User Settings Routes
@api_bp.route('/users/settings/<int:user_id>', methods=['GET'])
def get_user_settings(user_id):
    """Get user settings and preferences.
    
    Returns user data including model preferences.
    """
    logger.info("Received request to get settings for user with ID: %d", user_id)
    try:
        settings = UserService.get_user_settings(user_id)
        if not settings:
            logger.error("User with ID %d not found", user_id)
            return jsonify({'error': 'User not found'}), 404
        
        logger.info("Successfully retrieved settings for user with ID: %d", user_id)
        return jsonify(settings), 200
    except Exception as e:
        logger.error("Error retrieving user settings for user %d: %s", user_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to retrieve user settings: {str(e)}'}), 500

@api_bp.route('/users/settings/<int:user_id>', methods=['PUT'])
def update_user_settings(user_id):
    """Update user settings and preferences.
    
    Request body should contain settings to update.
    """
    logger.info("Received request to update settings for user with ID: %d", user_id)
    try:
        settings = request.get_json()
        if not settings:
            logger.warning("No settings provided for user with ID: %d", user_id)
            return jsonify({'error': 'No settings provided'}), 400
            
        logger.debug("Updating settings: %s", settings)
        
        # Validate model selections if provided
        if 'preferred_text_model' in settings or 'preferred_image_model' in settings:
            text_model = settings.get('preferred_text_model', '')
            image_model = settings.get('preferred_image_model', '')
            validation = UserService.validate_model_selection(text_model, image_model)
            
            if not validation['valid']:
                logger.warning("Invalid model selection for user %d: %s", user_id, validation['messages'])
                return jsonify({
                    'error': 'Invalid model selection',
                    'messages': validation['messages']
                }), 400
            
            # Return warnings if models are not installed but valid
            if validation['warnings']:
                logger.info("Model selection warnings for user %d: %s", user_id, validation['warnings'])
        
        updated_user = UserService.update_user_settings(user_id, settings)
        if not updated_user:
            logger.error("User with ID %d not found", user_id)
            return jsonify({'error': 'User not found'}), 404
        
        response_data = updated_user.to_dict()
        
        # Add validation warnings if any
        if 'preferred_text_model' in settings or 'preferred_image_model' in settings:
            text_model = settings.get('preferred_text_model', updated_user.preferred_text_model)
            image_model = settings.get('preferred_image_model', updated_user.preferred_image_model)
            validation = UserService.validate_model_selection(text_model, image_model)
            if validation['warnings']:
                response_data['warnings'] = validation['warnings']
        
        logger.info("Successfully updated settings for user with ID: %d", user_id)
        return jsonify(response_data), 200
    except ValueError as e:
        logger.error("Value error when updating user settings for user %d: %s", user_id, str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when updating user settings for user %d: %s", user_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to update user settings: {str(e)}'}), 500

@api_bp.route('/users/models', methods=['GET'])
def get_available_models():
    """Get available Ollama models and system status.
    
    Returns Ollama installation status and categorized models.
    """
    logger.info("Received request to get available models")
    try:
        models_data = UserService.get_available_models()
        logger.info("Successfully retrieved available models")
        return jsonify(models_data), 200
    except Exception as e:
        logger.error("Error retrieving available models: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to retrieve models: {str(e)}'}), 500

@api_bp.route('/users/ollama-installer', methods=['GET'])
def get_ollama_installer_info():
    """Get Ollama installer information and performance profiles.
    
    Returns download links and installation instructions.
    """
    logger.info("Received request to get Ollama installer information")
    try:
        installer_info = UserService.get_ollama_installer_info()
        logger.info("Successfully retrieved Ollama installer information")
        return jsonify(installer_info), 200
    except Exception as e:
        logger.error("Error retrieving Ollama installer info: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to retrieve installer info: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/extract-fields', methods=['POST'])
def extract_fields_from_workflow_documents(order_id):
    """Extract template fields from all documents in a workflow using AI
    
    Request body should contain:
    {
        "template_id": int,
        "user_model_preference": "optional_model_name"
    }
    """
    logger.info("Received request to extract fields from workflow documents: %d", order_id)
    try:
        # Get request data
        data = request.get_json() or {}
        template_id = data.get('template_id')
        user_model = data.get('user_model_preference')
        
        if not template_id:
            return jsonify({'error': 'template_id is required'}), 400
        
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
        
        # Get template with placeholders
        template = Document.query.get(template_id)
        if not template:
            return jsonify({'error': f'Template with ID {template_id} not found'}), 404
        
        if not template.placeholders:
            return jsonify({
                'extracted_values': {},
                'message': 'No placeholders defined in template',
                'confidence': 1.0
            }), 200
        
        # Get all workflow documents
        workflow_documents = Document.query.filter_by(work_order_id=order_id).all()
        
        if not workflow_documents:
            return jsonify({
                'extracted_values': {},
                'message': 'No documents found in this workflow',
                'confidence': 0.0
            }), 200
        
        # Import services
        from app.services.llm_service import ollama_service
        from app.services.document_service import DocumentService
        document_service = DocumentService()
        
        # Check if Ollama is available
        if not ollama_service.is_ollama_available():
            return jsonify({
                'error': 'Ollama is not available. Please ensure Ollama is installed and running.',
                'extracted_values': {},
                'confidence': 0.0
            }), 503
        
        # Extract text from all documents and combine
        combined_text = []
        processed_documents = []
        
        for doc in workflow_documents:
            try:
                if doc.file_path:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)
                    if os.path.exists(file_path):
                        text_content = document_service.extract_text_from_file(file_path)
                        if text_content.strip():
                            combined_text.append(f"--- Document: {doc.title} ---\n{text_content}")
                            processed_documents.append({
                                'id': doc.id,
                                'name': doc.title,
                                'text_length': len(text_content)
                            })
                        else:
                            logger.warning("No text content extracted from document %s", doc.title)
                    else:
                        logger.warning("Document file not found: %s", file_path)
            except Exception as e:
                logger.error("Error processing document %s: %s", doc.title, str(e))
                continue
        
        if not combined_text:
            return jsonify({
                'extracted_values': {},
                'message': 'No readable text content found in workflow documents',
                'confidence': 0.0
            }), 200
        
        # Extract placeholders using AI
        full_text = '\n\n'.join(combined_text)
        
        try:
            extraction_result = ollama_service.extract_placeholders_from_text(
                document_text=full_text,
                placeholders=template.placeholders,
                model=user_model
            )
            
            # Add metadata
            extraction_result['processed_documents'] = processed_documents
            extraction_result['total_text_length'] = len(full_text)
            extraction_result['workflow_id'] = order_id
            extraction_result['template_id'] = template_id
            
            logger.info("Successfully extracted fields from %d documents for workflow %d", 
                       len(processed_documents), order_id)
            
            return jsonify(extraction_result), 200
            
        except Exception as e:
            logger.error("Error during AI extraction: %s", str(e), exc_info=True)
            return jsonify({
                'error': f'AI extraction failed: {str(e)}',
                'extracted_values': {},
                'confidence': 0.0
            }), 500
        
    except Exception as e:
        logger.error("Error extracting fields from workflow documents %d: %s", order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to extract fields: {str(e)}'}), 500

@api_bp.route('/work-orders/<int:order_id>/documents-summary', methods=['GET'])
def get_workflow_documents_summary(order_id):
    """Get AI-powered summary of all documents in a workflow"""
    logger.info("Received request to get documents summary for workflow: %d", order_id)
    try:
        # Check if work order exists
        work_order = WorkOrder.query.get_or_404(order_id)
        
        # Get all workflow documents
        workflow_documents = Document.query.filter_by(work_order_id=order_id).all()
        
        if not workflow_documents:
            return jsonify({
                'summary': 'Keine Dokumente in diesem Workflow vorhanden.',
                'document_count': 0,
                'confidence': 1.0
            }), 200
        
        # Import services
        from app.services.llm_service import ollama_service
        from app.services.document_service import DocumentService
        document_service = DocumentService()
        
        # Check if Ollama is available
        if not ollama_service.is_ollama_available():
            return jsonify({
                'summary': 'KI-Service nicht verfügbar. Manuelle Überprüfung der Dokumente erforderlich.',
                'document_count': len(workflow_documents),
                'confidence': 0.0,
                'error': 'Ollama not available'
            }), 200
        
        # Extract text from all documents
        document_summaries = []
        
        for doc in workflow_documents:
            try:
                if doc.file_path:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)
                    if os.path.exists(file_path):
                        text_content = document_service.extract_text_from_file(file_path)
                        if text_content.strip():
                            # Get individual document summary
                            summary_result = ollama_service.summarize_document_content(
                                document_text=text_content,
                                max_summary_length=200
                            )
                            
                            document_summaries.append({
                                'name': doc.title,
                                'summary': summary_result.get('summary', 'Keine Zusammenfassung verfügbar'),
                                'word_count': summary_result.get('word_count', 0)
                            })
            except Exception as e:
                logger.error("Error summarizing document %s: %s", doc.title, str(e))
                document_summaries.append({
                    'name': doc.title,
                    'summary': 'Fehler beim Verarbeiten des Dokuments',
                    'word_count': 0
                })
        
        # Create combined summary
        if document_summaries:
            combined_summary = f"Workflow enthält {len(document_summaries)} Dokument(e):\n\n"
            for doc_sum in document_summaries:
                combined_summary += f"• {doc_sum['name']}: {doc_sum['summary']}\n"
        else:
            combined_summary = "Keine verarbeitbaren Dokumente gefunden."
        
        return jsonify({
            'summary': combined_summary,
            'document_count': len(workflow_documents),
            'processed_count': len(document_summaries),
            'document_summaries': document_summaries,
            'confidence': 0.8 if document_summaries else 0.0
        }), 200
        
    except Exception as e:
        logger.error("Error getting workflow documents summary %d: %s", order_id, str(e), exc_info=True)
        return jsonify({'error': f'Failed to get documents summary: {str(e)}'}), 500

@api_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user.
    
    Request body should contain user data.
    """
    logger.info("Received request to create new user")
    try:
        user_data = request.get_json()
        if not user_data:
            logger.warning("No user data provided")
            return jsonify({'error': 'No user data provided'}), 400
            
        required_fields = ['email', 'name']
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            logger.warning("Missing required fields: %s", missing_fields)
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Check if user already exists
        existing_user = UserService.get_user_by_email(user_data['email'])
        if existing_user:
            logger.warning("User with email %s already exists", user_data['email'])
            return jsonify({'error': 'User with this email already exists'}), 409
        
        user = UserService.create_user(
            email=user_data['email'],
            name=user_data['name'],
            role=user_data.get('role', 'user'),
            language=user_data.get('language', 'de')
        )
        
        logger.info("Successfully created user with ID: %d", user.id)
        return jsonify(user.to_dict()), 201
    except ValueError as e:
        logger.error("Value error when creating user: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error("Exception when creating user: %s", str(e), exc_info=True)
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

# AI Agent Routes
@api_bp.route('/ai-agent/process-documents', methods=['POST'])
def ai_agent_process_documents():
    """
    AI Agent: Intelligent document processing
    
    Multipart form data with:
    - documents: List of files to process
    - user_preferences: JSON string with user preferences (optional)
    """
    logger.info("Received request for AI agent document processing")
    try:
        # Import AI agent service
        from app.services.agent_service import ai_agent_service
        
        # Check if files are present
        uploaded_files = request.files.getlist('documents')
        if not uploaded_files:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Get user preferences if provided
        user_preferences = {}
        if 'user_preferences' in request.form:
            try:
                user_preferences = json.loads(request.form['user_preferences'])
            except json.JSONDecodeError:
                logger.warning("Invalid user_preferences JSON, using defaults")
        
        # Process documents intelligently
        result = ai_agent_service.process_documents_intelligently(
            uploaded_files=uploaded_files,
            user_preferences=user_preferences
        )
        
        if result['success']:
            logger.info("AI agent successfully processed %d documents", len(uploaded_files))
            return jsonify(result), 200
        else:
            logger.error("AI agent processing failed: %s", result.get('error', 'Unknown error'))
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in AI agent document processing: %s", str(e), exc_info=True)
        return jsonify({'error': f'AI agent processing failed: {str(e)}'}), 500

@api_bp.route('/ai-agent/create-workflow', methods=['POST'])
def ai_agent_create_workflow():
    """
    AI Agent: Create intelligent workflow with document processing
    
    Multipart form data with:
    - documents: List of files to process
    - workflow_name: Name for the workflow
    - workflow_description: Description (optional)
    - user_preferences: JSON string with user preferences (optional)
    """
    logger.info("Received request for AI agent workflow creation")
    try:
        # Import AI agent service
        from app.services.agent_service import ai_agent_service
        
        # Check if files are present
        uploaded_files = request.files.getlist('documents')
        if not uploaded_files:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Get workflow parameters
        workflow_name = request.form.get('workflow_name')
        if not workflow_name:
            return jsonify({'error': 'workflow_name is required'}), 400
        
        workflow_description = request.form.get('workflow_description', '')
        
        # Get user preferences if provided
        user_preferences = {}
        if 'user_preferences' in request.form:
            try:
                user_preferences = json.loads(request.form['user_preferences'])
            except json.JSONDecodeError:
                logger.warning("Invalid user_preferences JSON, using defaults")
        
        # Create intelligent workflow
        result = ai_agent_service.create_intelligent_workflow(
            uploaded_files=uploaded_files,
            workflow_name=workflow_name,
            workflow_description=workflow_description,
            user_preferences=user_preferences
        )
        
        if result['success']:
            logger.info("AI agent successfully created workflow: %s", workflow_name)
            return jsonify(result), 201
        else:
            logger.error("AI agent workflow creation failed: %s", result.get('error', 'Unknown error'))
            return jsonify(result), 400
            
    except Exception as e:
        logger.error("Error in AI agent workflow creation: %s", str(e), exc_info=True)
        return jsonify({'error': f'AI agent workflow creation failed: {str(e)}'}), 500

@api_bp.route('/ai-agent/analyze-client-match', methods=['POST'])
def ai_agent_analyze_client_match():
    """
    AI Agent: Analyze documents and find matching clients
    
    Multipart form data with:
    - documents: List of files to analyze
    """
    logger.info("Received request for AI agent client matching")
    try:
        # Import AI agent service
        from app.services.agent_service import ai_agent_service
        
        # Check if files are present
        uploaded_files = request.files.getlist('documents')
        if not uploaded_files:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Extract text from documents
        extraction_result = ai_agent_service._extract_and_analyze_documents(uploaded_files)
        if not extraction_result['success']:
            return jsonify(extraction_result), 400
        
        # Analyze and match clients
        client_matching_result = ai_agent_service._analyze_and_match_clients(
            extraction_result['combined_text'],
            extraction_result['document_summaries']
        )
        
        logger.info("AI agent completed client matching analysis")
        return jsonify({
            'success': True,
            'document_analysis': extraction_result,
            'client_matching': client_matching_result
        }), 200
        
    except Exception as e:
        logger.error("Error in AI agent client matching: %s", str(e), exc_info=True)
        return jsonify({'error': f'AI agent client matching failed: {str(e)}'}), 500

@api_bp.route('/ai-agent/suggest-template', methods=['POST'])
def ai_agent_suggest_template():
    """
    AI Agent: Suggest optimal template based on document content
    
    Multipart form data with:
    - documents: List of files to analyze
    """
    logger.info("Received request for AI agent template suggestion")
    try:
        # Import AI agent service
        from app.services.agent_service import ai_agent_service
        
        # Check if files are present
        uploaded_files = request.files.getlist('documents')
        if not uploaded_files:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Extract text from documents
        extraction_result = ai_agent_service._extract_and_analyze_documents(uploaded_files)
        if not extraction_result['success']:
            return jsonify(extraction_result), 400
        
        # Get document type hints (simplified client analysis)
        document_type_hints = []
        if ai_agent_service.ollama_service.is_ollama_available():
            try:
                client_info = ai_agent_service._extract_client_information(extraction_result['combined_text'])
                document_type_hints = client_info.get('document_type_hints', [])
            except Exception as e:
                logger.warning("Could not extract document type hints: %s", str(e))
        
        # Select optimal template
        template_selection_result = ai_agent_service._select_optimal_template(
            extraction_result['combined_text'],
            document_type_hints
        )
        
        logger.info("AI agent completed template suggestion")
        return jsonify({
            'success': True,
            'document_analysis': extraction_result,
            'template_suggestion': template_selection_result,
            'document_type_hints': document_type_hints
        }), 200
        
    except Exception as e:
        logger.error("Error in AI agent template suggestion: %s", str(e), exc_info=True)
        return jsonify({'error': f'AI agent template suggestion failed: {str(e)}'}), 500

@api_bp.route('/ai-agent/extract-all-fields', methods=['POST'])
def ai_agent_extract_all_fields():
    """
    AI Agent: Extract both client and template fields from documents
    
    Multipart form data with:
    - documents: List of files to analyze
    - template_id: ID of template to use for field extraction
    - user_preferences: JSON string with user preferences (optional)
    """
    logger.info("Received request for AI agent field extraction")
    try:
        # Import AI agent service
        from app.services.agent_service import ai_agent_service
        
        # Check if files are present
        uploaded_files = request.files.getlist('documents')
        if not uploaded_files:
            return jsonify({'error': 'No documents provided'}), 400
        
        # Get template ID
        template_id = request.form.get('template_id', type=int)
        if not template_id:
            return jsonify({'error': 'template_id is required'}), 400
        
        # Get template
        template = Document.query.get(template_id)
        if not template:
            return jsonify({'error': f'Template with ID {template_id} not found'}), 404
        
        # Get user preferences if provided
        user_preferences = {}
        if 'user_preferences' in request.form:
            try:
                user_preferences = json.loads(request.form['user_preferences'])
            except json.JSONDecodeError:
                logger.warning("Invalid user_preferences JSON, using defaults")
        
        # Extract text from documents
        extraction_result = ai_agent_service._extract_and_analyze_documents(uploaded_files)
        if not extraction_result['success']:
            return jsonify(extraction_result), 400
        
        # Extract client information and match
        client_matching_result = ai_agent_service._analyze_and_match_clients(
            extraction_result['combined_text'],
            extraction_result['document_summaries']
        )
        
        # Extract template fields
        field_extraction_result = ai_agent_service._extract_template_fields(
            extraction_result['combined_text'],
            template,
            user_preferences
        )
        
        # Combine all field values
        all_fields = {
            **client_matching_result.get('client_fields', {}),
            **field_extraction_result.get('extracted_values', {})
        }
        
        logger.info("AI agent completed comprehensive field extraction")
        return jsonify({
            'success': True,
            'document_analysis': extraction_result,
            'client_matching': client_matching_result,
            'field_extraction': field_extraction_result,
            'all_fields': all_fields,
            'template': {
                'id': template.id,
                'name': template.title,
                'placeholder_count': len(template.placeholders) if template.placeholders else 0
            }
        }), 200
        
    except Exception as e:
        logger.error("Error in AI agent field extraction: %s", str(e), exc_info=True)
        return jsonify({'error': f'AI agent field extraction failed: {str(e)}'}), 500