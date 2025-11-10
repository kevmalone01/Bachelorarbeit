<template>
    <div class="intelligent-document-processing">
        <v-btn 
            color="brown" 
            variant="outlined" 
            @click="goBackToDashboard"
            class="mr-4"
        >
            <v-icon class="mr-1">mdi-arrow-left</v-icon>
            Zurück zum Dashboard
        </v-btn>

        <!-- Main Processing Interface -->
        <v-row class="main-interface">
            <!-- Chat Column -->
            <v-col cols="12" :lg="showPdfResult && currentStep >= 4 ? 6 : 12">
                <div class="chat-container">
                    <v-card class="chat-card" elevation="1">
                        <div class="chat-header">
                            <div class="status-dot" :class="{ 'active': isProcessing, 'completed': allStepsCompleted }"></div>
                            <span class="chat-title">Automatische Dokumentverarbeitung</span>
                            <v-spacer></v-spacer>
                            <span class="status-text">{{ getStatusText() }}</span>
                        </div>
                        
                        <div class="chat-messages" ref="chatMessages">
                            <!-- Processing Steps -->
                            <div class="process-step" v-for="(step, index) in processSteps" :key="index">
                                <div class="step-indicator">
                                    <div class="step-number" :class="getStepClass(index + 1)">{{ index + 1 }}</div>
                                    <div class="step-connector" v-if="index < processSteps.length - 1"></div>
                                </div>
                                <div class="step-content">
                                    <div class="step-title">{{ step.title }}</div>
                                    <div class="step-description">{{ step.description }}</div>
                                    <div class="step-status" v-if="getStepStatus(index + 1)">
                                        <span class="status-text">{{ getStepStatus(index + 1) }}</span>
                                    </div>
                                    
                                    <!-- Step-specific content -->
                                    <div v-if="index === 0 && step1Completed" class="step-result">
                                        <v-chip size="small" variant="flat" color="success">
                                            {{ documents.length }} Dokument(e) analysiert
                                        </v-chip>
                                    </div>
                                    
                                    <div v-if="index === 1 && selectedTemplate" class="step-result">
                                        <v-chip size="small" variant="flat" color="success">
                                            {{ selectedTemplate.name }}
                                        </v-chip>
                                    </div>
                                    
                                    <div v-if="index === 2 && extractionResults" class="step-result">
                                        <v-chip size="small" variant="flat" color="success">
                                            {{ Object.keys(extractionResults.extracted_values || {}).length }} Felder extrahiert
                                        </v-chip>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Completion Message -->
                            <div v-if="showPdfResult && currentStep >= 4" class="completion-step mt-4">
                                <v-alert
                                    type="success"
                                    variant="tonal"
                                    prominent
                                    border
                                >
                                    <template v-slot:prepend>
                                        <v-icon>mdi-check-circle</v-icon>
                                    </template>
                                    <div class="alert-title">Verarbeitung abgeschlossen!</div>
                                    <div class="alert-subtitle">
                                        Template "{{ selectedTemplate?.name }}" wurde mit {{ Object.keys(extractionResults?.extracted_values || {}).length }} extrahierten Feldern gefüllt.
                                    </div>
                                </v-alert>
                            </div>
                        </div>
                        
                        <!-- Template Selection (only show if needed) -->
                        <div v-if="currentStep === 2 && !selectedTemplate && templates.length > 1" class="template-selector mt-4">
                            <div class="selector-title">Template auswählen:</div>
                            <div class="template-grid">
                                <v-card
                                    v-for="template in templates" 
                                    :key="template.id"
                                    class="template-card"
                                    @click="selectTemplate(template)"
                                    variant="outlined"
                                    hover
                                >
                                    <v-card-text class="pa-3">
                                        <div class="template-name">{{ template.name }}</div>
                                        <div class="template-info">{{ template.placeholders?.length || 0 }} Felder</div>
                                    </v-card-text>
                                </v-card>
                            </div>
                        </div>
                    </v-card>
                </div>
            </v-col>
            
            <!-- PDF Viewer Column -->
            <v-col cols="12" lg="6" v-show="showPdfResult && currentStep >= 4" style="max-height: 805px;">
                <DocumentPreview
                    v-if="selectedTemplate"
                    ref="documentPreviewRef"
                    :documentId="selectedTemplate.id"
                    :placeholderValues="formValues"
                    :title="`Generiertes Dokument: ${selectedTemplate.name}`"
                    :autoGenerate="true"
                    :initialViewMode="'pdf'"
                    @preview-generated="onPreviewGenerated"
                    @error="onPreviewError"
                />
            </v-col>
        </v-row>

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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import store from '@/store/store'
import WorkflowDocumentViewer from '@/components/WorkflowDocumentViewer.vue'
import DocumentPreview from '@/components/DocumentPreview.vue'
import { WorkflowAPI, DocumentAPI } from '@/services/api'

