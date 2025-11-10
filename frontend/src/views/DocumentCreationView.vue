<template>
    <div class="document-creation-container">
        <!-- View toggle switch -->
        <div class="view-toggle-container">
            <div class="view-toggle">
                <input type="radio" id="list-view" value="list" v-model="viewMode" />
                <label :class="{ active: viewMode === 'list' }" for="list-view">
                    <v-icon size="small" class="toggle-icon">mdi-format-list-bulleted</v-icon>
                    Dokumentenliste
                </label>
                <input type="radio" id="form-view" value="form" v-model="viewMode" />
                <label :class="{ active: viewMode === 'form' }" for="form-view">
                    <v-icon size="small" class="toggle-icon">mdi-file-document-plus-outline</v-icon>
                    Erstellen
                </label>
            </div>
        </div>

        <!-- Dynamic content based on selected view -->
        <transition name="fade" mode="out-in">
            <!-- Document List View -->
            <div v-if="viewMode === 'list'" class="list-view">
                <!-- This is where the document list component would go -->
                <DocumentList @view-document="handleViewDocument" />
            </div>
            
            <!-- Document Creation View -->
            <div v-else class="create-view">
                <v-card-text>
                    <div class="split-view">
                        <div class="mask-editor">
                            <div class="editor-toolbar">
                                <v-btn color="brown" prepend-icon="mdi-upload" @click="triggerFileInput">
                                    Dokument hochladen
                                </v-btn>
                                <v-btn color="brown" prepend-icon="mdi-content-save" :disabled="!uploadedDocument && !documentId"
                                    @click="saveTemplate" :loading="isSaving">
                                    {{ documentId ? 'Template aktualisieren' : 'Template speichern' }}
                                </v-btn>
                                <v-chip 
                                    v-if="documentId && isAutoSaving" 
                                    color="info" 
                                    size="small" 
                                    variant="outlined"
                                    class="ml-2"
                                >
                                    <v-icon size="x-small" class="mr-1">mdi-content-save</v-icon>
                                    Wird gespeichert...
                                </v-chip>
                            </div>

                            <!-- File upload input (hidden) -->
                            <input ref="fileInput" type="file" accept=".pdf,.docx" style="display: none"
                                @change="handleFileUpload" />

                            <!-- Upload dropzone -->
                            <div v-if="!uploadedDocument && !documentId" 
                                class="upload-zone"
                                :class="{ 'upload-zone--active': dragover }"
                                @drop="handleFileDrop" 
                                @dragover.prevent="dragover = true" 
                                @dragleave.prevent="dragover = false"
                                @click="triggerFileInput">
                                <div class="upload-zone-content">
                                    <v-icon size="64" class="upload-icon mb-4" color="brown">mdi-cloud-upload-outline</v-icon>
                                    <h3 class="upload-title mb-3">Dokument hier ablegen</h3>
                                    <p class="upload-subtitle mb-6">oder klicken zum Auswählen</p>
                                    <v-btn 
                                        variant="outlined" 
                                        prepend-icon="mdi-folder-open-outline"
                                        class="upload-btn"
                                        size="large"
                                        color="brown"
                                    >
                                        Datei auswählen
                                    </v-btn>
                                    <p class="upload-hint mt-4">
                                        Unterstützte Formate: PDF, DOCX (Max. 10MB pro Datei)
                                    </p>
                                </div>
                            </div>

                            <!-- Upload progress -->
                            <v-progress-linear color="brown" v-if="isUploading" :model-value="uploadProgress" height="15" style="margin-top: 10px; border-radius: 10px;">
                                <template v-slot:default>
                                    <strong>{{ Math.ceil(uploadProgress) }}%</strong>
                                </template>
                            </v-progress-linear>

                            <!-- Document details after upload or template loaded -->
                            <div v-if="(uploadedDocument || documentId) && !showTestMask" class="editor-workspace">
                                <v-tabs v-model="activeTab" color="brown" class="mb-4">
                                    <v-tab value="settings">Dokument-Einstellungen</v-tab>
                                    <v-tab value="mask">Formular</v-tab>
                                </v-tabs>

                                <v-window v-model="activeTab">
                                    <v-window-item value="settings">
                                        <!-- Template editing notification -->
                                        <v-alert
                                            v-if="documentId"
                                            type="info"
                                            variant="tonal"
                                            class="mb-4"
                                            icon="mdi-information"
                                            color="brown"
                                        >
                                            Sie bearbeiten das Template "{{ templateName }}". Änderungen an Platzhaltern werden automatisch gespeichert.
                                        </v-alert>

                                        <v-card class="mb-4 settings-card">
                                            <v-card-text>
                                                <v-text-field v-model="templateName" label="Template-Name"
                                                    placeholder="Geben Sie einen Namen für dieses Template ein" variant="outlined"
                                                    required></v-text-field>

                                                <v-textarea v-model="templateDescription" label="Beschreibung"
                                                    placeholder="Beschreiben Sie den Zweck dieses Templates" variant="outlined"
                                                    rows="3"></v-textarea>
                                            </v-card-text>
                                        </v-card>

                                        <v-card class="placeholders-card">
                                            <v-card-title class="d-flex align-center justify-space-between">
                                                <span class="text-h6">Erkannte Platzhalter</span>
                                                <!-- <v-btn color="brown" icon="mdi-plus" @click="addField"
                                                    :disabled="!uploadedDocument"></v-btn> -->
                                            </v-card-title>
                                            <v-card-text>
                                                <div v-if="placeholders.length === 0" class="text-center empty-state">
                                                    <v-icon size="48" color="grey">mdi-text-box-outline</v-icon>
                                                    <p>Keine Platzhalter erkannt. Fügen Sie manuell Felder hinzu oder laden Sie ein
                                                        Dokument mit Platzhaltern hoch.</p>
                                                </div>
                                                <v-list v-else class="placeholders-list">
                                                    <v-list-item v-for="(placeholder, index) in placeholders" :key="index"
                                                        class="placeholder-item" :class="{ 'client-field-item': placeholder.isClientField }">
                                                        <v-list-item-title class="d-flex align-center">
                                                            
                                                            <v-icon v-if="placeholder.isClientField" size="small" color="brown" class="mr-2">
                                                                mdi-account-outline
                                                            </v-icon>
                                                            <span>{{ placeholder.name }}</span>
                                                            <v-chip size="small" class="ml-2" :color="getTypeColor(placeholder.type)">
                                                                {{ placeholder.type }}
                                                            </v-chip>
                                                            <v-chip v-if="placeholder.isClientField" 
                                                                size="small" 
                                                                class="ml-2" 
                                                                color="brown" 
                                                                variant="outlined">
                                                                {{ placeholder.clientFieldGroup }}
                                                            </v-chip>
                                                        </v-list-item-title>
                                                        <v-list-item-subtitle v-if="placeholder.isClientField" class="mt-1">
                                                            Mandanten-Feld: {{ getClientFieldDisplayName(placeholder.clientFieldName) }}
                                                        </v-list-item-subtitle>
                                                        <template v-slot:append>
                                                            <v-btn icon="mdi-tune" variant="text" density="compact" color="brown"
                                                                @click="editPlaceholder(index)"></v-btn>
                                                        </template>
                                                    </v-list-item>
                                                </v-list>
                                            </v-card-text>
                                        </v-card>
                                    </v-window-item>

                                    <v-window-item value="mask">
                                        <DynamicMask 
                                            key="main-mask"
                                            :placeholders="placeholders || []" 
                                            :initial-values="allPlaceholderValues || {}"
                                            :client-field-groups="clientFieldGroups || []"
                                            :clients="clients || []"
                                            :title="'Test: ' + (templateName || 'Dokumenten-Maske')" 
                                            @update:values="updateTestValues"
                                            @client-selected="onClientSelected"
                                            @submit="generatePreview" />
                                    </v-window-item>
                                </v-window>
                            </div>
                        </div>
                        <div class="preview-workspace">
                            <DocumentPreview
                                v-if="uploadedDocument || documentId"
                                ref="documentPreviewRef"
                                :documentId="documentId"
                                :documentFile="uploadedDocument"
                                :placeholderValues="allPlaceholderValues"
                                :title="templateName || 'Dokument-Vorschau'"
                                :autoGenerate="false"
                                :initialViewMode="previewMode"
                                @preview-generated="onPreviewGenerated"
                                @error="onPreviewError"
                                @view-mode-change="handleViewModeChange"
                            />
                            
                            <!-- Show generated time for PDF -->
                            <div v-if="previewMode === 'pdf' && pdfLastGeneratedAt" class="pdf-timestamp">
                                <v-chip
                                    color="success"
                                    size="small"
                                    variant="outlined"
                                    prepend-icon="mdi-check-circle"
                                >
                                    PDF generiert: {{ formatTimestamp(pdfLastGeneratedAt) }}
                                </v-chip>
                            </div>
                            <div v-else-if="(uploadedDocument || documentId) && isLoadingPreview" class="loading-preview">
                                <v-progress-circular indeterminate color="brown" size="64"></v-progress-circular>
                                <p>Dokument wird für die Vorschau vorbereitet...</p>
                            </div>
                        </div>
                    </div>
                </v-card-text>
            </div>
        </transition>

        <!-- Placeholder Dialog -->
        <v-dialog v-model="showPlaceholderDialog" max-width="700px">
            <v-card>
                <v-card-title>{{ editingPlaceholderIndex === -1 ? 'Feld hinzufügen' : 'Feld bearbeiten' }}</v-card-title>
                <v-card-text>
                    <!-- Client field configuration -->
                    <v-checkbox 
                        v-model="editingPlaceholder.isClientField" 
                        label="Dieses Feld mit Mandanten-Daten verknüpfen"
                        @update:model-value="onClientFieldToggle">
                    </v-checkbox>

                    <div v-if="editingPlaceholder.isClientField" class="client-field-config">
                        <v-text-field 
                            v-model="editingPlaceholder.clientFieldGroup"
                            label="Mandanten-Gruppe"
                            placeholder="z.B. 1, 2, 3"
                            hint="Eindeutige Bezeichnung für die Mandanten-Gruppe"
                            variant="outlined"
                            class="mb-3">
                        </v-text-field>

                        <v-select 
                            v-model="selectedClientFieldName"
                            label="Mandanten-Feldname"
                            :items="getClientFieldNames()"
                            hint="Wählen Sie das entsprechende Mandanten-Feld aus"
                            variant="outlined"
                            @update:model-value="onClientFieldNameChange">
                        </v-select>

                        <!-- <v-alert type="info" variant="tonal" class="mt-3 mb-3">
                            <div class="text-body-2">
                                <strong>Mandanten-Feld:</strong> {{ selectedClientFieldName || 'Nicht ausgewählt' }}<br>
                                <strong>Datenbank-Feld:</strong> {{ editingPlaceholder.clientFieldName || 'Nicht zugeordnet' }}
                            </div>
                        </v-alert> -->
                    </div>


                    <v-text-field v-if="!editingPlaceholder.isClientField" v-model="editingPlaceholder.name" label="Feldname"
                        placeholder="z.B. vorname, nachname, geburtsdatum" variant="outlined" required
                        :disabled="editingPlaceholder.isClientField"></v-text-field>

                    <v-select v-if="!editingPlaceholder.isClientField" v-model="editingPlaceholder.type" label="Feldtyp" :items="fieldTypes" variant="outlined"
                        required @update:model-value="onFieldTypeChange" 
                        :disabled="editingPlaceholder.isClientField"></v-select>

                    <!-- Standard field configuration (disabled for client fields) -->
                    <div v-if="!editingPlaceholder.isClientField">
                        <!-- Dynamic field for entering a default value depending on the type -->
                        <v-text-field v-if="editingPlaceholder.type === 'text' || editingPlaceholder.type === 'textarea'" 
                            v-model="editingPlaceholder.defaultValue" label="Standardwert"
                            placeholder="z.B. Max Mustermann" variant="outlined"></v-text-field>
                            
                        <v-text-field v-else-if="editingPlaceholder.type === 'number'" 
                            v-model.number="editingPlaceholder.defaultValue" label="Standardwert" type="number"
                            placeholder="z.B. 100" variant="outlined"></v-text-field>
                            
                        <v-text-field v-else-if="editingPlaceholder.type === 'date'" 
                            v-model="editingPlaceholder.defaultValue" label="Standardwert" type="date"
                            variant="outlined"></v-text-field>
                            
                        <v-checkbox v-else-if="editingPlaceholder.type === 'checkbox'" 
                            v-model="editingPlaceholder.defaultValue" label="Standardwert"></v-checkbox>
                            
                        <v-select v-else-if="editingPlaceholder.type === 'select' && editingPlaceholder.options && editingPlaceholder.options.length > 0" 
                            v-model="editingPlaceholder.defaultValue" label="Standardwert" 
                            :items="editingPlaceholder.options" variant="outlined"></v-select>
                        
                        <v-text-field v-else
                            v-model="editingPlaceholder.defaultValue" label="Standardwert"
                            placeholder="Standardwert eingeben" variant="outlined"></v-text-field>

                        <v-checkbox v-model="editingPlaceholder.required" label="Erforderlich"></v-checkbox>

                        <v-text-field v-if="editingPlaceholder.type === 'select'" v-model="optionsInput"
                            label="Auswahloptionen" placeholder="Option 1, Option 2, Option 3"
                            hint="Komma-getrennte Liste von Optionen" variant="outlined"></v-text-field>

                        <v-expansion-panels v-model="validationPanel">
                            <v-expansion-panel>
                                <v-expansion-panel-title>Validierungsregeln</v-expansion-panel-title>
                                <v-expansion-panel-text>
                                    <v-text-field v-if="['text', 'textarea'].includes(editingPlaceholder.type)"
                                        v-model.number="editingPlaceholder.validation.minLength" label="Minimale Länge"
                                        type="number" variant="outlined"></v-text-field>

                                    <v-text-field v-if="['text', 'textarea'].includes(editingPlaceholder.type)"
                                        v-model.number="editingPlaceholder.validation.maxLength" label="Maximale Länge"
                                        type="number" variant="outlined"></v-text-field>

                                    <v-text-field v-if="editingPlaceholder.type === 'number'"
                                        v-model.number="editingPlaceholder.validation.min" label="Minimalwert" type="number"
                                        variant="outlined"></v-text-field>

                                    <v-text-field v-if="editingPlaceholder.type === 'number'"
                                        v-model.number="editingPlaceholder.validation.max" label="Maximalwert" type="number"
                                        variant="outlined"></v-text-field>

                                    <v-text-field v-if="['text', 'textarea'].includes(editingPlaceholder.type)"
                                        v-model="editingPlaceholder.validation.pattern" label="Regex-Muster"
                                        placeholder="z.B. ^[0-9]{5}$ für PLZ" variant="outlined"></v-text-field>

                                    <v-text-field v-model="editingPlaceholder.validation.errorMessage" label="Fehlermeldung"
                                        placeholder="Benutzerdefinierte Fehlermeldung bei ungültiger Eingabe"
                                        variant="outlined"></v-text-field>
                                </v-expansion-panel-text>
                            </v-expansion-panel>
                        </v-expansion-panels>
                    </div>
                    <div v-else>
                        <v-alert type="warning" variant="tonal">
                            Mandanten-Felder verwenden automatisch die Daten des ausgewählten Mandanten. 
                            Standardwerte und Validierungsregeln sind nicht verfügbar.
                        </v-alert>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" @click="cancelPlaceholderEdit">Abbrechen</v-btn>
                    <v-btn color="brown" @click="savePlaceholderEdit">Speichern</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

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
import { ref, reactive, computed, onUnmounted, watch, onMounted, nextTick } from 'vue'
import store from '@/store/store'
import DynamicMask from '@/components/DynamicMask.vue'
import DocumentPreview from '@/components/DocumentPreview.vue'
import DocumentList from '@/components/DocumentList.vue'
import mammoth from 'mammoth'
import { DocumentAPI } from '@/services/api'

