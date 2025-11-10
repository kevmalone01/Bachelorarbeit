<template>
    <div class="ai-agent-view">
        <v-btn 
            color="brown" 
            variant="outlined" 
            @click="goBackToDashboard"
            class="mr-4"
        >
            <v-icon class="mr-1">mdi-arrow-left</v-icon>
            Zurück zum Dashboard
        </v-btn>

        <!-- Main Chat Interface -->
        <v-row class="main-interface">
            <!-- Chat Column -->
            <v-col cols="12" :lg="12">
                <div class="chat-container">
                    <v-card class="chat-card" elevation="1">
                        <div class="chat-header">
                            <div class="status-dot" :class="{ 'active': isProcessing, 'completed': allStepsCompleted }"></div>
                            <span class="chat-title">AI Agent - Intelligente Dokumentverarbeitung</span>
                            <v-spacer></v-spacer>
                            <span class="status-text">{{ getStatusText() }}</span>
                        </div>
                        
                        <div class="chat-messages" ref="chatMessages">
                            <!-- Welcome Message -->
                            <div class="process-step">
                                <div class="step-indicator">
                                    <v-icon color="brown">mdi-creation</v-icon>
                                </div>
                                <div class="step-content">
                                    <div class="step-title">Willkommen beim KI Agent</div>
                                    <div class="step-description">
                                        Laden Sie Ihre Dokumente hoch und wählen Sie eine Aktion aus. 
                                        Der AI Agent analysiert Ihre Dokumente automatisch und führt intelligente Verarbeitung durch.
                                    </div>
                                </div>
                            </div>

                            <!-- File Upload Step -->
                            <div class="process-step">
                                <div class="step-indicator">
                                    <div class="step-number" :class="getFileUploadStepClass()">1</div>
                                    <div class="step-connector" v-if="chatSteps.length > 1"></div>
                                </div>
                                <div class="step-content">
                                    <div class="step-title">Dokumente hochladen</div>
                                    <div class="step-description">Wählen Sie PDF oder DOCX Dateien aus</div>
                                    
                                    <!-- File Input -->
                                    <div class="mt-3">
                                        <v-file-input
                                            v-model="selectedFiles"
                                            :accept="acceptedFileTypes"
                                            label="Dokumente auswählen"
                                            multiple
                                            variant="outlined"
                                            density="compact"
                                            prepend-icon="mdi-paperclip"
                                            hide-details
                                            @change="onFilesSelected"
                                        ></v-file-input>
                                    </div>
                                </div>
                            </div>

                            <!-- Processing Steps -->
                            <div 
                                v-for="(step, index) in chatSteps" 
                                :key="index" 
                                class="process-step"
                                :class="{ 'animate-step': step.isNew }"
                            >
                                <div class="step-indicator">
                                    <div class="step-number" :class="getStepClass(index + 2)">{{ index + 2 }}</div>
                                    <div class="step-connector" v-if="index < chatSteps.length - 1"></div>
                                </div>
                                <div class="step-content">
                                    <div class="step-title">{{ step.title }}</div>
                                    <div class="step-description">{{ step.description }}</div>
                                    
                                    <!-- Step Status -->
                                    <div v-if="step.status" class="step-status mt-2">
                                        <v-progress-circular 
                                            v-if="step.status === 'processing'"
                                            :size="16" 
                                            :width="2"
                                            color="brown"
                                            indeterminate
                                            class="mr-1"
                                        ></v-progress-circular>
                                        <v-icon 
                                            v-else
                                            :color="getStatusColor(step.status)" 
                                            size="16" 
                                            class="mr-1"
                                        >
                                            {{ getStatusIcon(step.status) }}
                                        </v-icon>
                                        <span class="status-text">{{ step.statusText }}</span>
                                    </div>
                                    
                                    <!-- Step Results -->
                                    <div v-if="step.result" class="step-result mt-2">
                                        
                                        <!-- Client Information -->
                                        <div v-if="step.clientInfo" class="client-info mt-2">
                                            <v-chip color="primary" variant="outlined" class="mb-2">
                                                <v-icon class="mr-1" size="16">mdi-account</v-icon>
                                                Mandant: {{ step.clientInfo.name || 'Nicht bestimmt' }}
                                            </v-chip>
                                            <div v-if="step.clientInfo.details" class="client-details">
                                                <small class="text-grey-600">{{ step.clientInfo.details }}</small>
                                            </div>
                                        </div>

                                        <!-- Template Information -->
                                        <div v-if="step.templateInfo" class="template-info mt-2">
                                            <v-chip color="success" variant="outlined" class="mb-2">
                                                <v-icon class="mr-1" size="16">mdi-file-document</v-icon>
                                                Vorlage: {{ step.templateInfo.name || 'Nicht ausgewählt' }}
                                            </v-chip>
                                            <div v-if="step.templateInfo.reason" class="template-reason">
                                                <small class="text-grey-600">{{ step.templateInfo.reason }}</small>
                                            </div>
                                        </div>
                                        
                                        <!-- Detailed Results -->
                                        <div v-if="step.details" class="result-details mt-2">
                                            <v-expansion-panels variant="accordion" class="result-expansion">
                                                <v-expansion-panel>
                                                    <v-expansion-panel-title class="result-expansion-title">
                                                        Details anzeigen
                                                    </v-expansion-panel-title>
                                                    <v-expansion-panel-text>
                                                        <pre class="result-content">{{ JSON.stringify(step.details, null, 2) }}</pre>
                                                    </v-expansion-panel-text>
                                                </v-expansion-panel>
                                            </v-expansion-panels>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Action Button -->
                        <div class="chat-actions" v-if="selectedFiles.length > 0 && !processingStarted">
                            <v-btn
                                color="brown"
                                variant="outlined"
                                :loading="isProcessing"
                                :disabled="isProcessing"
                                @click="startFullProcessing"
                                size="large"
                            >
                                <v-icon class="mr-2">mdi-play</v-icon>
                                Start
                            </v-btn>
                        </div>
                    </v-card>
                </div>
            </v-col>
        </v-row>

        <!-- Workflow Name Dialog -->
        <v-dialog v-model="workflowDialog" max-width="500px">
            <v-card>
                <v-card-title>
                    <span class="text-h5">Workflow erstellen</span>
                </v-card-title>
                <v-card-text>
                    <v-text-field
                        v-model="workflowName"
                        label="Workflow Name"
                        variant="outlined"
                        required
                    ></v-text-field>
                    <v-textarea
                        v-model="workflowDescription"
                        label="Beschreibung (optional)"
                        variant="outlined"
                        rows="3"
                    ></v-textarea>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" variant="text" @click="workflowDialog = false">
                        Abbrechen
                    </v-btn>
                    <v-btn 
                        color="primary" 
                        variant="elevated"
                        :loading="processing.workflow"
                        @click="submitWorkflowCreation"
                    >
                        Erstellen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

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
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// File handling
const selectedFiles = ref<File[]>([])
const acceptedFileTypes = ref('.pdf,.docx')