const router = useRouter()

// Props from route
const workflowId = computed(() => Number(router.currentRoute.value.params.workflowId))

// Stepper and workflow state
const currentStep = ref(1)

// Data management
const workflow = ref<any>(null)
const documents = ref<any[]>([])
const templates = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const extractionResults = ref<any>(null)
const extractingFields = ref(false)

// Chat state management
const step1Completed = ref(false)
const step2Completed = ref(false)
const step3Completed = ref(false)
const step1Time = ref(new Date())
const step2Time = ref(new Date())
const step3Time = ref(new Date())
const step4Time = ref(new Date())

// UI state
const showPdfResult = ref(false)
const chatMessages = ref<HTMLElement | null>(null)

// Document generation state (handled by DocumentPreview component)

// Process steps configuration
const processSteps = ref([
    {
        title: 'Dokumente analysieren',
        description: 'Hochgeladene Dokumente werden verarbeitet'
    },
    {
        title: 'Template auswählen',
        description: 'Passende Vorlage für die Dokumenterstellung'
    },
    {
        title: 'KI-Extraktion',
        description: 'Automatische Feldextraktion aus Dokumenten'
    },
    {
        title: 'Formular ausfüllen',
        description: 'Überprüfung und Ergänzung der Daten'
    }
])

// Processing state
const isProcessing = computed(() => {
    return !step1Completed.value || !step2Completed.value || !step3Completed.value || extractingFields.value
})

// Form values and preview
const formValues = ref<Record<string, any>>({})
const documentPreviewRef = ref<InstanceType<typeof DocumentPreview> | null>(null)

