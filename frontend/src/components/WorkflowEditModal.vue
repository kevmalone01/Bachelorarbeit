<template>
    <v-dialog v-model="show" max-width="800" persistent>
        <v-card class="workflow-edit-modal">
            <v-card-title class="workflow-edit-header pa-8">
                <div class="d-flex justify-space-between align-center w-100">
                    <div>
                        <h2 class="modal-title mb-2">Workflow bearbeiten</h2>
                    </div>
                    <v-btn
                        @click="closeModal"
                        icon="mdi-close"
                        variant="text"
                        size="small"
                        class="close-btn"
                    />
                </div>
            </v-card-title>

            <v-card-text class="modal-content pa-4 pt-2">
                <v-form v-if="editForm && props.workflow && !isLoadingWorkflow" ref="form" @submit.prevent="saveWorkflow">
                    <v-row>
                        <!-- Workflow Name -->
                        <v-col cols="12" md="6">
                            <v-text-field
                                v-model="editForm.name"
                                label="Workflow Name *"
                                variant="outlined"
                                density="comfortable"
                                prepend-inner-icon="mdi-file-document-edit"
                                :rules="[v => !!v || 'Name ist erforderlich']"
                                class="edit-field"
                            />
                        </v-col>

                        <!-- Priority -->
                        <v-col cols="12" md="6">
                            <v-select
                                v-model="editForm.priority"
                                :items="priorityItems"
                                item-title="title"
                                item-value="value"
                                label="Priorität"
                                variant="outlined"
                                density="comfortable"
                                prepend-inner-icon="mdi-flag"
                                class="edit-field"
                            />
                        </v-col>

                        <!-- Status -->
                        <v-col cols="12" md="6">
                            <v-select
                                v-model="editForm.status"
                                :items="statusItems"
                                item-title="title"
                                item-value="value"
                                label="Status"
                                variant="outlined"
                                density="comfortable"
                                prepend-inner-icon="mdi-clipboard-check"
                                class="edit-field"
                            />
                        </v-col>

                        <!-- Client Selection -->
                        <v-col cols="12" md="6">
                            <v-select
                                v-model="editForm.client_id"
                                :items="clients"
                                item-title="displayName"
                                item-value="id"
                                label="Mandant"
                                variant="outlined"
                                density="comfortable"
                                prepend-inner-icon="mdi-account-tie"
                                class="edit-field"
                                :loading="isLoadingClients"
                            >
                                <template #item="{ props, item }">
                                    <v-list-item v-bind="props">
                                        <template #prepend>
                                            <v-avatar size="32" color="primary" variant="tonal">
                                                <v-icon size="16">
                                                    {{ item.raw.client_type === 'natural' ? 'mdi-account' : 'mdi-domain' }}
                                                </v-icon>
                                            </v-avatar>
                                        </template>
                                        <v-list-item-title>{{ item.raw.displayName }}</v-list-item-title>
                                        <v-list-item-subtitle>
                                            {{ item.raw.client_type === 'natural' ? 'Natürliche Person' : 'Unternehmen' }}
                                        </v-list-item-subtitle>
                                    </v-list-item>
                                </template>
                            </v-select>
                        </v-col>

                        <!-- Due Date -->
                        <v-col cols="12" md="6">
                            <v-text-field
                                v-model="editForm.due_date"
                                label="Fälligkeitsdatum"
                                variant="outlined"
                                density="comfortable"
                                type="date"
                                prepend-inner-icon="mdi-calendar"
                                class="edit-field"
                            />
                        </v-col>

                        <!-- Assigned To -->
                        <v-col cols="12" md="6">
                            <v-select
                                v-model="editForm.assigned_to"
                                :items="workers"
                                item-title="name"
                                item-value="id"
                                label="Bearbeiter"
                                variant="outlined"
                                density="comfortable"
                                prepend-inner-icon="mdi-account-cog"
                                class="edit-field"
                            />
                        </v-col>

                        <!-- Description -->
                        <v-col cols="12">
                            <v-textarea
                                v-model="editForm.description"
                                label="Beschreibung"
                                variant="outlined"
                                density="comfortable"
                                rows="3"
                                prepend-inner-icon="mdi-text"
                                class="edit-field"
                            />
                        </v-col>
                    </v-row>

                    <!-- Workflow Info -->
                    <v-card variant="outlined" class="info-card mt-4">
                        <v-card-text class="pa-4">
                            <h4 class="info-title mb-3">Workflow Information</h4>
                            <v-row>
                                <v-col cols="6" md="3">
                                    <div class="info-item">
                                        <span class="info-label">Erstellt:</span>
                                        <span class="info-value">{{ formatDate(workflow?.createdAt) }}</span>
                                    </div>
                                </v-col>
                                <v-col cols="6" md="3">
                                    <div class="info-item">
                                        <span class="info-label">ID:</span>
                                        <span class="info-value">#{{ workflow?.id }}</span>
                                    </div>
                                </v-col>
                                <v-col cols="6" md="3">
                                    <div class="info-item">
                                        <span class="info-label">Dokumente:</span>
                                        <span class="info-value">{{ workflow?.documentCount || 0 }}</span>
                                    </div>
                                </v-col>
                                <v-col cols="6" md="3">
                                    <div class="info-item">
                                        <span class="info-label">Template:</span>
                                        <span class="info-value">{{ workflow?.template_id ? `#${workflow.template_id}` : 'Keine' }}</span>
                                    </div>
                                </v-col>
                            </v-row>
                        </v-card-text>
                    </v-card>
                </v-form>

                <!-- Loading State -->
                <div v-else-if="isLoadingWorkflow || !props.workflow" class="text-center py-8">
                    <v-progress-circular indeterminate color="brown" />
                    <p class="mt-4">Lade Workflow-Daten...</p>
                </div>
                
                <!-- No workflow selected -->
                <div v-else class="text-center py-8">
                    <v-icon size="64" color="grey-lighten-2" class="mb-4">mdi-clipboard-text-outline</v-icon>
                    <h4 class="mb-2">Kein Workflow ausgewählt</h4>
                    <p class="text-grey">Wählen Sie einen Workflow zum Bearbeiten aus.</p>
                </div>
            </v-card-text>

            <v-card-actions class="workflow-edit-actions pa-8">
                <v-btn
                    @click="confirmDelete"
                    variant="outlined"
                    size="large"
                    color="error"
                    prepend-icon="mdi-delete"
                    class="delete-btn"
                >
                    Löschen
                </v-btn>
                <v-spacer />
                <v-btn
                    @click="saveWorkflow"
                    :disabled="!isFormValid || isLoadingWorkflow"
                    :loading="isSaving"
                    size="large"
                    color="brown"
                    variant="outlined"
                    prepend-icon="mdi-content-save"
                    class="save-btn"
                >
                    Speichern
                </v-btn>
            </v-card-actions>
        </v-card>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="showDeleteDialog" max-width="500">
            <v-card class="delete-dialog">
                <v-card-title class="pa-6">
                    <div class="d-flex align-center">
                        <v-icon color="error" size="32" class="me-3">mdi-alert-circle</v-icon>
                        <span class="delete-title">Workflow löschen</span>
                    </div>
                </v-card-title>
                <v-card-text class="pa-6 pt-0">
                    <p class="delete-message">
                        Sind Sie sicher, dass Sie den Workflow 
                        <strong>"{{ workflow?.name }}"</strong> 
                        löschen möchten?
                    </p>
                    <p class="delete-warning">
                        Diese Aktion kann nicht rückgängig gemacht werden.
                    </p>
                </v-card-text>
                <v-card-actions class="pa-6 pt-0">
                    <v-spacer />
                    <v-btn
                        @click="showDeleteDialog = false"
                        variant="outlined"
                        class="cancel-btn"
                    >
                        Abbrechen
                    </v-btn>
                    <v-btn
                        @click="deleteWorkflow"
                        :loading="isDeleting"
                        color="error"
                        prepend-icon="mdi-delete"
                        class="delete-confirm-btn"
                    >
                        Löschen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { WorkflowAPI } from '@/services/api'