// Processing states
const processing = reactive({
    full: false,
    client: false,
    template: false,
    workflow: false
})

const processingStarted = ref(false)

// Chat interface
const chatMessages = ref<HTMLElement | null>(null)
const chatSteps = ref<Array<{
    title: string,
    description: string,
    status?: 'processing' | 'completed' | 'error',
    statusText?: string,
    result?: boolean,
    success?: boolean,
    resultText?: string,
    details?: any,
    isNew?: boolean,
    clientInfo?: any,
    templateInfo?: any
}>>([])

// Results
const results = ref<Array<{
    title: string,
    success: boolean,
    data: any,
    timestamp: string
}>>([])
const expandedPanel = ref<number[]>([])
const showResults = ref(false)
const currentResult = ref<any>(null)

// Processing results
const selectedClient = ref<any>(null)
const selectedTemplate = ref<any>(null)

// Workflow dialog
const workflowDialog = ref(false)
const workflowName = ref('')
const workflowDescription = ref('')

// UI state
const snackbar = reactive({
    show: false,
    text: '',
    color: 'success' as 'success' | 'error' | 'warning' | 'info'
})

// Computed properties
const isProcessing = computed(() => {
    return processing.full || processing.client || processing.template || processing.workflow
})

const allStepsCompleted = computed(() => {
    return chatSteps.value.length > 0 && chatSteps.value.every(step => step.status === 'completed')
})

