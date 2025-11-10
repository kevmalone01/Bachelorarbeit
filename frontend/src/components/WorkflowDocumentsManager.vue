<template>
    <div class="workflow-documents-manager">
        <!-- Header (optional, controlled by showHeader prop) -->
        <div v-if="showHeader" class="d-flex justify-space-between align-center w-100 mb-4 mt-4 pa-8">
            <v-btn 
                color="brown" 
                variant="outlined" 
                @click="handleBack"
                class="mr-4"
            >
                <v-icon class="mr-1">mdi-arrow-left</v-icon>
                Zurück zum Dashboard
            </v-btn>
            <v-btn 
                @click="uploadAdditionalDocuments" 
                variant="outlined"
                prepend-icon="mdi-plus"
                class="action-btn"
            >
                Dokumente hinzufügen
            </v-btn>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="loading-state text-center py-16">
            <v-progress-circular 
                indeterminate 
                color="brown" 
                size="64"
                class="mb-4"
            />
            <h3 class="loading-title mb-3">Dokumente werden geladen...</h3>
            <p class="loading-subtitle">Bitte warten Sie einen Moment.</p>
        </div>

        <!-- Documents Grid -->
        <div v-else-if="documents.length > 0" class="documents-grid-card" elevation="0">
            <v-card-text class="pa-8">
                <v-row>
                    <v-col 
                        v-for="document in documents" 
                        :key="document.id"
                        cols="12" md="6" lg="4"
                    >
                        <v-card 
                            class="document-card" 
                            elevation="2"
                            @click="viewDocument(document)"
                        >
                            <div class="document-card-header pa-6 pb-4">
                                <div class="d-flex align-center justify-space-between mb-3">
                                    <v-icon 
                                        :color="getFileTypeColor(document.file_type)" 
                                        size="32"
                                    >
                                        {{ getFileTypeIcon(document.file_type) }}
                                    </v-icon>
                                    <v-menu>
                                        <template #activator="{ props }">
                                            <v-btn
                                                v-bind="props"
                                                icon="mdi-dots-vertical"
                                                variant="text"
                                                size="small"
                                                @click.stop
                                            />
                                        </template>
                                        <v-list>
                                            <v-list-item 
                                                @click="deleteDocument(document)"
                                                class="text-error"
                                            >
                                                <template #prepend>
                                                    <v-icon color="error">mdi-delete</v-icon>
                                                </template>
                                                <v-list-item-title>Löschen</v-list-item-title>
                                            </v-list-item>
                                        </v-list>
                                    </v-menu>
                                </div>
                                <h4 class="document-title mb-2">{{ document.name || document.file_name }}</h4>
                                <div class="document-meta">
                                    <v-chip 
                                        :color="getFileTypeColor(document.file_type)" 
                                        variant="tonal" 
                                        size="small"
                                        class="mb-2"
                                    >
                                        {{ formatFileType(document.file_type) }}
                                    </v-chip>
                                    <p class="document-size">{{ formatFileSize(document.file_size) }}</p>
                                    <p class="document-date">
                                        Hochgeladen: {{ formatDate(document.created_at) }}
                                    </p>
                                </div>
                            </div>
                        </v-card>
                    </v-col>
                </v-row>
            </v-card-text>
        </div>

        <!-- Empty State -->
        <v-card v-else class="empty-state-card" elevation="0">
            <v-card-text class="text-center py-16">
                <div class="empty-state-icon mb-6">
                    <v-icon size="80" color="grey-lighten-2">mdi-file-document-multiple-outline</v-icon>
                </div>
                <h3 class="empty-state-title mb-3">Keine Dokumente vorhanden</h3>
                <p class="empty-state-subtitle mb-8">
                    Für diesen Workflow wurden noch keine Dokumente hochgeladen.
                </p>
                <v-btn 
                    @click="uploadAdditionalDocuments" 
                    size="large"
                    color="brown"
                    prepend-icon="mdi-plus-circle"
                    class="action-btn-primary"
                >
                    Erste Dokumente hinzufügen
                </v-btn>
            </v-card-text>
        </v-card>

        <!-- Document Upload Dialog -->
        <v-dialog v-model="showUploadDialog" max-width="800" persistent>
            <v-card class="upload-dialog">
                <v-card-title class="upload-dialog-header pa-6">
                    <div class="d-flex justify-space-between align-center w-100">
                        <h3>Dokumente hinzufügen</h3>
                        <v-btn
                            @click="closeUploadDialog"
                            icon="mdi-close"
                            variant="text"
                            size="small"
                        />
                    </div>
                </v-card-title>

                <v-card-text class="pa-10">
                    <div 
                        class="upload-zone"
                        :class="{ 'upload-zone--active': dragover }"
                        @drop="handleFileDrop" 
                        @dragover.prevent="dragover = true" 
                        @dragleave.prevent="dragover = false"
                        @click="triggerFileInput"
                    >
                        <div class="upload-zone-content">
                            <v-icon size="48" class="upload-icon mb-3">mdi-cloud-upload-outline</v-icon>
                            <h4 class="upload-title mb-2">Dateien hier ablegen</h4>
                            <p class="upload-subtitle mb-4">oder klicken zum Auswählen</p>
                            <v-btn 
                                variant="outlined" 
                                prepend-icon="mdi-folder-open-outline"
                                class="upload-btn"
                            >
                                Dateien auswählen
                            </v-btn>
                            <p class="upload-hint mt-3">
                                Unterstützte Formate: PDF, DOCX, DOC (Max. 10MB pro Datei)
                            </p>
                        </div>
                        <input 
                            ref="fileInput" 
                            type="file" 
                            multiple 
                            accept=".pdf,.docx,.doc" 
                            @change="handleFileSelect" 
                            style="display: none"
                        >
                    </div>
                    
                    <div v-if="uploadFiles.length > 0" class="upload-files-section mt-6">
                        <h4 class="files-title mb-3">Ausgewählte Dateien ({{ uploadFiles.length }})</h4>
                        <div class="files-chips d-flex flex-wrap ga-2">
                            <v-chip
                                v-for="(file, index) in uploadFiles"
                                :key="index"
                                variant="tonal"
                                color="brown"
                                size="default"
                                class="pa-6"
                                closable
                                @click:close="removeUploadFile(index)"
                                prepend-icon="mdi-file-document-outline"
                            >
                                <span class="file-chip-content">
                                    {{ file.name }}
                                    <span class="file-size-small">({{ formatFileSize(file.size) }})</span>
                                </span>
                            </v-chip>
                        </div>
                    </div>
                </v-card-text>

                <v-card-actions class="upload-dialog-actions pa-6 pt-0">
                    <v-btn 
                        @click="closeUploadDialog" 
                        variant="outlined"
                        size="large"
                    >
                        Abbrechen
                    </v-btn>
                    <v-spacer />
                    <v-btn 
                        @click="startUpload" 
                        :disabled="uploadFiles.length === 0"
                        :loading="isUploading"
                        color="brown"
                        size="large"
                        prepend-icon="mdi-upload"
                    >
                        {{ uploadFiles.length }} Datei(en) hochladen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- PDF Viewer Modal -->
        <PDFViewer
            v-model="showPDFViewer"
            :pdf-url="documentViewerUrl"
            :file-name="selectedDocument?.name || selectedDocument?.file_name"
            @download="downloadDocument(selectedDocument)"
        />

        <!-- Document Viewer Dialog (for non-PDF files) -->
        <v-dialog v-model="showViewerDialog" fullscreen>
            <v-card class="document-viewer">
                <v-toolbar dark color="brown" class="viewer-toolbar">
                    <v-btn
                        @click="closeViewerDialog"
                        icon="mdi-close"
                        variant="text"
                    />
                    <v-toolbar-title>
                        {{ selectedDocument?.name || selectedDocument?.file_name }}
                    </v-toolbar-title>
                    <v-spacer />
                    <v-btn
                        @click="downloadDocument(selectedDocument)"
                        icon="mdi-download"
                        variant="text"
                    />
                </v-toolbar>
                
                <v-card-text class="pa-0 viewer-content">
                    <div v-if="isLoadingViewer" class="viewer-loading text-center py-16">
                        <v-progress-circular 
                            indeterminate 
                            color="brown" 
                            size="64"
                            class="mb-4"
                        />
                        <h3 class="loading-title mb-3">Dokument wird geladen...</h3>
                    </div>
                    
                    <iframe
                        v-else-if="documentViewerUrl"
                        :src="documentViewerUrl"
                        width="100%"
                        height="100%"
                        frameborder="0"
                        class="document-iframe"
                    />
                    
                    <div v-else class="viewer-error text-center py-16">
                        <v-icon size="64" color="error" class="mb-4">mdi-alert-circle-outline</v-icon>
                        <h3 class="error-title mb-3">Dokument kann nicht angezeigt werden</h3>
                        <p class="error-subtitle">
                            Das Dokument kann in diesem Format nicht im Browser angezeigt werden.
                        </p>
                        <v-btn 
                            @click="downloadDocument(selectedDocument)"
                            color="brown"
                            class="mt-4"
                            prepend-icon="mdi-download"
                        >
                            Dokument herunterladen
                        </v-btn>
                    </div>
                </v-card-text>
            </v-card>
        </v-dialog>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="showDeleteDialog" max-width="400">
            <v-card elevation="2">
                <v-card-title class="pa-6 pb-4">
                    <div class="d-flex justify-space-between align-center ga-3">
                        <span class="text-h6">Dokument löschen</span>
                        <v-btn 
                            @click="showDeleteDialog = false" 
                            variant="text"
                            :disabled="isDeleting"
                            icon="mdi-close"
                        >
                        </v-btn>
                    </div>
                </v-card-title>
                
                <v-card-text class="pa-6 pt-0">
                    <p class="mb-3 background-color: #fafafa;">
                        Möchten Sie das Dokument 
                        <strong>"{{ documentToDelete?.name || documentToDelete?.file_name }}"</strong> 
                        wirklich löschen?
                    </p>
                    <p class="text-caption text-grey-darken-1">
                        Diese Aktion kann nicht rückgängig gemacht werden.
                    </p>
                </v-card-text>
                
                <v-card-actions class="pa-6 pt-0 d-flex justify-center">
                    <v-btn 
                        @click="confirmDeleteDocument" 
                        :loading="isDeleting"
                        color="error"
                        size="large"
                    >
                        <v-icon size="30">mdi-delete</v-icon>
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Notification Snackbar -->
        <v-snackbar 
            v-model="showNotificationSnackbar" 
            :color="notificationColor" 
            :timeout="4000"
            location="bottom right"
        >
            {{ notificationText }}
            <template v-slot:actions>
                <v-btn 
                    variant="text" 
                    @click="showNotificationSnackbar = false"
                    color="white"
                >
                    Schließen
                </v-btn>
            </template>
        </v-snackbar>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { WorkflowAPI } from '@/services/api'