// Notification system
const snackbar = reactive({
    show: false,
    text: '',
    color: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Client management (from store)
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
const getNonClientFields = () => {
    if (!selectedTemplate.value?.placeholders) return []
    return selectedTemplate.value.placeholders.filter((p: any) => !p.isClientField)
}

const getNonClientFieldsCount = () => {
    return getNonClientFields().length
}

const canGenerateDocument = computed(() => {
    if (!selectedTemplate.value) return false
    
    const requiredFields = selectedTemplate.value.placeholders?.filter((p: any) => p.required) || []
    return requiredFields.every((field: any) => {
        return formValues.value[field.name] !== undefined && formValues.value[field.name] !== ''
    })
})

const allStepsCompleted = computed(() => {
    return step1Completed.value && step2Completed.value && step3Completed.value && currentStep.value >= 4
})

// Utility functions
const formatTime = (date: Date) => {
    return date.toLocaleTimeString('de-DE', { 
        hour: '2-digit', 
        minute: '2-digit' 
    })
}

const getStatusText = () => {
    if (allStepsCompleted.value) return 'Abgeschlossen'
    if (extractingFields.value) return 'KI-Extraktion läuft...'
    if (currentStep.value === 1) return 'Analysiere Dokumente...'
    if (currentStep.value === 2) return 'Warte auf Template-Auswahl'
    if (currentStep.value === 3) return 'Bereit für KI-Extraktion'
    if (currentStep.value === 4) return 'Formular bereit'
    return 'Verarbeitung...'
}

const getStepClass = (stepNumber: number) => {
    if (stepNumber < currentStep.value) return 'completed'
    if (stepNumber === currentStep.value) return 'active'
    return 'pending'
}

const getStepStatus = (stepNumber: number) => {
    if (stepNumber === 1 && step1Completed.value) return '✓ Abgeschlossen'
    if (stepNumber === 2 && step2Completed.value) return '✓ Abgeschlossen'  
    if (stepNumber === 3 && step3Completed.value) return '✓ Abgeschlossen'
    if (stepNumber === 4 && currentStep.value >= 4) return '✓ Bereit'
    if (stepNumber === currentStep.value) {
        if (stepNumber === 1 && !step1Completed.value) return 'Läuft...'
        if (stepNumber === 2 && !step2Completed.value) return 'Warten...'
        if (stepNumber === 3 && extractingFields.value) return 'Extrahiert...'
        if (stepNumber === 3 && !step3Completed.value) return 'Bereit'
    }
    return ''
}

// Load data on mount
onMounted(async () => {
    await loadWorkflow()
    await loadTemplates()
    await loadClients()
    await loadDocuments()
    
    // Start automated process
    startAutomatedProcess()
})

// Cleanup on unmount
onUnmounted(() => {
    cleanup()
})

// Automated process management
const startAutomatedProcess = async () => {
    // Step 1: Mark documents as analyzed
    setTimeout(() => {
        step1Completed.value = true
        step1Time.value = new Date()
        
        // Auto-advance to template selection
        setTimeout(() => {
            currentStep.value = 2
            step2Time.value = new Date()
            
            // Auto-select template if only one available
            if (templates.value.length === 1) {
                selectTemplate(templates.value[0])
            }
        }, 500)
    }, 1000)
}

// Data loading functions
const loadWorkflow = async () => {
    try {
        const response = await WorkflowAPI.getWorkOrder(workflowId.value)
        workflow.value = response.data
    } catch (error) {
        console.error('Error loading workflow:', error)
        showNotification('Fehler beim Laden des Workflows', 'error')
    }
}

const loadTemplates = async () => {
    try {
        const response = await DocumentAPI.getTemplates()
        templates.value = response.data || []
    } catch (error) {
        console.error('Error loading templates:', error)
        showNotification('Fehler beim Laden der Templates', 'error')
        templates.value = []
    }
}

const loadClients = async () => {
    try {
        if (store && store.dispatch) {
            await store.dispatch('client/fetchClients');
        }
    } catch (error) {
        console.warn('Error fetching clients:', error);
    }
}

const loadDocuments = async () => {
    try {
        const response = await WorkflowAPI.getWorkflowDocuments(workflowId.value)
        documents.value = response.data || []
    } catch (error) {
        console.error('Error loading documents:', error)
        showNotification('Fehler beim Laden der Dokumente', 'error')
        documents.value = []
    }
}

// Template selection
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
    
    formValues.value = { ...initialValues }
    
    // Mark step 2 as completed and auto-advance
    step2Completed.value = true
    step2Time.value = new Date()
    
    // Auto-advance to AI extraction
    setTimeout(() => {
        currentStep.value = 3
        step3Time.value = new Date()
        
        // Auto-start AI extraction
        setTimeout(() => {
            performAIExtraction()
        }, 500)
    }, 500)
}

// AI Extraction
const performAIExtraction = async () => {
    if (!selectedTemplate.value) return
    
    try {
        extractingFields.value = true
        const response = await WorkflowAPI.extractFieldsFromDocuments(
            workflowId.value, 
            selectedTemplate.value.id
        )
        
        extractionResults.value = response.data
        
        // Merge extracted values with existing form values
        if (response.data.extracted_values) {
            Object.keys(response.data.extracted_values).forEach(key => {
                if (response.data.extracted_values[key] !== undefined) {
                    formValues.value[key] = response.data.extracted_values[key]
                }
            })
            
            // Trigger reactivity
            formValues.value = { ...formValues.value }
        }
        
        // Mark step 3 as completed and auto-advance
        step3Completed.value = true
        step3Time.value = new Date()
        
        if (response.data.extracted_values && Object.keys(response.data.extracted_values).length > 0) {
            showNotification(
                `${Object.keys(response.data.extracted_values).length} Felder erfolgreich extrahiert!`, 
                'success'
            )
        } else {
            showNotification('Keine Felder konnten extrahiert werden', 'warning')
        }
        
        // Auto-advance to document generation
        setTimeout(() => {
            currentStep.value = 4
            step4Time.value = new Date()
            showPdfResult.value = true
        }, 1000)
        
    } catch (error) {
        console.error('Error extracting fields:', error)
        showNotification('Fehler bei der KI-Extraktion', 'error')
    } finally {
        extractingFields.value = false
    }
}

// Preview callbacks
const onPreviewGenerated = () => {
    showNotification('Dokument erfolgreich generiert', 'success')
}

const onPreviewError = (errorMessage: string) => {
    showNotification(`Fehler bei der Dokument-Generierung: ${errorMessage}`, 'error')
}

// Cleanup function
const cleanup = () => {
    // Cleanup is handled by DocumentPreview component
}

// Utility functions
const showNotification = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
    snackbar.text = text
    snackbar.color = color
    snackbar.show = true
}

