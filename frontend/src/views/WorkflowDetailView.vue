<template>
    <div class="workflow-detail-container">
        <!-- Header with workflow info and actions -->
        <header class="workflow-header">
            <div class="header-left">
                <button @click="goBack" class="back-btn">
                    <i class="icon-back">←</i>
                    Zurück zum Dashboard
                </button>
                <div class="workflow-info">
                    <h1>{{ workflow?.name || 'Workflow Details' }}</h1>
                    <div class="status-badge" :class="getStatusClass(workflow?.status)">
                        <span class="status-indicator"></span>
                        {{ workflow?.status }}
                    </div>
                </div>
            </div>
            <div class="header-actions">
                <button @click="changeStatus" class="btn-status">
                    Status ändern
                </button>
                <button @click="assignWorkflow" class="btn-assign">
                    Zuweisen
                </button>
            </div>
        </header>

        <!-- Workflow metadata -->
        <section class="metadata-section">
            <div class="metadata-card">
                <h3>Workflow-Details</h3>
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <span class="label">Mandant:</span>
                        <span class="value">{{ workflow?.client }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Verantwortlicher:</span>
                        <span class="value">{{ workflow?.assignedTo }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Erstellt:</span>
                        <span class="value">{{ formatDate(workflow?.createdAt) }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Fälligkeitsdatum:</span>
                        <span class="value" :class="{ 'overdue': isOverdue(workflow?.dueDate) }">
                            {{ formatDate(workflow?.dueDate) }}
                        </span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Priorität:</span>
                        <span class="value priority" :class="getPriorityClass(workflow?.priority)">
                            {{ workflow?.priority }}
                        </span>
                    </div>
                    <div class="metadata-item">
                        <span class="label">Dokumente:</span>
                        <span class="value">{{ workflow?.documentCount }} Dokument(e)</span>
                    </div>
                </div>
                <div class="description-section" v-if="workflow?.description">
                    <h4>Beschreibung:</h4>
                    <p>{{ workflow.description }}</p>
                </div>
            </div>
        </section>

        <!-- Main content with tabs -->
        <section class="main-content">
            <div class="content-tabs">
                <button 
                    v-for="tab in tabs" 
                    :key="tab.id"
                    @click="activeTab = tab.id"
                    :class="{ 'active': activeTab === tab.id }"
                    class="tab-button"
                >
                    <i :class="tab.icon"></i>
                    {{ tab.label }}
                </button>
            </div>

            <div class="tab-content">
                <!-- Documents Tab -->
                <div v-if="activeTab === 'documents'" class="documents-tab">
                    <div class="documents-header">
                        <h3>Workflow-Dokumente</h3>
                        <button @click="uploadNewDocument" class="btn-upload">
                            <i class="icon-upload">📁</i>
                            Dokument hochladen
                        </button>
                    </div>
                    
                    <div class="documents-list">
                        <div v-for="document in workflowDocuments" :key="document.id" class="document-card">
                            <div class="document-info">
                                <div class="document-icon">
                                    <i :class="getDocumentIcon(document.type)">📄</i>
                                </div>
                                <div class="document-details">
                                    <h4>{{ document.name }}</h4>
                                    <p>{{ document.type }} • {{ formatFileSize(document.size) }}</p>
                                    <span class="upload-date">Hochgeladen: {{ formatDate(document.uploadedAt) }}</span>
                                </div>
                            </div>
                            <div class="document-actions">
                                <button @click="viewOriginalText(document)" class="btn-view">
                                    Original anzeigen
                                </button>
                                <button @click="editMaskedDocument(document)" class="btn-edit">
                                    Bearbeiten
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Document Filling Tab (replaced Text Processing) -->
                <div v-if="activeTab === 'filling'" class="filling-tab">
                    <div v-if="!selectedTemplate" class="template-selection-section">
                        <!-- Template Selection -->
                        <div class="section-header">
                            <h3>Template für Workflow auswählen</h3>
                            <p>Wählen Sie ein Document-Template aus, um es für diesen Workflow zu verwenden</p>
                        </div>
                        
                        <div class="templates-grid">
                            <div 
                                v-for="template in templates" 
                                :key="template.id" 
                                class="template-card"
                                @click="selectTemplate(template)"
                            >
                                <div class="template-content">
                                    <div class="template-icon">
                                        <i class="icon-document">📄</i>
                                    </div>
                                    <div class="template-details">
                                        <h4>{{ template.name }}</h4>
                                        <p>{{ template.description || 'Keine Beschreibung verfügbar' }}</p>
                                        <div class="template-meta">
                                            <span class="field-count">{{ template.placeholders?.length || 0 }} Felder</span>
                                            <span class="template-date">{{ formatDate(template.created_at) }}</span>
                                        </div>
                                    </div>
                                </div>
                                <button class="btn-select">
                                    Auswählen
                                </button>
                            </div>
                        </div>
                        
                        <!-- Empty state -->
                        <div v-if="templates.length === 0" class="empty-templates">
                            <i class="icon-empty">📄</i>
                            <h4>Keine Templates verfügbar</h4>
                            <p>Es wurden noch keine Document-Templates erstellt.</p>
                            <button @click="goToCreation" class="btn-create">
                                Template erstellen
                            </button>
                        </div>
                        
                        <!-- Loading state -->
                        <div v-if="isLoadingTemplates" class="loading-state">
                            <div class="spinner"></div>
                            <p>Templates werden geladen...</p>
                        </div>
                    </div>

                    <!-- Document Filling Interface -->
                    <div v-else class="filling-interface">
                        <!-- Template info header -->
                        <div class="template-info-header">
                            <button @click="goBackToTemplateSelection" class="back-to-templates">
                                ← Zurück zur Template-Auswahl
                            </button>
                            
                            <div class="selected-template-info">
                                <div class="template-details">
                                    <h3>{{ selectedTemplate.name }}</h3>
                                    <p>{{ selectedTemplate.description || 'Keine Beschreibung verfügbar' }}</p>
                                </div>
                                <div class="template-stats">
                                    <span class="field-count">{{ selectedTemplate.placeholders?.length || 0 }} Felder</span>
                                </div>
                            </div>
                        </div>

                        <!-- Split view for form and preview -->
                        <div class="document-workspace">
                            <!-- Form Section -->
                            <div class="form-section">
                                <div class="section-title">
                                    <h4>Formular ausfüllen</h4>
                                </div>
                                
                                <div class="form-content">
                                    <DynamicMask 
                                        v-if="selectedTemplate.placeholders"
                                        key="workflow-filling-mask"
                                        :placeholders="selectedTemplate.placeholders || []" 
                                        :initial-values="formValues || {}"
                                        :client-field-groups="clientFieldGroups || []"
                                        :clients="clients || []"
                                        :title="'Formular: ' + selectedTemplate.name" 
                                        @update:values="updateFormValues"
                                        @client-selected="onClientSelected"
                                        @submit="generateDocument" 
                                    />
                                    <div v-else class="no-fields">
                                        <i class="icon-form">📝</i>
                                        <p>Dieses Template hat keine ausfüllbaren Felder.</p>
                                    </div>
                                </div>
                            </div>

                            <!-- Preview Section -->
                            <div class="preview-section">
                                <div class="section-title">
                                    <h4>Dokument-Vorschau</h4>
                                    <div v-if="previewMode === 'pdf' && pdfLastGeneratedAt" class="pdf-timestamp">
                                        <span class="timestamp-label">
                                            PDF generiert: {{ formatTimestamp(pdfLastGeneratedAt) }}
                                        </span>
                                    </div>
                                </div>
                                
                                <DocumentPreview
                                    v-if="selectedTemplate"
                                    ref="documentPreviewRef"
                                    :documentId="selectedTemplate.id"
                                    :placeholderValues="formValues"
                                    :title="'Vorschau: ' + selectedTemplate.name"
                                    :autoGenerate="false"
                                    :initialViewMode="previewMode"
                                    @preview-generated="onPreviewGenerated"
                                    @error="onPreviewError"
                                    @view-mode-change="handleViewModeChange"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <!-- History Tab -->
                <div v-if="activeTab === 'history'" class="history-tab">
                    <h3>Workflow-Verlauf</h3>
                    <div class="timeline">
                        <div v-for="event in workflowHistory" :key="event.id" class="timeline-item">
                            <div class="timeline-marker" :class="getEventTypeClass(event.type)"></div>
                            <div class="timeline-content">
                                <div class="event-header">
                                    <span class="event-title">{{ event.title }}</span>
                                    <span class="event-date">{{ formatDateTime(event.timestamp) }}</span>
                                </div>
                                <p class="event-description">{{ event.description }}</p>
                                <span class="event-user">{{ event.user }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- File Upload Modal -->
        <div v-if="showUploadModal" class="modal-overlay" @click="closeUploadModal">
            <div class="upload-modal" @click.stop>
                <div class="modal-header">
                    <h3>Dokument zu Workflow hinzufügen</h3>
                    <button @click="closeUploadModal" class="close-btn">×</button>
                </div>
                <div class="modal-body">
                    <div class="upload-area" 
                         @drop="handleFileDrop" 
                         @dragover.prevent="dragover = true" 
                         @dragleave.prevent="dragover = false"
                         :class="{ 'dragover': dragover }">
                        <div class="upload-icon">📁</div>
                        <p>Datei hier ablegen oder klicken zum Auswählen</p>
                        <input ref="fileUploadInput" type="file" accept=".pdf,.docx,.doc" @change="handleFileSelect" style="display: none">
                        <button @click="triggerFileInput" class="btn-select-file">Datei auswählen</button>
                    </div>
                    
                    <div v-if="uploadFile" class="upload-preview">
                        <div class="file-info">
                            <span class="file-name">{{ uploadFile.name }}</span>
                            <span class="file-size">{{ formatFileSize(uploadFile.size) }}</span>
                        </div>
                        <button @click="removeUploadFile" class="remove-file">×</button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button @click="closeUploadModal" class="btn-cancel">Abbrechen</button>
                    <button @click="startUpload" :disabled="!uploadFile" class="btn-upload">
                        Hochladen
                    </button>
                </div>
            </div>
        </div>

        <!-- Notification Snackbar -->
        <div v-if="notification.show" class="notification" :class="`notification--${notification.type}`">
            <span>{{ notification.message }}</span>
            <button @click="hideNotification" class="notification-close">×</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import store from '@/store/store'
import DynamicMask from '@/components/DynamicMask.vue'
import DocumentPreview from '@/components/DocumentPreview.vue'
import { DocumentAPI } from '@/services/api'

const router = useRouter()
const route = useRoute()

// Reactive data
const activeTab = ref('documents')
const dragover = ref(false)
const showUploadModal = ref(false)
const uploadFile = ref<File | null>(null)
const fileUploadInput = ref<HTMLInputElement>()

// Workflow data
const workflow = ref<any>(null)

// Document filling integration
const selectedTemplate = ref<any>(null)
const templates = ref<any[]>([])
const isLoadingTemplates = ref(false)
const formValues = ref<Record<string, any>>({})
const previewMode = ref('text')
const pdfLastGeneratedAt = ref<Date | null>(null)
const documentPreviewRef = ref<InstanceType<typeof DocumentPreview> | null>(null)

// Notification system
const notification = reactive({
    show: false,
    message: '',
    type: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Mock data
const workflowDocuments = ref([
    {
        id: 1,
        name: 'Jahresabschluss_2023.pdf',
        type: 'PDF',
        size: 2450000,
        uploadedAt: '2024-04-01',
        hasOriginalText: true,
        hasMaskedVersion: false
    },
    {
        id: 2,
        name: 'Bilanzdaten.docx',
        type: 'Word',
        size: 890000,
        uploadedAt: '2024-04-02',
        hasOriginalText: true,
        hasMaskedVersion: true
    },
    {
        id: 3,
        name: 'Kostenstellen_Q1.xlsx',
        type: 'Excel',
        size: 1200000,
        uploadedAt: '2024-04-03',
        hasOriginalText: false,
        hasMaskedVersion: false
    }
])

const workflowHistory = ref([
    {
        id: 1,
        type: 'created',
        title: 'Workflow erstellt',
        description: 'Workflow wurde von Dr. Schmidt erstellt',
        user: 'Dr. Schmidt',
        timestamp: '2024-04-01T09:00:00Z'
    },
    {
        id: 2,
        type: 'document_added',
        title: 'Dokument hinzugefügt',
        description: 'Jahresabschluss_2023.pdf wurde hochgeladen',
        user: 'Dr. Schmidt',
        timestamp: '2024-04-01T09:15:00Z'
    },
    {
        id: 3,
        type: 'status_changed',
        title: 'Status geändert',
        description: 'Status von "zu erledigen" zu "in Arbeit" geändert',
        user: 'Dr. Schmidt',
        timestamp: '2024-04-02T14:30:00Z'
    }
])

const tabs = [
    { id: 'documents', label: 'Dokumente', icon: 'icon-documents' },
    { id: 'filling', label: 'Dokument ausfüllen', icon: 'icon-edit' },
    { id: 'history', label: 'Verlauf', icon: 'icon-history' }
]

// Client management (from DocumentFillingView)
const clients = computed(() => {
    const storeClients = store.getters['client/getClients'];
    
    if (!storeClients || !Array.isArray(storeClients)) {
        return [];
    }
    
    return storeClients.map((client: any) => ({
        id: client.id,
        clientDisplayName: client.client_type === 'person' 
            ? `${client.first_name || ''} ${client.last_name || ''}`.trim() || client.email || `Person ${client.id}`
            : client.company_name || client.email || `Unternehmen ${client.id}`,
        client_type: client.client_type,
        ...client
    }));
});

// Group client fields by clientFieldGroup
const clientFieldGroups = computed(() => {
    if (!selectedTemplate.value?.placeholders) {
        return [];
    }
    
    const groups: Record<string, any[]> = {}
    
    selectedTemplate.value.placeholders.forEach((placeholder: any) => {
        if (placeholder?.isClientField && placeholder?.clientFieldGroup) {
            if (!groups[placeholder.clientFieldGroup]) {
                groups[placeholder.clientFieldGroup] = []
            }
            groups[placeholder.clientFieldGroup].push(placeholder)
        }
    })
    
    return Object.entries(groups).map(([groupName, fields]) => ({
        groupName,
        fields: fields || []
    }))
})

// Computed properties
const workflowId = computed(() => route.params.id)

// Methods
const goBack = () => {
    router.push('/dashboard')
}

const getStatusClass = (status: string) => {
    switch (status) {
        case 'zu erledigen': return 'status-todo'
        case 'in Arbeit': return 'status-in-progress'
        case 'abgeschlossen': return 'status-completed'
        default: return 'status-unknown'
    }
}

const getPriorityClass = (priority: string) => {
    switch (priority) {
        case 'Hoch': return 'priority-high'
        case 'Mittel': return 'priority-medium'
        case 'Niedrig': return 'priority-low'
        default: return 'priority-medium'
    }
}

const formatDate = (dateString: string) => {
    if (!dateString) return 'Nicht festgelegt'
    const date = new Date(dateString)
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}

const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const isOverdue = (dueDateString: string) => {
    if (!dueDateString) return false
    const dueDate = new Date(dueDateString)
    const today = new Date()
    return dueDate < today
}

const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getDocumentIcon = (type: string) => {
    switch (type.toLowerCase()) {
        case 'pdf': return 'icon-pdf'
        case 'word': return 'icon-word'
        case 'excel': return 'icon-excel'
        default: return 'icon-document'
    }
}

const getEventTypeClass = (type: string) => {
    switch (type) {
        case 'created': return 'event-created'
        case 'document_added': return 'event-document'
        case 'status_changed': return 'event-status'
        default: return 'event-default'
    }
}

// Workflow actions
const changeStatus = () => {
    // TODO: Implement status change dialog
}

const assignWorkflow = () => {
    // TODO: Implement assignment dialog
}

// Document actions
const viewOriginalText = (document: any) => {
    selectedTemplate.value = document
    activeTab.value = 'filling'
    // Load original text
    loadOriginalText(document)
}

const editMaskedDocument = (document: any) => {
    selectedTemplate.value = document
    activeTab.value = 'filling'
    loadMaskedText(document)
}

const loadOriginalText = (document: any) => {
    // Mock loading original text
    formValues.value = {
        // Populate formValues with document-specific data
    }
}

const loadMaskedText = (document: any) => {
    // Mock loading masked text
    formValues.value = {
        // Populate formValues with masked data
    }
}

// Document filling actions
const selectTemplate = (template: any) => {
    selectedTemplate.value = template
    
    // Initialize form values with default values (only for non-client fields)
    const initialValues: Record<string, any> = {}
    
    if (template.placeholders) {
        template.placeholders.forEach((placeholder: any) => {
            if (!placeholder.isClientField && placeholder.defaultValue !== undefined) {
                initialValues[placeholder.name] = placeholder.defaultValue
            }
        })
    }
    
    formValues.value = initialValues
    showNotification(`Template "${template.name}" ausgewählt`, 'success')
}

const goBackToTemplateSelection = () => {
    selectedTemplate.value = null
    formValues.value = {}
    pdfLastGeneratedAt.value = null
}

const goToCreation = () => {
    router.push('/documents/creation')
}

const generateDocument = async (values?: Record<string, any>) => {
    if (!selectedTemplate.value) {
        showNotification('Kein Template ausgewählt', 'error')
        return
    }
    
    // If values are provided (from form submission), update formValues first
    if (values) {
        Object.keys(values).forEach(key => {
            if (values[key] !== undefined) {
                formValues.value[key] = values[key]
            }
        })
        
        // Trigger reactivity
        formValues.value = { ...formValues.value }
    }
    
    if (Object.keys(formValues.value).length === 0) {
        showNotification('Bitte füllen Sie mindestens ein Feld aus', 'warning')
        return
    }
    
    // Validate required fields
    const missingRequired = selectedTemplate.value.placeholders
        ?.filter((p: any) => {
            if (!p.required) return false;
            
            // For client fields, check if we have a value
            if (p.isClientField) {
                return !formValues.value[p.name] || formValues.value[p.name] === '';
            }
            
            // For regular fields
            return !formValues.value[p.name] && formValues.value[p.name] !== 0 && formValues.value[p.name] !== false;
        })
        .map((p: any) => p.name) || []
    
    if (missingRequired.length > 0) {
        showNotification(`Bitte füllen Sie alle erforderlichen Felder aus: ${missingRequired.join(', ')}`, 'warning')
        return
    }
    
    if (documentPreviewRef.value) {
        await documentPreviewRef.value.generatePreview()
        pdfLastGeneratedAt.value = new Date()
    }
}

const onPreviewGenerated = (previewData: any) => {
    pdfLastGeneratedAt.value = new Date()
    showNotification('Vorschau erfolgreich generiert', 'success')
}

const onPreviewError = (errorMessage: string) => {
    showNotification(`Fehler bei der Vorschau-Generierung: ${errorMessage}`, 'error')
}

const handleViewModeChange = (newMode: string) => {
    previewMode.value = newMode;
}

const updateFormValues = (values: Record<string, any>) => {
    if (!values || typeof values !== 'object') {
        return;
    }
    
    // Check if values actually changed to avoid unnecessary updates
    let hasChanges = false;
    Object.keys(values).forEach(key => {
        if (values[key] !== undefined && formValues.value[key] !== values[key]) {
            hasChanges = true;
        }
    });
    
    if (!hasChanges) {
        return;
    }
    
    // Update formValues with new values
    Object.keys(values).forEach(key => {
        if (values[key] !== undefined) {
            formValues.value[key] = values[key];
        }
    });
    
    // Trigger reactivity
    formValues.value = { ...formValues.value };
}

const onClientSelected = (groupName: string, clientId: number | null) => {
    if (!clientId) {
        // Clear client field values for this group
        clientFieldGroups.value.forEach(group => {
            if (group.groupName === groupName) {
                group.fields.forEach((field: any) => {
                    if (formValues.value[field.name] !== undefined) {
                        delete formValues.value[field.name];
                    }
                });
            }
        });
        // Update values to trigger reactivity
        formValues.value = { ...formValues.value };
        return;
    }
    
    // Find the selected client
    const selectedClient = clients.value.find(client => client.id === clientId);
    
    if (!selectedClient) {
        console.warn('Client not found:', clientId);
        return;
    }
    
    // Fill client field values for this group
    const groupFields = clientFieldGroups.value.find(group => group.groupName === groupName);
    
    if (groupFields) {
        groupFields.fields.forEach((field: any) => {
            if (field.isClientField && field.clientFieldName) {
                let value = selectedClient[field.clientFieldName as keyof typeof selectedClient];
                
                // Format value based on field type
                if (value !== undefined && value !== null) {
                    switch (field.type) {
                        case 'date':
                            if (value instanceof Date) {
                                const year = value.getFullYear();
                                const month = String(value.getMonth() + 1).padStart(2, '0');
                                const day = String(value.getDate()).padStart(2, '0');
                                value = `${year}-${month}-${day}`;
                            } else if (typeof value === 'string') {
                                const dateMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
                                if (dateMatch) {
                                    value = `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`;
                                } else {
                                    const date = new Date(value);
                                    if (!isNaN(date.getTime())) {
                                        const year = date.getFullYear();
                                        const month = String(date.getMonth() + 1).padStart(2, '0');
                                        const day = String(date.getDate()).padStart(2, '0');
                                        value = `${year}-${month}-${day}`;
                                    }
                                }
                            }
                            break;
                        case 'number':
                            value = Number(value);
                            break;
                        case 'checkbox':
                            value = Boolean(value);
                            break;
                        default:
                            value = String(value);
                    }
                    
                    // Set the value
                    formValues.value[field.name] = value;
                } else {
                    // Clear the field if no value found
                    if (formValues.value[field.name] !== undefined) {
                        delete formValues.value[field.name];
                    }
                }
            }
        });
        
        // Update values to trigger reactivity
        formValues.value = { ...formValues.value };
        
        // Show notification
        const groupDisplayName = formatGroupName(groupName);
        showNotification(`Mandanten-Felder für ${groupDisplayName} wurden automatisch ausgefüllt`, 'success');
    }
};

const formatGroupName = (groupName: string): string => {
    return groupName
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

const formatTimestamp = (date: Date) => {
    if (!date) return '';
    
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    
    return `${hours}:${minutes}:${seconds}`;
}

const showNotification = (message: string, type: 'success' | 'error' | 'warning' | 'info') => {
    notification.message = message
    notification.type = type
    notification.show = true
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.show = false
    }, 3000)
}

const hideNotification = () => {
    notification.show = false
}

// Load templates when needed
const loadTemplates = async () => {
    try {
        isLoadingTemplates.value = true
        const response = await DocumentAPI.getTemplates()
        templates.value = response.data || []
        
        if (templates.value.length === 0) {
            showNotification('Keine Templates gefunden', 'info')
        }
    } catch (error) {
        console.error('Error loading templates:', error)
        showNotification('Fehler beim Laden der Templates', 'error')
        templates.value = []
    } finally {
        isLoadingTemplates.value = false
    }
}

const loadWorkflowData = async () => {
    // Mock workflow data - in real app, fetch from API
    workflow.value = {
        id: workflowId.value,
        name: 'Jahresabschluss 2023',
        status: 'in Arbeit',
        client: 'Max Mustermann GmbH',
        assignedTo: 'Dr. Schmidt',
        createdAt: '2024-04-01',
        dueDate: '2024-04-15',
        documentCount: 3,
        priority: 'Hoch',
        description: 'Erstellung des Jahresabschlusses für das Geschäftsjahr 2023 inklusive Bilanz, GuV und Anhang.'
    }
}

onMounted(async () => {
    await loadWorkflowData()
    await loadTemplates()
    
    // Load clients for client field support
    try {
        if (store && store.dispatch) {
            await store.dispatch('client/fetchClients');
        }
    } catch (error) {
        console.warn('Error fetching clients:', error);
    }
})

// File upload
const uploadNewDocument = () => {
    showUploadModal.value = true
}

const closeUploadModal = () => {
    showUploadModal.value = false
    uploadFile.value = null
    dragover.value = false
}

const triggerFileInput = () => {
    fileUploadInput.value?.click()
}

const handleFileDrop = (e: DragEvent) => {
    e.preventDefault()
    dragover.value = false
    const files = e.dataTransfer?.files
    if (files && files.length > 0) {
        uploadFile.value = files[0]
    }
}

const handleFileSelect = (e: Event) => {
    const target = e.target as HTMLInputElement
    const files = target.files
    if (files && files.length > 0) {
        uploadFile.value = files[0]
    }
}

const removeUploadFile = () => {
    uploadFile.value = null
}

const startUpload = async () => {
    if (!uploadFile.value) return
    
    // TODO: Implement actual upload
    
    // Mock adding to documents list
    workflowDocuments.value.push({
        id: Date.now(),
        name: uploadFile.value.name,
        type: uploadFile.value.type.includes('pdf') ? 'PDF' : 'Word',
        size: uploadFile.value.size,
        uploadedAt: new Date().toISOString().split('T')[0],
        hasOriginalText: false,
        hasMaskedVersion: false
    })
    
    closeUploadModal()
}
</script>

<style scoped>
.workflow-detail-container {
    min-height: 100vh;
    background-color: #f8f9fa;
    padding: 1rem;
}

.workflow-header {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.header-left {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.back-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: 1px solid #ddd;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    color: #6c757d;
    align-self: flex-start;
}

.back-btn:hover {
    background-color: #f8f9fa;
}

.workflow-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.workflow-info h1 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.8rem;
    font-weight: 600;
}

.status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
    text-transform: uppercase;
}

.status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.status-todo {
    background-color: #fff3cd;
    color: #856404;
}

.status-todo .status-indicator {
    background-color: #ffc107;
}

.status-in-progress {
    background-color: #d1ecf1;
    color: #0c5460;
}

.status-in-progress .status-indicator {
    background-color: #17a2b8;
}

.status-completed {
    background-color: #d4edda;
    color: #155724;
}

.status-completed .status-indicator {
    background-color: #28a745;
}

.header-actions {
    display: flex;
    gap: 1rem;
}

.btn-status,
.btn-assign {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}

.btn-status {
    background-color: #17a2b8;
    color: white;
}

.btn-assign {
    background-color: #28a745;
    color: white;
}

.metadata-section {
    margin-bottom: 2rem;
}

.metadata-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.metadata-card h3 {
    margin: 0 0 1.5rem 0;
    color: #2c3e50;
    font-size: 1.3rem;
}

.metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.metadata-item {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.metadata-item .label {
    color: #6c757d;
    font-weight: 500;
}

.metadata-item .value {
    color: #495057;
    font-weight: 600;
}

.metadata-item .value.overdue {
    color: #dc3545;
}

.metadata-item .value.priority.priority-high {
    color: #dc3545;
}

.metadata-item .value.priority.priority-medium {
    color: #ffc107;
}

.metadata-item .value.priority.priority-low {
    color: #17a2b8;
}

.description-section h4 {
    margin: 0 0 0.5rem 0;
    color: #495057;
}

.description-section p {
    margin: 0;
    color: #6c757d;
    line-height: 1.5;
}

.main-content {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.content-tabs {
    display: flex;
    border-bottom: 1px solid #e9ecef;
}

.tab-button {
    flex: 1;
    padding: 1rem 1.5rem;
    border: none;
    background: none;
    cursor: pointer;
    color: #6c757d;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
}

.tab-button:hover {
    background-color: #f8f9fa;
}

.tab-button.active {
    background-color: #4CAF50;
    color: white;
    border-bottom: 3px solid #45a049;
}

.tab-content {
    padding: 2rem;
}

.documents-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.documents-header h3 {
    margin: 0;
    color: #2c3e50;
}

.btn-upload {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}

.documents-list {
    display: grid;
    gap: 1rem;
}

.document-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.document-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.document-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.document-icon {
    font-size: 2rem;
}

.document-details h4 {
    margin: 0 0 0.25rem 0;
    color: #2c3e50;
}

.document-details p {
    margin: 0 0 0.25rem 0;
    color: #6c757d;
    font-size: 0.9rem;
}

.upload-date {
    font-size: 0.8rem;
    color: #9ca3af;
}

.document-actions {
    display: flex;
    gap: 0.5rem;
}

.btn-view,
.btn-edit {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
}

.btn-view {
    background-color: #17a2b8;
    color: white;
}

.btn-edit {
    background-color: #28a745;
    color: white;
}

.filling-tab {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.template-selection-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.section-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.section-header h3 {
    margin: 0;
    color: #2c3e50;
}

.section-header p {
    margin: 0;
    color: #6c757d;
}

.templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
}

.template-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.5rem;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.template-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.template-icon {
    font-size: 2rem;
}

.template-details {
    text-align: center;
}

.template-details h4 {
    margin: 0 0 0.25rem 0;
    color: #2c3e50;
}

.template-details p {
    margin: 0;
    color: #6c757d;
    font-size: 0.9rem;
}

.template-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
}

.field-count {
    color: #6c757d;
    font-size: 0.9rem;
}

.template-date {
    color: #9ca3af;
    font-size: 0.9rem;
}

.btn-select {
    background-color: #28a745;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}

.empty-templates {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
}

.empty-templates i {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.empty-templates h4 {
    margin: 0 0 0.5rem 0;
    color: #2c3e50;
}

.empty-templates p {
    margin: 0;
    color: #6c757d;
}

.btn-create {
    background-color: #28a745;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
}

.filling-interface {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.template-info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e9ecef;
}

.back-to-templates {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6c757d;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.selected-template-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.template-details {
    display: flex;
    flex-direction: column;
}

.template-details h3 {
    margin: 0 0 0.25rem 0;
    color: #2c3e50;
}

.template-details p {
    margin: 0;
    color: #6c757d;
    font-size: 0.9rem;
}

.template-stats {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.document-workspace {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.form-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.section-title h4 {
    margin: 0;
    color: #2c3e50;
}

.form-content {
    padding: 1rem;
}

.preview-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
}

.section-title h4 {
    margin: 0;
    color: #2c3e50;
}

.pdf-timestamp {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 0.5rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.timestamp-label {
    color: #6c757d;
    font-size: 0.9rem;
}

.timeline {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.timeline-item {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

.timeline-marker {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 0.5rem;
    flex-shrink: 0;
}

.event-created {
    background-color: #28a745;
}

.event-document {
    background-color: #17a2b8;
}

.event-status {
    background-color: #ffc107;
}

.event-default {
    background-color: #6c757d;
}

.timeline-content {
    flex: 1;
}

.event-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.event-title {
    font-weight: 600;
    color: #2c3e50;
}

.event-date {
    font-size: 0.9rem;
    color: #6c757d;
}

.event-description {
    margin: 0 0 0.5rem 0;
    color: #495057;
    line-height: 1.4;
}

.event-user {
    font-size: 0.9rem;
    color: #6c757d;
    font-style: italic;
}

/* Modal Styles */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.upload-modal {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
    margin: 0;
    color: #2c3e50;
}

.close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6c757d;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-body {
    padding: 1.5rem;
}

.upload-area {
    border: 2px dashed #ddd;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.upload-area.dragover {
    border-color: #4CAF50;
    background-color: #f8fff8;
}

.upload-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.btn-select-file {
    background-color: #f8f9fa;
    color: #495057;
    border: 1px solid #ced4da;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 1rem;
}

.upload-preview {
    margin-top: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.file-info {
    display: flex;
    flex-direction: column;
}

.file-name {
    font-weight: 500;
    color: #495057;
}

.file-size {
    color: #6c757d;
    font-size: 0.9rem;
}

.remove-file {
    background: none;
    border: none;
    color: #dc3545;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0;
    width: 25px;
    height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    padding: 1.5rem;
    border-top: 1px solid #e9ecef;
}

.btn-cancel {
    background-color: #6c757d;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
}

.btn-upload:disabled {
    background-color: #6c757d;
    cursor: not-allowed;
}

@media (max-width: 768px) {
    .workflow-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .metadata-grid {
        grid-template-columns: 1fr;
    }
    
    .filling-interface {
        grid-template-columns: 1fr;
    }
    
    .content-tabs {
        flex-direction: column;
    }
    
    .document-card {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .document-actions {
        width: 100%;
        justify-content: flex-end;
    }
}

/* Custom scrollbar for form section */
.form-card .v-card-text::-webkit-scrollbar {
    width: 6px;
}

.form-card .v-card-text::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.form-card .v-card-text::-webkit-scrollbar-thumb {
    background: #c2a47b;
    border-radius: 3px;
}

.form-card .v-card-text::-webkit-scrollbar-thumb:hover {
    background: #a08660;
}

/* Loading spinner */
.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    color: #6c757d;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #4CAF50;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Notification styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    z-index: 1000;
    min-width: 300px;
    animation: slideIn 0.3s ease;
}

.notification--success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.notification--error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.notification--warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.notification--info {
    background-color: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

.notification-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: inherit;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* No fields state */
.no-fields {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 2rem;
    color: #6c757d;
    text-align: center;
}

.no-fields i {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.no-fields p {
    margin: 0;
    font-size: 1rem;
}

@media (max-width: 768px) {
    .workflow-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .metadata-grid {
        grid-template-columns: 1fr;
    }
    
    .document-workspace {
        flex-direction: column;
    }
    
    .content-tabs {
        flex-direction: column;
    }
    
    .document-card {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .document-actions {
        width: 100%;
        justify-content: flex-end;
    }
    
    .templates-grid {
        grid-template-columns: 1fr;
    }
    
    .template-info-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .notification {
        left: 20px;
        right: 20px;
        min-width: auto;
    }
}
</style> 