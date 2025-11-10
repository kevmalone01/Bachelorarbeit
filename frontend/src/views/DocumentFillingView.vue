<template>
    <div class="document-filling-container">
        <!-- Document Filling Interface Tab -->
        <div v-if="activeTab === 'filling'" class="filling-tab">
            <!-- Document Filling Interface -->
            <div v-if="selectedTemplate" class="filling-interface">
                <!-- Back button -->
                <v-btn color="brown" variant="outlined" @click="goBackToDashboard" class="mb-4">
                    <v-icon class="mr-2">mdi-arrow-left</v-icon>
                    Zurück zum Dashboard
                </v-btn>
                
                <!-- Split view for form and preview -->
                <div class="split-view">
                    <!-- Form Section -->
                    <div class="form-section">
                        <v-card class="form-card">
                            <v-card-text>
                                <DynamicMask 
                                    v-if="selectedTemplate.placeholders"
                                    key="filling-mask"
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
                                    <v-icon size="48" color="grey">mdi-form-select</v-icon>
                                    <p>Dieses Template hat keine ausfüllbaren Felder.</p>
                                </div>
                            </v-card-text>
                        </v-card>
                    </div>

                    <!-- Preview Section -->
                    <div class="preview-section">
                        <v-card class="preview-card">
                            <!-- Preview Section Toggle -->
                            <v-card-title class="d-flex align-center justify-center pb-2">
                                <div class="preview-toggle">
                                    <v-btn-toggle 
                                        v-model="previewSectionMode" 
                                        color="brown" 
                                        variant="outlined" 
                                        density="compact"
                                        mandatory
                                    >
                                        <v-btn value="preview" size="small">
                                            <v-icon size="16" class="mr-1">mdi-eye</v-icon>
                                            Vorschau
                                        </v-btn>
                                        <v-btn value="documents" size="small" :disabled="!workflowId">
                                            <v-icon size="16" class="mr-1">mdi-folder-multiple</v-icon>
                                            Dokumente
                                        </v-btn>
                                    </v-btn-toggle>
                                </div>
                            </v-card-title>
                            
                            <v-card-text class="preview-content">
                                <!-- Document Preview -->
                                <div v-show="previewSectionMode === 'preview'" class="preview-container">
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
                                
                                <!-- Workflow Documents -->
                                <div v-show="previewSectionMode === 'documents'" class="documents-container">
                                    <WorkflowDocumentsManager
                                        v-if="workflowId && workflowIdNumber"
                                        :workflow-id="workflowIdNumber"
                                        :title="'Workflow Dokumente'"
                                        :subtitle="`Workflow ${workflowId}`"
                                        :show-header="false"
                                        :show-back-button="false"
                                        @document-uploaded="handleDocumentUploaded"
                                        @document-deleted="handleDocumentDeleted"
                                        @document-viewed="handleDocumentViewed"
                                        @documents-loaded="handleDocumentsLoaded"
                                    />
                                    <div v-else class="no-workflow-warning-small">
                                        <v-alert type="info" variant="tonal" density="compact">
                                            <v-icon size="small">mdi-information</v-icon>
                                            Kein Workflow ausgewählt
                                        </v-alert>
                                    </div>
                                </div>
                            </v-card-text>
                        </v-card>
                    </div>
                </div>
            </div>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="loading-overlay">
            <v-progress-circular indeterminate color="brown" size="64"></v-progress-circular>
            <p class="mt-4">Template wird geladen...</p>
        </div>

        <!-- Error state -->
        <div v-if="!isLoading && !selectedTemplate" class="error-state">
            <v-card class="error-card">
                <v-card-text class="text-center">
                    <v-icon size="64" color="error">mdi-alert-circle</v-icon>
                    <h3 class="mt-4 mb-2">Template nicht gefunden</h3>
                    <p class="mb-4">Das für diesen Workflow zugewiesene Template konnte nicht geladen werden.</p>
                    <v-btn color="brown" variant="outlined" @click="goBackToDashboard" class="mt-4">
                        Zurück zum Dashboard
                    </v-btn>
                </v-card-text>
            </v-card>
        </div>

        <!-- Success/Error Snackbar -->
        <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
            {{ snackbar.text }}
            <template v-slot:actions>
                <v-btn variant="text" @click="snackbar.show = false">Schließen</v-btn>
            </template>
        </v-snackbar>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import store from '@/store/store'
import DynamicMask from '@/components/DynamicMask.vue'
import DocumentPreview from '@/components/DocumentPreview.vue'
import WorkflowDocumentsManager from '@/components/WorkflowDocumentsManager.vue'
import { DocumentAPI } from '@/services/api'

const router = useRouter()