const goBackToDashboard = () => {
    router.push('/dashboard')
}
</script>

<style scoped>
.intelligent-document-processing {
    padding: 1.5rem;
    min-height: calc(100vh - 64px);
    background: #f8f9fa;
}

.header-card {
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
}

.page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #2c3e50;
    margin: 0;
    display: flex;
    align-items: center;
}

.page-subtitle {
    font-size: 1rem;
    color: #6b5d4f;
    margin: 0.5rem 0 0 0;
}

.workflow-info {
    display: flex;
    align-items: center;
}

/* Minimal Process Interface */
.chat-container {
    width: 100%;
}

.chat-card {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    overflow: hidden;
}

.chat-header {
    background: #f5f5f5;
    color: #333;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #e0e0e0;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ccc;
    margin-right: 12px;
    transition: background-color 0.3s ease;
}

.status-dot.active {
    background: #2196F3;
    animation: pulse 2s infinite;
}

.status-dot.completed {
    background: #4CAF50;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.chat-title {
    font-weight: 500;
    font-size: 1rem;
    color: #333;
}

.status-text {
    font-size: 0.875rem;
    color: #666;
}

.chat-messages {
    padding: 20px;
    background: #fff;
}

.process-step {
    display: flex;
    margin-bottom: 24px;
}

.step-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-right: 16px;
}

.step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.step-number.pending {
    background: #f5f5f5;
    color: #999;
    border: 2px solid #e0e0e0;
}

.step-number.active {
    background: #2196F3;
    color: white;
    border: 2px solid #2196F3;
}

.step-number.completed {
    background: #4CAF50;
    color: white;
    border: 2px solid #4CAF50;
}

.step-connector {
    width: 2px;
    height: 24px;
    background: #e0e0e0;
    margin-top: 8px;
}

.step-content {
    flex: 1;
    padding-top: 4px;
}

.step-title {
    font-weight: 500;
    font-size: 1rem;
    color: #333;
    margin-bottom: 4px;
}

.step-description {
    font-size: 0.875rem;
    color: #666;
    margin-bottom: 8px;
}

.step-status {
    font-size: 0.875rem;
    color: #2196F3;
    margin-bottom: 8px;
}

.step-result {
    margin-top: 8px;
}

.template-selector {
    padding: 16px 20px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
}

.selector-title {
    font-size: 0.875rem;
    font-weight: 500;
    color: #333;
    margin-bottom: 12px;
}

.template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
}

.template-card {
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 6px;
}

.template-card:hover {
    border-color: #2196F3;
    transform: translateY(-1px);
}

.template-name {
    font-weight: 500;
    font-size: 0.875rem;
    color: #333;
    margin-bottom: 4px;
}

.template-info {
    font-size: 0.75rem;
    color: #666;
}

.main-interface {
    margin-top: 0;
}

.completion-step {
    border-top: 1px solid #e0e0e0;
    padding-top: 16px;
}

.alert-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.alert-subtitle {
    font-size: 0.95rem;
    opacity: 0.9;
    line-height: 1.4;
}

/* Animation */
@keyframes slideIn {
    from { 
        opacity: 0; 
        transform: translateY(20px);
    }
    to { 
        opacity: 1; 
        transform: translateY(0);
    }
}

/* Responsive design */
@media (max-width: 768px) {
    .intelligent-document-processing {
        padding: 1rem;
    }
    
    .page-title {
        font-size: 1.5rem;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .workflow-info {
        margin-top: 1rem;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
    
    .header-card .v-card-title {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }
    
    .chat-container {
        margin: 0;
    }
    
    .message-bubble {
        max-width: 95%;
    }
    
    .chat-messages {
        padding: 12px;
        max-height: 500px;
    }
    
    .form-section {
        padding: 12px;
    }
}
</style> 