import PDFViewer from '@/components/PDFViewer.vue'

// Props
interface Props {
    workflowId: number
    title?: string
    subtitle?: string
    showHeader?: boolean
    showBackButton?: boolean
    autoLoad?: boolean
}

const props = withDefaults(defineProps<Props>(), {
    title: 'Workflow Dokumente',
    showHeader: true,
    showBackButton: true,
    autoLoad: true
})

// Emits
const emit = defineEmits<{
    'back': []
    'document-uploaded': [documents: any[]]
    'document-deleted': [documentId: number]
    'document-viewed': [document: any]
    'documents-loaded': [documents: any[]]
}>()

// Reactive data
const documents = ref<any[]>([])
const isLoading = ref(false)

// Upload dialog
const showUploadDialog = ref(false)
const uploadFiles = ref<File[]>([])
const isUploading = ref(false)
const dragover = ref(false)
const fileInput = ref<HTMLInputElement>()

// Document viewer
const showViewerDialog = ref(false)
const showPDFViewer = ref(false)
const selectedDocument = ref<any>(null)
const documentViewerUrl = ref('')
const isLoadingViewer = ref(false)

// Delete dialog
const showDeleteDialog = ref(false)
const documentToDelete = ref<any>(null)
const isDeleting = ref(false)

// Notification system
const showNotificationSnackbar = ref(false)
const notificationText = ref('')
const notificationColor = ref('success')

