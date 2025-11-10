<template>
    <div class="workflow-document-viewer">
        <!-- Header with workflow info and AI controls -->
        <v-card class="header-card mb-4">
            <v-card-title class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                    <v-icon color="brown" class="mr-3">mdi-file-document-multiple</v-icon>
                    <div>
                        <h3>Workflow-Dokumente</h3>
                        <div class="text-subtitle-2 text-grey-600">
                            {{ documents.length }} Dokument(e) verfügbar
                        </div>
                    </div>
                </div>
                <div class="d-flex align-center gap-2">
                    <v-btn 
                        color="primary" 
                        variant="outlined" 
                        @click="loadDocumentsSummary"
                        :loading="loadingSummary"
                        prepend-icon="mdi-robot"
                    >
                        KI-Zusammenfassung
                    </v-btn>
                    <v-btn 
                        color="success" 
                        @click="startAIExtraction"
                        :disabled="!selectedTemplate || documents.length === 0"
                        :loading="extractingFields"
                        prepend-icon="mdi-magic-staff"
                    >
                        KI-Extraktion
                    </v-btn>
                </div>
            </v-card-title>
        </v-card>

        <!-- AI Summary Section -->
        <v-card v-if="documentsSummary" class="summary-card mb-4">
            <v-card-title class="d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-robot</v-icon>
                KI-Dokumentzusammenfassung
                <v-chip 
                    v-if="documentsSummary.confidence" 
                    :color="getSummaryConfidenceColor(documentsSummary.confidence)"
                    size="small"
                    class="ml-2"
                >
                    {{ Math.round(documentsSummary.confidence * 100) }}% Vertrauen
                </v-chip>
            </v-card-title>
            <v-card-text>
                <div class="summary-content">
                    {{ documentsSummary.summary }}
                </div>
                <div v-if="documentsSummary.document_summaries" class="mt-3">
                    <v-expansion-panels variant="accordion">
                        <v-expansion-panel 
                            v-for="docSum in documentsSummary.document_summaries" 
                            :key="docSum.name"
                        >
                            <v-expansion-panel-title>
                                <v-icon class="mr-2">mdi-file-document</v-icon>
                                {{ docSum.name }}
                                <v-spacer></v-spacer>
                                <v-chip size="small" color="grey-lighten-1">
                                    {{ docSum.word_count }} Wörter
                                </v-chip>
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                {{ docSum.summary }}
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                </div>
            </v-card-text>
        </v-card>

        <!-- Template Selection for AI Extraction -->
        <v-card v-if="showTemplateSelection" class="template-selection-card mb-4">
            <v-card-title>
                <v-icon color="brown" class="mr-2">mdi-form-select</v-icon>
                Template für KI-Extraktion wählen
            </v-card-title>
            <v-card-text>
                <v-select
                    v-model="selectedTemplate"
                    :items="templates"
                    item-title="name"
                    item-value="id"
                    label="Ziel-Template auswählen"
                    placeholder="Wählen Sie ein Template für die Feldextraktion"
                    prepend-icon="mdi-file-document-edit"
                    variant="outlined"
                    @update:model-value="onTemplateSelected"
                >
                    <template v-slot:item="{ props, item }">
                        <v-list-item v-bind="props">
                            <template v-slot:prepend>
                                <v-icon>mdi-file-document</v-icon>
                            </template>
                            <v-list-item-title>{{ item.raw.name }}</v-list-item-title>
                            <v-list-item-subtitle v-if="item.raw.description">
                                {{ item.raw.description }}
                            </v-list-item-subtitle>
                        </v-list-item>
                    </template>
                </v-select>
                <div v-if="selectedTemplate" class="mt-3">
                    <v-chip-group>
                        <v-chip 
                            v-for="placeholder in getTemplateNonClientFields()" 
                            :key="placeholder.name"
                            size="small"
                            :color="placeholder.required ? 'orange' : 'grey-lighten-1'"
                        >
                            {{ placeholder.name }}
                            <v-tooltip activator="parent" location="top">
                                {{ placeholder.type }} {{ placeholder.required ? '(Erforderlich)' : '' }}
                            </v-tooltip>
                        </v-chip>
                    </v-chip-group>
                </div>
            </v-card-text>
        </v-card>

        <!-- AI Extraction Results -->
        <v-card v-if="extractionResults" class="extraction-results-card mb-4">
            <v-card-title class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                    <v-icon color="success" class="mr-2">mdi-magic-staff</v-icon>
                    KI-Extraktionsergebnisse
                    <v-chip 
                        :color="getExtractionConfidenceColor(extractionResults.confidence)"
                        size="small"
                        class="ml-2"
                    >
                        {{ Math.round(extractionResults.confidence * 100) }}% Vertrauen
                    </v-chip>
                </div>
                <v-btn
                    color="primary"
                    @click="applyExtractedValues"
                    :disabled="!extractionResults.extracted_values || Object.keys(extractionResults.extracted_values).length === 0"
                    prepend-icon="mdi-check"
                >
                    Werte übernehmen
                </v-btn>
            </v-card-title>
            <v-card-text>
                <div v-if="extractionResults.notes" class="mb-3">
                    <v-alert type="info" variant="tonal">
                        <strong>KI-Hinweise:</strong> {{ extractionResults.notes }}
                    </v-alert>
                </div>
                
                <div v-if="Object.keys(extractionResults.extracted_values).length > 0" class="extracted-fields">
                    <h4 class="mb-3">Extrahierte Felder:</h4>
                    <v-row>
                        <v-col 
                            v-for="(value, fieldName) in extractionResults.extracted_values" 
                            :key="fieldName"
                            cols="12" 
                            md="6"
                        >
                            <v-card variant="outlined" class="field-card">
                                <v-card-text>
                                    <div class="field-label">{{ fieldName }}</div>
                                    <div class="field-value">{{ formatFieldValue(value) }}</div>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </div>
                
                <div v-else>
                    <v-alert type="warning" variant="tonal">
                        Keine Werte konnten automatisch extrahiert werden. 
                        Bitte überprüfen Sie die Dokumente und Template-Felder.
                    </v-alert>
                </div>

                <div v-if="extractionResults.processed_documents" class="mt-4">
                    <h4 class="mb-2">Verarbeitete Dokumente:</h4>
                    <v-chip-group>
                        <v-chip 
                            v-for="doc in extractionResults.processed_documents" 
                            :key="doc.id"
                            size="small"
                        >
                            {{ doc.name }}
                            <v-tooltip activator="parent" location="top">
                                {{ doc.text_length }} Zeichen extrahiert
                            </v-tooltip>
                        </v-chip>
                    </v-chip-group>
                </div>

                <div v-if="extractionResults.errors && extractionResults.errors.length > 0" class="mt-3">
                    <v-alert type="error" variant="tonal">
                        <strong>Fehler bei der Extraktion:</strong>
                        <ul class="mt-2">
                            <li v-for="error in extractionResults.errors" :key="error">{{ error }}</li>
                        </ul>
                    </v-alert>
                </div>
            </v-card-text>
        </v-card>

        <!-- Documents Grid -->
        <v-card class="documents-grid-card">
            <v-card-title class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                    <v-icon color="brown" class="mr-2">mdi-view-grid</v-icon>
                    Dokumente
                </div>
                <v-btn 
                    color="primary" 
                    variant="outlined" 
                    @click="uploadNewDocument"
                    prepend-icon="mdi-plus"
                >
                    Dokument hinzufügen
                </v-btn>
            </v-card-title>
            <v-card-text>
                <div v-if="isLoading" class="loading-state text-center py-8">
                    <v-progress-circular indeterminate color="brown" size="64"></v-progress-circular>
                    <p class="mt-4">Dokumente werden geladen...</p>
                </div>

                <div v-else-if="documents.length === 0" class="empty-state text-center py-8">
                    <v-icon size="64" color="grey-lighten-1">mdi-file-document-plus</v-icon>
                    <h3 class="mt-4 mb-2">Keine Dokumente vorhanden</h3>
                    <p class="mb-4">Fügen Sie Dokumente zu diesem Workflow hinzu.</p>
                    <v-btn color="primary" @click="uploadNewDocument" prepend-icon="mdi-plus">
                        Erstes Dokument hinzufügen
                    </v-btn>
                </div>

                <v-row v-else>
                    <v-col 
                        v-for="document in documents" 
                        :key="document.id"
                        cols="12" 
                        sm="6" 
                        md="4"
                    >
                        <v-card class="document-card" elevation="2" @click="viewDocument(document)">
                            <v-card-text>
                                <div class="d-flex align-center mb-3">
                                    <v-icon :color="getDocumentIconColor(document.file_type)" size="32" class="mr-3">
                                        {{ getDocumentIcon(document.file_type) }}
                                    </v-icon>
                                    <div class="flex-grow-1 min-width-0">
                                        <div class="document-name text-truncate" :title="document.name">
                                            {{ document.name }}
                                        </div>
                                        <div class="document-meta text-caption text-grey-600">
                                            {{ formatFileSize(document.file_size) }} • 
                                            {{ formatDate(document.created_at) }}
                                        </div>
                                    </div>
                                </div>
                                
                                <v-chip 
                                    :color="getStatusColor(document.status)" 
                                    size="small" 
                                    class="mb-2"
                                >
                                    {{ document.status }}
                                </v-chip>
                            </v-card-text>
                            
                            <v-card-actions>
                                <v-btn 
                                    size="small" 
                                    variant="text" 
                                    @click.stop="viewDocument(document)"
                                    prepend-icon="mdi-eye"
                                >
                                    Anzeigen
                                </v-btn>
                                <v-btn 
                                    size="small" 
                                    variant="text" 
                                    @click.stop="downloadDocument(document)"
                                    prepend-icon="mdi-download"
                                >
                                    Download
                                </v-btn>
                                <v-spacer></v-spacer>
                                <v-btn 
                                    size="small" 
                                    variant="text" 
                                    color="error"
                                    @click.stop="deleteDocument(document)"
                                    icon="mdi-delete"
                                >
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-col>
                </v-row>
            </v-card-text>
        </v-card>

        <!-- Success/Error Snackbar -->
        <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
            {{ snackbar.text }}
            <template v-slot:actions>
                <v-btn variant="text" @click="snackbar.show = false">Schließen</v-btn>
            </template>
        </v-snackbar>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { WorkflowAPI, DocumentAPI } from '@/services/api'

