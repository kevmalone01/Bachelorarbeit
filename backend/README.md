# Document Processing System Backend

This directory contains the Flask based API used by the Document Processing System. The application uses SQLAlchemy for data persistence, Flask-Migrate for migrations and integrates with an Ollama LLM service for AI-powered document processing.

## Project Structure

```
backend/
├── app/
│   ├── routes/     # API endpoints
│   ├── db/         # Database initialization helpers
│   ├── models/     # ORM models
│   ├── services/   # Business logic and integrations
│   └── __init__.py # Application factory
├── config.py       # Configuration classes
├── main.py         # Application entry point and CLI commands
├── requirements.txt
└── tests/          # Pytest test suite
```

### File Overview

| Path | Purpose |
| ---- | ------- |
| `app/__init__.py` | Creates the Flask application and registers blueprints. |
| `app/config/` | Logging configuration and helpers. |
| `app/db/__init__.py` | Initializes the SQLAlchemy database instance. |
| `app/models/client.py` | Client data model with legal forms and salutations. |
| `app/models/document.py` | Document template model with placeholder support. |
| `app/models/user.py` | User model with Ollama model preferences. |
| `app/models/tax_advisor.py` | Tax advisor information model. |
| `app/models/work_order.py` | Work order/workflow management model. |
| `app/models/placeholder.py` | Document placeholder definition model. |
| `app/routes/routes.py` | REST API endpoints including user settings. |
| `app/services/database_service.py` | CRUD helper around the models. |
| `app/services/document_service.py` | Document upload, preview, and processing utilities. |
| `app/services/llm_service.py` | Ollama API wrapper with status checking. |
| `app/services/user_service.py` | User management and model configuration service. |
| `config.py` | Environment specific configuration classes. |
| `main.py` | Entry point with CLI commands and logging setup. |
| `migrations/` | Alembic migration environment files. |
| `tests/` | Pytest suite validating the database service. |

## Requirements

- [Python](https://www.python.org/) and pip
- [Ollama](https://ollama.com/) running locally for LLM features (optional but recommended)

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env` if needed and set environment variables such as `FLASK_APP`, `FLASK_ENV`, `DATABASE_URI` and `SECRET_KEY`.

## Database Initialization

Create the database tables:

```bash
flask init-db
```

Seed sample data (optional):

```bash
flask seed-db
```

## Running the Server

Start the development server with:

```bash
flask run
```

or

```bash
python main.py
```

## CLI Commands

The application exposes several helper commands:

- `flask reset-db` – drop and recreate all tables
- `flask show-db` – print database contents
- `flask delete-doc <id>` – remove a document entry

## API Endpoints

### User Settings & Ollama Configuration

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/api/users/settings/<user_id>` | GET | Get user settings and preferences |
| `/api/users/settings/<user_id>` | PUT | Update user settings and model preferences |
| `/api/users/models` | GET | Get available Ollama models and installation status |
| `/api/users/ollama-installer` | GET | Get Ollama installer information and performance profiles |
| `/api/users` | POST | Create a new user |

### Document Management

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/api/documents/templates` | GET | Get all document templates |
| `/api/documents/upload` | POST | Upload new document template |
| `/api/documents/preview/<id>` | POST | Generate document preview with placeholders |
| `/api/documents/download/<id>` | POST | Download filled document |
| `/api/documents/<id>` | GET, PUT, DELETE | Manage specific documents |

### Client & Workflow Management

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/api/clients` | GET, POST | Manage client data |
| `/api/work-orders` | GET, POST | Manage work orders/workflows |
| `/api/work-orders/<id>/documents` | GET, POST | Manage workflow documents |

## Ollama Integration

The system integrates with Ollama for AI-powered document processing:

### Features
- **Automatic Detection:** Checks if Ollama is installed and running
- **Model Management:** Categorizes models into text and image processing types  
- **User Preferences:** Stores user-selected models for text and image processing
- **Fallback Support:** Provides installation guidance when Ollama is not available
- **Performance Profiles:** Recommends models based on system capabilities (low/medium/high)

### Configuration
Set the Ollama API base URL in your environment or config:
```bash
export OLLAMA_API_BASE="http://localhost:11434"
export DEFAULT_LLM_MODEL="llama3"
```

### Supported Models
- **Text Models:** llama3, mistral, gemma (various sizes)
- **Image Models:** llava, bakllava, moondream (vision models)

## Tests

Run the unit tests using pytest:

```bash
pytest
```

## Recent Updates

### User Account Settings Feature
- Added comprehensive user management system
- Integrated Ollama model selection and configuration  
- Implemented installation status checking and guidance
- Added performance-based model recommendations
- Enhanced API with user settings endpoints