// View toggle
const viewMode = ref<string>('list') // Default to form view

// Refs for file upload
const fileInput = ref<HTMLInputElement | null>(null)
const uploadedDocument = ref<File | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const dragover = ref(false)

// Template metadata
const templateName = ref('')
const templateDescription = ref('')

// Loading states
const isSaving = ref(false)
const isAutoSaving = ref(false)

// Placeholder management
interface Placeholder {
    name: string;
    type: string;
    required: boolean;
    defaultValue?: any;
    options?: string[];
    validation: {
        pattern?: string;
        min?: number;
        max?: number;
        minLength?: number;
        maxLength?: number;
        errorMessage?: string;
    };
    // Client field properties
    isClientField?: boolean;
    clientFieldGroup?: string; // e.g., "1", "2", "3"
    clientFieldName?: string; // The actual client property name
}

const placeholders = ref<Placeholder[]>([])
const showPlaceholderDialog = ref(false)
const editingPlaceholderIndex = ref(-1)
const editingPlaceholder = reactive<Placeholder>({
    name: '',
    type: 'text',
    required: false,
    validation: {}
})
const optionsInput = ref('')
const validationPanel = ref(-1)

// Client field management
const selectedClientFieldName = ref('')

// Field types for selection
const fieldTypes = [
    'text',
    'number',
    'date',
    'select',
    'checkbox',
    'textarea'
]