// Props
interface Props {
    workflowId: number
    templates?: Array<any>
    autoLoadSummary?: boolean
}

const props = withDefaults(defineProps<Props>(), {
    templates: () => ([]),
    autoLoadSummary: false
})

// Emits
const emit = defineEmits<{
    'document-uploaded': []
    'document-deleted': [documentId: number]
    'document-viewed': [document: any]
    'fields-extracted': [values: Record<string, any>]
}>()

// Reactive data
const isLoading = ref(false)
const loadingSummary = ref(false)
const extractingFields = ref(false)
const documents = ref<any[]>([])
const documentsSummary = ref<any>(null)
const extractionResults = ref<any>(null)
const selectedTemplate = ref<number | null>(null)
const showTemplateSelection = ref(false)

const snackbar = reactive({
    show: false,
    text: '',
    color: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Load documents on mount
onMounted(async () => {
    await loadDocuments()
    if (props.autoLoadSummary) {
        await loadDocumentsSummary()
    }
})

// Watch for workflow changes
watch(() => props.workflowId, async () => {
    await loadDocuments()
    documentsSummary.value = null
    extractionResults.value = null
})

// Load workflow documents
const loadDocuments = async () => {
    try {
        isLoading.value = true
        const response = await WorkflowAPI.getWorkflowDocuments(props.workflowId)
        documents.value = response.data || []
    } catch (error) {
        console.error('Error loading documents:', error)
        showNotification('Fehler beim Laden der Dokumente', 'error')
        documents.value = []
    } finally {
        isLoading.value = false
    }
}

// Load AI summary of documents
const loadDocumentsSummary = async () => {
    try {
        loadingSummary.value = true
        const response = await WorkflowAPI.getWorkflowDocumentsSummary(props.workflowId)
        documentsSummary.value = response.data
        showNotification('KI-Zusammenfassung erstellt', 'success')
    } catch (error) {
        console.error('Error loading documents summary:', error)
        showNotification('Fehler bei der KI-Zusammenfassung', 'error')
    } finally {
        loadingSummary.value = false
    }
}

// Start AI extraction process
const startAIExtraction = () => {
    if (!selectedTemplate.value) {
        showTemplateSelection.value = true
        showNotification('Bitte wählen Sie zuerst ein Template aus', 'warning')
        return
    }
    performExtraction()
}

// Perform the actual AI extraction
const performExtraction = async () => {
    if (!selectedTemplate.value) return
    
    try {
        extractingFields.value = true
        const response = await WorkflowAPI.extractFieldsFromDocuments(
            props.workflowId, 
            selectedTemplate.value
        )
        
        extractionResults.value = response.data
        
        if (response.data.extracted_values && Object.keys(response.data.extracted_values).length > 0) {
            showNotification(
                `${Object.keys(response.data.extracted_values).length} Felder erfolgreich extrahiert!`, 
                'success'
            )
        } else {
            showNotification('Keine Felder konnten extrahiert werden', 'warning')
        }
        
    } catch (error) {
        console.error('Error extracting fields:', error)
        showNotification('Fehler bei der KI-Extraktion', 'error')
    } finally {
        extractingFields.value = false
    }
}

// Template selection handler
const onTemplateSelected = (templateId: number) => {
    selectedTemplate.value = templateId
    showTemplateSelection.value = false
}

// Get non-client fields from selected template
const getTemplateNonClientFields = () => {
    if (!selectedTemplate.value || !props.templates) return []
    
    const template = props.templates.find(t => t.id === selectedTemplate.value)
    if (!template?.placeholders) return []
    
    return template.placeholders.filter((p: any) => !p.isClientField)
}

// Apply extracted values to form
const applyExtractedValues = () => {
    if (extractionResults.value?.extracted_values) {
        emit('fields-extracted', extractionResults.value.extracted_values)
        showNotification('Extrahierte Werte wurden übernommen', 'success')
    }
}

// Document actions
const viewDocument = (document: any) => {
    emit('document-viewed', document)
}

const downloadDocument = async (document: any) => {
    try {
        const response = await WorkflowAPI.getWorkflowDocumentFile(props.workflowId, document.id)
        const blob = response.data
        
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = document.name || document.file_name || 'document'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
        showNotification('Download gestartet', 'success')
    } catch (error) {
        console.error('Error downloading document:', error)
        showNotification('Fehler beim Download', 'error')
    }
}

const deleteDocument = async (document: any) => {
    if (!confirm(`Dokument "${document.name}" wirklich löschen?`)) return
    
    try {
        await WorkflowAPI.deleteWorkflowDocument(props.workflowId, document.id)
        await loadDocuments()
        emit('document-deleted', document.id)
        showNotification('Dokument gelöscht', 'success')
    } catch (error) {
        console.error('Error deleting document:', error)
        showNotification('Fehler beim Löschen', 'error')
    }
}

const uploadNewDocument = () => {
    // This would typically open a file upload dialog
    // For now, we'll emit an event to let the parent handle it
    emit('document-uploaded')
}

// Utility functions
const showNotification = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
    snackbar.text = text
    snackbar.color = color
    snackbar.show = true
}

const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('de-DE')
}

