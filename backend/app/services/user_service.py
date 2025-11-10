from typing import Dict, Any, Optional, List
from flask import current_app
from app.db import db
from app.models.user import User
from app.services.llm_service import ollama_service

class UserService:
    """Service for managing user data and preferences"""
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email
        
        Args:
            email: User email address
            
        Returns:
            User object or None if not found
        """
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def create_user(email: str, name: str, role: str = 'user', language: str = 'de') -> User:
        """Create a new user
        
        Args:
            email: User email address
            name: User full name
            role: User role (default: 'user')
            language: User language preference (default: 'de')
            
        Returns:
            Created User object
        """
        user = User(
            email=email,
            name=name,
            role=role,
            language=language
        )
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"Created new user: {email}")
        return user
    
    @staticmethod
    def update_user_settings(user_id: int, settings: Dict[str, Any]) -> Optional[User]:
        """Update user settings
        
        Args:
            user_id: User ID
            settings: Dictionary of settings to update
            
        Returns:
            Updated User object or None if user not found
        """
        user = User.query.get(user_id)
        if not user:
            return None
        
        user.update_preferences(**settings)
        db.session.commit()
        
        current_app.logger.info(f"Updated settings for user {user.email}")
        return user
    
    @staticmethod
    def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings
        
        Args:
            user_id: User ID
            
        Returns:
            User settings dictionary or None if user not found
        """
        user = User.query.get(user_id)
        if not user:
            return None
        
        return user.to_dict()
    
    @staticmethod
    def get_available_models() -> Dict[str, Any]:
        """Get available Ollama models and system status
        
        Returns:
            Dictionary containing Ollama status and available models
        """
        ollama_status = ollama_service.get_ollama_status()
        
        result = {
            'ollama_status': ollama_status,
            'available_models': {
                'text': [],
                'image': []
            },
            'recommended_models': ollama_service.get_recommended_models()
        }
        
        if ollama_status['installed']:
            categorized_models = ollama_service.categorize_models()
            result['available_models'] = categorized_models
        
        return result
    
    @staticmethod
    def validate_model_selection(text_model: str, image_model: str) -> Dict[str, Any]:
        """Validate user's model selection
        
        Args:
            text_model: Selected text model name
            image_model: Selected image model name
            
        Returns:
            Validation result with status and messages
        """
        result = {
            'valid': True,
            'messages': [],
            'warnings': []
        }
        
        # Check if Ollama is available
        if not ollama_service.is_ollama_available():
            result['valid'] = False
            result['messages'].append("Ollama ist nicht verfügbar. Bitte installieren Sie Ollama.")
            return result
        
        # Get available models
        categorized_models = ollama_service.categorize_models()
        available_text_models = [model['name'] for model in categorized_models['text']]
        available_image_models = [model['name'] for model in categorized_models['image']]
        
        # Validate text model
        if text_model and text_model not in available_text_models:
            result['warnings'].append(f"Textmodell '{text_model}' ist nicht installiert.")
        
        # Validate image model  
        if image_model and image_model not in available_image_models:
            result['warnings'].append(f"Bildmodell '{image_model}' ist nicht installiert.")
        
        return result
    
    @staticmethod
    def get_ollama_installer_info() -> Dict[str, Any]:
        """Get information about Ollama installer for different performance levels
        
        Returns:
            Dictionary with installer information and performance recommendations
        """
        return {
            'download_url': 'https://ollama.com/download',
            'installer_file': 'OllamaSetup.exe',
            'performance_profiles': {
                'low': {
                    'name': 'Niedrige Leistung',
                    'description': 'Für grundlegende Aufgaben, geringe Systemanforderungen',
                    'recommended_models': ['qwen3:0.6b', 'qwen2.5vl:3b'],
                    'min_ram': '4 GB',
                    'min_storage': '8 GB'
                },
                'medium': {
                    'name': 'Mittlere Leistung', 
                    'description': 'Ausgewogene Leistung für die meisten Anwendungsfälle',
                    'recommended_models': ['qwen3:0.6b', 'qwen2.5vl:3b'],
                    'min_ram': '8 GB',
                    'min_storage': '12 GB'
                },
                'high': {
                    'name': 'Hohe Leistung',
                    'description': 'Beste Qualität für anspruchsvolle Aufgaben',
                    'recommended_models': ['qwen3:0.6b', 'qwen2.5vl:3b'],
                    'min_ram': '16 GB',
                    'min_storage': '16 GB'
                }
            },
            'installation_steps': [
                '1. Laden Sie den Ollama-Installer herunter',
                '2. Führen Sie OllamaSetup.exe als Administrator aus',
                '3. Folgen Sie den Installationsanweisungen',
                '4. Starten Sie das System neu',
                '5. Laden Sie die gewünschten Modelle über die Konsole herunter',
                '6. Kommen Sie zu den Einstellungen zurück, um Ihre Modelle zu konfigurieren'
            ]
        } 