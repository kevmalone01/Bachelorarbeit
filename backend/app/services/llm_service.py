import requests
import json
import os
import re
from typing import Dict, Any, List, Optional
from flask import current_app

class OllamaService:
    """Service for interacting with Ollama LLM API"""
    
    def __init__(self, base_url: str = None):
        """Initialize the Ollama service with configuration
        
        Args:
            base_url: Base URL for Ollama API. If None, will use environment variable or default.
        """
        self.base_url = None  # Will be set when used within application context
        
    def _clean_thinking_tags(self, text: str) -> str:
        """Remove <think>...</think> tags from LLM responses and return only the content after them
        
        Args:
            text: Raw text response from LLM
            
        Returns:
            Cleaned text with thinking tags removed
        """
        if not text:
            return text
            
        # Remove <think>...</think> blocks and everything before the last closing tag
        think_pattern = r'<think>.*?</think>\s*'
        
        # Find all thinking blocks
        matches = list(re.finditer(think_pattern, text, re.DOTALL | re.IGNORECASE))
        
        if matches:
            # Get the position after the last thinking block
            last_match = matches[-1]
            # Return everything after the last thinking block
            cleaned_text = text[last_match.end():].strip()
            return cleaned_text if cleaned_text else text
        
        return text
        
    def _get_base_url(self) -> str:
        """Get the base URL for Ollama API, using application config if available"""
        if not self.base_url:
            try:
                return current_app.config.get('OLLAMA_API_BASE', 'http://localhost:11434')
            except RuntimeError:
                # Not in application context, use environment variable
                return os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        return self.base_url
        
    def _get_default_model(self) -> str:
        """Get the default model from application config if available"""
        try:
            return current_app.config.get('DEFAULT_LLM_MODEL', 'qwen3:0.6b')
        except RuntimeError:
            # Not in application context, use environment variable
            return os.getenv("DEFAULT_LLM_MODEL", "qwen3:0.6b")
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama is installed and running
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self._get_base_url()}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            current_app.logger.debug(f"Ollama not available: {str(e)}")
            return False
    
    def get_ollama_status(self) -> Dict[str, Any]:
        """Get comprehensive Ollama status information
        
        Returns:
            Dictionary with installation status, version, and available models
        """
        status = {
            'installed': False,
            'version': None,
            'models': [],
            'error': None
        }
        
        try:
            # Check if Ollama is available
            response = requests.get(f"{self._get_base_url()}/api/tags", timeout=5)
            if response.status_code == 200:
                status['installed'] = True
                status['models'] = response.json().get("models", [])
                
                # Try to get version information
                try:
                    version_response = requests.get(f"{self._get_base_url()}/api/version", timeout=3)
                    if version_response.status_code == 200:
                        status['version'] = version_response.json().get('version', 'unknown')
                except Exception:
                    pass  # Version endpoint might not be available in all versions
                    
            else:
                status['error'] = f"Ollama responded with status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            status['error'] = "Cannot connect to Ollama. Please ensure Ollama is installed and running."
        except requests.exceptions.Timeout:
            status['error'] = "Timeout connecting to Ollama."
        except Exception as e:
            status['error'] = f"Error checking Ollama status: {str(e)}"
            
        return status
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(f"{self._get_base_url()}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                current_app.logger.error(f"Failed to get models: {response.text}")
                return []
        except Exception as e:
            current_app.logger.error(f"Error fetching models: {str(e)}")
            return []
    
    def categorize_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize available models into text and image models
        
        Returns:
            Dictionary with 'text' and 'image' keys containing respective model lists
        """
        models = self.get_models()
        categorized = {
            'text': [],
            'image': []
        }
        
        # Known image/vision models
        image_model_keywords = ['llava', 'vision', 'clip', 'bakllava', 'moondream', 'vl', 'qwen2.5vl']
        
        for model in models:
            model_name = model.get('name', '').lower()
            
            # Check if it's an image model
            is_image_model = any(keyword in model_name for keyword in image_model_keywords)
            
            if is_image_model:
                categorized['image'].append(model)
            else:
                categorized['text'].append(model)
        
        return categorized
    
    def get_recommended_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get recommended models for different performance levels
        
        Returns:
            Dictionary with performance levels and their recommended models
        """
        return {
            'low': [
                {'name': 'qwen3:0.6b', 'type': 'text', 'description': 'Fast and efficient text processing'},
                {'name': 'qwen2.5vl:3b', 'type': 'image', 'description': 'Compact vision-language model'}
            ],
            'medium': [
                {'name': 'qwen3:0.6b', 'type': 'text', 'description': 'Excellent balance of speed and quality'},
                {'name': 'qwen2.5vl:3b', 'type': 'image', 'description': 'Advanced image analysis and description'}
            ],
            'high': [
                {'name': 'qwen3:0.6b', 'type': 'text', 'description': 'Optimized for production use'},
                {'name': 'qwen2.5vl:3b', 'type': 'image', 'description': 'Best vision-language understanding'}
            ]
        }

    def generate_completion(
        self,
        prompt: str,
        model: str = None,  
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate text completion using Ollama API
        
        Args:
            prompt: The user prompt to generate completion for
            model: Model name to use (default: from config)
            system_prompt: Optional system prompt to set context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            API response containing generated text and metadata
        """
        url = f"{self._get_base_url()}/api/generate"
        
        if model is None:
            model = self._get_default_model()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                if stream:
                    return response  # Return the response object for streaming
                response_data = response.json()
                # Clean thinking tags from the response
                if "response" in response_data:
                    response_data["response"] = self._clean_thinking_tags(response_data["response"])
                return response_data
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                current_app.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Failed to communicate with Ollama: {str(e)}"
            current_app.logger.error(error_msg)
            return {"error": error_msg}
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = 'qwen3:0.6b',
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate chat completion using Ollama API
        
        Args:
            messages: List of message dictionaries with role and content
            model: Model name to use (default: from config)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            API response containing generated chat completion
        """
        url = f"{self._get_base_url()}/api/chat"
        
        if model is None:
            model = self._get_default_model()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
            
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                if stream:
                    return response  # Return the response object for streaming
                response_data = response.json()
                # Clean thinking tags from the response
                if "message" in response_data and "content" in response_data["message"]:
                    response_data["message"]["content"] = self._clean_thinking_tags(response_data["message"]["content"])
                return response_data
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                current_app.logger.error(error_msg)
                return {"error": error_msg}
            
                
        except Exception as e:
            error_msg = f"Failed to communicate with Ollama: {str(e)}"
            current_app.logger.error(error_msg)
            return {"error": error_msg}
        
    def extract_placeholders(self, document: str, placeholders: List[str]) -> Dict[str, Any]:
        """Extract placeholders from a document using Ollama API
        
        Args:
            document: The document to extract placeholders from
            placeholders: List of placeholder names to extract
            
        """
            
        prompt = """
            Extract placeholders: {placeholders} from the following document:
            {document}.
            Return the placeholders with their values in a json format {{...}}.
        """
        
        response_text = self.generate_completion(prompt.format(placeholders=placeholders, document=document), model="qwen3:0.6b").get("response")
        return self._clean_thinking_tags(response_text) if response_text else response_text
        
    def extract_placeholders_from_text(
        self, 
        document_text: str, 
        placeholders: List[Dict[str, Any]], 
        model: str = 'qwen3:0.6b'
    ) -> Dict[str, Any]:
        """Extract template placeholders from document text using AI
        
        Args:
            document_text: The text content of the document
            placeholders: List of placeholder definitions with name, type, required fields
            model: Model name to use (default: from config)
            
        Returns:
            Dictionary containing extracted values and metadata
        """
        if not document_text or not placeholders:
            return {"extracted_values": {}, "confidence": 0.0, "errors": []}
        
        # Filter out client fields - we only extract non-client data
        non_client_placeholders = [
            p for p in placeholders 
            if not p.get('isClientField', False)
        ]
        
        if not non_client_placeholders:
            return {
                "extracted_values": {}, 
                "confidence": 1.0, 
                "message": "No non-client fields to extract"
            }
        
        # Build extraction prompt
        system_prompt = """You are an expert document analyst specializing in extracting specific information from legal and business documents. Your task is to identify and extract only the requested information with high accuracy."""
        
        # Build field descriptions
        field_descriptions = []
        for placeholder in non_client_placeholders:
            field_desc = f"- {placeholder['name']} ({placeholder.get('type', 'text')})"
            if placeholder.get('required'):
                field_desc += " [REQUIRED]"
            if placeholder.get('description'):
                field_desc += f": {placeholder['description']}"
            field_descriptions.append(field_desc)
        
        user_prompt = f"""
Analyze the following document and extract ONLY the requested information. 
Return the results in valid JSON format.

FIELDS TO EXTRACT:
{chr(10).join(field_descriptions)}

DOCUMENT TEXT:
{document_text[:4000]}  # Limit text to avoid token limits

INSTRUCTIONS:
1. Extract only the specific fields listed above
2. Do NOT extract client/customer information (names, addresses, contact details)
3. Return values in the correct data type (string, number, date, boolean)
4. Use null for missing or unclear information
5. For dates, use YYYY-MM-DD format
6. Be conservative - only extract information you are confident about

Return ONLY a JSON object in this format:
{{
  "extracted_values": {{
    "field_name": "extracted_value",
    ...
  }},
  "confidence": 0.85,
  "notes": "Any relevant observations"
}}
"""
        
        try:
            response = self.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=1000
            )
            
            if "error" in response:
                return {
                    "extracted_values": {},
                    "confidence": 0.0,
                    "errors": [response["error"]]
                }
            
            # Parse the AI response
            ai_text = response.get("response", "").strip()
            # Clean thinking tags from AI response
            ai_text = self._clean_thinking_tags(ai_text)
            
            # Try to extract JSON from the response
            import re
            import json
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    
                    # Validate and clean the extracted values
                    cleaned_values = self._validate_extracted_values(
                        result.get("extracted_values", {}),
                        non_client_placeholders
                    )
                    
                    return {
                        "extracted_values": cleaned_values,
                        "confidence": result.get("confidence", 0.5),
                        "notes": result.get("notes", ""),
                        "ai_model": model or self._get_default_model()
                    }
                    
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Failed to parse AI JSON response: {str(e)}")
                    current_app.logger.debug(f"AI response was: {ai_text}")
                    
            return {
                "extracted_values": {},
                "confidence": 0.0,
                "errors": ["Could not parse AI response into valid JSON"],
                "raw_response": ai_text
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in placeholder extraction: {str(e)}")
            return {
                "extracted_values": {},
                "confidence": 0.0,
                "errors": [f"Extraction failed: {str(e)}"]
            }
    
    def _validate_extracted_values(
        self, 
        extracted_values: Dict[str, Any], 
        placeholders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate and clean extracted values according to placeholder definitions
        
        Args:
            extracted_values: Raw extracted values from AI
            placeholders: Placeholder definitions for validation
            
        Returns:
            Cleaned and validated values
        """
        cleaned_values = {}
        placeholder_map = {p['name']: p for p in placeholders}
        
        for field_name, value in extracted_values.items():
            if field_name not in placeholder_map:
                continue  # Skip unknown fields
                
            placeholder = placeholder_map[field_name]
            field_type = placeholder.get('type', 'text')
            
            if value is None or value == "":
                continue  # Skip empty values
                
            try:
                # Type conversion and validation
                if field_type == 'number':
                    if isinstance(value, str):
                        # Try to extract number from string
                        import re
                        number_match = re.search(r'-?\d+\.?\d*', str(value))
                        if number_match:
                            value = float(number_match.group()) if '.' in number_match.group() else int(number_match.group())
                        else:
                            continue
                    cleaned_values[field_name] = float(value) if isinstance(value, (int, float)) else None
                    
                elif field_type == 'date':
                    if isinstance(value, str):
                        # Try to normalize date format
                        import re
                        from datetime import datetime
                        
                        # Look for date patterns
                        date_patterns = [
                            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                            r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY
                            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # D.M.YYYY
                            r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, value)
                            if match:
                                try:
                                    if pattern == date_patterns[0]:  # YYYY-MM-DD
                                        cleaned_values[field_name] = match.group(1)
                                    elif pattern in [date_patterns[1], date_patterns[2]]:  # DD.MM.YYYY
                                        day, month, year = match.groups()
                                        cleaned_values[field_name] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    elif pattern == date_patterns[3]:  # MM/DD/YYYY
                                        month, day, year = match.groups()
                                        cleaned_values[field_name] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    break
                                except ValueError:
                                    continue
                                    
                elif field_type == 'checkbox':
                    if isinstance(value, str):
                        value = value.lower() in ['true', '1', 'yes', 'ja', 'wahr']
                    cleaned_values[field_name] = bool(value)
                    
                elif field_type == 'select':
                    # Validate against options if available
                    options = placeholder.get('options', [])
                    if options and value not in options:
                        # Try fuzzy matching
                        value_lower = str(value).lower()
                        for option in options:
                            if value_lower in option.lower() or option.lower() in value_lower:
                                value = option
                                break
                    cleaned_values[field_name] = str(value)
                    
                else:  # text and other types
                    cleaned_values[field_name] = str(value).strip()
                    
            except Exception as e:
                current_app.logger.warning(f"Failed to validate field {field_name}: {str(e)}")
                continue
                
        return cleaned_values

    def summarize_document_content(
        self, 
        document_text: str, 
        max_summary_length: int = 500,
        model: str = None
    ) -> Dict[str, Any]:
        """Generate a summary of document content
        
        Args:
            document_text: The text content to summarize
            max_summary_length: Maximum length of summary
            model: Model name to use
            
        Returns:
            Dictionary with summary and metadata
        """
        if not document_text:
            return {"summary": "", "word_count": 0, "confidence": 0.0}
        
        system_prompt = """You are an expert document analyst. Create concise, professional summaries of business and legal documents."""
        
        user_prompt = f"""
Summarize the following document in German. Focus on:
1. Document type and purpose
2. Key dates and deadlines  
3. Important amounts or numbers
4. Main legal or business obligations
5. Critical information for processing

Keep the summary under {max_summary_length} characters and use professional language.

DOCUMENT:
{document_text[:3000]}

SUMMARY:
"""
        
        try:
            response = self.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            if "error" in response:
                return {"summary": "", "error": response["error"], "confidence": 0.0}
            
            summary = response.get("response", "").strip()
            # Clean thinking tags from AI response
            summary = self._clean_thinking_tags(summary)
            
            return {
                "summary": summary[:max_summary_length],
                "word_count": len(document_text.split()),
                "confidence": 0.8 if len(summary) > 50 else 0.4,
                "ai_model": model or self._get_default_model()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating summary: {str(e)}")
            return {"summary": "", "error": str(e), "confidence": 0.0}

# Singleton instance
ollama_service = OllamaService()

if __name__ == "__main__":
    print(ollama_service.extract_placeholders("Die Firma Muster GmbH wird vertreten von Max Mustermann. Die Frist für den Bericht endet am 31.12.2025.", ['Firma', 'Ansprechpartner', 'Frist']))