// Props
interface Props {
    modelValue: boolean
    workflow: any
    clients: any[]
    isLoadingClients?: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
    'update:modelValue': [value: boolean]
    'workflow-updated': [workflow: any]
    'workflow-deleted': [workflowId: number]
    'show-notification': [message: string, color: 'success' | 'error' | 'warning' | 'info']
}>()

// Reactive data
const show = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value)
})

const editForm = ref<any>({
    name: '',
    priority: 'medium',
    status: 'to do',
    client_id: null,
    due_date: '',
    assigned_to: null,
    description: ''
})
const form = ref()
const isSaving = ref(false)
const isDeleting = ref(false)
const isLoadingWorkflow = ref(false)
const showDeleteDialog = ref(false)

// Form validation
const isFormValid = computed(() => {
    return editForm.value?.name?.trim() && editForm.value?.client_id && props.workflow
})

// Data arrays
const statusItems = ref([
    { title: 'Zu erledigen', value: 'to do' },
    { title: 'In Arbeit', value: 'in progress' },
    { title: 'Abgeschlossen', value: 'done' }
])

const priorityItems = ref([
    { title: 'Hoch', value: 'high' },
    { title: 'Mittel', value: 'medium' },
    { title: 'Niedrig', value: 'low' }
])

const workers = ref([
    { id: 1, name: 'Dr. Schmidt', role: 'Senior Berater' },
    { id: 2, name: 'M. Weber', role: 'Steuerberater' },
    { id: 3, name: 'A. Müller', role: 'Buchhalter' },
    { id: 4, name: 'R. Fischer', role: 'Rechtsanwalt' }
])