// Helper functions
const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}

const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatFileType = (fileType: string) => {
    if (!fileType) return 'Unbekannt'
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return 'PDF'
    if (type.includes('word') || type.includes('docx')) return 'Word'
    if (type.includes('excel') || type.includes('xlsx')) return 'Excel'
    return fileType
}

const getFileTypeIcon = (fileType: string) => {
    if (!fileType) return 'mdi-file-document-outline'
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return 'mdi-file-pdf-box'
    if (type.includes('word') || type.includes('docx')) return 'mdi-file-word-box'
    if (type.includes('excel') || type.includes('xlsx')) return 'mdi-file-excel-box'
    return 'mdi-file-document-outline'
}

const getFileTypeColor = (fileType: string) => {
    if (!fileType) return 'grey'
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return 'red'
    if (type.includes('word') || type.includes('docx')) return 'blue'
    if (type.includes('excel') || type.includes('xlsx')) return 'green'
    return 'brown'
}

// Show notification helper
const displayNotification = (message: string, color: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    notificationText.value = message
    notificationColor.value = color
    showNotificationSnackbar.value = true
}

// Navigation
const handleBack = () => {
    emit('back')
}

// Load documents
const loadDocuments = async () => {
    try {
        isLoading.value = true
        const response = await WorkflowAPI.getWorkflowDocuments(props.workflowId)
        documents.value = response.data || []
        emit('documents-loaded', documents.value)
    } catch (error) {
        console.error('Error loading documents:', error)
        displayNotification('Fehler beim Laden der Dokumente.', 'error')
        documents.value = []
    } finally {
        isLoading.value = false
    }
}

