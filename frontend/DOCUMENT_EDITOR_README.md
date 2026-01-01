# Dokumenten-Editor

## Installation

Die benötigten tiptap-Pakete wurden bereits installiert:
- `@tiptap/vue-3`
- `@tiptap/pm`
- `@tiptap/starter-kit`
- `@tiptap/extension-*` (Bold, Italic, Underline, BulletList, OrderedList, CodeBlock, Link, History)

## Route

Der Dokumenten-Editor ist über folgende Route erreichbar:
```
/editor/:id
```

Beispiel: `/editor/123` öffnet den Editor für Template mit ID 123.

## Komponenten-Struktur

### Hauptkomponenten

- **`DocumentEditor.vue`** - Hauptseite, orchestriert alle Komponenten
- **`EditorTopbar.vue`** - Toolbar oben mit Name, Preview, Export, Speichern
- **`LeftPanelTabs.vue`** - Tab-Navigation für EINSTELLUNGEN / FORMULAR
- **`SettingsPanel.vue`** - Platzhalter-Verwaltung und Mapping
- **`FormPanel.vue`** - Auto-generiertes Formular zum Befüllen der Platzhalter
- **`EditorCanvas.vue`** - tiptap Rich-Text-Editor mit Placeholder-Highlighting
- **`PreviewDrawer.vue`** - Vorschau-Drawer mit gemergtem Inhalt

### Composables

- **`useDocumentPlaceholders.ts`** - Extrahiert aus `DocumentCreationView.vue`:
  - `extractPlaceholders(html)` - Erkennt `{{ key }}` Platzhalter
  - `mergeContent(html, values)` - Ersetzt Platzhalter mit Werten
  - `guessType(key)` - Heuristische Typ-Erkennung
  - `mergePlaceholders()` - Merge-Funktion für Platzhalter-Listen

- **`useTemplateEditor.ts`** - Editor-State-Management:
  - Verwaltet `contentHtml`, `placeholders`, `fillValues`
  - Dirty-Tracking
  - Methoden zum Aktualisieren von Platzhaltern und Werten

### Custom Extension

- **`PlaceholderMark.ts`** - tiptap Mark Extension:
  - Erkennt und markiert `{{ key }}` Platzhalter
  - Unterstützt gefüllte/ungefüllte Zustände
  - Tooltip mit Wert und Quelle
  - Klick-Handler für Navigation zum Formular

## Features

### Platzhalter-Erkennung
- Automatische Erkennung von `{{ key }}` Platzhaltern im Dokument
- "Erneut scannen" Button zum Neuerkennen
- Heuristische Typ-Erkennung (text, number, date, dropdown, multiline)

### Platzhalter-Verwaltung
- Typ-Zuordnung (text, number, date, dropdown, multiline)
- DB-Feld-Mapping (Verknüpfung zu Mandant/Dokument/Adresse Feldern)
- Standardwerte, Pflichtfelder, Beschreibungen
- Anzeigename-Konfiguration

### Formular
- Auto-generiert aus erkannten Platzhaltern
- Verschiedene Input-Typen je nach Platzhalter-Typ:
  - `text` → NInput
  - `multiline` → NInput (textarea)
  - `number` → NInputNumber
  - `date` → NDatePicker
  - `dropdown` → NSelect
- Live-Update der Editor-Hervorhebung bei Eingabe

### Editor
- Rich-Text-Editor mit tiptap
- Toolbar: Undo/Redo, Bold/Italic/Underline, Listen, Code, Link, Clear
- Echtzeit-Highlighting:
  - Ungefüllt: Gelber Hintergrund (`ph`)
  - Gefüllt: Grüner Hintergrund (`ph--filled`) + Tooltip
- Klick auf Platzhalter → wechselt zu Formular-Tab
- Rohsicht-Toggle (`{}` Button)

### Preview & Export
- Preview-Drawer zeigt gemergten Inhalt
- Export als PDF oder DOCX (via Backend)
- Download der exportierten Datei

## API-Endpunkte

Die API-Funktionen sind in `src/lib/api.ts` unter `documentEditorApi`:

- `getTemplate(id)` - Lädt Template-Daten
- `updateTemplate(id, payload)` - Speichert Änderungen
- `exportTemplate(id, fillValues, format)` - Exportiert als PDF/DOCX
- `getDbFields()` - Lädt mappbare DB-Felder

**Hinweis:** Aktuell sind Mock-Daten implementiert. Die Backend-Integration muss noch erfolgen.

## Styling

Platzhalter-Styling (in `EditorCanvas.vue`):
```css
.ph {
  @apply bg-yellow-100 text-yellow-900 underline decoration-dotted cursor-pointer;
}

.ph--filled {
  @apply bg-green-100 text-green-900 ring-1 ring-green-300;
}
```

## Nächste Schritte

1. Backend-Integration:
   - `/api/templates/:id` GET/PATCH Endpunkte
   - `/api/templates/:id/export` POST Endpunkt
   - `/api/db-fields` GET Endpunkt

2. Verbesserungen:
   - Placeholder-Klick fokussiert entsprechendes Formular-Feld
   - Bessere Placeholder-Erkennung (auch in komplexen HTML-Strukturen)
   - Undo/Redo für Platzhalter-Änderungen
   - Validierung von Platzhalter-Werten

3. Erweiterte Features:
   - Drag & Drop für Platzhalter-Reihenfolge
   - Platzhalter-Gruppen
   - Vorlagen-Versionierung