// Chat utility functions
const getStatusText = () => {
    if (allStepsCompleted.value) return 'Alle Aufgaben abgeschlossen'
    if (isProcessing.value) return 'Verarbeitung läuft...'
    if (selectedFiles.value.length === 0) return 'Bereit für Dokumente'
    return 'Bereit für Verarbeitung'
}

const getFileUploadStepClass = () => {
    if (selectedFiles.value.length > 0) return 'completed'
    return 'pending'
}

const getStepClass = (stepNumber: number) => {
    const step = chatSteps.value[stepNumber - 2]
    if (!step) return 'pending'
    if (step.status === 'completed') return 'completed'
    if (step.status === 'processing') return 'active'
    if (step.status === 'error') return 'error'
    return 'pending'
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'completed': return 'success'
        case 'processing': return 'primary'
        case 'error': return 'error'
        default: return 'grey'
    }
}

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'completed': return 'mdi-check'
        case 'processing': return 'mdi-loading'
        case 'error': return 'mdi-alert'
        default: return 'mdi-circle-outline'
    }
}

// File handling methods
const onFilesSelected = (files: File[]) => {
    console.log('Files selected:', files)
}

const getFileIcon = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase()
    switch (extension) {
        case 'pdf':
            return 'mdi-file-pdf-box'
        case 'docx':
        case 'doc':
            return 'mdi-file-word-box'
        default:
            return 'mdi-file-document'
    }
}

const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Chat step management
const addChatStep = (
    title: string, 
    description: string, 
    status: 'processing' | 'completed' | 'error', 
    statusText: string
): number => {
    const newStep = {
        title,
        description,
        status,
        statusText,
        isNew: true
    }
    chatSteps.value.push(newStep)
    
    // Remove isNew flag after animation
    setTimeout(() => {
        newStep.isNew = false
    }, 500)
    
    return chatSteps.value.length - 1
}

const updateChatStep = (
    index: number,
    status: 'processing' | 'completed' | 'error',
    statusText: string,
    result: boolean,
    resultText: string,
    details?: any,
    clientInfo?: any,
    templateInfo?: any
) => {
    if (index >= 0 && index < chatSteps.value.length) {
        const step = chatSteps.value[index]
        step.status = status
        step.statusText = statusText
        step.result = result
        step.success = result
        step.resultText = resultText
        step.details = details
        if (clientInfo) step.clientInfo = clientInfo
        if (templateInfo) step.templateInfo = templateInfo
    }
}

// AI Agent API methods
const startFullProcessing = async () => {
    if (selectedFiles.value.length === 0) return

    processingStarted.value = true
    showResults.value = true

    // Step 1: Client Analysis
    await analyzeClientMatch()
    
    // Step 2: Template Suggestion
    await suggestTemplate()
    
    // Step 3: Create Workflow
    workflowName.value = `Automatischer Workflow ${new Date().toLocaleDateString()}`
    workflowDescription.value = 'Automatisch erstellter Workflow auf Basis des Dokumentenanalysen'
    await submitWorkflowCreation()
}



