# Document Processing System (RechtsUndSteuerKI)

A comprehensive document processing system built for legal and tax advisory workflows.

## Features

### Core Functionality
- **Document Template Management** - Create, upload, and manage document templates with dynamic placeholders
- **Client Management** - Comprehensive client database with legal forms and contact information
- **Workflow Processing** - End-to-end document processing workflows from template to final document

### NEW: User Account Settings
- **User Profile Management** - Personalized settings for name, role, and language preferences

## Architecture

```
RechtsUndSteuerKI/
├── backend/          # Flask API server
│   ├── app/
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── routes/   # REST API endpoints
│   │   └── services/ # Business logic
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

## 🚀 Anwendung starten

### Backend starten

1. **Navigieren Sie zum Backend-Verzeichnis:**
   ```bash
   cd backend
   ```

2. **Aktivieren Sie die virtuelle Umgebung:**
   ```bash
   source .venv/bin/activate  # Linux/Mac
   # oder
   .venv\Scripts\activate     # Windows
   ```

3. **Starten Sie den Flask-Server:**
   ```bash
   flask run
   # oder
   python main.py
   ```

   Der Backend-Server läuft nun auf **http://localhost:5000**

### Frontend starten

1. **Öffnen Sie ein neues Terminal und navigieren Sie zum Frontend-Verzeichnis:**
   ```bash
   cd frontend
   ```

2. **Starten Sie den Development-Server:**
   ```bash
   npm run dev
   ```

   Der Frontend-Server läuft nun auf **http://localhost:5173**

### Zugriff auf die Anwendung

- **Frontend (Web-Interface):** http://localhost:5173
- **Backend API:** http://localhost:5000
- **Account Settings:** Navigieren Sie zu "Konto-Einstellungen" in der App

**Wichtig:** Stellen Sie sicher, dass sowohl Backend als auch Frontend gleichzeitig laufen, damit die Anwendung vollständig funktioniert.

## Documentation

### API Endpoints

**User Management:**
- `GET /api/users/settings/<id>` - Get user settings
- `PUT /api/users/settings/<id>` - Update user preferences  

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
- **Konto-Einstellungen** - User account configuration

## Configuration

### Environment Variables

**Backend (.env):**
```bash
FLASK_APP=main.py
FLASK_ENV=development
DATABASE_URI=sqlite:///app.db
SECRET_KEY=your-secret-key
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

 