// Test and preview
const showTestMask = ref(false)
const testValues = ref<Record<string, any>>({})
const showPreview = ref(true)
const previewUrl = ref('')
const documentPreviewRef = ref<InstanceType<typeof DocumentPreview> | null>(null)
const documentId = ref<number | undefined>(undefined)
const previewMode = ref('text') // Default to text preview
const isLoadingTextPreview = ref(false)
const documentText = ref('') // Store the document text content
const pdfLastGeneratedAt = ref<Date | null>(null) // Track when PDF was last generated

// Client management
const clients = computed(() => {
    const storeClients = store.getters['client/getClients'];
    
    // Add null check to prevent errors
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
    // Add null checks to prevent errors
    if (!Array.isArray(placeholders.value)) {
        return [];
    }
    
    const groups: Record<string, Placeholder[]> = {}
    
    placeholders.value.forEach(placeholder => {
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

// Computed property that combines all placeholder values including client fields
const allPlaceholderValues = computed(() => {
    // Start with testValues
    let combinedValues = { ...testValues.value }
    
    // Ensure all placeholder values are properly included
    if (Array.isArray(placeholders.value)) {
        placeholders.value.forEach(placeholder => {
            if (placeholder?.name && testValues.value[placeholder.name] !== undefined) {
                combinedValues[placeholder.name] = testValues.value[placeholder.name]
            }
        })
    }
    
    return combinedValues
})

// Client field mapping for easier management
const CLIENT_FIELD_MAPPING = {
    // Common fields for both person and company
    'Mandatsmanager': 'mandate_manager',
    'Mandatsverantwortlicher': 'mandate_responsible', 
    'E-Mail': 'email',
    'Steuernummer': 'tax_number',
    'Finanzamt': 'tax_office',
    'Finanzgericht': 'tax_court',
    'PLZ': 'address_zip',
    'Ort': 'address_city',
    'Straße': 'address_street',
    'Hausnummer': 'address_number',
    
    // Person specific fields
    'Anrede': 'salutation',
    'Titel': 'title',
    'Vorname': 'first_name',
    'Nachname': 'last_name',
    'Geburtsdatum': 'birth_date',
    'Steuer-ID': 'tax_id',
    
    // Company specific fields
    'Firmenname': 'company_name',
    'Rechtsform': 'legal_form',
    'USt-ID': 'vat_id',
    
    // Contact person fields
    'Anrede Ansprechpartner': 'contact_salutation',
    'Nachname Ansprechpartner': 'contact_last_name',
    'Telefon Ansprechpartner': 'contact_phone',
    'E-Mail Ansprechpartner': 'contact_email',
    'Fax Ansprechpartner': 'contact_fax',
    
    // Tax office fields
    'PLZ Finanzamt': 'tax_office_zip',
    'Ort Finanzamt': 'tax_office_city',
    'Straße Finanzamt': 'tax_office_street',
    'Hausnummer Finanzamt': 'tax_office_number',
    'E-Mail Finanzamt': 'tax_office_email',
    'Fax Finanzamt': 'tax_office_fax',
} as const;

// Get available client field names for selection
const getClientFieldNames = (): string[] => {
    return Object.keys(CLIENT_FIELD_MAPPING);
};

// Get display name for client field
const getClientFieldDisplayName = (clientFieldName?: string): string => {
    if (!clientFieldName) return 'Nicht zugeordnet';
    
    const displayName = Object.keys(CLIENT_FIELD_MAPPING).find(
        key => CLIENT_FIELD_MAPPING[key as keyof typeof CLIENT_FIELD_MAPPING] === clientFieldName
    );
    
    return displayName || clientFieldName;
};

// Computed property for highlighted text preview
const highlightedTextPreview = computed(() => {
    if (!documentText.value) return ''
    
    let result = documentText.value
    
    // Use allPlaceholderValues to get the most current values including client fields
    const currentValues = allPlaceholderValues.value
    
    // Sort placeholders by length (longest first) to avoid replacing parts of longer placeholders
    const sortedPlaceholders = [...placeholders.value].sort((a, b) => 
        b.name.length - a.name.length
    )
    
    // Replace each placeholder with its value or highlight it
    for (const placeholder of sortedPlaceholders) {
        const placeholderPattern = new RegExp(`\\{\\{${placeholder.name}\\}\\}`, 'g')
        const value = currentValues[placeholder.name] || `{{${placeholder.name}}}`
        
        if (value === `{{${placeholder.name}}}`) {
            // Placeholder not filled - highlight in yellow
            result = result.replace(
                placeholderPattern, 
                `<span class="highlight-placeholder unfilled">{{${placeholder.name}}}</span>`
            )
        } else {
            // Placeholder filled - highlight in green
            result = result.replace(
                placeholderPattern, 
                `<span class="highlight-placeholder filled">${value}</span>`
            )
        }
    }
    
    // Format line breaks
    result = result.replace(/\n/g, '<br>')
    
    return result
})

// Snackbar for notifications
const snackbar = reactive({
    show: false,
    text: '',
    color: 'success'
})

// Add new ref for active tab and saved tab
const activeTab = ref('settings')

// Add helper function for type colors
const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
        text: 'primary',
        number: 'success',
        date: 'info',
        select: 'warning',
        checkbox: 'error',
        textarea: 'secondary'
    }
    return colors[type] || 'grey'
}

// Trigger file input click
const triggerFileInput = () => {
    if (fileInput.value) {
        fileInput.value.click()
    }
}

// Handle file upload
const handleFileUpload = async (event: Event) => {
    const target = event.target as HTMLInputElement
    if (target.files && target.files.length > 0) {
        const file = target.files[0]
        await processFile(file)
    }
}

// Handle file drop
const handleFileDrop = async (event: DragEvent) => {
    dragover.value = false
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
        const file = event.dataTransfer.files[0]
        await processFile(file)
    }
}

// Process the uploaded file
const processFile = async (file: File) => {
    // Check file type
    if (!file.type.includes('pdf') && !file.name.endsWith('.docx')) {
        showNotification('Nur PDF und DOCX Dateien werden unterstützt', 'error')
        return
    }

    // Start upload
    isUploading.value = true
    uploadProgress.value = 0
    
    // Reset document text
    documentText.value = ''

    try {
        // Simulate upload progress
        const uploadInterval = setInterval(() => {
            uploadProgress.value += 2
            if (uploadProgress.value >= 100) {
                clearInterval(uploadInterval)
            }
        }, 100)

        // Process file
        await simulateProcessing()

        // Store uploaded document
        uploadedDocument.value = file
        templateName.value = file.name.split('.')[0]

        // Create preview URL for the original document
        createOriginalDocumentPreview(file)

        // Extract placeholders from document
        await extractPlaceholders(file)

        // Clear upload progress
        clearInterval(uploadInterval)
        uploadProgress.value = 100

        setTimeout(() => {
            isUploading.value = false
            showNotification('Dokument erfolgreich hochgeladen', 'success')
        }, 500)

        // Simulate upload to backend and get document ID
        const formData = new FormData()
        formData.append('file', file)
        formData.append('name', templateName.value)
        formData.append('description', templateDescription.value)
    } catch (error) {
        isUploading.value = false
        showNotification('Fehler beim Hochladen des Dokuments', 'error')
        console.error('Upload error:', error)
    }
}

// Simulate processing delay
const simulateProcessing = () => {
    return new Promise((resolve) => {
        setTimeout(resolve, 2000)
    })
}

// Extract placeholders from document
const extractPlaceholders = async (file: File) => {
    try {
        // Read file content
        const text = await readFileContent(file);
        // Remove line breaks where there are three or more
        documentText.value = text.replace(/\n\n\n+/g, '\n\n'); // Store the document text
        
        // Define placeholder patterns
        const patterns = [
            /\{\{([^}]+)\}\}/g,  // {{placeholder}}
        ];

        // Set to store unique placeholders
        const uniquePlaceholders = new Set<string>();

        // Extract placeholders using each pattern
        patterns.forEach(pattern => {
            const matches = text.matchAll(pattern);
            for (const match of matches) {
                const placeholder = match[1].trim();
                if (placeholder && !uniquePlaceholders.has(placeholder)) {
                    uniquePlaceholders.add(placeholder);
                }
            }
        });

        // Convert unique placeholders to placeholder objects
        placeholders.value = Array.from(uniquePlaceholders).map(name => ({
            name,
            type: determineFieldType(name),
            required: true,
            validation: getDefaultValidation(name)
        }));

        showNotification(`${placeholders.value.length} Platzhalter gefunden`, 'success');
    } catch (error) {
        console.error('Error extracting placeholders:', error);
        showNotification('Fehler beim Extrahieren der Platzhalter', 'error');
    }
};