// Initialize form with default values
const initializeForm = async () => {
    if (!props.workflow) {
        // Initialize with empty form
        editForm.value = {
            name: '',
            priority: 'medium',
            status: 'to do',
            client_id: null,
            due_date: '',
            assigned_to: null,
            description: ''
        }
        return
    }
    
    try {
        isLoadingWorkflow.value = true
        
        // Load fresh workflow data from API
        const response = await WorkflowAPI.getWorkOrder(props.workflow.id)
        const freshWorkflowData = response.data
        
        // Initialize with fresh workflow data
        editForm.value = {
            name: freshWorkflowData.title || freshWorkflowData.name || props.workflow.name || '',
            priority: freshWorkflowData.priority || 'medium',
            status: mapAPIStatusToDisplay(freshWorkflowData.status) || props.workflow.status || 'to do',
            client_id: freshWorkflowData.client_id || props.workflow.client_id || null,
            due_date: freshWorkflowData.due_date ? freshWorkflowData.due_date.split('T')[0] : (props.workflow.due_date || props.workflow.dueDate || ''),
            assigned_to: freshWorkflowData.assigned_to || props.workflow.assigned_to || null,
            description: freshWorkflowData.description || props.workflow.description || ''
        }
        
    } catch (error) {
        console.error('Error loading workflow details:', error)
        
        // Fallback to props data
        editForm.value = {
            name: props.workflow.name || '',
            priority: props.workflow.priority || 'medium',
            status: props.workflow.status || 'to do',
            client_id: props.workflow.client_id || null,
            due_date: props.workflow.due_date || props.workflow.dueDate || '',
            assigned_to: props.workflow.assigned_to || null,
            description: props.workflow.description || ''
        }
        
        emit('show-notification', 'Fehler beim Laden der aktuellen Workflow-Daten. Verwende gespeicherte Daten.', 'warning')
    } finally {
        isLoadingWorkflow.value = false
    }
}

// Helper function to map API status to display status
const mapAPIStatusToDisplay = (apiStatus: string) => {
    switch (apiStatus?.toLowerCase()) {
        case 'open':
            return 'to do'
        case 'in_progress':
        case 'in progress':
        case 'processing':
            return 'in progress'
        case 'completed':
        case 'done':
        case 'finished':
        case 'closed':
            return 'done'
        default:
            return apiStatus || 'to do'
    }
}

// Watch for workflow changes and modal opening
watch(() => props.workflow, (newWorkflow) => {
    if (newWorkflow) {
        initializeForm()
    }
}, { immediate: true })

// Watch for modal opening
watch(() => props.modelValue, (isOpen) => {
    if (isOpen) {
        initializeForm()
    }
})

const formatDate = (dateString: string) => {
    if (!dateString) return 'Nicht gesetzt'
    const date = new Date(dateString)
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}

const closeModal = () => {
    show.value = false
    // Reset form to default values
    editForm.value = {
        name: '',
        priority: 'medium',
        status: 'to do',
        client_id: null,
        due_date: '',
        assigned_to: null,
        description: ''
    }
    if (form.value) {
        form.value.resetValidation()
    }
}

