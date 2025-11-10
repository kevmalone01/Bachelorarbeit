import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from flask import current_app
from app.models import Client, Document, WorkOrder
from app.services.llm_service import ollama_service
from app.services.document_service import document_service
from app import db
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AIAgentService:
    """
    AI Agent that automatically processes documents:
    1. Analyzes document content
    2. Extracts client information
    3. Matches with existing clients
    4. Selects optimal template
    5. Extracts remaining fields
    6. Generates final PDF document
    """
    
    def __init__(self):
        self.ollama_service = ollama_service
        self.document_service = document_service
        
    def process_documents_intelligently(
        self, 
        uploaded_files: List[Any], 
        work_order_id: Optional[int] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for intelligent document processing
        
        Args:
            uploaded_files: List of uploaded file objects
            work_order_id: Optional work order ID to associate documents with
            user_preferences: Optional user preferences for models, etc.
            
        Returns:
            Processing result with generated document and metadata
        """
        logger.info("Starting intelligent document processing for %d files", len(uploaded_files))
        
        try:
            # Step 1: Extract and analyze text from all documents
            extraction_result = self._extract_and_analyze_documents(uploaded_files)
            if not extraction_result['success']:
                return extraction_result
            
            # Step 2: Extract client information and match with existing clients
            client_matching_result = self._analyze_and_match_clients(
                extraction_result['combined_text'],
                extraction_result['document_summaries']
            )
            
            # Step 3: Select optimal template based on document content
            template_selection_result = self._select_optimal_template(
                extraction_result['combined_text'],
                client_matching_result.get('document_type_hints', [])
            )
            
            # Step 4: Extract non-client fields using selected template
            selected_template_dict = template_selection_result['selected_template']
            if selected_template_dict:
                # Get the actual Document object for template operations
                template_obj = Document.query.get(selected_template_dict['id'])
                
                field_extraction_result = self._extract_template_fields(
                    extraction_result['combined_text'],
                    template_obj,
                    user_preferences
                )
                
                # Step 5: Generate final PDF document
                document_generation_result = self._generate_final_document(
                    template_obj,
                    {
                        **client_matching_result.get('client_fields', {}),
                        **field_extraction_result.get('extracted_values', {})
                    }
                )
            else:
                field_extraction_result = {
                    'extracted_values': {},
                    'confidence': 0.0,
                    'error': 'No template selected'
                }
                document_generation_result = {
                    'success': False,
                    'error': 'No template available for document generation'
                }
            
            # Compile final result
            result = {
                'success': True,
                'client_match': client_matching_result,
                'template_selection': template_selection_result,
                'field_extraction': field_extraction_result,
                'document_generation': document_generation_result,
                'metadata': {
                    'processed_documents': extraction_result['document_summaries'],
                    'total_text_length': len(extraction_result['combined_text']),
                    'processing_time': datetime.utcnow().isoformat(),
                    'work_order_id': work_order_id
                }
            }
            
            logger.info("Successfully completed intelligent document processing")
            return result
            
        except Exception as e:
            logger.error("Error in intelligent document processing: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': f"Processing failed: {str(e)}",
                'step': 'initialization'
            }
    
    def _extract_and_analyze_documents(self, uploaded_files: List[Any]) -> Dict[str, Any]:
        """Extract text content from all uploaded documents"""
        logger.info("Extracting text from %d documents", len(uploaded_files))
        
        try:
            combined_text = []
            document_summaries = []
            
            for i, file in enumerate(uploaded_files):
                if not file or not file.filename:
                    continue
                    
                try:
                    # Extract text from file
                    text_content = self.document_service.extract_text_from_uploaded_file(file)
                    
                    if text_content and text_content.strip():
                        doc_summary = {
                            'filename': file.filename,
                            'text_length': len(text_content),
                            'content_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
                        }
                        
                        # Generate AI summary for the document
                        if self.ollama_service.is_ollama_available():
                            summary_result = self.ollama_service.summarize_document_content(
                                document_text=text_content,
                                max_summary_length=300
                            )
                            doc_summary['ai_summary'] = summary_result.get('summary', '')
                            doc_summary['confidence'] = summary_result.get('confidence', 0.0)
                        
                        combined_text.append(f"--- Dokument: {file.filename} ---\n{text_content}")
                        document_summaries.append(doc_summary)
                        
                        logger.debug("Extracted %d characters from %s", len(text_content), file.filename)
                    else:
                        logger.warning("No text content extracted from %s", file.filename)
                        
                except Exception as e:
                    logger.error("Error extracting text from %s: %s", file.filename, str(e))
                    continue
            
            if not combined_text:
                return {
                    'success': False,
                    'error': 'No readable text content found in any uploaded documents'
                }
            
            return {
                'success': True,
                'combined_text': '\n\n'.join(combined_text),
                'document_summaries': document_summaries
            }
            
        except Exception as e:
            logger.error("Error in document text extraction: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': f"Document extraction failed: {str(e)}"
            }
    
    def _analyze_and_match_clients(self, combined_text: str, document_summaries: List[Dict]) -> Dict[str, Any]:
        """Analyze documents to extract client information and match with existing clients"""
        logger.info("Analyzing client information and matching with database")
        
        try:
            if not self.ollama_service.is_ollama_available():
                logger.warning("Ollama not available for client analysis")
                return {
                    'client_match': None,
                    'confidence': 0.0,
                    'error': 'AI service not available'
                }
            
            # Extract client information using AI
            client_info = self._extract_client_information(combined_text)
            
            # Get all existing clients from database
            existing_clients = Client.query.all()
            
            if not existing_clients:
                logger.warning("No existing clients in database")
                return {
                    'client_match': None,
                    'client_info': client_info,
                    'confidence': 0.0,
                    'message': 'No existing clients found in database'
                }
            
            # Find best matching client
            best_match = self._find_best_client_match(client_info, existing_clients)
            
            # Extract client field values for form filling
            client_fields = self._extract_client_field_values(best_match['client']) if best_match['client'] else {}
            
            return {
                'client_match': best_match['client'].to_dict() if best_match['client'] else None,
                'match_confidence': best_match['confidence'],
                'match_reasons': best_match['reasons'],
                'extracted_client_info': client_info,
                'client_fields': client_fields,
                'document_type_hints': client_info.get('document_type_hints', [])
            }
            
        except Exception as e:
            logger.error("Error in client analysis and matching: %s", str(e), exc_info=True)
            return {
                'client_match': None,
                'confidence': 0.0,
                'error': f"Client matching failed: {str(e)}"
            }
    
    def _extract_client_information(self, text: str) -> Dict[str, Any]:
        """Extract client information from document text using AI"""
        logger.debug("Extracting client information from document text")
        
        system_prompt = """You are an expert at extracting client information from German legal and business documents. 
        Extract client/customer information with high accuracy."""
        
        user_prompt = f"""
Analyze the following document text and extract client/customer information.
Focus on identifying:

1. PERSON INFORMATION:
   - First name (Vorname)
   - Last name (Nachname) 
   - Full name (Vollständiger Name)
   - Title/Salutation (Anrede: Herr, Frau, Dr., etc.)
   - Birth date (Geburtsdatum)

2. COMPANY INFORMATION:
   - Company name (Firmenname)
   - Legal form (Rechtsform: GmbH, AG, KG, etc.)
   - Contact person (Ansprechpartner)

3. CONTACT INFORMATION:
   - Email address
   - Phone number (Telefonnummer)
   - Address (street, city, postal code)

4. IDENTIFICATION:
   - Tax number (Steuernummer)
   - VAT ID (Umsatzsteuer-ID)
   - Business registration number

5. DOCUMENT TYPE HINTS:
   - What type of document is this? (contract, invoice, tax form, etc.)
   - What legal area? (tax law, business law, etc.)

DOCUMENT TEXT:
{text[:4000]}

Return ONLY a JSON object with this structure:
{{
  "person_info": {{
    "first_name": "extracted_value_or_null",
    "last_name": "extracted_value_or_null", 
    "full_name": "extracted_value_or_null",
    "title": "extracted_value_or_null",
    "birth_date": "YYYY-MM-DD_or_null"
  }},
  "company_info": {{
    "company_name": "extracted_value_or_null",
    "legal_form": "extracted_value_or_null",
    "contact_person": "extracted_value_or_null"
  }},
  "contact_info": {{
    "email": "extracted_value_or_null",
    "phone": "extracted_value_or_null",
    "street": "extracted_value_or_null",
    "city": "extracted_value_or_null",
    "postal_code": "extracted_value_or_null"
  }},
  "identification": {{
    "tax_number": "extracted_value_or_null",
    "vat_id": "extracted_value_or_null",
    "business_reg_number": "extracted_value_or_null"
  }},
  "document_type_hints": ["type1", "type2"],
  "confidence": 0.85
}}
"""
        
        try:
            response = self.ollama_service.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=800
            )
            
            if "error" in response:
                logger.error("AI client extraction error: %s", response["error"])
                return {}
            
            ai_text = response.get("response", "").strip()
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse AI client extraction JSON: %s", str(e))
                    
            return {}
            
        except Exception as e:
            logger.error("Error in AI client information extraction: %s", str(e))
            return {}
    
    def _find_best_client_match(self, client_info: Dict[str, Any], existing_clients: List[Client]) -> Dict[str, Any]:
        """Find the best matching client from existing database entries"""
        logger.debug("Finding best client match among %d existing clients", len(existing_clients))
        
        best_match = {'client': None, 'confidence': 0.0, 'reasons': []}
        
        try:
            for client in existing_clients:
                match_score = 0.0
                reasons = []
                
                # Extract info from AI analysis
                person_info = client_info.get('person_info', {})
                company_info = client_info.get('company_info', {})
                contact_info = client_info.get('contact_info', {})
                identification = client_info.get('identification', {})
                
                # Exact matches (high score)
                if identification.get('tax_number') and client.tax_number:
                    if identification['tax_number'].lower() in client.tax_number.lower():
                        match_score += 0.4
                        reasons.append(f"Tax number match: {identification['tax_number']}")
                
                if contact_info.get('email') and client.email:
                    if contact_info['email'].lower() == client.email.lower():
                        match_score += 0.3
                        reasons.append(f"Email exact match: {contact_info['email']}")
                
                # Name matching for persons
                if client.client_type == 'person' and (person_info.get('first_name') or person_info.get('last_name')):
                    name_score = 0.0
                    if person_info.get('first_name') and client.first_name:
                        if person_info['first_name'].lower() in client.first_name.lower():
                            name_score += 0.15
                            reasons.append(f"First name match: {person_info['first_name']}")
                    
                    if person_info.get('last_name') and client.last_name:
                        if person_info['last_name'].lower() in client.last_name.lower():
                            name_score += 0.15
                            reasons.append(f"Last name match: {person_info['last_name']}")
                    
                    match_score += name_score
                
                # Company name matching
                if client.client_type == 'company' and company_info.get('company_name') and client.company_name:
                    if company_info['company_name'].lower() in client.company_name.lower():
                        match_score += 0.25
                        reasons.append(f"Company name match: {company_info['company_name']}")
                
                # Phone number matching (partial)
                if contact_info.get('phone') and client.contact_phone:
                    # Extract digits only for comparison
                    extracted_digits = re.sub(r'\D', '', contact_info['phone'])
                    client_digits = re.sub(r'\D', '', client.contact_phone)
                    if len(extracted_digits) >= 6 and extracted_digits in client_digits:
                        match_score += 0.1
                        reasons.append(f"Phone number match")
                
                # Address matching (city, postal code)
                if contact_info.get('city') and client.address_city:
                    if contact_info['city'].lower() in client.address_city.lower():
                        match_score += 0.05
                        reasons.append(f"City match: {contact_info['city']}")
                
                if contact_info.get('postal_code') and client.address_zip:
                    if contact_info['postal_code'] == client.address_zip:
                        match_score += 0.05
                        reasons.append(f"Postal code match: {contact_info['postal_code']}")
                
                # Update best match if this client has higher score
                if match_score > best_match['confidence']:
                    best_match = {
                        'client': client,
                        'confidence': match_score,
                        'reasons': reasons
                    }
            
            logger.info("Best client match found with confidence: %.2f", best_match['confidence'])
            return best_match
            
        except Exception as e:
            logger.error("Error finding best client match: %s", str(e))
            return {'client': None, 'confidence': 0.0, 'reasons': []}
    
    def _extract_client_field_values(self, client: Client) -> Dict[str, Any]:
        """Extract client field values for template filling"""
        logger.debug("Extracting client field values for client ID: %d", client.id)
        
        try:
            client_fields = {}
            
            # Person fields
            if client.client_type == 'person':
                if client.first_name:
                    client_fields['client_first_name'] = client.first_name
                    client_fields['client_vorname'] = client.first_name
                if client.last_name:
                    client_fields['client_last_name'] = client.last_name
                    client_fields['client_nachname'] = client.last_name
                if client.first_name and client.last_name:
                    client_fields['client_full_name'] = f"{client.first_name} {client.last_name}"
                    client_fields['client_name'] = f"{client.first_name} {client.last_name}"
                if client.birth_date:
                    client_fields['client_birth_date'] = client.birth_date.strftime('%Y-%m-%d')
                    client_fields['client_geburtsdatum'] = client.birth_date.strftime('%d.%m.%Y')
            
            # Company fields
            elif client.client_type == 'company':
                if client.company_name:
                    client_fields['client_company_name'] = client.company_name
                    client_fields['client_name'] = client.company_name
                    client_fields['client_firma'] = client.company_name
                if client.contact_last_name:
                    client_fields['client_contact_person'] = client.contact_last_name
                    client_fields['client_ansprechpartner'] = client.contact_last_name
            
            # Common fields
            if client.email:
                client_fields['client_email'] = client.email
            if client.contact_phone:
                client_fields['client_phone'] = client.contact_phone
                client_fields['client_telefon'] = client.contact_phone
            if client.tax_number:
                client_fields['client_tax_number'] = client.tax_number
                client_fields['client_steuernummer'] = client.tax_number
            
            # Address fields
            address_parts = []
            if client.address_street:
                client_fields['client_street'] = client.address_street
                client_fields['client_strasse'] = client.address_street
                address_parts.append(client.address_street)
            if client.address_zip:
                client_fields['client_postal_code'] = client.address_zip
                client_fields['client_plz'] = client.address_zip
                address_parts.append(client.address_zip)
            if client.address_city:
                client_fields['client_city'] = client.address_city
                client_fields['client_stadt'] = client.address_city
                address_parts.append(client.address_city)
            
            if address_parts:
                client_fields['client_address'] = ', '.join(address_parts)
                client_fields['client_adresse'] = ', '.join(address_parts)
            
            logger.debug("Extracted %d client field values", len(client_fields))
            return client_fields
            
        except Exception as e:
            logger.error("Error extracting client field values: %s", str(e))
            return {}
    
    def _select_optimal_template(self, combined_text: str, document_type_hints: List[str]) -> Dict[str, Any]:
        """Select the most suitable template based on document content"""
        logger.info("Selecting optimal template based on document analysis")
        
        try:
            # Get all available templates
            templates = Document.query.filter(Document.placeholders.isnot(None)).all()
            
            if not templates:
                logger.warning("No templates found in database")
                return {
                    'selected_template': None,
                    'confidence': 0.0,
                    'error': 'No templates available'
                }
            
            if len(templates) == 1:
                logger.info("Only one template available, selecting it")
                template_dict = {
                    'id': templates[0].id,
                    'title': templates[0].title,
                    'content': templates[0].content,
                    'document_type': templates[0].document_type,
                    'placeholders': templates[0].placeholders or []
                }
                return {
                    'selected_template': template_dict,
                    'confidence': 1.0,
                    'selection_reason': 'Only template available'
                }
            
            # Use AI to select best template if Ollama is available
            if self.ollama_service.is_ollama_available():
                ai_selection = self._ai_template_selection(combined_text, templates, document_type_hints)
                if ai_selection['selected_template']:
                    return ai_selection
            
            # Fallback: simple template selection based on placeholder count
            logger.info("Using fallback template selection based on placeholder count")
            best_template = max(templates, key=lambda t: len(t.placeholders) if t.placeholders else 0)
            
            template_dict = {
                'id': best_template.id,
                'title': best_template.title,
                'content': best_template.content,
                'document_type': best_template.document_type,
                'placeholders': best_template.placeholders or []
            }
            
            return {
                'selected_template': template_dict,
                'confidence': 0.5,
                'selection_reason': 'Fallback: template with most placeholders'
            }
            
        except Exception as e:
            logger.error("Error in template selection: %s", str(e), exc_info=True)
            template_dict = None
            try:
                # Try to get templates again for fallback
                fallback_templates = Document.query.filter(Document.placeholders.isnot(None)).all()
                if fallback_templates:
                    template_dict = {
                        'id': fallback_templates[0].id,
                        'title': fallback_templates[0].title,
                        'content': fallback_templates[0].content,
                        'document_type': fallback_templates[0].document_type,
                        'placeholders': fallback_templates[0].placeholders or []
                    }
            except Exception as fallback_error:
                logger.error("Fallback template query also failed: %s", str(fallback_error))
            
            return {
                'selected_template': template_dict,
                'confidence': 0.1,
                'error': f"Template selection failed: {str(e)}"
            }
    
    def _ai_template_selection(self, text: str, templates: List[Document], document_type_hints: List[str]) -> Dict[str, Any]:
        """Use AI to select the best template based on document content"""
        logger.debug("Using AI for template selection among %d templates", len(templates))
        
        try:
            # Build template descriptions for AI
            template_descriptions = []
            for i, template in enumerate(templates):
                placeholders = template.placeholders or []
                placeholder_names = [p.get('name', '') for p in placeholders if p.get('name')]
                
                template_desc = {
                    'index': i,
                    'name': template.title or f'Template {template.id}',
                    'description': template.content or 'Keine Beschreibung',
                    'placeholder_count': len(placeholders),
                    'key_fields': placeholder_names[:10]  # First 10 fields
                }
                template_descriptions.append(template_desc)
            
            system_prompt = """You are an expert at matching documents with appropriate templates for legal and business document generation."""
            
            user_prompt = f"""
Analyze the following document content and select the most appropriate template.

DOCUMENT TYPE HINTS: {', '.join(document_type_hints) if document_type_hints else 'None detected'}

AVAILABLE TEMPLATES:
{json.dumps(template_descriptions, indent=2, ensure_ascii=False)}

DOCUMENT CONTENT (first 2000 chars):
{text[:2000]}

Select the template that best matches the document content and purpose.
Consider:
1. Document type and legal area
2. Required fields and placeholders
3. Template description relevance
4. Field names that appear in the document

Return ONLY a JSON object:
{{
  "selected_template_index": 0,
  "confidence": 0.85,
  "reasoning": "Why this template was selected",
  "matching_fields": ["field1", "field2"]
}}
"""
            
            response = self.ollama_service.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=300
            )
            
            if "error" in response:
                logger.error("AI template selection error: %s", response["error"])
                return {'selected_template': None, 'confidence': 0.0}
            
            ai_text = response.get("response", "").strip()
            
            # Parse AI response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                try:
                    ai_result = json.loads(json_match.group())
                    template_index = ai_result.get('selected_template_index', 0)
                    
                    if 0 <= template_index < len(templates):
                        selected_template = templates[template_index]
                        template_dict = {
                            'id': selected_template.id,
                            'title': selected_template.title,
                            'content': selected_template.content,
                            'document_type': selected_template.document_type,
                            'placeholders': selected_template.placeholders or []
                        }
                        return {
                            'selected_template': template_dict,
                            'confidence': ai_result.get('confidence', 0.5),
                            'selection_reason': ai_result.get('reasoning', 'AI selection'),
                            'matching_fields': ai_result.get('matching_fields', [])
                        }
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse AI template selection: %s", str(e))
            
            return {'selected_template': None, 'confidence': 0.0}
            
        except Exception as e:
            logger.error("Error in AI template selection: %s", str(e))
            return {'selected_template': None, 'confidence': 0.0}
    
    def _extract_template_fields(
        self, 
        text: str, 
        template: Document, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract non-client fields from text using the selected template"""
        logger.info("Extracting template fields for template: %s", template.title if template else 'None')
        
        if not template or not template.placeholders:
            return {
                'extracted_values': {},
                'confidence': 0.0,
                'message': 'No template or placeholders available'
            }
        
        try:
            # Use existing placeholder extraction service
            model = user_preferences.get('preferred_text_model') if user_preferences else None
            
            result = self.ollama_service.extract_placeholders_from_text(
                document_text=text,
                placeholders=template.placeholders,
                model=model
            )
            
            logger.info("Extracted %d template fields", len(result.get('extracted_values', {})))
            return result
            
        except Exception as e:
            logger.error("Error extracting template fields: %s", str(e), exc_info=True)
            return {
                'extracted_values': {},
                'confidence': 0.0,
                'error': f"Field extraction failed: {str(e)}"
            }
    
    def _generate_final_document(self, template: Document, field_values: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final PDF document with all extracted values"""
        logger.info("Generating final document from template: %s", template.title if template else 'None')
        
        if not template:
            return {
                'success': False,
                'error': 'No template provided for document generation'
            }
        
        try:
            # Generate document preview/PDF using existing service
            preview_data = self.document_service.create_document_preview(
                template.id, 
                field_values
            )
            
            logger.info("Successfully generated final document")
            return {
                'success': True,
                'preview_data': preview_data,
                'field_count': len(field_values),
                'template_name': template.title
            }
            
        except Exception as e:
            logger.error("Error generating final document: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': f"Document generation failed: {str(e)}"
            }
    
    def create_intelligent_workflow(
        self, 
        uploaded_files: List[Any], 
        workflow_name: str,
        workflow_description: str = "",
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete workflow with intelligent document processing
        
        Args:
            uploaded_files: List of uploaded files
            workflow_name: Name for the workflow
            workflow_description: Description for the workflow
            user_preferences: User preferences and settings
            
        Returns:
            Complete workflow result with work order, processed documents, and generated PDF
        """
        logger.info("Creating intelligent workflow: %s", workflow_name)
        
        try:
            # Step 1: Process documents intelligently
            processing_result = self.process_documents_intelligently(
                uploaded_files=uploaded_files,
                user_preferences=user_preferences
            )
            
            if not processing_result['success']:
                return processing_result
            
            # Step 2: Create work order with matched client
            client_match = processing_result['client_match']['client_match']
            
            if not client_match:
                return {
                    'success': False,
                    'error': 'No matching client found. Please create a client first.',
                    'processing_result': processing_result
                }
            
            # Get first available tax advisor
            from app.models import TaxAdvisor
            tax_advisor = TaxAdvisor.query.first()
            if not tax_advisor:
                return {
                    'success': False,
                    'error': 'No tax advisor available'
                }
            
            # Create work order
            work_order = WorkOrder(
                title=workflow_name,
                description=workflow_description,
                status='completed',  # Mark as completed since we're generating the final document
                priority='medium',
                client_id=client_match['id'],
                tax_advisor_id=tax_advisor.id,
                template_id=processing_result['template_selection']['selected_template']['id']
            )
            
            db.session.add(work_order)
            db.session.flush()  # Get work order ID
            
            # Step 3: Save uploaded documents to workflow
            saved_documents = []
            for file in uploaded_files:
                if file and file.filename:
                    try:
                        # Convert and save document
                        pdf_file_path, pdf_filename = self.document_service.convert_file_to_pdf(
                            file, file.filename, getattr(file, 'content_type', 'application/octet-stream')
                        )
                        
                        document = Document(
                            title=pdf_filename,
                            document_type='application/pdf',
                            status='processed',
                            file_path=os.path.relpath(pdf_file_path, current_app.config['UPLOAD_FOLDER']),
                            client_id=client_match['id'],
                            tax_advisor_id=tax_advisor.id,
                            work_order_id=work_order.id
                        )
                        
                        db.session.add(document)
                        saved_documents.append(document)
                        
                    except Exception as e:
                        logger.error("Error saving document %s: %s", file.filename, str(e))
                        continue
            
            db.session.commit()
            
            logger.info("Successfully created intelligent workflow with ID: %d", work_order.id)
            
            return {
                'success': True,
                'work_order': {
                    'id': work_order.id,
                    'title': work_order.title,
                    'status': work_order.status,
                    'client_id': work_order.client_id,
                    'template_id': work_order.template_id
                },
                'processing_result': processing_result,
                'saved_documents': len(saved_documents),
                'message': f'Intelligent workflow created successfully with {len(saved_documents)} documents'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating intelligent workflow: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': f"Workflow creation failed: {str(e)}"
            }

# Singleton instance
ai_agent_service = AIAgentService() 