// Helper function to read file content
const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        if (file.type === 'application/pdf') {
            reject(new Error('PDF parsing is not implemented yet'));
        } else if (file.name.endsWith('.docx')) {
            // For DOCX files, use mammoth to extract text
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const arrayBuffer = e.target?.result as ArrayBuffer;
                    const result = await mammoth.extractRawText({ arrayBuffer });
                    resolve(result.value);
                } catch (error) {
                    reject(new Error('Failed to parse DOCX file: ' + error));
                }
            };
            reader.onerror = (e) => reject(e);
            reader.readAsArrayBuffer(file);
        } else {
            // For text files
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        }
    });
};

// Helper function to determine field type based on placeholder name
const determineFieldType = (name: string): string => {
    const lowerName = name.toLowerCase();
    
    if (lowerName.includes('datum') || lowerName.includes('date')) {
        return 'date';
    }
    if (lowerName.includes('betrag') || lowerName.includes('summe') || 
        lowerName.includes('preis') || lowerName.includes('kosten')) {
        return 'number';
    }
    if (lowerName.includes('beschreibung') || lowerName.includes('text') || 
        lowerName.includes('kommentar')) {
        return 'textarea';
    }
    if (lowerName.includes('status') || lowerName.includes('typ') || 
        lowerName.includes('art') || lowerName.includes('kategorie')) {
        return 'select';
    }
    if (lowerName.includes('aktiv') || lowerName.includes('bestätigt') || lowerName.includes('erledigt')) {
        return 'checkbox';
    }
    return 'text';
};

// Helper function to get default validation rules based on field type
const getDefaultValidation = (name: string) => {
    const type = determineFieldType(name);
    const validation: any = {};

    switch (type) {
        case 'text':
            validation.minLength = 1;
            validation.maxLength = 100;
            validation.errorMessage = 'Der Text darf nicht länger als 100 Zeichen sein';
            break;
        case 'textarea':
            validation.minLength = 1;
            validation.maxLength = 1000;
            validation.errorMessage = 'Der Text darf nicht länger als 1000 Zeichen sein';
            break;
        case 'number':
            validation.min = 0;
            validation.errorMessage = 'Der Betrag darf nicht negativ sein';
            break;
        case 'date':
            validation.minDate = new Date();
            validation.maxDate = new Date(new Date().setFullYear(new Date().getFullYear() + 1));
            validation.errorMessage = 'Das Datum muss zwischen dem 01.01.2025 und dem 01.01.2026 liegen';
            break;
    }

    return validation;
};

// Format file size
const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    const kb = bytes / 1024
    if (kb < 1024) return kb.toFixed(1) + ' KB'
    const mb = kb / 1024
    return mb.toFixed(1) + ' MB'
}

// Add new field
const addField = () => {
    editingPlaceholderIndex.value = -1
    editingPlaceholder.name = ''
    editingPlaceholder.type = 'text'
    editingPlaceholder.required = false
    editingPlaceholder.defaultValue = ''
    editingPlaceholder.validation = {}
    
    // Reset client field properties
    editingPlaceholder.isClientField = false
    editingPlaceholder.clientFieldGroup = undefined
    editingPlaceholder.clientFieldName = undefined
    selectedClientFieldName.value = ''
    
    delete editingPlaceholder.options
    optionsInput.value = ''
    showPlaceholderDialog.value = true
}

// Edit existing placeholder
const editPlaceholder = (index: number) => {
    editingPlaceholderIndex.value = index
    const placeholder = placeholders.value[index]
    editingPlaceholder.name = placeholder.name
    editingPlaceholder.type = placeholder.type
    editingPlaceholder.required = placeholder.required
    editingPlaceholder.validation = { ...placeholder.validation }
    
    // Handle client field properties
    editingPlaceholder.isClientField = placeholder.isClientField || false
    editingPlaceholder.clientFieldGroup = placeholder.clientFieldGroup
    editingPlaceholder.clientFieldName = placeholder.clientFieldName
    
    // Set selected client field name for display
    if (placeholder.isClientField && placeholder.clientFieldName) {
        // Find the display name for the client field
        const displayName = Object.keys(CLIENT_FIELD_MAPPING).find(
            key => CLIENT_FIELD_MAPPING[key as keyof typeof CLIENT_FIELD_MAPPING] === placeholder.clientFieldName
        )
        selectedClientFieldName.value = displayName || ''
    } else {
        selectedClientFieldName.value = ''
    }
    
    // Handle options for select type
    if (placeholder.options) {
        editingPlaceholder.options = [...placeholder.options]
        optionsInput.value = placeholder.options.join(', ')
    } else {
        delete editingPlaceholder.options
        optionsInput.value = ''
    }
    
    // Handle default value based on type
    if (placeholder.defaultValue !== undefined) {
        editingPlaceholder.defaultValue = placeholder.defaultValue
    } else {
        // Set appropriate empty default value
        switch (placeholder.type) {
            case 'checkbox':
                editingPlaceholder.defaultValue = false
                break
            case 'number':
                editingPlaceholder.defaultValue = null
                break
            case 'date':
                editingPlaceholder.defaultValue = ''
                break
            case 'select':
                editingPlaceholder.defaultValue = placeholder.options && placeholder.options.length > 0 
                    ? placeholder.options[0] 
                    : ''
                break
            default:
                editingPlaceholder.defaultValue = ''
        }
    }
    
    showPlaceholderDialog.value = true
}