const saveWorkflow = async () => {
    if (!isFormValid.value || !props.workflow) return
    
    try {
        isSaving.value = true
        
        // Prepare data for API
        const updateData = {
            title: editForm.value.name,
            priority: editForm.value.priority,
            status: mapStatusToAPI(editForm.value.status),
            client_id: editForm.value.client_id,
            due_date: editForm.value.due_date || null,
            description: editForm.value.description
        }
        
        // Call API to update workflow
        const response = await WorkflowAPI.updateWorkOrder(props.workflow.id, updateData)
        const updatedWorkflow = response.data
        
        // Emit success
        emit('workflow-updated', updatedWorkflow)
        emit('show-notification', 'Workflow erfolgreich aktualisiert!', 'success')
        closeModal()
        
    } catch (error) {
        console.error('Error updating workflow:', error)
        emit('show-notification', 'Fehler beim Aktualisieren des Workflows.', 'error')
    } finally {
        isSaving.value = false
    }
}

const confirmDelete = () => {
    showDeleteDialog.value = true
}

const deleteWorkflow = async () => {
    if (!props.workflow) return
    
    try {
        isDeleting.value = true
        
        // Call API to delete workflow
        await WorkflowAPI.deleteWorkOrder(props.workflow.id)
        
        // Emit success
        emit('workflow-deleted', props.workflow.id)
        emit('show-notification', 'Workflow erfolgreich gelöscht!', 'success')
        
        // Close dialogs
        showDeleteDialog.value = false
        closeModal()
        
    } catch (error) {
        console.error('Error deleting workflow:', error)
        emit('show-notification', 'Fehler beim Löschen des Workflows.', 'error')
    } finally {
        isDeleting.value = false
    }
}

// Helper function to map display status to API status
const mapStatusToAPI = (displayStatus: string) => {
    switch (displayStatus) {
        case 'to do':
            return 'open'
        case 'in progress':
            return 'in_progress'
        case 'done':
            return 'completed'
        default:
            return displayStatus
    }
}
</script>

<style scoped>
.workflow-edit-modal {
    border-radius: 20px !important;
    overflow: hidden;
    max-height: 90vh !important;
}

.workflow-edit-header {
}

.modal-content {
    max-height: 60vh;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    scrollbar-color: #94754a #f5f2ee;
}

/* Webkit Scrollbar Styling */
.modal-content::-webkit-scrollbar {
    width: 8px;
}

.modal-content::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 10px;
    margin: 8px 0;
}

.modal-content::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #b8956d 0%, #94754a 100%);
    border-radius: 10px;
    border: 1px solid rgba(232, 221, 208, 0.3);
    box-shadow: 0 2px 8px rgba(148, 117, 74, 0.4);
    transition: all 0.3s ease;
}

.modal-content::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #94754a 0%, #7a5d3a 100%);
    box-shadow: 0 4px 12px rgba(148, 117, 74, 0.6);
    transform: scaleX(1.3);
    border: 1px solid rgba(232, 221, 208, 0.5);
}

.modal-content::-webkit-scrollbar-thumb:active {
    background: linear-gradient(180deg, #7a5d3a 0%, #5d462c 100%);
    box-shadow: 0 2px 6px rgba(148, 117, 74, 0.8);
    transform: scaleX(1.1);
}

.modal-content::-webkit-scrollbar-corner {
    background: transparent;
}

/* Custom scrollbar for Firefox */
.modal-content {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 117, 74, 0.8) transparent;
}

.modal-title {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

.modal-subtitle {
    color: #d4c4b0 !important;
    font-weight: 500 !important;
}

.edit-field {
    border-radius: 12px;
}

.info-card {
    border-color: #d4c4b0 !important;
}

.info-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.info-label {
    font-size: 0.75rem !important;
    color: #6b5d4f !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.info-value {
    font-size: 0.875rem !important;
    color: #4a3528 !important;
    font-weight: 600 !important;
}

.workflow-edit-actions {
}

.save-btn {
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.cancel-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.delete-btn {
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

/* Delete Dialog */
.delete-dialog {
    border-radius: 16px !important;
}

.delete-title {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.delete-message {
    font-size: 1rem !important;
    color: #4a3528 !important;
    margin-bottom: 0.5rem;
}

.delete-warning {
    font-size: 0.875rem !important;
    color: #d32f2f !important;
    font-weight: 500 !important;
}

.delete-confirm-btn {
    border-radius: 8px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

/* Responsive */
@media (max-width: 600px) {
    .workflow-edit-modal {
        margin: 1rem;
        max-width: calc(100vw - 2rem) !important;
        max-height: 95vh !important;
    }
    
    .modal-content {
        max-height: 70vh;
    }
    
    .workflow-edit-actions {
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .workflow-edit-actions .v-btn {
        width: 100%;
    }
}
</style> 