const formatFieldValue = (value: any) => {
    if (value === null || value === undefined) return 'Kein Wert'
    if (typeof value === 'boolean') return value ? 'Ja' : 'Nein'
    if (typeof value === 'number') return value.toLocaleString('de-DE')
    return String(value)
}

const getFieldType = (fieldName: string) => {
    if (!selectedTemplate.value || !props.templates) return 'text'
    
    const template = props.templates.find(t => t.id === selectedTemplate.value)
    const field = template?.placeholders?.find((p: any) => p.name === fieldName)
    return field?.type || 'text'
}

const getDocumentIcon = (fileType: string) => {
    if (fileType?.includes('pdf')) return 'mdi-file-pdf-box'
    if (fileType?.includes('word') || fileType?.includes('document')) return 'mdi-file-word-box'
    if (fileType?.includes('excel') || fileType?.includes('spreadsheet')) return 'mdi-file-excel-box'
    return 'mdi-file-document'
}

const getDocumentIconColor = (fileType: string) => {
    if (fileType?.includes('pdf')) return 'red'
    if (fileType?.includes('word') || fileType?.includes('document')) return 'blue'
    if (fileType?.includes('excel') || fileType?.includes('spreadsheet')) return 'green'
    return 'grey'
}

const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
        case 'uploaded': return 'success'
        case 'processing': return 'warning'
        case 'error': return 'error'
        default: return 'grey'
    }
}

const getSummaryConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.5) return 'warning'
    return 'error'
}

const getExtractionConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.6) return 'warning'
    return 'error'
}
</script>

<style scoped>
.workflow-document-viewer {
    max-width: 100%;
}

.header-card {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.summary-card, 
.template-selection-card, 
.extraction-results-card,
.documents-grid-card {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.summary-content {
    font-size: 1rem;
    line-height: 1.5;
    color: #2c3e50;
    white-space: pre-line;
}

.document-card {
    border-radius: 12px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
    height: 100%;
}

.document-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.document-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #2c3e50;
}

.document-meta {
    margin-top: 4px;
}

.field-card {
    border-radius: 8px;
    height: 100%;
}

.field-label {
    font-weight: 600;
    color: #4a3528;
    font-size: 0.875rem;
    margin-bottom: 4px;
}

.field-value {
    font-size: 1rem;
    color: #2c3e50;
    margin-bottom: 4px;
    word-break: break-word;
}

.field-type {
    font-size: 0.75rem;
    color: #6b5d4f;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.extracted-fields {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.empty-state, 
.loading-state {
    color: #6b5d4f;
}

.gap-2 {
    gap: 8px;
}

/* Responsive design */
@media (max-width: 768px) {
    .document-card {
        margin-bottom: 1rem;
    }
    
    .extracted-fields {
        padding: 12px;
    }
    
    .header-card .v-card-title {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
}
</style> 