// Save placeholder edit
const savePlaceholderEdit = async () => {
    if (!editingPlaceholder.name.trim()) {
        showNotification('Feldname darf nicht leer sein', 'error')
        return
    }

    // Validate client field configuration
    if (editingPlaceholder.isClientField) {
        if (!editingPlaceholder.clientFieldGroup?.trim()) {
            showNotification('Mandanten-Gruppe darf nicht leer sein', 'error')
            return
        }
        if (!editingPlaceholder.clientFieldName) {
            showNotification('Bitte wählen Sie ein Mandanten-Feld aus', 'error')
            return
        }
    }

    // Set editing flag to prevent auto-save watchers
    isEditingPlaceholder.value = true

    try {
        // Create placeholder object with all necessary fields
        const placeholderToSave: Placeholder = {
            name: editingPlaceholder.name,
            type: editingPlaceholder.type,
            required: editingPlaceholder.required,
            validation: { ...editingPlaceholder.validation }
        }

        // Handle client fields
        if (editingPlaceholder.isClientField) {
            placeholderToSave.isClientField = true
            placeholderToSave.clientFieldGroup = editingPlaceholder.clientFieldGroup
            placeholderToSave.clientFieldName = editingPlaceholder.clientFieldName
            // Client fields don't have default values, options, etc.
        } else {
            // Handle regular fields
            placeholderToSave.isClientField = false
            
            // Process options for select type
            if (editingPlaceholder.type === 'select') {
                const options = optionsInput.value
                    .split(',')
                    .map(option => option.trim())
                    .filter(option => option)

                if (options.length === 0) {
                    showNotification('Auswahloptionen dürfen nicht leer sein', 'error')
                    return
                }

                placeholderToSave.options = options
                
                // Ensure default value is in options
                if (editingPlaceholder.defaultValue && !options.includes(String(editingPlaceholder.defaultValue))) {
                    placeholderToSave.defaultValue = options[0]
                } else if (!editingPlaceholder.defaultValue) {
                    placeholderToSave.defaultValue = options[0]
                } else {
                    placeholderToSave.defaultValue = editingPlaceholder.defaultValue
                }
            } else {
                // Ensure default value has correct type
                switch (editingPlaceholder.type) {
                    case 'number':
                        if (editingPlaceholder.defaultValue !== null && editingPlaceholder.defaultValue !== undefined) {
                            placeholderToSave.defaultValue = Number(editingPlaceholder.defaultValue)
                        }
                        break
                    case 'checkbox':
                        placeholderToSave.defaultValue = Boolean(editingPlaceholder.defaultValue)
                        break
                    default:
                        placeholderToSave.defaultValue = editingPlaceholder.defaultValue
                }
            }
        }

        // Save the placeholder
        if (editingPlaceholderIndex.value === -1) {
            // Add new placeholder
            placeholders.value.push(placeholderToSave)
            
            // For new fields, update the form value with defaultValue (only for non-client fields)
            if (!placeholderToSave.isClientField && placeholderToSave.defaultValue !== undefined) {
                await nextTick() // Wait for reactivity to settle
                testValues.value[placeholderToSave.name] = placeholderToSave.defaultValue
            }
        } else {
            // Update existing placeholder
            const oldName = placeholders.value[editingPlaceholderIndex.value].name
            const newName = placeholderToSave.name
            
            // Update placeholder in array
            placeholders.value[editingPlaceholderIndex.value] = placeholderToSave
            
            // Update testValues if field name has changed
            if (oldName !== newName && testValues.value[oldName] !== undefined) {
                await nextTick() // Wait for reactivity to settle
                // Save old value
                const oldValue = testValues.value[oldName]
                // Delete old value
                delete testValues.value[oldName]
                // Set value with new name
                testValues.value[newName] = oldValue
            }
            
            // Update document text with new placeholder name
            if (oldName !== newName && documentText.value) {
                updatePlaceholderInDocumentText(oldName, newName);
            }
            
            // Update pdf file when placeholder name changed
            if (oldName !== newName) {
                
                // Update placeholder name on backend
                try {
                    if (documentId.value) {
                        // If we have a document ID, use the regular endpoint
                        DocumentAPI.updatePlaceholderName(documentId.value, oldName, newName)
                            .then(() => {
                            })
                            .catch(error => {
                                console.error('Error updating placeholder on backend:', error);
                                showNotification('Fehler beim Aktualisieren des Platzhalters auf dem Server', 'warning');
                            });
                    } else if (uploadedDocument.value) {
                        // If we only have a temporary file, use the temporary file endpoint
                        DocumentAPI.updatePlaceholderNameInTemp(uploadedDocument.value, oldName, newName)
                            .then(response => {
                                
                                // Convert base64 data back to File object and update uploadedDocument
                                if (response.data && response.data.preview_data) {
                                    // Convert base64 to Blob
                                    const byteCharacters = atob(response.data.preview_data);
                                    const byteArrays = [];
                                    
                                    // Process in chunks to avoid memory issues with large documents
                                    const chunkSize = 512 * 1024; // 512KB chunks
                                    for (let offset = 0; offset < byteCharacters.length; offset += chunkSize) {
                                        const slice = byteCharacters.slice(offset, offset + chunkSize);
                                        
                                        const byteNumbers = new Array(slice.length);
                                        for (let i = 0; i < slice.length; i++) {
                                            byteNumbers[i] = slice.charCodeAt(i);
                                        }
                                        
                                        const byteArray = new Uint8Array(byteNumbers);
                                        byteArrays.push(byteArray);
                                    }
                                    
                                    // Create a blob with the correct MIME type
                                    const blob = new Blob(byteArrays, { type: response.data.mime_type });
                                    
                                    // Create a new File object
                                    const newFileName = response.data.filename || 'document';
                                    const updatedFile = new File([blob], newFileName, { 
                                        type: response.data.mime_type,
                                        lastModified: new Date().getTime()
                                    });
                                    
                                    // Update uploadedDocument value
                                    uploadedDocument.value = updatedFile;
                                    
                                    // Regenerate document text if we're in text preview mode
                                    if (previewMode.value === 'text') {
                                        isLoadingTextPreview.value = true;
                                        readFileContent(updatedFile)
                                            .then(text => {
                                                documentText.value = text.replace(/\n\n\n+/g, '\n\n');
                                                isLoadingTextPreview.value = false;
                                            })
                                            .catch(error => {
                                                console.error('Error loading updated text content:', error);
                                                isLoadingTextPreview.value = false;
                                            });
                                    }
                                    
                                    // If DocumentPreview component is visible, tell it to update
                                    if (documentPreviewRef.value && showPreview.value) {
                                        documentPreviewRef.value.updatePlaceholderName(oldName, newName);
                                    }
                                }
                            })
                            .catch(error => {
                                console.error('Error updating placeholder in temporary file:', error);
                                showNotification('Fehler beim Aktualisieren des Platzhalters in der temporären Datei', 'warning');
                            });
                    }
                } catch (error) {
                    console.error('Error calling placeholder update API:', error);
                }
            }
            
            // Important: Always update the field value in the form on defaultValue (only for non-client fields)
            if (!placeholderToSave.isClientField && placeholderToSave.defaultValue !== undefined) {
                await nextTick() // Wait for reactivity to settle
                testValues.value[newName] = placeholderToSave.defaultValue
            }
        }

        // Use nextTick to defer the reactive update and prevent recursive loops
        await nextTick()
        
        // Create a new object to trigger reactivity for testValues only
        testValues.value = { ...testValues.value }

        showPlaceholderDialog.value = false
        showNotification('Feld erfolgreich gespeichert', 'success')
        
    } finally {
        // Always reset the editing flag in a separate tick to allow auto-save to resume
        await nextTick()
        isEditingPlaceholder.value = false
        
        // Trigger auto-save after placeholder editing is complete
        if (documentId.value) {
            debouncedAutoSave()
        }
    }
}

// New function to update placeholder names in document text
const updatePlaceholderInDocumentText = (oldName: string, newName: string) => {
    if (!documentText.value) return;
    
    // Replace all occurrences of the old placeholder with the new one
    const oldPlaceholderPattern = new RegExp(`\\{\\{${oldName}\\}\\}`, 'g');
    documentText.value = documentText.value.replace(oldPlaceholderPattern, `{{${newName}}}`);
}

// Cancel placeholder edit
const cancelPlaceholderEdit = () => {
    showPlaceholderDialog.value = false
}

// Update test values
const isUpdatingValues = ref(false) // Add flag to prevent circular updates

const updateTestValues = (values: Record<string, any>) => {
    // Prevent circular updates
    if (isUpdatingValues.value) {
        return;
    }
    
    // Add null check and safe copying
    if (!values || typeof values !== 'object') {
        return;
    }
    
    // Check if values actually changed to avoid unnecessary updates
    let hasChanges = false;
    Object.keys(values).forEach(key => {
        if (values[key] !== undefined && testValues.value[key] !== values[key]) {
            hasChanges = true;
        }
    });
    
    if (!hasChanges) {
        return; // No changes, skip update
    }
    
    isUpdatingValues.value = true;
    
    try {
        // Update testValues with new values, preserving existing ones
        Object.keys(values).forEach(key => {
            if (values[key] !== undefined) {
                testValues.value[key] = values[key];
            }
        });
        
        // Trigger reactivity by creating new object reference
        testValues.value = { ...testValues.value };
    } finally {
        // Always reset flag, use nextTick to ensure it's reset after all reactive updates
        nextTick(() => {
            isUpdatingValues.value = false;
        });
    }
}

// Generate preview
const generatePreview = async (values?: Record<string, any>) => {
    if (!uploadedDocument.value && !documentId.value) {
        showNotification('Bitte laden Sie zuerst ein Dokument hoch oder wählen Sie ein Template aus', 'error')
        return
    }
    
    // If values are provided (from form submission), update testValues first
    if (values) {
        // Update testValues with provided values
        Object.keys(values).forEach(key => {
            if (values[key] !== undefined) {
                testValues.value[key] = values[key]
            }
        })
        
        // Trigger reactivity
        testValues.value = { ...testValues.value }
    }
    
    // Use the computed allPlaceholderValues which automatically includes all values
    const placeholderValues = allPlaceholderValues.value
    
    
    if (Object.keys(placeholderValues).length === 0) {
        showNotification('Bitte füllen Sie mindestens ein Feld aus', 'warning')
        return
    }
    
    // Validate required fields
    const missingRequired = placeholders.value
        .filter(p => {
            if (!p.required) return false;
            
            // For client fields, check if we have a value (they can be required too)
            if (p.isClientField) {
                return !placeholderValues[p.name] || placeholderValues[p.name] === '';
            }
            
            // For regular fields
            return !placeholderValues[p.name] && placeholderValues[p.name] !== 0 && placeholderValues[p.name] !== false;
        })
        .map(p => p.name)
    
    if (missingRequired.length > 0) {
        showNotification(`Bitte füllen Sie alle erforderlichen Felder aus: ${missingRequired.join(', ')}`, 'warning')
        return
    }
    
    showPreview.value = true
    
    if (documentPreviewRef.value) {
        // Call generatePreview directly - DocumentPreview will use the updated placeholderValues prop
        await documentPreviewRef.value.generatePreview()
        pdfLastGeneratedAt.value = new Date()
    }
}