// Upload functions
const uploadAdditionalDocuments = () => {
    showUploadDialog.value = true
    uploadFiles.value = []
    dragover.value = false
}

const closeUploadDialog = () => {
    showUploadDialog.value = false
    uploadFiles.value = []
    dragover.value = false
}

const triggerFileInput = () => {
    fileInput.value?.click()
}

const handleFileDrop = (e: DragEvent) => {
    e.preventDefault()
    dragover.value = false
    const files = e.dataTransfer?.files
    if (files) {
        addUploadFiles(Array.from(files))
    }
}

const handleFileSelect = (e: Event) => {
    const target = e.target as HTMLInputElement
    const files = target.files
    if (files) {
        addUploadFiles(Array.from(files))
    }
}

const addUploadFiles = (files: File[]) => {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
    const validFiles = files.filter(file => validTypes.includes(file.type))
    uploadFiles.value.push(...validFiles)
}

const removeUploadFile = (index: number) => {
    uploadFiles.value.splice(index, 1)
}

const startUpload = async () => {
    if (uploadFiles.value.length === 0) return
    
    try {
        isUploading.value = true
        
        await WorkflowAPI.uploadWorkflowDocuments(props.workflowId, uploadFiles.value)
        
        closeUploadDialog()
        await loadDocuments()
        
        displayNotification(`${uploadFiles.value.length} Dokument(e) erfolgreich hochgeladen!`, 'success')
        emit('document-uploaded', documents.value)
        
    } catch (error) {
        console.error('Error uploading documents:', error)
        displayNotification('Fehler beim Hochladen der Dokumente.', 'error')
    } finally {
        isUploading.value = false
    }
}

// Document actions
const viewDocument = async (document: any) => {
    try {
        selectedDocument.value = document
        isLoadingViewer.value = true
        documentViewerUrl.value = ''
        
        // Get document file as blob
        const response = await WorkflowAPI.getWorkflowDocumentFile(props.workflowId, document.id)
        const blob = response.data
        
        // Validate blob
        if (!blob || blob.size === 0) {
            throw new Error('Empty or invalid file received')
        }
        
        // Create object URL for viewing
        const url = URL.createObjectURL(blob)
        documentViewerUrl.value = url
        
        // Show appropriate viewer based on file type
        if (document.file_type?.includes('pdf')) {
            showPDFViewer.value = true
        } else {
            showViewerDialog.value = true
        }
        
        emit('document-viewed', document)
        
    } catch (error) {
        console.error('Error loading document for viewing:', error)
        displayNotification('Fehler beim Laden des Dokuments.', 'error')
        documentViewerUrl.value = ''
    } finally {
        isLoadingViewer.value = false
    }
}

