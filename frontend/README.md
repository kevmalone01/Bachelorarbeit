# Document Processing System Frontend

This directory contains the Vue 3 application that provides the user interface of the Document Processing System. The project uses TypeScript, Vue Router, Vuex and Vuetify.

## Project Structure

```
frontend/
├── src/
│   ├── assets/          # Static assets (images, fonts)
│   ├── components/      # Reusable Vue components
│   ├── router/          # Application routes
│   ├── services/        # API clients and helpers
│   ├── store/           # Vuex store modules
│   ├── types/           # TypeScript interfaces
│   ├── views/           # Page level components
│   ├── App.vue          # Root component
│   └── main.ts          # Entry point
├── public/              # Public files served as-is
└── ...config files      # Vite and TypeScript configuration
```

### File Overview

| Path | Purpose |
| ---- | ------- |
| `index.html` | HTML entry used by Vite during development. |
| `vite.config.ts` | Build and dev server configuration. |
| `src/main.ts` | Bootstraps the Vue application. |
| `src/App.vue` | Root component containing the layout shell. |
| `src/assets/` | Global styles and images. |
| `src/components/ClientList.vue` | Lists existing clients. |
| `src/components/DocumentList.vue` | Displays uploaded templates. |
| `src/components/DocumentPreview.vue` | Shows document previews. |
| `src/components/DynamicMask.vue` | Dynamically builds forms from placeholders. |
| `src/components/Mask.vue` | Base document mask component. |
| `src/components/WorkflowEditModal.vue` | Modal dialog for editing workflows. |
| `src/router/index.ts` | Application routing definitions. |
| `src/services/api.ts` | Axios instance and REST API helpers. |
| `src/services/authService.ts` | Authentication helper functions. |
| `src/store/store.ts` | Vuex store initialization. |
| `src/store/modules/*` | Feature-specific Vuex modules. |
| `src/views/` | Page components mapped to routes. |
| `src/views/AuthView.vue` | Login form for user authentication. |
| `src/views/DashboardView.vue` | Overview dashboard listing workflows and stats. |
| `src/views/ClientCreationView.vue` | Interface for adding and listing clients. |
| `src/views/DocumentCreationView.vue` | Upload and edit document templates. |
| `src/views/DocumentFillingView.vue` | Fill out a template for a specific client. |
| `src/views/WorkflowDetailView.vue` | Detailed view of a single workflow. |
| `src/views/WorkflowDocumentsView.vue` | View for managing uploaded documents. |

## Requirements

- [Node.js](https://nodejs.org/) and npm

## Setup

Install dependencies with:

```bash
npm install
```

### Development

Run the dev server with hot reload:

```bash
npm run dev
```

### Production Build

Compile and minify the project:

```bash
npm run build
```

### Code Format

Format source files using Prettier:

```bash
npm run format
```