// Workflow context
const workflowId = computed(() => router.currentRoute.value.query.workflowId as string | undefined)
const workflowIdNumber = computed(() => {
    if (workflowId.value) {
        const num = Number(workflowId.value)
        return isNaN(num) ? undefined : num
    }
    return undefined
})
const templateId = computed(() => router.currentRoute.value.query.templateId as string | undefined)

// Loading and error states
const isLoading = ref(false)
const snackbar = reactive({
    show: false,
    text: '',
    color: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Tab management
const activeTab = ref('documents')

// Preview section mode (for toggling between preview and documents in filling tab)
const previewSectionMode = ref('preview')

// Template management
interface Template {
    id: number;
    name: string;
    description?: string;
    file_type: string;
    created_at: string;
    placeholders?: Array<{
        name: string;
        type: string;
        required: boolean;
        defaultValue?: any;
        options?: string[];
        validation: any;
        isClientField?: boolean;
        clientFieldGroup?: string;
        clientFieldName?: string;
    }>;
}

const selectedTemplate = ref<Template | null>(null)

// Form values and preview
const formValues = ref<Record<string, any>>({})
const previewMode = ref('text')
const pdfLastGeneratedAt = ref<Date | null>(null)
const documentPreviewRef = ref<InstanceType<typeof DocumentPreview> | null>(null)

// Client management
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
    
    selectedTemplate.value.placeholders.forEach(placeholder => {
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

// Load template on component mount
onMounted(async () => {
    // Load clients for client field support
    try {
        if (store && store.dispatch) {
            await store.dispatch('client/fetchClients');
        }
    } catch (error) {
        console.warn('Error fetching clients:', error);
    }
    
    // Templates are now handled by WorkflowDocumentsManager
    
    // Check workflow context from routing
    const workflowIdParam = router.currentRoute.value.query.workflowId;
    const templateIdParam = router.currentRoute.value.query.templateId;
    
    if (templateIdParam) {
        // Load the specific template and switch to filling tab
        await loadTemplate(Number(templateIdParam));
        activeTab.value = 'filling';
        
        if (workflowIdParam) {
            showNotification(`Dokument-Ausfüllung für Workflow ${workflowIdParam} geöffnet`, 'info');
        }
    } else {
        // No template specified, stay on documents tab
        activeTab.value = 'documents';
        
        if (workflowIdParam) {
            showNotification(`Workflow ${workflowIdParam} Dokumente geöffnet`, 'info');
        }
    }
})

// Load specific template
const loadTemplate = async (templateIdToLoad: number) => {
    try {
        isLoading.value = true
        
        // Load the specific template
        const response = await DocumentAPI.getTemplates()
        const templates = response.data || []
        const template = templates.find((t: Template) => t.id === templateIdToLoad)
        
        if (template) {
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
            
            showNotification(`Template "${template.name}" geladen`, 'success');
        } else {
            showNotification('Template nicht gefunden', 'error');
        }
    } catch (error) {
        console.error('Error loading template:', error)
        showNotification('Fehler beim Laden des Templates', 'error')
    } finally {
        isLoading.value = false
    }
}

// Update form values
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

// Generate document preview/PDF
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
        ?.filter(p => {
            if (!p.required) return false;
            
            // For client fields, check if we have a value
            if (p.isClientField) {
                return !formValues.value[p.name] || formValues.value[p.name] === '';
            }
            
            // For regular fields
            return !formValues.value[p.name] && formValues.value[p.name] !== 0 && formValues.value[p.name] !== false;
        })
        .map(p => p.name) || []
    
    if (missingRequired.length > 0) {
        showNotification(`Bitte füllen Sie alle erforderlichen Felder aus: ${missingRequired.join(', ')}`, 'warning')
        return
    }
    
    if (documentPreviewRef.value) {
        await documentPreviewRef.value.generatePreview()
        pdfLastGeneratedAt.value = new Date()
    }
}

// Handle client selection for filling client fields
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
        showNotification(`Mandanten-Felder für ${formatGroupName(groupName)} wurden automatisch ausgefüllt`, 'success');
    }
};

// Preview callbacks
const onPreviewGenerated = (previewData: any) => {
    pdfLastGeneratedAt.value = new Date()
    showNotification('Vorschau erfolgreich generiert', 'success')
}

const onPreviewError = (errorMessage: string) => {
    showNotification(`Fehler bei der Vorschau-Generierung: ${errorMessage}`, 'error')
}

// Handle view mode changes from DocumentPreview component
const handleViewModeChange = (newMode: string) => {
    previewMode.value = newMode;
}

// Utility functions
const formatTimestamp = (date: Date) => {
    if (!date) return '';
    
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    
    return `${hours}:${minutes}:${seconds}`;
}

const formatGroupName = (groupName: string): string => {
    return groupName
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

// Show notification
const showNotification = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
    snackbar.text = text
    snackbar.color = color
    snackbar.show = true
}

// Tab functions
const switchToDocumentsTab = () => {
    activeTab.value = 'documents'
}

const switchToFillingTab = () => {
    activeTab.value = 'filling'
}

// Document event handlers
const handleDocumentUploaded = (documents: any[]) => {
    showNotification('Dokument erfolgreich hochgeladen', 'success')
}

const handleDocumentDeleted = (documentId: number) => {
    showNotification('Dokument erfolgreich gelöscht', 'success')
}

const handleDocumentViewed = (document: any) => {
    // Could open a document viewer modal here
    console.log('Viewing document:', document)
}

const handleDocumentsLoaded = (documents: any[]) => {
    // Optional: Handle documents loaded event
    console.log('Documents loaded:', documents.length)
}

const handleFieldsExtracted = (values: Record<string, any>) => {
    // Merge extracted values with existing form values
    Object.keys(values).forEach(key => {
        if (values[key] !== undefined) {
            formValues.value[key] = values[key]
        }
    })
    
    // Trigger reactivity
    formValues.value = { ...formValues.value }
    
    // Switch to filling tab to show the extracted values
    activeTab.value = 'filling'
    
    showNotification(`${Object.keys(values).length} Felder automatisch ausgefüllt`, 'success')
}

// Back to dashboard
const goBackToDashboard = () => {
    router.push('/dashboard')
}
</script>

<style scoped>
.document-filling-container {
    padding: 1.5rem;
    min-height: calc(100vh - 64px);
}

.tab-navigation {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.documents-tab,
.filling-tab {
    animation: fadeIn 0.3s ease;
}

.no-workflow-warning {
    max-width: 600px;
    margin: 2rem auto;
}

.page-header {
    text-align: center;
    margin-bottom: 2rem;
}

.page-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #4a3528;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.page-subtitle {
    font-size: 1.1rem;
    color: #6b5d4f;
    margin: 0;
}

/* Filling Interface Styles */
.filling-interface {
    max-width: 1700px;
    margin: 0 auto;
}

.template-header {
    margin-bottom: 1.5rem;
}

.template-info-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.template-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
}