const downloadDocument = async (document: any) => {
    try {
        const response = await WorkflowAPI.getWorkflowDocumentFile(props.workflowId, document.id)
        const blob = response.data
        
        // Create download link
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = document.name || document.file_name || 'document'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
        displayNotification('Download gestartet!', 'success')
        
    } catch (error) {
        console.error('Error downloading document:', error)
        displayNotification('Fehler beim Herunterladen des Dokuments.', 'error')
    }
}

const deleteDocument = (document: any) => {
    documentToDelete.value = document
    showDeleteDialog.value = true
}

const confirmDeleteDocument = async () => {
    if (!documentToDelete.value) return
    
    try {
        isDeleting.value = true
        
        await WorkflowAPI.deleteWorkflowDocument(props.workflowId, documentToDelete.value.id)
        
        showDeleteDialog.value = false
        const deletedId = documentToDelete.value.id
        documentToDelete.value = null
        
        await loadDocuments()
        
        displayNotification('Dokument erfolgreich gelöscht!', 'success')
        emit('document-deleted', deletedId)
        
    } catch (error) {
        console.error('Error deleting document:', error)
        displayNotification('Fehler beim Löschen des Dokuments.', 'error')
    } finally {
        isDeleting.value = false
    }
}

const closeViewerDialog = () => {
    showViewerDialog.value = false
    showPDFViewer.value = false
    selectedDocument.value = null
    if (documentViewerUrl.value) {
        URL.revokeObjectURL(documentViewerUrl.value)
        documentViewerUrl.value = ''
    }
}

// Expose methods for parent components
defineExpose({
    loadDocuments
})

// Watch workflowId changes
watch(() => props.workflowId, (newId) => {
    if (newId && props.autoLoad) {
        loadDocuments()
    }
}, { immediate: true })

// Initialize
onMounted(() => {
    if (props.workflowId && props.autoLoad) {
        loadDocuments()
    }
})
</script>

<style scoped>
.documents-header-card,
.documents-grid-card,
.empty-state-card {
    border-radius: 16px;
    margin-bottom: 24px;
}

.section-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: #2c3e50;
}

.workflow-name {
    color: #666;
    font-size: 0.9rem;
    margin: 0;
}

.count-chip {
    font-weight: 500;
}

.back-btn {
    color: #666;
}

.action-btn {
    border-color: #8D6E63;
    color: #8D6E63;
}

.action-btn-primary {
    background-color: #8D6E63;
    color: white;
}

.document-card {
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
}

.document-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.document-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #2c3e50;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.document-meta {
    font-size: 0.85rem;
    color: #666;
}

.document-size,
.document-date {
    margin: 0;
    font-size: 0.8rem;
}

.upload-zone {
    border: 2px dashed #ccc;
    border-radius: 12px;
    padding: 48px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: #fafafa;
}

.upload-zone:hover,
.upload-zone--active {
    border-color: #8D6E63;
    background-color: #f5f5f5;
}

.upload-icon {
    color: #8D6E63;
}

.upload-title {
    color: #2c3e50;
    font-weight: 600;
}

.upload-subtitle {
    color: #666;
}

.upload-hint {
    color: #999;
    font-size: 0.85rem;
}

.file-chip-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.file-size-small {
    font-size: 0.75rem;
    opacity: 0.7;
}

.document-viewer {
    height: 100vh;
}

.viewer-content {
    height: calc(100vh - 64px);
}

.document-iframe {
    height: 100%;
}

.viewer-loading,
.viewer-error {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.loading-state {
    padding: 64px 0;
}

.loading-title,
.empty-state-title,
.error-title {
    color: #2c3e50;
    font-weight: 600;
}

.loading-subtitle,
.empty-state-subtitle,
.error-subtitle {
    color: #666;
    max-width: 400px;
    margin: 0 auto;
}

.empty-state-icon {
    opacity: 0.3;
}

.text-caption {
    font-size: 0.8rem;
    background-color: #fafafa;
    color: #666;
    padding: 0.5rem;
    border-radius: 8px;
    margin-top: 1rem;
}
</style>