// Preview callbacks
const onPreviewGenerated = (previewData: any) => {
    pdfLastGeneratedAt.value = new Date() // Update timestamp when preview is generated
    showNotification('Vorschau erfolgreich generiert', 'success')
}

const onPreviewError = (errorMessage: string) => {
    showNotification(`Fehler bei der Vorschau-Generierung: ${errorMessage}`, 'error')
    showPreview.value = false
};

// Handle view mode changes from DocumentPreview component
const handleViewModeChange = (newMode: string) => {
    previewMode.value = newMode;
};

// Auto-save placeholders for existing templates
const isEditingPlaceholder = ref(false) // Add flag to prevent auto-save during editing

const autoSavePlaceholders = async () => {
    if (!documentId.value || isEditingPlaceholder.value) return; // Skip if editing
    
    try {
        isAutoSaving.value = true;
        await DocumentAPI.updateTemplate(
            documentId.value,
            null, // No file update, just placeholders
            templateName.value,
            templateDescription.value,
            placeholders.value
        );
    } catch (error) {
        console.error('Error auto-saving placeholders:', error);
        // Don't show notification for auto-save errors to avoid spam
    } finally {
        isAutoSaving.value = false;
    }
};

// Debounced auto-save function
let autoSaveTimer: number | null = null;
const debouncedAutoSave = () => {
    if (!documentId.value || isEditingPlaceholder.value) return; // Skip if editing
    
    if (autoSaveTimer !== null) {
        clearTimeout(autoSaveTimer);
    }
    
    autoSaveTimer = setTimeout(() => {
        autoSavePlaceholders();
    }, 2000); // Auto-save after 2 seconds of inactivity
};

// Watch for changes in placeholders for existing templates
watch(placeholders, () => {
    if (documentId.value && !isEditingPlaceholder.value) { // Only trigger if not editing
        debouncedAutoSave();
    }
}, { deep: true });

// Watch for changes in template name and description
watch([templateName, templateDescription], () => {
    if (documentId.value && !isEditingPlaceholder.value) { // Only trigger if not editing
        debouncedAutoSave();
    }
});

// Save template
const saveTemplate = async () => {
    if (!templateName.value.trim()) {
        showNotification('Bitte geben Sie einen Template-Namen ein', 'error')
        return
    }

    if (placeholders.value.length === 0) {
        showNotification('Fügen Sie mindestens ein Feld hinzu', 'warning')
        return
    }

    try {
        isSaving.value = true

        if (documentId.value) {
            // Update existing template
            const response = await DocumentAPI.updateTemplate(
                documentId.value,
                uploadedDocument.value, // File might be null if not changed
                templateName.value,
                templateDescription.value,
                placeholders.value
            )
            
            showNotification('Template erfolgreich aktualisiert', 'success')
        } else if (uploadedDocument.value) {
            // Save new template
            const response = await DocumentAPI.saveTemplate(
                uploadedDocument.value,
                templateName.value,
                templateDescription.value,
                placeholders.value
            )
            
            // Store document ID if response contains it
            if (response.data && response.data.id) {
                documentId.value = response.data.id
            }

            showNotification('Template erfolgreich gespeichert', 'success')
        } else {
            showNotification('Kein Dokument zum Speichern vorhanden', 'error')
            return
        }
    } catch (error) {
        const errorMessage = documentId.value 
            ? 'Fehler beim Aktualisieren des Templates' 
            : 'Fehler beim Speichern des Templates';
        showNotification(errorMessage, 'error')
        console.error('Save/Update error:', error)
    } finally {
        isSaving.value = false
    }
}

// Show notification
const showNotification = (text: string, color: 'success' | 'error' | 'warning' | 'info') => {
    snackbar.text = text
    snackbar.color = color
    snackbar.show = true
}

// Create original document preview
const originalDocumentUrl = ref<string | null>(null)
const originalDocumentHtml = ref<string | null>(null)
const isLoadingPreview = ref(false)
const isFileTypePdf = computed(() => 
    uploadedDocument.value?.type === 'application/pdf' || 
    uploadedDocument.value?.name.endsWith('.pdf')
)

const createOriginalDocumentPreview = async (file: File) => {
    try {
        isLoadingPreview.value = true;
        
        if (isFileTypePdf.value) {
            // Use Blob URL instead of data URI
            const blobUrl = URL.createObjectURL(file);
            originalDocumentUrl.value = blobUrl;
            originalDocumentHtml.value = null;

            // Store the blobUrl for later cleanup
            if ((createOriginalDocumentPreview as any).lastBlobUrl) {
                URL.revokeObjectURL((createOriginalDocumentPreview as any).lastBlobUrl);
            }
            (createOriginalDocumentPreview as any).lastBlobUrl = blobUrl;
        } else if (file.name.endsWith('.docx')) {
            // For DOCX files, we use mammoth for conversion to HTML
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const arrayBuffer = e.target?.result as ArrayBuffer;
                    const result = await mammoth.convertToHtml({ arrayBuffer });
                    
                    // Create HTML content
                    originalDocumentHtml.value = `
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
                                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                                td, th { border: 1px solid #ddd; padding: 8px; }
                                img { max-width: 100%; height: auto; }
                            </style>
                        </head>
                        <body>
                            ${result.value}
                        </body>
                        </html>
                    `;
                    
                    // We don't need to create a blob URL, we'll use srcdoc directly
                    originalDocumentUrl.value = null;
                } catch (error) {
                    console.error('Error converting DOCX to HTML:', error);
                    originalDocumentUrl.value = null;
                    originalDocumentHtml.value = null;
                }
            };
            reader.onerror = () => {
                originalDocumentUrl.value = null;
                originalDocumentHtml.value = null;
            };
            reader.readAsArrayBuffer(file);
        } else {
            originalDocumentUrl.value = null;
            originalDocumentHtml.value = null;
        }
    } catch (error) {
        console.error('Error creating document preview:', error);
        originalDocumentUrl.value = null;
        originalDocumentHtml.value = null;
    } finally {
        isLoadingPreview.value = false;
    }
}

// Update preview
const cleanupResources = () => {
    if ((createOriginalDocumentPreview as any).lastBlobUrl) {
        URL.revokeObjectURL((createOriginalDocumentPreview as any).lastBlobUrl);
        (createOriginalDocumentPreview as any).lastBlobUrl = null;
    }
    originalDocumentUrl.value = null;
    originalDocumentHtml.value = null;
    documentText.value = '';
    
    // Clean up text selection popup
    hideTextPopup();
}

// Use instead of onUnmounted, calling this function when needed
onUnmounted(cleanupResources);

// Add this new function to handle field type changes
const onFieldTypeChange = () => {
    // Reset the defaultValue based on the field type
    switch (editingPlaceholder.type) {
        case 'text':
        case 'textarea':
            editingPlaceholder.defaultValue = editingPlaceholder.defaultValue && typeof editingPlaceholder.defaultValue === 'string' 
                ? editingPlaceholder.defaultValue 
                : '';
            break;
        case 'number':
            // Convert to number or set to null
            editingPlaceholder.defaultValue = editingPlaceholder.defaultValue !== undefined && editingPlaceholder.defaultValue !== null
                ? Number(editingPlaceholder.defaultValue) || 0
                : null;
            break;
        case 'date':
            // Handle date format (YYYY-MM-DD for input type="date")
            if (editingPlaceholder.defaultValue) {
                if (typeof editingPlaceholder.defaultValue === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(editingPlaceholder.defaultValue)) {
                    // Already in correct format
                } else {
                    // Set to today's date in proper format
                    const today = new Date();
                    const year = today.getFullYear();
                    const month = String(today.getMonth() + 1).padStart(2, '0');
                    const day = String(today.getDate()).padStart(2, '0');
                    editingPlaceholder.defaultValue = `${year}.${month}.${day}`;
                }
            } else {
                editingPlaceholder.defaultValue = '';
            }
            break;
        case 'checkbox':
            // Convert to boolean
            editingPlaceholder.defaultValue = Boolean(editingPlaceholder.defaultValue);
            break;
        case 'select':
            // Handle select options
            if (!editingPlaceholder.options || editingPlaceholder.options.length === 0) {
                // If no options yet, reset default value
                editingPlaceholder.defaultValue = '';
            } else if (editingPlaceholder.defaultValue && !editingPlaceholder.options.includes(String(editingPlaceholder.defaultValue))) {
                // If default value not in options, set to first option
                editingPlaceholder.defaultValue = editingPlaceholder.options[0];
            }
            break;
    }
};

