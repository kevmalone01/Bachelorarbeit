# RechtsUndSteuerKI - Funktionsdokumentation

Eine umfassende Dokumentationsdatei, die alle Funktionen, Module und Features der RechtsUndSteuerKI-Software beschreibt.

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Hauptfunktionen](#hauptfunktionen)
3. [Frontend-Module](#frontend-module)
4. [Backend-API](#backend-api)
5. [Datenmodelle](#datenmodelle)
6. [Workflows](#workflows)
7. [Technische Details](#technische-details)

---

## Übersicht

**RechtsUndSteuerKI** ist ein umfassendes Dokumentenverarbeitungssystem für Rechts- und Steuerberatungsbüros. Die Software ermöglicht die Verwaltung von Dokumentenvorlagen, Mandanten, Workflows und die Verarbeitung von Dokumenten.

### Hauptmerkmale

- **Dokumentenvorlagen-Management** - Erstellen, Hochladen und Verwalten von Dokumentenvorlagen mit dynamischen Platzhaltern
- **Mandantenverwaltung** - Umfassende Mandantendatenbank mit Rechtsformen und Kontaktinformationen
- **Workflow-Verarbeitung** - End-to-End Dokumentenverarbeitung von Vorlage bis finales Dokument
- **Benutzerverwaltung** - Personalisierte Einstellungen

---

## Hauptfunktionen

### 1. Dokumentenvorlagen-Management

#### Vorlagen erstellen und bearbeiten
- **Hochladen von Dokumenten**: Unterstützung für DOCX-Dateien
- **Platzhalter-Erkennung**: Automatische Erkennung von Platzhaltern im Dokument
- **Platzhalter-Verwaltung**: 
  - Platzhalter hinzufügen, bearbeiten und löschen
  - Platzhalter mit Datenbankfeldern verknüpfen (`mappedFieldId`, `mappedDbField`)
  - Platzhalter-Typen: Text, Zahl, Datum, Dropdown, Mehrzeilig
- **Vorlagen bearbeiten**: WYSIWYG-Editor für direkte Bearbeitung von Vorlagen
- **Vorlagen speichern**: Automatisches Speichern mit `contentHtml` und Platzhaltern

#### Vorlagen verwenden
- **Dokument aus Vorlage erstellen**: Neues Dokument basierend auf einer Vorlage erstellen
- **Platzhalter ausfüllen**: Automatisches Ausfüllen von Platzhaltern mit Mandantendaten
- **Vorschau**: Live-Vorschau des Dokuments mit ausgefüllten Platzhaltern
- **Export**: Export als PDF oder DOCX

### 2. Mandantenverwaltung

#### Mandanten-Datenbank
- **Mandanten erstellen**: 
  - Natürliche Personen (mit Anrede, Titel, Vorname, Nachname, Geburtstag)
  - Juristische Personen (mit Firmenname, Rechtsform, Umsatzsteuer-ID)
- **Kontaktinformationen**: E-Mail, Telefon, Adresse
- **Steuerinformationen**: Steuernummer, Steuer-ID, Finanzamt-Daten
- **Mandanten bearbeiten**: Vollständige Bearbeitung aller Mandantendaten
- **Mandanten löschen**: Mit Bestätigung

#### Mandanten-Filterung und Suche
- **Suche**: Volltextsuche über alle Mandantenfelder
- **Filter**: 
  - Nach Rechtsform
  - Nach Steuerberater
  - Nach Erstellungsdatum
- **Sortierung**: Nach verschiedenen Kriterien sortierbar
- **Paginierung**: Seitenweise Anzeige mit konfigurierbarer Seitengröße

### 3. Dokumentenverarbeitung

#### Dokument-Editor
- **WYSIWYG-Editor**: Rich-Text-Editor für direkte Dokumentenbearbeitung
- **Platzhalter-Markierung**: Visuelle Markierung von Platzhaltern im Dokument
- **Platzhalter-Einstellungen**: 
  - Platzhalter konfigurieren (Typ, Standardwert, Beschreibung)
  - Platzhalter mit Datenbankfeldern verknüpfen
- **Formular-Panel**: Automatisches Formular für Platzhalter-Ausfüllung
- **Vorschau-Panel**: Live-Vorschau des Dokuments
- **Auto-Save**: Automatisches Speichern von Änderungen

#### Dokument-Erstellung
- **Aus Vorlage**: Neues Dokument aus einer Vorlage erstellen
- **Direkt hochladen**: Dokument direkt hochladen und bearbeiten
- **Platzhalter scannen**: Automatische Erkennung von Platzhaltern
- **Mandanten-Verknüpfung**: Dokument mit Mandanten verknüpfen

### 4. Workflow-Management

#### Workflows erstellen
- **Workflow-Schritte**:
  1. Dokumente hochladen
  2. Beteiligte auswählen (Mandant, Empfänger, Bearbeiter)
  3. Vorlage auswählen
  4. Bestätigung
- **Workflow-Metadaten**: Titel, Beschreibung, Priorität, Fälligkeitsdatum
- **Status-Verwaltung**: Zu erledigen, In Arbeit, Abgeschlossen

#### Workflow-Verarbeitung
- **Dokumentenverarbeitung**: Analyse von Dokumenten
- **Feld-Extraktion**: Extraktion von Feldern aus Dokumenten
- **Vorlagen-Auswahl**: Auswahl passender Vorlagen
- **Mandanten-Zuordnung**: Zuordnung zu Mandanten

### 5. Benutzerverwaltung

#### Benutzer-Einstellungen
- **Profil**: Name, E-Mail, Rolle, Sprache

---

## Frontend-Module

### Seiten (Pages)

#### Dashboard (`/dashboard`)
- **Übersicht**: Systemübersicht mit Statistiken
- **Dokumenten-Tabelle**: Liste aller Dokumente mit Filterung und Sortierung
- **Schnellaktionen**: Dokument erstellen
- **Filter**: Nach Benutzer, Vorlage, Status, Datum filtern

#### Mandanten (`/clients`)
- **Mandanten-Grid**: Kartenansicht aller Mandanten
- **Mandanten-Details**: Detailansicht eines Mandanten
- **Mandanten erstellen**: Formular zum Erstellen neuer Mandanten
- **Bulk-Operationen**: Mehrere Mandanten gleichzeitig auswählen und löschen

#### Vorlagen (`/templates`)
- **Vorlagen-Tabelle**: Liste aller Vorlagen
- **Vorlagen erstellen**: Hochladen und Konfigurieren neuer Vorlagen
- **Vorlagen bearbeiten**: Direkte Bearbeitung von Vorlagen
- **Vorlagen löschen**: Mit Bestätigung

#### Dokument-Editor (`/editor/:id`)
- **Editor-Canvas**: WYSIWYG-Editor für Dokumentenbearbeitung
- **Einstellungen-Panel**: Platzhalter-Konfiguration
- **Formular-Panel**: Platzhalter-Ausfüllung
- **Vorschau-Panel**: Live-Vorschau des Dokuments
- **Auto-Save**: Automatisches Speichern

### Views

#### DocumentFromTemplateView (`/document-from-template`)
- **Vorlagen-Auswahl**: Dropdown zur Auswahl einer Vorlage
- **Mandanten-Auswahl**: Dropdown zur Auswahl eines Mandanten
- **Vorschau**: Anzeige der ausgewählten Vorlage und des Mandanten
- **Dokument erstellen**: Navigation zum Editor mit Template-ID und Client-ID

#### DocumentCreationView (`/document-creation`)
- **Dokument hochladen**: Datei-Upload für neue Dokumente
- **Vorlagen-Konfiguration**: Platzhalter und Einstellungen
- **Speichern**: Als Vorlage oder Dokument speichern

#### WorkflowDetailView (`/workflow/:id`)
- **Workflow-Übersicht**: Details eines Workflows
- **Dokumente**: Liste der Workflow-Dokumente
- **Status-Verwaltung**: Status ändern

#### AccountSettingsView (`/account-settings`)
- **Benutzer-Profil**: Name, E-Mail, Rolle, Sprache

### Komponenten

#### Editor-Komponenten
- **EditorCanvas**: WYSIWYG-Editor mit Tiptap
- **SettingsPanel**: Platzhalter-Konfiguration
- **FormPanel**: Platzhalter-Ausfüllung
- **PreviewDrawer**: Dokument-Vorschau
- **PlaceholderMark**: Platzhalter-Markierung im Editor

#### Client-Komponenten
- **ClientList**: Liste aller Mandanten
- **ClientCard**: Kartenansicht eines Mandanten
- **CreateClientModal**: Modal zum Erstellen von Mandanten
- **Filters**: Filter-Komponente für Mandanten
- **Toolbar**: Toolbar mit Aktionen

#### Template-Komponenten
- **TemplatesTable**: Tabelle aller Vorlagen
- **Filters**: Filter-Komponente für Vorlagen
- **Toolbar**: Toolbar mit Aktionen

#### Workflow-Komponenten
- **WorkflowEditModal**: Modal zum Bearbeiten von Workflows
- **WorkflowDocumentsManager**: Verwaltung von Workflow-Dokumenten
- **WorkflowDocumentViewer**: Anzeige von Workflow-Dokumenten

### Composables

#### useTemplateEditor
- **State Management**: Verwaltung von Editor-State
- **Platzhalter-Scanning**: Automatische Erkennung von Platzhaltern
- **Platzhalter-Verwaltung**: Hinzufügen, Bearbeiten, Löschen
- **Fill Values**: Verwaltung von Ausfüllwerten
- **Auto-Save**: Automatisches Speichern

#### useDocumentPlaceholders
- **Platzhalter-Extraktion**: Extraktion von Platzhaltern aus Dokumenten
- **Platzhalter-Validierung**: Validierung von Platzhaltern

---

## Backend-API

### Dokumenten-Endpunkte

#### Vorlagen-Management
- `GET /api/documents/templates` - Alle Vorlagen abrufen
- `GET /api/documents/templates/<id>` - Vorlage abrufen
- `PATCH /api/documents/templates/<id>` - Vorlage aktualisieren
- `PUT /api/documents/templates/<id>` - Vorlage aktualisieren
- `DELETE /api/documents/templates/<id>` - Vorlage löschen

#### Dokument-Management
- `GET /api/documents` - Alle Dokumente abrufen
- `GET /api/documents/<id>` - Dokument abrufen
- `POST /api/documents` - Dokument erstellen
- `PUT /api/documents/<id>` - Dokument aktualisieren
- `DELETE /api/documents/<id>` - Dokument löschen
- `GET /api/documents/<id>/file` - Dokument-Datei abrufen
- `GET /api/documents/<id>/text` - Dokument-Text abrufen

#### Dokument-Verarbeitung
- `POST /api/documents/upload` - Dokument hochladen
- `POST /api/documents/preview/<id>` - Dokument-Vorschau generieren
- `POST /api/documents/download/<id>` - Dokument herunterladen
- `POST /api/documents/create-from-template/<id>` - Dokument aus Vorlage erstellen
- `POST /api/documents/preview-temp` - Temporäre Vorschau
- `POST /api/documents/placeholders/rename-temp` - Platzhalter umbenennen (temporär)

#### Platzhalter-Management
- `GET /api/placeholders` - Alle Platzhalter abrufen
- `GET /api/placeholders/<id>` - Platzhalter abrufen
- `PUT /api/documents/<id>/placeholders/rename` - Platzhalter umbenennen

### Mandanten-Endpunkte

- `GET /api/clients` - Alle Mandanten abrufen (mit Filterung und Paginierung)
- `GET /api/clients/<id>` - Mandant abrufen
- `POST /api/clients` - Mandant erstellen
- `PUT /api/clients/<id>` - Mandant aktualisieren
- `DELETE /api/clients/<id>` - Mandant löschen

### Workflow-Endpunkte

- `GET /api/work-orders` - Alle Workflows abrufen
- `GET /api/work-orders/<id>` - Workflow abrufen
- `POST /api/work-orders` - Workflow erstellen
- `PUT /api/work-orders/<id>` - Workflow aktualisieren
- `DELETE /api/work-orders/<id>` - Workflow löschen
- `POST /api/work-orders/with-documents` - Workflow mit Dokumenten erstellen
- `GET /api/work-orders/<id>/documents` - Workflow-Dokumente abrufen
- `POST /api/work-orders/<id>/documents` - Dokument zu Workflow hinzufügen
- `GET /api/work-orders/<id>/documents/<doc_id>/file` - Workflow-Dokument-Datei abrufen
- `DELETE /api/work-orders/<id>/documents/<doc_id>` - Workflow-Dokument löschen
- `POST /api/work-orders/<id>/extract-fields` - Felder aus Workflow-Dokumenten extrahieren
- `GET /api/work-orders/<id>/documents-summary` - Workflow-Dokumente-Zusammenfassung

### Benutzer-Endpunkte

- `GET /api/users` - Alle Benutzer abrufen
- `POST /api/users` - Benutzer erstellen
- `GET /api/users/settings/<id>` - Benutzer-Einstellungen abrufen
- `PUT /api/users/settings/<id>` - Benutzer-Einstellungen aktualisieren

### Datenbank-Felder

- `GET /api/db-fields` - Alle verfügbaren Datenbankfelder für Platzhalter-Verknüpfung

### Steuerberater-Endpunkte

- `GET /api/tax-advisors` - Alle Steuerberater abrufen
- `GET /api/tax-advisors/<id>` - Steuerberater abrufen

---

## Datenmodelle

### Document (Dokument/Vorlage)
- `id`: Eindeutige ID
- `title`: Titel des Dokuments
- `content`: HTML-Inhalt des Dokuments
- `document_type`: Dokumenttyp (z.B. "docx")
- `file_path`: Pfad zur Originaldatei
- `is_template`: Boolean, ob es eine Vorlage ist
- `placeholders`: JSON-Array von Platzhaltern
- `linked_client_group_ids`: JSON-Array von verknüpften Mandantengruppen-IDs
- `client_id`: ID des zugeordneten Mandanten (bei Dokumenten)
- `status`: Status des Dokuments
- `created_at`: Erstellungsdatum
- `updated_at`: Aktualisierungsdatum

### Client (Mandant)
- `id`: Eindeutige ID
- `type`: Typ ("Natürliche Person" oder "Juristische Person")
- `salutation`: Anrede
- `title`: Titel
- `firstName`: Vorname
- `lastName`: Nachname
- `companyName`: Firmenname
- `legalForm`: Rechtsform
- `email`: E-Mail
- `phone`: Telefon
- `street`: Straße
- `number`: Hausnummer
- `zip`: Postleitzahl
- `city`: Stadt
- `taxNumber`: Steuernummer
- `vatId`: Umsatzsteuer-ID
- `taxOffice`: Finanzamt
- `birthDate`: Geburtstag
- `created_at`: Erstellungsdatum
- `updated_at`: Aktualisierungsdatum

### Placeholder (Platzhalter)
- `key`: Eindeutiger Schlüssel
- `label`: Anzeigename
- `type`: Typ (text, number, date, dropdown, multiline)
- `defaultValue`: Standardwert
- `description`: Beschreibung
- `mappedFieldId`: ID des verknüpften Datenbankfelds
- `mappedDbField`: Schlüssel des verknüpften Datenbankfelds

### WorkOrder (Workflow)
- `id`: Eindeutige ID
- `title`: Titel
- `description`: Beschreibung
- `status`: Status (to do, in progress, done)
- `priority`: Priorität (high, medium, low)
- `due_date`: Fälligkeitsdatum
- `client_id`: ID des Mandanten
- `tax_advisor_id`: ID des Steuerberaters
- `template_id`: ID der Vorlage
- `created_at`: Erstellungsdatum
- `updated_at`: Aktualisierungsdatum

### User (Benutzer)
- `id`: Eindeutige ID
- `name`: Name
- `email`: E-Mail
- `role`: Rolle
- `language`: Sprache

---

## Workflows

### Dokument aus Vorlage erstellen

1. **Vorlage auswählen**: Benutzer wählt eine Vorlage aus der Liste
2. **Mandant auswählen**: Benutzer wählt einen Mandanten
3. **Dokument erstellen**: System erstellt ein neues Dokument basierend auf der Vorlage
4. **Platzhalter ausfüllen**: 
   - Automatisches Ausfüllen mit Mandantendaten (wenn verknüpft)
   - Manuelles Ausfüllen über Formular
5. **Bearbeiten**: Dokument im Editor bearbeiten
6. **Speichern**: Dokument speichern
7. **Export**: Dokument als PDF oder DOCX exportieren

### Workflow-Verarbeitung

1. **Workflow erstellen**: 
   - Dokumente hochladen
   - Beteiligte auswählen
   - Vorlage auswählen
2. **Verarbeitung**:
   - Dokumente werden analysiert
   - Felder werden extrahiert
   - Vorlage wird ausgewählt
3. **Dokument generieren**:
   - Dokument wird aus Vorlage generiert
   - Felder werden automatisch ausgefüllt
4. **Überprüfung**: Dokument wird überprüft und bearbeitet
5. **Abschluss**: Workflow wird abgeschlossen

### Vorlage bearbeiten

1. **Vorlage öffnen**: Vorlage im Editor öffnen
2. **Bearbeiten**: Dokument im WYSIWYG-Editor bearbeiten
3. **Platzhalter hinzufügen**: Platzhalter manuell hinzufügen oder automatisch scannen
4. **Platzhalter konfigurieren**: 
   - Typ, Standardwert, Beschreibung
   - Mit Datenbankfeldern verknüpfen
5. **Speichern**: Vorlage speichern (mit `contentHtml` und Platzhaltern)

---

## Technische Details

### Frontend-Architektur

#### Technologie-Stack
- **Framework**: Vue.js 3 mit Composition API
- **Sprache**: TypeScript
- **Styling**: Custom CSS, Tailwind CSS
- **State Management**: Vuex
- **Routing**: Vue Router
- **HTTP Client**: Axios
- **UI Components**: Naive UI
- **Editor**: Tiptap (WYSIWYG-Editor)

#### Wichtige Dateien
- `src/pages/DocumentEditor.vue` - Haupt-Editor-Komponente
- `src/views/DocumentFromTemplateView.vue` - Dokument aus Vorlage erstellen
- `src/components/editor/` - Editor-Komponenten
- `src/composables/useTemplateEditor.ts` - Editor-Logik
- `src/lib/api.ts` - API-Client

### Backend-Architektur

#### Technologie-Stack
- **Framework**: Flask (Python)
- **Datenbank**: SQLAlchemy ORM mit SQLite/PostgreSQL
- **API**: RESTful Endpoints mit JSON

#### Wichtige Dateien
- `app/routes/routes.py` - API-Endpunkte
- `app/models/` - Datenmodelle
- `app/services/` - Business-Logik
- `app/services/document_service.py` - Dokumenten-Service

### Datenbank-Schema

#### Tabellen
- `document` - Dokumente und Vorlagen
- `client` - Mandanten
- `work_order` - Workflows
- `user` - Benutzer
- `tax_advisor` - Steuerberater
- `placeholder` - Platzhalter-Definitionen
- `salutation` - Anreden
- `legal_form` - Rechtsformen

### Sicherheit

#### Authentifizierung
- Route-Guards für geschützte Seiten
- Benutzer-Authentifizierung (in Entwicklung)

#### Datenvalidierung
- Frontend-Validierung mit Formular-Regeln
- Backend-Validierung in API-Endpunkten
- SQL-Injection-Schutz durch SQLAlchemy ORM

### Performance-Optimierungen

#### Frontend
- Lazy Loading von Komponenten
- Vue Query für Caching und automatisches Refetching
- Optimistische Updates
- Debouncing bei Suche

#### Backend
- Datenbank-Indizes
- Query-Optimierung
- Caching von häufig verwendeten Daten
- Asynchrone Verarbeitung für lange Operationen

---

## Besondere Features

### Platzhalter-Verknüpfung

Platzhalter können mit Datenbankfeldern verknüpft werden:
- **Automatisches Ausfüllen**: Wenn ein Platzhalter mit einem Datenbankfeld verknüpft ist, wird er automatisch mit den Mandantendaten ausgefüllt
- **Verknüpfte Felder**: 
  - Mandanten-Felder (Name, E-Mail, Steuernummer, etc.)
  - Adress-Felder (Straße, PLZ, Ort)
  - Finanzamt-Felder (Name, Adresse, E-Mail)

### Template-ID-Verwaltung

Beim Erstellen eines Dokuments aus einer Vorlage:
- **Template-ID im Query**: Die Template-ID wird im Query-Parameter gespeichert
- **Korrekte Vorlage laden**: Die richtige Vorlage wird immer geladen, auch wenn die Route geändert wird
- **Bearbeitete Vorlage**: Die bearbeitete Vorlage (mit `contentHtml`) wird verwendet, nicht die ursprüngliche Datei

### Auto-Save

- **Automatisches Speichern**: Änderungen werden automatisch gespeichert
- **Dirty-State**: Anzeige, ob ungespeicherte Änderungen vorhanden sind
- **Speicher-Status**: Visuelle Anzeige des Speicher-Status

### Responsive Design

- **Desktop**: Vollständige Funktionalität mit Sidebar
- **Mobile**: Optimierte Ansicht mit Drawer für Filter
- **Tablet**: Angepasste Layouts

---

## Entwicklung

### Setup

Siehe `README.md` für detaillierte Installationsanweisungen.

### Code-Struktur

```
RechtsUndSteuerKI/
├── backend/
│   ├── app/
│   │   ├── models/        # Datenmodelle
│   │   ├── routes/        # API-Endpunkte
│   │   └── services/      # Business-Logik
│   └── main.py            # Entry Point
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue-Komponenten
│   │   ├── pages/         # Seiten
│   │   ├── views/         # Views
│   │   ├── composables/   # Composables
│   │   └── lib/           # Utilities
│   └── package.json
└── README.md
```

### Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

---

## Support und Kontakt

Für Fragen und Support:
- Dokumentation in `/backend/README.md` und `/frontend/README.md`
- API-Endpunkte und Konfiguration

---

**Version**: 2.0  
**Letzte Aktualisierung**: 2024  
**Lizenz**: MIT License