.template-desc {
    color: #5c6b7a;
    margin: 0.25rem 0 0 0;
    font-size: 0.875rem;
}

.split-view {
    display: flex;
    gap: 1.5rem;
    height: calc(100vh - 125px);
}

.form-section,
.preview-section {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.dynamic-mask {
    max-height: 100% !important;
}

.document-preview-component {
    height: 100% !important;
}

.form-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    height: 100%;
    display: flex;
    flex-direction: column;
}

.form-card .v-card-text {
    flex: 1;
    overflow: auto;
}

.no-fields {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: #5c6b7a;
    text-align: center;
}

.no-fields p {
    margin-top: 1rem;
    font-size: 1rem;
}

.pdf-timestamp {
    margin-top: 8px;
    display: flex;
    justify-content: flex-end;
}

/* Error state */
.error-state {
    max-width: 600px;
    margin: 2rem auto;
}

.error-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.error-state h3 {
    color: #2c3e50;
    font-weight: 600;
}

.error-state p {
    color: #5c6b7a;
    margin: 0;
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-overlay p {
    color: #5c6b7a;
    font-size: 1rem;
    margin: 0;
}

/* Responsive Design */
@media (max-width: 1024px) {
    .split-view {
        flex-direction: column;
        height: auto;
        gap: 1.25rem;
    }

    .form-section,
    .preview-section {
        width: 100%;
        height: 500px;
    }

    .page-title {
        font-size: 2rem;
    }
}

@media (max-width: 768px) {
    .document-filling-container {
        padding: 1rem;
    }

    .page-title {
        font-size: 1.75rem;
        flex-direction: column;
        gap: 0.5rem;
    }

    .page-subtitle {
        font-size: 1rem;
    }
}

/* Animation */
@keyframes fadeIn {
    from { 
        opacity: 0; 
        transform: translateY(20px);
    }
    to { 
        opacity: 1; 
        transform: translateY(0);
    }
}

.filling-interface {
    animation: fadeIn 0.5s ease;
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

/* Preview Section Styles */
.preview-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    height: 100%;
    display: flex;
    flex-direction: column;
}

.preview-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #2c3e50;
}

.preview-toggle .v-btn-toggle {
    border-radius: 8px;
}

.preview-content {
    flex: 1;
    overflow: hidden;
    padding: 0 !important;
}

.preview-container,
.documents-container {
    height: 100%;
    overflow: auto;
}

.preview-container {
    padding: 1rem;
}

.documents-container {
    padding: 0.5rem;
}

.no-workflow-warning-small {
    padding: 1rem;
}
</style> 