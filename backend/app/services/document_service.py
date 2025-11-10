import os
import tempfile
import logging
import platform
import subprocess
import shutil
from typing import Dict, Any, List, Optional, BinaryIO, Tuple
import base64

import docx2pdf

from flask import current_app

from werkzeug.utils import secure_filename

from app.db import db
from app.models.document import Document
from app.models.placeholder import Placeholder

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document operations including preview and processing"""
    
    def __init__(self):
        self.allowed_extensions = {'pdf', 'docx', 'doc'}
        self.allowed_mime_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/x-msword',
            'application/octet-stream',
            'application/msword; charset=binary',
            'application/vnd.ms-word',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document; charset=binary'
        }
        self.upload_folder = None
        logger.info("DocumentService initialized with allowed extensions: %s", self.allowed_extensions)
        logger.info("DocumentService initialized with allowed MIME types: %s", self.allowed_mime_types)    
    
    def _get_upload_folder(self) -> str:
        """Get upload folder from app config or default"""
        if not self.upload_folder:
            try:
                folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                logger.debug("Upload folder from config: %s", folder)
                return folder
            except RuntimeError:
                folder = os.getenv("UPLOAD_FOLDER", "uploads")
                logger.debug("Upload folder from environment: %s", folder)
                return folder
        logger.debug("Using cached upload folder: %s", self.upload_folder)
        return self.upload_folder
    
    def _allowed_file(self, filename: str, content_type: str = None) -> bool:
        """Check if file extension and MIME type are allowed"""
        # Check file extension
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        extension_allowed = extension in self.allowed_extensions
        
        # Log initial validation info
        logger.info("Validating file: %s (type: %s)", filename, content_type)
        logger.debug("File extension: %s, Allowed extensions: %s", extension, self.allowed_extensions)
        
        # Für DOCX: Immer erlauben, wenn die Endung stimmt
        if extension == 'docx':
            logger.info("DOCX-Datei erkannt, Endung stimmt. Upload wird erlaubt.")
            return True
        
        # Für PDF und DOC: Extension und MIME-Type prüfen
        mime_type_allowed = True
        if content_type:
            normalized_content_type = content_type.lower().split(';')[0].strip()
            mime_type_allowed = any(
                allowed_type.lower().split(';')[0].strip() == normalized_content_type
                for allowed_type in self.allowed_mime_types
            )
            logger.debug("Normalized content type: %s", normalized_content_type)
            logger.debug("Allowed MIME types: %s", self.allowed_mime_types)
        
        is_allowed = extension_allowed or mime_type_allowed
        
        if not is_allowed:
            logger.warning("File validation failed:")
            logger.warning("- Filename: %s", filename)
            logger.warning("- Content type: %s", content_type)
            logger.warning("- Extension: %s", extension)
            logger.warning("- Extension allowed: %s", extension_allowed)
            logger.warning("- MIME type allowed: %s", mime_type_allowed)
            logger.warning("- Allowed extensions: %s", self.allowed_extensions)
            logger.warning("- Allowed MIME types: %s", self.allowed_mime_types)
            raise ValueError(f"Nur PDF und DOCX Dateien werden unterstützt. Ihre Datei hat die Endung '{extension}' und den MIME-Type '{content_type}'.")
        else:
            logger.info("File validation successful")
            logger.debug("- Extension allowed: %s", extension_allowed)
            logger.debug("- MIME type allowed: %s", mime_type_allowed)
        
        return is_allowed
    
    def save_document(self, file: BinaryIO, filename: str, content_type: str = None) -> str:
        """Save uploaded document and return the path"""
        logger.info("Saving document: %s (type: %s)", filename, content_type)
        
        # If content type is not provided, try to determine it from the filename
        if not content_type:
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if extension == 'docx':
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif extension == 'pdf':
                content_type = 'application/pdf'
            logger.info("Determined content type from extension: %s", content_type)
        
        if not self._allowed_file(filename, content_type):
            logger.error("File type not allowed for file: %s (type: %s)", filename, content_type)
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}")
        
        upload_folder = self._get_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)
        logger.debug("Created upload folder: %s", upload_folder)
        
        secure_name = secure_filename(filename)
        file_path = os.path.join(upload_folder, secure_name)
        logger.debug("Saving file to: %s", file_path)
        
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        logger.info("Successfully saved document to: %s", file_path)
        return file_path
    
    def create_document_preview(self, document_id: int, placeholder_values: Dict[str, Any]) -> Dict[str, Any]:
        """Create a preview of a document with placeholders filled in
        
        Args:
            document_id: ID of the document template
            placeholder_values: Dictionary of placeholder values keyed by placeholder name
            
        Returns:
            Dictionary with preview info including base64 data and mime type
        """
        logger.info("Creating document preview for document ID: %d", document_id)
        logger.debug("Placeholder values: %s", placeholder_values)
        
        document = Document.query.get(document_id)
        if not document:
            logger.error("Document with ID %d not found", document_id)
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Get associated placeholders from the document's placeholders JSON field
        placeholders = document.placeholders or []
        logger.debug("Found %d placeholders for document", len(placeholders))
        
        # Validate required placeholders are provided
        missing_required = []
        for placeholder in placeholders:
            if placeholder.get('required', False) and placeholder.get('name') not in placeholder_values:
                missing_required.append(placeholder.get('name'))
        
        if missing_required:
            logger.error("Missing required placeholders: %s", ", ".join(missing_required))
            raise ValueError(f"Missing required placeholders: {', '.join(missing_required)}")
        
        # Process document based on type
        if document.document_type == 'application/pdf':
            logger.info("Processing PDF document: %s", document.title)
            return self._process_pdf_preview(document, placeholder_values)
        elif document.document_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            logger.info("Processing DOCX document: %s", document.title)
            return self._process_docx_preview(document, placeholder_values)
        else:
            logger.error("Unsupported document type: %s", document.document_type)
            raise ValueError(f"Unsupported document type: {document.document_type}")
    
    def _process_pdf_preview(self, document: Document, placeholder_values: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF document with placeholders
        
        Note: This is a simplified implementation. In a real-world scenario,
        you might use libraries like PyPDF2, pdfrw, or ReportLab to modify PDFs.
        """
        try:
            logger.debug("Processing PDF preview for document: %s", document.title)
            # In a real implementation, you would manipulate the PDF here
            # For now, we'll just read the original file
            with open(document.file_path, 'rb') as f:
                file_data = f.read()
            
            # Return base64 encoded data
            base64_data = base64.b64encode(file_data).decode('utf-8')
            logger.info("Successfully created PDF preview for: %s", document.title)
            return {
                'preview_data': base64_data,
                'mime_type': 'application/pdf',
                'filename': f"{document.title}_preview.pdf"
            }
        except Exception as e:
            logger.error("Error processing PDF preview: %s", str(e), exc_info=True)
            current_app.logger.error(f"Error processing PDF preview: {str(e)}")
            raise Exception(f"Failed to create PDF preview: {str(e)}")
    
    def _convert_with_docx2pdf(self, docx_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Convert DOCX to PDF using docx2pdf library
        
        Args:
            docx_path: Path to the DOCX file
            output_path: Path where the PDF should be saved
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            from docx2pdf import convert
            
            logger.debug("Converting DOCX to PDF using docx2pdf library")
            output_dir = os.path.dirname(output_path)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Initialize COM for Windows if needed
            if platform.system() == 'Windows':
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    logger.debug("COM initialized for Windows")
                except Exception as com_error:
                    logger.warning("Failed to initialize COM: %s", str(com_error))
            
            # Convert the document
            convert(docx_path, output_path)
            
            # Check if the conversion was successful
            if os.path.exists(output_path):
                logger.info("Successfully converted DOCX to PDF using docx2pdf")
                return True, ""
            else:
                logger.error("docx2pdf did not create output file at: %s", output_path)
                return False, "PDF file not created by docx2pdf"
                
        except Exception as e:
            logger.error("Error using docx2pdf for conversion: %s", str(e), exc_info=True)
            return False, str(e)
        finally:
            # Uninitialize COM if we're on Windows
            if platform.system() == 'Windows':
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                    logger.debug("COM uninitialized for Windows")
                except Exception:
                    pass
    
    def _convert_with_pypdf_docx2pdf(self, docx_path: str) -> Tuple[bool, str, str]:
        """
        Convert DOCX to PDF using pypdf-docx2pdf library
        
        Args:
            docx_path: Path to the DOCX file
            
        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        # Check if pypdf-docx2pdf is installed
        try:
            import importlib.util
            spec = importlib.util.find_spec('pypdf_docx2pdf')
            if spec is None:
                logger.info("pypdf-docx2pdf module is not installed, skipping this conversion method")
                return False, "", "Module pypdf-docx2pdf is not installed"
        except ImportError:
            logger.info("Unable to check for pypdf-docx2pdf module, skipping this conversion method")
            return False, "", "Unable to check for pypdf-docx2pdf module"
            
        # Module is available, try to use it
        try:
            from pypdf_docx2pdf import convert as pdf_convert
            
            pdf_path = os.path.splitext(docx_path)[0] + '.pdf'
            logger.debug("Converting DOCX to PDF using pypdf-docx2pdf library")
            
            # Convert the document
            pdf_convert(docx_path, pdf_path)
            
            # Check if the conversion was successful
            if os.path.exists(pdf_path):
                logger.info("Successfully converted DOCX to PDF using pypdf-docx2pdf")
                return True, pdf_path, ""
            else:
                logger.error("pypdf-docx2pdf did not create output file at: %s", pdf_path)
                return False, "", "PDF file not created by pypdf-docx2pdf"
                
        except Exception as e:
            logger.error("Error using pypdf-docx2pdf for conversion: %s", str(e), exc_info=True)
            return False, "", str(e)
    
    def _try_convert_docx_to_pdf(self, docx_path: str) -> Tuple[bool, str, str]:
        """
        Try to convert DOCX to PDF using available methods
        
        Args:
            docx_path: Path to the DOCX file
            
        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        docx_dir = os.path.dirname(docx_path)
        pdf_path = os.path.splitext(docx_path)[0] + '.pdf'
        
        # Try using docx2pdf library first
        try:
            success, error_msg = self._convert_with_docx2pdf(docx_path, pdf_path)
            if success:
                return True, pdf_path, ""
            logger.warning("docx2pdf conversion failed: %s. Trying next method.", error_msg)
        except Exception as e:
            logger.warning("docx2pdf conversion error: %s. Trying next method.", str(e))
        
        # Try using pypdf-docx2pdf as a second option
        try:
            success, pypdf_path, error_msg = self._convert_with_pypdf_docx2pdf(docx_path)
            if success:
                return True, pypdf_path, ""
            logger.warning("pypdf-docx2pdf conversion failed: %s. Trying next method.", error_msg)
        except Exception as e:
            logger.warning("pypdf-docx2pdf conversion error: %s. Trying next method.", str(e))
            
        # If all conversion methods fail, return a failure result
        # This will cause the system to fall back to showing the DOCX file directly
        logger.info("All PDF conversion methods failed, falling back to DOCX format")
        return False, "", "All PDF conversion methods failed"
    
    def _process_docx_preview(self, document: Document, placeholder_values: Dict[str, Any]) -> Dict[str, Any]:
        """Process DOCX document with placeholders
        
        First replaces placeholders in the document, then converts to PDF
        """
        try:
            import docx
            from docx.shared import Pt
            
            logger.debug("Processing DOCX preview for document: %s", document.title)
            
            # Open the template document
            logger.debug("Opening template document: %s", document.file_path)
            doc = docx.Document(document.file_path)
            
            # Replace placeholders in all paragraphs
            placeholder_replacements = 0
            for paragraph in doc.paragraphs:
                for key, value in placeholder_values.items():
                    placeholder = '{{' + key + '}}'
                    if placeholder in paragraph.text:
                        logger.debug("Replacing placeholder '%s' in paragraph", key)
                        paragraph.text = paragraph.text.replace(placeholder, str(value))
                        placeholder_replacements += 1
            
            # Replace placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in placeholder_values.items():
                            placeholder = '{{' + key + '}}'
                            if placeholder in cell.text:
                                logger.debug("Replacing placeholder '%s' in table cell", key)
                                cell.text = cell.text.replace(placeholder, str(value))
                                placeholder_replacements += 1
            
            logger.info("Replaced %d placeholders in document", placeholder_replacements)
            
            # Save to temporary file with placeholders replaced
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
                doc.save(tmp_docx.name)
                tmp_docx_path = tmp_docx.name
                logger.debug("Saved document with replacements to temp file: %s", tmp_docx_path)
            
            # Convert DOCX to PDF 
            success, pdf_path, error_msg = self._try_convert_docx_to_pdf(tmp_docx_path)
            
            if success:
                # PDF conversion succeeded, read the file
                logger.debug("PDF created at: %s", pdf_path)
                
                try:
                    with open(pdf_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Clean up temporary files
                    os.unlink(tmp_docx_path)
                    os.unlink(pdf_path)
                    logger.debug("Temporary files cleaned up")
                    
                    # Return base64 encoded PDF data
                    base64_data = base64.b64encode(file_data).decode('utf-8')
                    logger.info("Successfully created PDF preview from DOCX for: %s", document.title)
                    return {
                        'preview_data': base64_data,
                        'mime_type': 'application/pdf',
                        'filename': f"{document.title}_preview.pdf"
                    }
                except Exception as e:
                    logger.error("Error reading created PDF file: %s", str(e))
                    # Continue to fallback
            
            # If we got here, either conversion failed or reading the PDF failed
            # Fall back to returning the DOCX
            logger.warning("PDF conversion failed or unavailable: %s. Falling back to DOCX format", error_msg)
            
            # Read the DOCX file
            with open(tmp_docx_path, 'rb') as f:
                file_data = f.read()
            
            # Clean up temporary file
            os.unlink(tmp_docx_path)
            logger.debug("Temporary DOCX file cleaned up")
            
            # Return base64 encoded DOCX data
            base64_data = base64.b64encode(file_data).decode('utf-8')
            logger.info("Successfully created DOCX preview as fallback for: %s", document.title)
            return {
                'preview_data': base64_data,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'filename': f"{document.title}_preview.docx"
            }
                
        except Exception as e:
            logger.error("Error processing DOCX preview: %s", str(e), exc_info=True)
            current_app.logger.error(f"Error processing DOCX preview: {str(e)}")
            raise Exception(f"Failed to create DOCX preview: {str(e)}")
    
    def save_document_with_placeholders(self, file_data: Dict[str, Any], placeholders: List[Dict[str, Any]]) -> Document:
        """Save a document template with its placeholders
        
        Args:
            file_data: Dictionary with file information (name, description, file_path, etc.)
            placeholders: List of placeholder dictionaries
            
        Returns:
            The created Document object
        """
        try:
            logger.info("Saving document with placeholders: %s", file_data.get('name'))
            logger.debug("Document data: %s", file_data)
            logger.debug("Placeholders count: %d", len(placeholders))
            
            # Create document without requiring client and tax advisor
            document = Document(
                title=file_data.get('name'),  # Map name to title
                content=file_data.get('description', ''),
                document_type=file_data.get('file_type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),  # Use file_type as document_type
                status='active',
                file_path=file_data.get('file_path'),
                client_id=None,  # No default client required
                tax_advisor_id=None,  # No default tax advisor required
                placeholders=placeholders  # Store placeholders directly in JSON field
            )
            db.session.add(document)
            
            # We don't need to create separate Placeholder records anymore
            # as we're storing the placeholder data directly in the Document's JSON field
            
            db.session.commit()
            logger.info("Successfully saved document with ID %d and %d placeholders", document.id, len(placeholders))
            return document
        except Exception as e:
            logger.error("Failed to save document with placeholders: %s", str(e), exc_info=True)
            db.session.rollback()
            raise Exception(f"Failed to save document with placeholders: {str(e)}")

    def create_preview_from_uploaded_file(self, file: BinaryIO, placeholder_values: Dict[str, Any]) -> Dict[str, Any]:
        """Create a preview from an uploaded file without saving to database
        
        Args:
            file: The uploaded file object (BytesIO or similar)
            placeholder_values: Dictionary of placeholder values keyed by placeholder name
            
        Returns:
            Dictionary with preview info including base64 data and mime type
        """
        try:
            filename = getattr(file, 'filename', 'document')
            logger.info("Creating preview from uploaded file: %s", filename)
            logger.debug("Placeholder values count: %d", len(placeholder_values))
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.seek(0)  # Reset file pointer to beginning
                tmp.write(file.read())
                tmp_path = tmp.name
                logger.debug("Saved to temporary file: %s", tmp_path)
            
            # Determine file type
            content_type = None
            
            if filename.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.lower().endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                logger.error("Unsupported file type: %s", filename)
                os.unlink(tmp_path)
                raise ValueError("Unsupported file type")
            
            logger.debug("Determined content type: %s", content_type)
            
            # Process based on file type
            if content_type == 'application/pdf':
                logger.info("Processing temporary PDF file")
                result = self._process_temp_pdf_preview(tmp_path, placeholder_values, filename)
            elif content_type.endswith('document'):
                logger.info("Processing temporary DOCX file")
                result = self._process_temp_docx_preview(tmp_path, placeholder_values, filename)
            else:
                logger.error("Unsupported content type: %s", content_type)
                raise ValueError(f"Unsupported content type: {content_type}")
                
            # Clean up temporary file
            os.unlink(tmp_path)
            logger.debug("Temporary file cleaned up")
            
            logger.info("Successfully created preview for uploaded file: %s", filename)
            return result
        except Exception as e:
            logger.error("Error processing temporary file preview: %s", str(e), exc_info=True)
            current_app.logger.error(f"Error processing temporary file preview: {str(e)}")
            raise Exception(f"Failed to create preview: {str(e)}")
    
    def _process_temp_pdf_preview(self, file_path: str, placeholder_values: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Process a temporary PDF file for preview
        
        Note: In a real implementation, you would use PDF manipulation libraries here
        """
        try:
            logger.debug("Processing temporary PDF preview: %s", file_path)
            # In a real implementation, you would manipulate the PDF with placeholders here
            # For now, we'll just read the file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Return base64 encoded data
            base64_data = base64.b64encode(file_data).decode('utf-8')
            logger.info("Successfully created PDF preview from temporary file")
            return {
                'preview_data': base64_data,
                'mime_type': 'application/pdf',
                'filename': f"{os.path.splitext(filename)[0]}_preview.pdf"
            }
        except Exception as e:
            logger.error("Failed to process temporary PDF preview: %s", str(e), exc_info=True)
            raise Exception(f"Failed to process PDF preview: {str(e)}")
    
    def _process_temp_docx_preview(self, file_path: str, placeholder_values: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Process a temporary DOCX file for preview with placeholders
        
        First replaces placeholders in the document, then converts to PDF
        """
        try:
            import docx
            
            logger.debug("Processing temporary DOCX preview: %s", file_path)
            
            # Open the template document
            logger.debug("Opening DOCX file")
            doc = docx.Document(file_path)
            
            # Replace placeholders in all paragraphs
            placeholder_replacements = 0
            for paragraph in doc.paragraphs:
                for key, value in placeholder_values.items():
                    placeholder = '{{' + key + '}}'
                    if placeholder in paragraph.text:
                        logger.debug("Replacing placeholder '%s' with value '%s'", key, value)
                        paragraph.text = paragraph.text.replace(placeholder, str(value))
                        placeholder_replacements += 1
            
            # Replace placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in placeholder_values.items():
                            placeholder = '{{' + key + '}}'
                            if placeholder in cell.text:
                                logger.debug("Replacing placeholder '%s' in table cell", key)
                                cell.text = cell.text.replace(placeholder, str(value))
                                placeholder_replacements += 1
            
            logger.info("Replaced %d placeholders in temporary DOCX", placeholder_replacements)
            
            # Save to temporary file with placeholders replaced
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
                doc.save(tmp_docx.name)
                tmp_docx_path = tmp_docx.name
                logger.debug("Saved processed DOCX to temp file: %s", tmp_docx_path)
            
            # Convert DOCX to PDF
            success, pdf_path, error_msg = self._try_convert_docx_to_pdf(tmp_docx_path)
            
            if success:
                # PDF conversion succeeded, read the file
                logger.debug("PDF created at: %s", pdf_path)
                
                try:
                    with open(pdf_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Clean up temporary files
                    os.unlink(tmp_docx_path)
                    os.unlink(pdf_path)
                    logger.debug("Temporary files cleaned up")
                    
                    # Return base64 encoded PDF data
                    base64_data = base64.b64encode(file_data).decode('utf-8')
                    logger.info("Successfully created PDF preview from temporary DOCX")
                    return {
                        'preview_data': base64_data,
                        'mime_type': 'application/pdf',
                        'filename': f"{os.path.splitext(filename)[0]}_preview.pdf"
                    }
                except Exception as e:
                    logger.error("Error reading created PDF file: %s", str(e))
                    # Continue to fallback
            
            # If we got here, either conversion failed or reading the PDF failed
            # Fall back to returning the DOCX
            logger.warning("PDF conversion failed or unavailable: %s. Falling back to DOCX format", error_msg)
            
            # Read the DOCX file
            with open(tmp_docx_path, 'rb') as f:
                file_data = f.read()
            
            # Clean up temporary file
            os.unlink(tmp_docx_path)
            logger.debug("Temporary DOCX file cleaned up")
            
            # Return base64 encoded DOCX data
            base64_data = base64.b64encode(file_data).decode('utf-8')
            logger.info("Successfully created DOCX preview as fallback from temporary file")
            return {
                'preview_data': base64_data,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'filename': f"{os.path.splitext(filename)[0]}_preview.docx"
            }
                
        except Exception as e:
            logger.error("Failed to process temporary DOCX preview: %s", str(e), exc_info=True)
            raise Exception(f"Failed to process DOCX preview: {str(e)}")

    def update_placeholder_name(self, document_id: int, old_name: str, new_name: str) -> bool:
        """Update a placeholder name in a document.
        
        This updates both the database record and the actual placeholders in the document file.
        
        Args:
            document_id: The ID of the document
            old_name: Current placeholder name
            new_name: New placeholder name
            
        Returns:
            Boolean indicating success
        """
        try:
            logger.info("Updating placeholder name from '%s' to '%s' in document %d", old_name, new_name, document_id)
            
            # 1. Find the document
            document = Document.query.get(document_id)
            if not document:
                logger.error("Document with ID %d not found", document_id)
                raise ValueError(f"Document with ID {document_id} not found")
                
            # 2. Update placeholder in document.placeholders JSON field
            placeholders = document.placeholders or []
            placeholder_updated = False
            
            for placeholder in placeholders:
                if placeholder.get('name') == old_name:
                    placeholder['name'] = new_name
                    placeholder_updated = True
                    logger.debug("Updated placeholder name in JSON from '%s' to '%s'", old_name, new_name)
                    
            if placeholder_updated:
                # Save the updated placeholders JSON
                document.placeholders = placeholders
                db.session.commit()
                logger.debug("Saved updated placeholders to database")
            else:
                # No placeholder in JSON, but we'll still update the document content
                logger.warning("No placeholder record found for '%s' in document %d JSON", old_name, document_id)
            
            # 3. Update the document file content based on its type
            if document.document_type.endswith('document'):  # DOCX file
                logger.info("Updating placeholder in DOCX document")
                self._update_placeholder_in_docx(document.file_path, old_name, new_name)
            elif document.document_type == 'application/pdf':
                logger.info("Updating placeholder in PDF document")
                # PDF editing is more complex and might require more specialized handling
                # For now, we'll just log this
                logger.warning("PDF placeholder update not fully implemented")
            
            logger.info("Successfully updated placeholder from '%s' to '%s' in document %d", 
                        old_name, new_name, document_id)
            return True
            
        except Exception as e:
            logger.error("Error updating placeholder name: %s", str(e), exc_info=True)
            db.session.rollback()
            raise Exception(f"Failed to update placeholder: {str(e)}")
    
    def _update_placeholder_in_docx(self, file_path: str, old_name: str, new_name: str) -> None:
        """Update placeholder names in a DOCX document.
        
        Args:
            file_path: Path to the DOCX file
            old_name: Current placeholder name
            new_name: New placeholder name
        """
        try:
            import docx
            
            logger.debug("Opening DOCX document at %s to update placeholders", file_path)
            doc = docx.Document(file_path)
            
            # Replace in paragraphs
            replacements = 0
            old_placeholder = '{{' + old_name + '}}'
            new_placeholder = '{{' + new_name + '}}'
            
            for paragraph in doc.paragraphs:
                if old_placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(old_placeholder, new_placeholder)
                    replacements += 1
            
            # Replace in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if old_placeholder in cell.text:
                            cell.text = cell.text.replace(old_placeholder, new_placeholder)
                            replacements += 1
            
            # Save the document if changes were made
            if replacements > 0:
                logger.info("Made %d placeholder replacements in document, saving changes", replacements)
                doc.save(file_path)
            else:
                logger.warning("No placeholders found to replace in document")
                
        except Exception as e:
            logger.error("Error updating placeholders in DOCX: %s", str(e), exc_info=True)
            raise Exception(f"Error updating DOCX placeholders: {str(e)}")

    def update_placeholder_in_temp_file(self, file: BinaryIO, old_name: str, new_name: str) -> Dict[str, Any]:
        """Update a placeholder name in a temporary document file.
        
        Args:
            file: The uploaded file object (BytesIO or similar)
            old_name: Current placeholder name
            new_name: New placeholder name
            
        Returns:
            Dictionary with updated file info including base64 data and mime type
        """
        try:
            filename = getattr(file, 'filename', 'document')
            logger.info("Updating placeholder from '%s' to '%s' in temporary file: %s", old_name, new_name, filename)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.seek(0)  # Reset file pointer to beginning
                tmp.write(file.read())
                tmp_path = tmp.name
                logger.debug("Saved to temporary file: %s", tmp_path)
            
            # Determine file type
            content_type = None
            
            if filename.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.lower().endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                logger.error("Unsupported file type: %s", filename)
                os.unlink(tmp_path)
                raise ValueError("Unsupported file type")
            
            logger.debug("Determined content type: %s", content_type)
            
            # Process based on file type
            if content_type.endswith('document'):  # DOCX file
                logger.info("Updating placeholder in DOCX file")
                # Create a new temporary file for the updated document
                updated_file_path = tmp_path + '_updated'
                
                # Copy the file first
                shutil.copy2(tmp_path, updated_file_path)
                
                # Update placeholder in the copy
                self._update_placeholder_in_docx(updated_file_path, old_name, new_name)
                
                # Read updated file
                with open(updated_file_path, 'rb') as f:
                    file_data = f.read()
                
                # Clean up temporary files
                os.unlink(tmp_path)
                os.unlink(updated_file_path)
                logger.debug("Temporary files cleaned up")
                
                # Return base64 encoded DOCX data
                base64_data = base64.b64encode(file_data).decode('utf-8')
                logger.info("Successfully updated placeholder in DOCX file")
                return {
                    'preview_data': base64_data,
                    'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'filename': filename
                }
            elif content_type == 'application/pdf':
                logger.info("PDF placeholder update not fully implemented")
                # For PDF files, we might need more complex handling
                # For now, return the original file
                with open(tmp_path, 'rb') as f:
                    file_data = f.read()
                
                # Clean up temporary file
                os.unlink(tmp_path)
                logger.debug("Temporary file cleaned up")
                
                # Return base64 encoded PDF data
                base64_data = base64.b64encode(file_data).decode('utf-8')
                logger.info("Returning original PDF (placeholder update not implemented)")
                return {
                    'preview_data': base64_data,
                    'mime_type': 'application/pdf',
                    'filename': filename
                }
            else:
                logger.error("Unsupported content type: %s", content_type)
                raise ValueError(f"Unsupported content type: {content_type}")
                
        except Exception as e:
            logger.error("Error updating placeholder in temporary file: %s", str(e), exc_info=True)
            raise Exception(f"Failed to update placeholder: {str(e)}")

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from a document file
        
        Args:
            file_path: Path to the document file
            
        Returns:
            String containing the text content of the document
        """
        try:
            logger.info("Extracting text from file: %s", file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error("File does not exist: %s", file_path)
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type by extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.docx':
                return self._extract_text_from_docx(file_path)
            elif file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            else:
                # Try to read as plain text
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    # Try with different encoding
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                        
        except Exception as e:
            logger.error("Error extracting text from file %s: %s", file_path, str(e), exc_info=True)
            raise Exception(f"Failed to extract text from file: {str(e)}")
    
    def extract_text_from_uploaded_file(self, file) -> str:
        """Extract text content from an uploaded file object
        
        Args:
            file: Uploaded file object (werkzeug FileStorage)
            
        Returns:
            String containing the text content of the document
        """
        logger.info("Extracting text from uploaded file: %s", getattr(file, 'filename', 'unknown'))
        
        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{getattr(file, 'filename', 'temp')}") as temp_file:
                # Reset file pointer to beginning
                file.seek(0)
                temp_file.write(file.read())
                temp_file_path = temp_file.name
                
            logger.debug("Saved uploaded file to temporary location: %s", temp_file_path)
            
            # Extract text from temporary file
            text_content = self.extract_text_from_file(temp_file_path)
            
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                logger.debug("Cleaned up temporary file: %s", temp_file_path)
            except OSError as e:
                logger.warning("Could not delete temporary file %s: %s", temp_file_path, str(e))
            
            return text_content
            
        except Exception as e:
            logger.error("Error extracting text from uploaded file %s: %s", 
                        getattr(file, 'filename', 'unknown'), str(e), exc_info=True)
            raise Exception(f"Failed to extract text from uploaded file: {str(e)}")
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file"""
        try:
            import docx
            
            logger.debug("Extracting text from DOCX file: %s", file_path)
            doc = docx.Document(file_path)
            
            text_content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(' | '.join(row_text))
            
            result = '\n'.join(text_content)
            logger.info("Successfully extracted %d characters from DOCX file", len(result))
            return result
            
        except Exception as e:
            logger.error("Error extracting text from DOCX: %s", str(e), exc_info=True)
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file"""
        try:
            # Try to use PyPDF2 if available
            try:
                import PyPDF2
                
                logger.debug("Extracting text from PDF using PyPDF2: %s", file_path)
                text_content = []
                
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                text_content.append(page_text)
                        except Exception as page_error:
                            logger.warning("Failed to extract text from page %d: %s", page_num, str(page_error))
                
                result = '\n'.join(text_content)
                logger.info("Successfully extracted %d characters from PDF file using PyPDF2", len(result))
                return result
                
            except ImportError:
                logger.warning("PyPDF2 not available, trying pdfplumber")
                
                # Try pdfplumber as fallback
                try:
                    import pdfplumber
                    
                    logger.debug("Extracting text from PDF using pdfplumber: %s", file_path)
                    text_content = []
                    
                    with pdfplumber.open(file_path) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            try:
                                page_text = page.extract_text()
                                if page_text and page_text.strip():
                                    text_content.append(page_text)
                            except Exception as page_error:
                                logger.warning("Failed to extract text from page %d: %s", page_num, str(page_error))
                    
                    result = '\n'.join(text_content)
                    logger.info("Successfully extracted %d characters from PDF file using pdfplumber", len(result))
                    return result
                    
                except ImportError:
                    logger.warning("Neither PyPDF2 nor pdfplumber available for PDF text extraction")
                    return "PDF-Textextraktion ist nicht verfügbar. Bitte installieren Sie PyPDF2 oder pdfplumber."
                    
        except Exception as e:
            logger.error("Error extracting text from PDF: %s", str(e), exc_info=True)
            return f"Fehler beim Extrahieren des Textes aus der PDF-Datei: {str(e)}"

    def convert_file_to_pdf(self, file: BinaryIO, filename: str, content_type: str = None) -> Tuple[str, str]:
        """Convert uploaded file to PDF format and return the PDF file path and filename
        
        Args:
            file: The uploaded file object
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Tuple of (pdf_file_path, pdf_filename)
        """
        logger.info("Converting file to PDF: %s (type: %s)", filename, content_type)
        
        # First validate the file
        if not self._allowed_file(filename, content_type):
            logger.error("File type not allowed for file: %s (type: %s)", filename, content_type)
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}")
        
        # Determine file type
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # If it's already a PDF, just save it
        if file_extension == 'pdf':
            logger.info("File is already PDF, saving directly")
            pdf_path = self.save_document(file, filename, content_type)
            return pdf_path, filename
        
        # If it's a DOCX file, convert to PDF
        elif file_extension == 'docx':
            logger.info("Converting DOCX file to PDF")
            
            # Save the original DOCX file temporarily
            upload_folder = self._get_upload_folder()
            os.makedirs(upload_folder, exist_ok=True)
            
            # Create temporary file for the original DOCX
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
                tmp_docx.write(file.read())
                tmp_docx_path = tmp_docx.name
                logger.debug("Saved temporary DOCX file: %s", tmp_docx_path)
            
            try:
                # Convert DOCX to PDF
                success, pdf_path, error_msg = self._try_convert_docx_to_pdf(tmp_docx_path)
                
                if not success:
                    logger.error("Failed to convert DOCX to PDF: %s", error_msg)
                    # Clean up temporary file
                    os.unlink(tmp_docx_path)
                    raise ValueError(f"Failed to convert DOCX to PDF: {error_msg}")
                
                # Create final PDF filename
                base_name = os.path.splitext(filename)[0]
                pdf_filename = f"{base_name}.pdf"
                
                # Create unique filename for storage
                from datetime import datetime
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
                unique_pdf_filename = f"{timestamp}_{pdf_filename}"
                
                # Move the converted PDF to the upload folder
                final_pdf_path = os.path.join(upload_folder, unique_pdf_filename)
                shutil.move(pdf_path, final_pdf_path)
                
                # Clean up temporary DOCX file
                os.unlink(tmp_docx_path)
                
                logger.info("Successfully converted DOCX to PDF: %s -> %s", filename, pdf_filename)
                return final_pdf_path, pdf_filename
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(tmp_docx_path):
                    os.unlink(tmp_docx_path)
                raise
        
        # For other file types (DOC), try to handle them
        elif file_extension == 'doc':
            logger.warning("DOC files are not fully supported for conversion. Consider converting to DOCX first.")
            # For now, just save the original file without conversion
            original_path = self.save_document(file, filename, content_type)
            return original_path, filename
        
        else:
            logger.error("Unsupported file type for conversion: %s", file_extension)
            raise ValueError(f"Unsupported file type for PDF conversion: {file_extension}")

# Singleton instance
document_service = DocumentService() 