const analyzeClientMatch = async () => {
    if (selectedFiles.value.length === 0) return

    processing.client = true
    
    const stepIndex = addChatStep(
        'Kundenanalyse & Zuordnung',
        'Extrahiere Kundeninformationen und finde passende Kunden',
        'processing',
        'Analysiere Kundendaten...'
    )
    
    try {
        const formData = new FormData()
        selectedFiles.value.forEach(file => {
            formData.append('documents', file)
        })

        const response = await axios.post('/api/ai-agent/analyze-client-match', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        // Extract client information from response
        const clientInfo = {
            name: response.data.client?.name || response.data.matched_client?.name || 'Mandant gefunden',
            details: response.data.client?.details || response.data.confidence || 'Automatisch bestimmt'
        }
        selectedClient.value = clientInfo

        updateChatStep(stepIndex, 'completed', 'Kundenanalyse abgeschlossen', true, 'Kunden erfolgreich zugeordnet', response.data, clientInfo)
        
        currentResult.value = {
            title: 'Kundenanalyse & Zuordnung',
            success: true,
            data: response.data
        }
        showResults.value = true
        
        showNotification('Kundenanalyse erfolgreich abgeschlossen!', 'success')

    } catch (error: any) {
        console.error('Error analyzing client match:', error)
        updateChatStep(stepIndex, 'error', 'Fehler bei Kundenanalyse', false, 'Analyse fehlgeschlagen', error.response?.data || error.message)
        showNotification('Fehler bei der Kundenanalyse', 'error')
    } finally {
        processing.client = false
    }
}

const suggestTemplate = async () => {
    if (selectedFiles.value.length === 0) return

    processing.template = true
    
    const stepIndex = addChatStep(
        'Template-Vorschlag',
        'KI analysiert Dokumentinhalt und schlägt passende Templates vor',
        'processing',
        'Analysiere Templates...'
    )
    
    try {
        const formData = new FormData()
        selectedFiles.value.forEach(file => {
            formData.append('documents', file)
        })

        const response = await axios.post('/api/ai-agent/suggest-template', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        // Extract template information from response
        const templateInfo = {
            name: response.data.template?.name || response.data.suggested_template?.name || 'Vorlage vorgeschlagen',
            reason: response.data.template?.reason || response.data.reasoning || 'Optimal für diesen Dokumenttyp'
        }
        selectedTemplate.value = templateInfo

        updateChatStep(stepIndex, 'completed', 'Template-Vorschlag erstellt', true, 'Optimales Template gefunden', response.data, undefined, templateInfo)
        
        currentResult.value = {
            title: 'Template-Vorschlag',
            success: true,
            data: response.data
        }
        showResults.value = true
        
        showNotification('Template-Vorschlag erfolgreich erstellt!', 'success')

    } catch (error: any) {
        console.error('Error suggesting template:', error)
        updateChatStep(stepIndex, 'error', 'Fehler bei Template-Auswahl', false, 'Vorschlag fehlgeschlagen', error.response?.data || error.message)
        showNotification('Fehler beim Template-Vorschlag', 'error')
    } finally {
        processing.template = false
    }
}

const createIntelligentWorkflow = () => {
    if (selectedFiles.value.length === 0) return
    workflowDialog.value = true
}

const submitWorkflowCreation = async () => {
    if (!workflowName.value.trim()) {
        showNotification('Bitte geben Sie einen Workflow-Namen ein', 'warning')
        return
    }

    processing.workflow = true
    
    const stepIndex = addChatStep(
        'Intelligenter Workflow',
        'Erstelle kompletten Workflow mit intelligenter Verarbeitung',
        'processing',
        'Workflow wird erstellt...'
    )
    
    try {
        const formData = new FormData()
        selectedFiles.value.forEach(file => {
            formData.append('documents', file)
        })
        formData.append('workflow_name', workflowName.value)
        formData.append('workflow_description', workflowDescription.value)

        const response = await axios.post('/api/ai-agent/create-workflow', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        updateChatStep(stepIndex, 'completed', 'Workflow erfolgreich erstellt', true, 'Kompletter Workflow bereit', response.data)
        
        currentResult.value = {
            title: 'Intelligenter Workflow',
            success: true,
            data: response.data
        }
        showResults.value = true
        
        showNotification('Intelligenter Workflow erfolgreich erstellt!', 'success')
        workflowDialog.value = false
        workflowName.value = ''
        workflowDescription.value = ''

    } catch (error: any) {
        console.error('Error creating workflow:', error)
        updateChatStep(stepIndex, 'error', 'Fehler beim Workflow-Erstellen', false, 'Erstellung fehlgeschlagen', error.response?.data || error.message)
        showNotification('Fehler beim Erstellen des Workflows', 'error')
    } finally {
        processing.workflow = false
    }
}

// Helper methods
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
.ai-agent-view {
    margin: 0 auto;
    padding: 1.5rem;
    min-height: calc(100vh - 64px);
    max-width: 1000px;
}

/* Chat Container */
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
    background: #94754a;
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
    max-height: 70vh;
    overflow-y: auto;
}

/* Process Steps */
.process-step {
    display: flex;
    margin-bottom: 24px;
    animation: slideIn 0.3s ease-out;
}

.process-step.animate-step {
    animation: slideIn 0.5s ease-out;
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
    background: #f5f5f5;
    color: #999;
    border: 2px solid #e0e0e0;
    animation: pulse 2s infinite;
}

.step-number.completed {
    background: #4CAF50;
    color: white;
    border: 2px solid #4CAF50;
}

.step-number.error {
    background: #f44336;
    color: white;
    border: 2px solid #f44336;
}

.step-number.welcome {
    background: #e3f2fd;
    color: #94754a;
    border: 2px solid #94754a;
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
    line-height: 1.4;
}

.step-status {
    font-size: 0.875rem;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
}

.step-result {
    margin-top: 8px;
}

/* Chat Actions */
.chat-actions {
    padding: 16px 20px;
    border-top: 1px solid #e0e0e0;
    background: #fafafa;
}

/* Results Card */
.results-card {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    overflow: hidden;
}

.results-card .v-card-title {
    background: #f5f5f5;
    color: #333;
    padding: 16px 20px;
    border-bottom: 1px solid #e0e0e0;
    font-weight: 500;
    font-size: 1rem;
}

.current-result h4 {
    font-weight: 500;
    color: #333;
    margin-bottom: 8px;
}

.result-content {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    font-size: 0.875rem;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    line-height: 1.4;
}

/* Result Expansion Panels */
.result-expansion {
    margin-top: 8px;
}

.result-expansion-title {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
}

/* Main Interface */
.main-interface {
    margin-top: 0;
}

/* Button styling */
.v-btn {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.v-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* File chips */
.step-result .v-chip {
    margin-right: 8px;
    margin-bottom: 4px;
}

/* Client and template info */
.client-info, .template-info {
    margin-top: 8px;
}

.client-details, .template-reason {
    margin-top: 4px;
    padding-left: 4px;
}

.client-details small, .template-reason small {
    font-style: italic;
}

/* Animations */
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

@keyframes spin {
    from { 
        transform: rotate(0deg);
    }
    to { 
        transform: rotate(360deg);
    }
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Loading icon animation */
.v-icon.mdi-loading {
    animation: spin 1s linear infinite;
}

/* Responsive design */
@media (max-width: 768px) {
    .ai-agent-view {
        padding: 1rem;
    }
    
    .chat-container {
        margin: 0;
    }
    
    .chat-messages {
        padding: 12px;
        max-height: 60vh;
    }
    
    .chat-actions {
        padding: 12px;
    }
    
    .process-step {
        margin-bottom: 16px;
    }
    
    .step-number {
        width: 28px;
        height: 28px;
        font-size: 12px;
    }
    
    .step-content {
        padding-top: 2px;
    }
    
    .step-title {
        font-size: 0.9rem;
    }
    
    .step-description {
        font-size: 0.8rem;
    }
}
</style> 