// Client field management functions
const onClientFieldToggle = () => {
    if (editingPlaceholder.isClientField) {
        // Reset client-specific properties when enabling client field
        editingPlaceholder.clientFieldGroup = editingPlaceholder.clientFieldGroup || '1';
        editingPlaceholder.clientFieldName = '';
        selectedClientFieldName.value = '';
        
        // Reset standard field properties that don't apply to client fields
        editingPlaceholder.type = 'text';
        editingPlaceholder.required = false;
        editingPlaceholder.defaultValue = undefined;
        editingPlaceholder.options = undefined;
        editingPlaceholder.validation = {};
    } else {
        // Reset client field properties when disabling client field
        editingPlaceholder.clientFieldGroup = undefined;
        editingPlaceholder.clientFieldName = undefined;
        selectedClientFieldName.value = '';
    }
};

const onClientFieldNameChange = () => {
    if (selectedClientFieldName.value && CLIENT_FIELD_MAPPING[selectedClientFieldName.value as keyof typeof CLIENT_FIELD_MAPPING]) {
        // Set the database field name
        editingPlaceholder.clientFieldName = CLIENT_FIELD_MAPPING[selectedClientFieldName.value as keyof typeof CLIENT_FIELD_MAPPING];
        
        // Auto-generate a placeholder name if not already set or if it was auto-generated before
        if (!editingPlaceholder.name || editingPlaceholder.name.startsWith('client_')) {
            const groupPrefix = editingPlaceholder.clientFieldGroup || '1';
            const fieldPart = selectedClientFieldName.value.toLowerCase().replace(/[^a-z0-9]/g, '_');
            editingPlaceholder.name = `${groupPrefix}_${fieldPart}`;
        }
        
        // Set appropriate type based on the field
        const fieldName = editingPlaceholder.clientFieldName;
        if (fieldName === 'birth_date') {
            editingPlaceholder.type = 'date';
        } else if (['salutation', 'title', 'legal_form', 'contact_salutation'].includes(fieldName)) {
            editingPlaceholder.type = 'select';
            // Set appropriate options based on field
            if (fieldName === 'salutation' || fieldName === 'contact_salutation') {
                editingPlaceholder.options = ['Herr', 'Frau', 'Divers'];
            } else if (fieldName === 'title') {
                editingPlaceholder.options = ['', 'Dr.', 'Prof.', 'Prof. Dr.'];
            } else if (fieldName === 'legal_form') {
                editingPlaceholder.options = ['GmbH', 'AG', 'KG', 'OHG', 'e.K.'];
            }
        } else {
            editingPlaceholder.type = 'text';
        }
    }
};

watch(activeTab, (newTab, oldTab) => {
}, { immediate: true });

// Add loading handler for text preview mode
watch(previewMode, (newMode) => {
    // Clean up any existing text selection handlers
    hideTextPopup()
    
    if (newMode === 'text' && uploadedDocument.value && !documentText.value) {
        isLoadingTextPreview.value = true
        readFileContent(uploadedDocument.value)
            .then(text => {
                documentText.value = text
                isLoadingTextPreview.value = false
            })
            .catch(error => {
                console.error('Error loading text content:', error)
                isLoadingTextPreview.value = false
                showNotification('Fehler beim Laden des Textes', 'error')
            })
    }
})

// New refs for text selection
const showTextSelectionPopup = ref(false)
const selectedText = ref('')
const textPopupStyle = ref({})
const isSelectingText = ref(false)

// New function to start text selection
const startTextSelection = () => {
    isSelectingText.value = true
    
    // If we're starting a new selection, hide any existing popup
    if (showTextSelectionPopup.value) {
        hideTextPopup()
    }
}

// Close popup when clicking outside
const closeTextPopupOnClickOutside = (event: MouseEvent) => {
    // If popup is not shown, do nothing
    if (!showTextSelectionPopup.value) {
        document.removeEventListener('click', closeTextPopupOnClickOutside)
        return
    }
    
    const popup = document.querySelector('.text-selection-popup')
    if (!popup) {
        hideTextPopup()
        return
    }
    
    if (!popup.contains(event.target as Node)) {
        hideTextPopup()
    }
}

// New function to hide text selection popup
const hideTextPopup = () => {
    showTextSelectionPopup.value = false
    document.removeEventListener('click', closeTextPopupOnClickOutside)
}

// Add a DOM event listener for selection changes
onMounted(async () => {
    try {
        // Ensure store is available before dispatching
        if (store && store.dispatch) {
            await store.dispatch('client/fetchClients');
        }
    } catch (error) {
        console.warn('Error fetching clients:', error);
        // Continue with empty clients array if store fails
    }
});

onUnmounted(() => {
    // Clean up event listeners
    document.removeEventListener('selectionchange', handleSelectionChange)
    document.removeEventListener('click', closeTextPopupOnClickOutside)
    
    // Clean up resources
    cleanupResources();
    
    // Clear any pending auto-save timers
    if (autoSaveTimer !== null) {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = null;
    }
});

// Selection change handler
const handleSelectionChange = () => {
    if (previewMode.value !== 'text') return
    
    // We'll only use this to detect when selection is cleared
    const selection = window.getSelection()
    if (!selection || selection.toString().trim().length === 0) {
        // Don't hide the popup immediately - let click handlers decide
        // This prevents popup from disappearing when trying to click it
    }
}

// Format timestamp for display
const formatTimestamp = (date: Date) => {
    if (!date) return '';
    
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    
    return `${hours}:${minutes}:${seconds}`;
}

// Handle view document event from DocumentList
const handleViewDocument = async (document: any) => {
    
    try {
        // Switch to form view
        viewMode.value = 'form';
        
        // Set document data
        documentId.value = document.id;
        templateName.value = document.name || '';
        templateDescription.value = document.description || '';
        
        // Set placeholders from document
        if (document.placeholders && Array.isArray(document.placeholders)) {
            placeholders.value = document.placeholders.map((placeholder: any) => ({
                name: placeholder.name || '',
                type: placeholder.type || 'text',
                required: placeholder.required !== undefined ? placeholder.required : true,
                defaultValue: placeholder.defaultValue,
                options: placeholder.options || undefined,
                validation: placeholder.validation || {},
                // Client field properties
                isClientField: placeholder.isClientField || false,
                clientFieldGroup: placeholder.clientFieldGroup || undefined,
                clientFieldName: placeholder.clientFieldName || undefined
            }));
        } else {
            placeholders.value = [];
        }
        
        // Initialize test values with default values (only for non-client fields)
        const initialTestValues: Record<string, any> = {};
        placeholders.value.forEach((placeholder: Placeholder) => {
            if (!placeholder.isClientField && placeholder.defaultValue !== undefined) {
                initialTestValues[placeholder.name] = placeholder.defaultValue;
            }
        });
        testValues.value = initialTestValues;
        
        // Try to load the original document file for preview
        try {
            const fileResponse = await DocumentAPI.getDocumentFile(document.id);
            const blob = fileResponse.data;
            
            // Create File object from blob
            const filename = `${document.name}.${document.file_type?.includes('pdf') ? 'pdf' : 'docx'}`;
            const file = new File([blob], filename, { 
                type: document.file_type || 'application/octet-stream' 
            });
            
            uploadedDocument.value = file;
        } catch (fileError) {
            console.warn('Could not load original document file:', fileError);
            // Still allow to work without the file, just disable text preview
            uploadedDocument.value = null;
        }
        
        // Make sure we're not in uploading state
        isUploading.value = false;
        
        // Switch to mask tab to show the form
        activeTab.value = 'mask';
        
        showNotification(`Template "${document.name}" geladen`, 'success');
        
    } catch (error) {
        console.error('Error loading document:', error);
        showNotification('Fehler beim Laden des Dokuments', 'error');
    }
};

