# Document Processing System (RechtsUndSteuerKI)

A comprehensive document processing system with AI-powered features, built for legal and tax advisory workflows. The system integrates with Ollama AI models for intelligent document analysis and processing.

## Features

### Core Functionality
- **Document Template Management** - Create, upload, and manage document templates with dynamic placeholders
- **Client Management** - Comprehensive client database with legal forms and contact information
- **Workflow Processing** - End-to-end document processing workflows from template to final document
- **AI Integration** - Powered by Ollama for intelligent text and image processing

### NEW: User Account Settings & AI Configuration
- **User Profile Management** - Personalized settings for name, role, and language preferences
- **Ollama Model Configuration** - Select and configure AI models for text and image processing
- **Automatic AI Detection** - Real-time checking of Ollama installation and available models
- **Performance Optimization** - Three-tier recommendation system (low/medium/high performance)
- **Installation Support** - Guided setup for Ollama with performance-based model suggestions

## Architecture

```
RechtsUndSteuerKI/
├── backend/          # Flask API server
│   ├── app/
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── routes/   # REST API endpoints
│   │   └── services/ # Business logic and AI integration
│   └── requirements.txt
├── frontend/         # Vue.js 3 application
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── services/
│   │   └── types/
│   └── package.json
└── README.md
```

### Technology Stack

**Backend:**
- **Framework:** Flask (Python)
- **Database:** SQLAlchemy ORM with SQLite/PostgreSQL
- **AI Integration:** Ollama API for LLM/vision models
- **API:** RESTful endpoints with JSON responses

**Frontend:**
- **Framework:** Vue.js 3 with Composition API
- **Language:** TypeScript for type safety
- **Styling:** Custom CSS with responsive design
- **State Management:** Vuex for application state
- **Routing:** Vue Router for SPA navigation

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** and pip
- **Node.js 16+** and npm
- **Ollama** (optional but recommended for AI features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd RechtsUndSteuerKI
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   flask init-db
   flask run
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Setup Ollama (Optional):**
   ```bash
   # Download from https://ollama.com/download
   # Or use the in-app installer guidance
   ollama pull llama3
   ollama pull llava
   ```

### Access the Application
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:5000
- **Account Settings:** Navigate to "Konto-Einstellungen" in the app

## Documentation

### API Endpoints

**User Management & AI Configuration:**
- `GET /api/users/settings/<id>` - Get user settings
- `PUT /api/users/settings/<id>` - Update user preferences  
- `GET /api/users/models` - Get available Ollama models
- `GET /api/users/ollama-installer` - Get installation guidance

**Document Processing:**
- `GET /api/documents/templates` - List document templates
- `POST /api/documents/upload` - Upload new template
- `POST /api/documents/preview/<id>` - Generate preview
- `POST /api/documents/download/<id>` - Download processed document

**Client & Workflow Management:**
- `GET /api/clients` - List clients
- `POST /api/work-orders` - Create new workflow
- `GET /api/work-orders/<id>/documents` - Get workflow documents

### User Interface

**Navigation:**
- **Dashboard** - System overview and statistics
- **Mandate** - Client management interface
- **Dokumente** - Document template management  
- **Konto-Einstellungen** - User account and AI model configuration

## AI Integration

### Ollama Models Support

**Text Processing Models:**
- **llama3** (8b, 13b, 70b) - General purpose language model
- **mistral** (7b, 22b) - Fast and efficient text processing
- **gemma** (2b, 7b) - Lightweight text analysis

**Image Processing Models:**
- **llava** (7b, 13b) - Vision language model for image analysis
- **bakllava** - Specialized vision model
- **moondream** - Lightweight image understanding

### Performance Profiles

**Low Performance (8GB RAM, 10GB storage):**
- Recommended: llama3:8b, mistral:7b, gemma:2b
- Good for basic document processing

**Medium Performance (16GB RAM, 25GB storage):**
- Recommended: llama3:13b, mistral:7b-instruct, llava:7b
- Balanced performance for most use cases

**High Performance (32GB+ RAM, 50GB+ storage):**
- Recommended: llama3:70b, mistral:22b, llava:13b
- Best quality for complex document analysis

## Configuration

### Environment Variables

**Backend (.env):**
```bash
FLASK_APP=main.py
FLASK_ENV=development
DATABASE_URI=sqlite:///app.db
SECRET_KEY=your-secret-key
OLLAMA_API_BASE=http://localhost:11434
DEFAULT_LLM_MODEL=llama3
```

**Frontend (Optional):**
```bash
VITE_API_BASE_URL=http://localhost:5000
```

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend  
cd frontend
npm run test
```

### Code Formatting
```bash
# Frontend
npm run format
```

### Database Management
```bash
# Reset database
flask reset-db

# Show database contents
flask show-db

# Delete document
flask delete-doc <id>
```

## Recent Updates

### Version 2.0 - Account Settings & AI Integration
- ✅ **User Account Management** - Complete user profile and preferences system
- ✅ **Ollama Integration** - AI model selection and configuration interface
- ✅ **Installation Detection** - Automatic checking and guided setup for Ollama
- ✅ **Performance Optimization** - Model recommendations based on system capabilities
- ✅ **Type Safety** - Full TypeScript integration for frontend components
- ✅ **Enhanced API** - New endpoints for user settings and AI model management

### Previous Features
- Document template management with placeholders
- Client database with legal forms
- Workflow processing and document generation  
- Responsive Vue.js frontend with modern UI
- RESTful API with comprehensive error handling

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in `/backend/README.md` and `/frontend/README.md`
- Review API endpoints and model configuration options
- Use the in-app Ollama installation guidance for AI setup

---

**Built with ❤️ for legal and tax advisory professionals**