// Handle client selection for filling client fields
const onClientSelected = (groupName: string, clientId: number | null) => {
    
    if (!clientId) {
        // Clear client field values for this group
        clientFieldGroups.value.forEach(group => {
            if (group.groupName === groupName) {
                group.fields.forEach(field => {
                    if (testValues.value[field.name] !== undefined) {
                        delete testValues.value[field.name];
                    }
                });
            }
        });
        // Update values to trigger reactivity
        testValues.value = { ...testValues.value };
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
        groupFields.fields.forEach(field => {
            if (field.isClientField && field.clientFieldName) {
                let value = selectedClient[field.clientFieldName as keyof typeof selectedClient];
                
                // Format value based on field type
                if (value !== undefined && value !== null) {
                    switch (field.type) {
                        case 'date':
                            // Convert date to proper format if needed
                            if (value instanceof Date) {
                                const year = value.getFullYear();
                                const month = String(value.getMonth() + 1).padStart(2, '0');
                                const day = String(value.getDate()).padStart(2, '0');
                                value = `${year}-${month}-${day}`;
                            } else if (typeof value === 'string') {
                                // If it's already a string, check if it needs formatting
                                const dateMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
                                if (dateMatch) {
                                    value = `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`;
                                } else {
                                    // Try to parse and format
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
                    testValues.value[field.name] = value;
                } else {
                    // Clear the field if no value found
                    if (testValues.value[field.name] !== undefined) {
                        delete testValues.value[field.name];
                    }
                }
            }
        });
        
        // Update values to trigger reactivity
        testValues.value = { ...testValues.value };
        
        // Show notification
        showNotification(`Mandanten-Felder für ${formatGroupName(groupName)} wurden automatisch ausgefüllt`, 'success');
    }
};

// Helper function to format group names
const formatGroupName = (groupName: string): string => {
    return groupName
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};
</script>

<style scoped>
.document-creation-container {
    padding: 1.5rem;
    min-height: calc(100vh - 64px);
}

/* View toggle styles */
.view-toggle-container {
    display: flex;
    justify-content: center;
    margin-bottom: 2rem;
}

.view-toggle {
    display: flex;
    background: #fff;
    border-radius: 40px;
    overflow: hidden;
    width: 350px;
    margin: 0 auto;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e0e0e0;
}

.view-toggle label {
    flex: 1;
    text-align: center;
    min-height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 15px;
    font-size: 14px;
    font-weight: 500;
    color: #666;
    background: #fff;
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
}

.view-toggle label.active {
    background: #c2a47b;
    color: #fff;
    font-weight: 500;
}

.view-toggle input[type="radio"] {
    display: none;
}

.toggle-icon {
    margin-right: 5px;
    color: #c2a47b;
}

.view-toggle label.active .toggle-icon {
    color: #fff;
}

/* List view styles */
.list-view {
    margin-top: 20px;
}

/* Animation transitions */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(10px);
}

.split-view {
    display: flex;
    gap: 1.5rem;
    height: calc(100vh - 200px);
}

.mask-editor,
.document-preview {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 12px;
    padding: 1.5rem;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
}

.editor-toolbar {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.editor-workspace,
.preview-workspace {
    flex: 1;
    border-radius: 8px;
    border: 1px solid #e0e4e8;
    overflow: auto;
    padding: 1.5rem;
    background-color: #fcfcfc;
}

.settings-card,
.placeholders-card {
    background: #ffffff;
    border-radius: 10px;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
    overflow: hidden;
}

.placeholders-list {
    background: transparent;
}

.placeholder-item {
    border-radius: 6px;
    margin-bottom: 6px;
    transition: all 0.2s;
}

.placeholder-item:hover {
    background-color: rgba(0, 0, 0, 0.03);
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 2rem;
    color: #5c6b7a;
    text-align: center;
}

.empty-state p {
    margin-top: 1rem;
    max-width: 320px;
    line-height: 1.6;
}

.upload-dropzone {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 240px;
    border-radius: 12px;
    background-color: #f9fafb;
    border: 2px dashed #e0e4e8;
    cursor: pointer;
    transition: all 0.3s ease;
}

.upload-dropzone:hover {
    background-color: #f0f4f8;
    border-color: #c0c8d0;
}

.upload-dropzone.dragover {
    border-color: #4CAF50;
    background-color: rgba(76, 175, 80, 0.08);
    transform: scale(1.01);
}

.supported-formats {
    font-size: 0.8rem;
    color: #8895a7;
    margin-top: 0.75rem;
}

.pdf-preview,
.docx-preview {
    width: 100%;
    height: 100%;
    border: none;
    background: #ffffff;
    border-radius: 6px;
    overflow: hidden;
}

.docx-preview {
    width: 100%;
    height: 100%;
    overflow: auto;
    background: white;
    padding: 20px;
    box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.05);
}

.preview-iframe {
    width: 100%;
    height: 100%;
    border: none;
    background: white;
}

.preview-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.preview-container {
    height: 100%;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.04);
}

.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #8895a7;
    text-align: center;
    padding: 2rem;
}

.loading-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    background-color: #f5f7fa;
    border-radius: 6px;
}

.loading-preview p {
    margin-top: 1.5rem;
    font-size: 1rem;
    color: #5c6b7a;
}

@media (max-width: 1024px) {
    .split-view {
        flex-direction: column;
        height: auto;
        gap: 1.25rem;
    }

    .mask-editor,
    .document-preview {
        width: 100%;
        height: 500px;
    }

    /* Additional responsive styles for the view toggle */
    .view-toggle {
        width: 100%;
        max-width: 400px;
    }
    
    .view-toggle label {
        font-size: 13px;
    }
}

/* Additional animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.v-card-title {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: #2c3e50;
}

.v-card {
    border-radius: 12px !important;
    overflow: hidden;
}

.preview-mode-switch {
    display: flex;
    justify-content: center;
}

.v-btn-toggle {
    max-height: 28px !important;
}

.text-preview-container {
    flex: 1;
    overflow: auto;
    padding: 2rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    height: 94%;
    position: relative;
}

.text-preview-content {
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    color: #333;
    padding-bottom: 3rem; /* Space for the hint */
    min-height: 100%;
    position: relative;
}

:deep(.highlight-placeholder) {
    padding: 2px 4px;
    border-radius: 4px;
    font-weight: 500;
}

:deep(.highlight-placeholder.filled) {
    background-color: rgba(76, 175, 80, 0.2);
    border: 1px solid rgba(76, 175, 80, 0.5);
    color: #2e7d32;
}

:deep(.highlight-placeholder.unfilled) {
    background-color: rgba(255, 193, 7, 0.2);
    border: 1px solid rgba(255, 193, 7, 0.5);
    color: #f57c00;
}

.text-selection-popup {
    position: absolute;
    background-color: white;
    border: 2px solid #8B4513;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    min-width: 220px;
    transform: translateX(-50%);
    animation: fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.text-selection-popup::after {
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    border-width: 10px 10px 0;
    border-style: solid;
    border-color: #8B4513 transparent transparent;
}

.text-selection-popup::before {
    content: '';
    position: absolute;
    bottom: -7px;
    left: 50%;
    transform: translateX(-50%);
    border-width: 8px 8px 0;
    border-style: solid;
    border-color: white transparent transparent;
    z-index: 1;
}

.popup-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}

.selected-text-preview {
    font-weight: 500;
    color: #8B4513;
    margin-right: 8px;
    word-break: break-word;
    font-style: italic;
    font-size: 14px;
    flex: 1;
}

.text-selection-hint {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background-color: rgba(250, 245, 240, 0.95);
    border-radius: 20px;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #8B4513;
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.1);
    pointer-events: none;
    opacity: 0.9;
    transition: opacity 0.3s ease;
    border: 1px solid rgba(139, 69, 19, 0.2);
}

.text-preview-content:hover .text-selection-hint {
    opacity: 0;
    transition-delay: 1s;
}

@keyframes fadeIn {
    from { 
        opacity: 0; 
        transform: translateX(-50%) translateY(10px);
    }
    to { 
        opacity: 1; 
        transform: translateX(-50%) translateY(0);
    }
}

.pdf-generate-hint {
    margin-top: 16px;
    width: 100%;
}

.pdf-timestamp {
    margin-top: 8px;
    display: flex;
    justify-content: flex-end;
}

/* Create view specific styles */
.create-view {
    animation: fadeIn 0.3s ease;
}

/* Client field specific styles */
.client-field-item {
    background-color: rgba(194, 164, 123, 0.04) !important;
    border-left: 3px solid #c2a47b;
    border-radius: 4px;
}

.client-field-item:hover {
    background-color: rgba(194, 164, 123, 0.08) !important;
}

.upload-zone {
    border: 2px dashed #b8926a;
    border-radius: 16px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.upload-zone::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at center, rgba(148, 117, 74, 0.05) 0%, transparent 70%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.upload-zone:hover::before,
.upload-zone--active::before {
    opacity: 1;
}

.upload-zone--active {
    border-color: #94754a;
    background: linear-gradient(135deg, #f2ead9 0%, #e8ddd1 100%);
}

.upload-icon {
    color: #94754a !important;
    transition: transform 0.3s ease;
}

.upload-zone:hover .upload-icon,
.upload-zone--active .upload-icon {
    transform: scale(1.1);
}

.upload-title {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.upload-subtitle {
    color: #6b5d4f !important;
}

.upload-hint {
    font-size: 0.875rem !important;
    color: #8a7b6d !important;
}

.upload-btn {
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.upload-files-list {
    background: #f5f2ee;
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid #d4c4b0;
}
</style>