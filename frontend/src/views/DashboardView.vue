<template>
    <v-container fluid class="dashboard-container">
        <!-- Workflows Section -->
        <v-card class="workflows-card" elevation="0">
            <!-- Header with stats -->
            <v-card-title class="workflows-header pa-8">
                <div class="d-flex justify-space-between align-center w-100">
                    <div class="d-flex align-center ga-4">
                        <h2 class="section-title">Aktive Workflows</h2>
                        <v-chip 
                            variant="tonal" 
                            color="brown" 
                            size="small"
                            class="count-chip"
                        >
                            {{ filteredWorkflows.length }} von {{ workflows.length }}
                        </v-chip>
                    </div>
                </div>
            </v-card-title>

            <!-- Filters -->
            <v-card-text class="filters-section pa-8 pt-0">
                <v-row align="center">
                    <v-col cols="auto">
                        <v-select
                            v-model="statusFilter"
                            :items="statusItems"
                            item-title="title"
                            item-value="value"
                            label="Status Filter"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            clearable
                            prepend-inner-icon="mdi-filter"
                            class="filter-select"
                            style="min-width: 180px"
                        />
                    </v-col>
                    <v-col cols="auto">
                        <v-select
                            v-model="priorityFilter"
                            :items="priorityItems"
                            item-title="title"
                            item-value="value"
                            label="Priorität Filter"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            clearable
                            prepend-inner-icon="mdi-flag"
                            class="filter-select"
                            style="min-width: 180px"
                        />
                    </v-col>
                    <v-col>
                        <v-text-field
                            v-model="searchQuery"
                            label="Mandant oder Workflow suchen..."
                            prepend-inner-icon="mdi-magnify"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            clearable
                            class="search-field"
                            style="max-width: 400px"
                        />
                    </v-col>
                    <v-col cols="auto">
                            <div class="action-buttons d-flex ga-3">
                                <v-btn 
                                    @click="openAIAgent" 
                                    size="large"
                                    prepend-icon="mdi-creation"
                                    class="action-btn-secondary"
                                    color="brown"
                                    variant="outlined"
                                >
                                    KI Agent
                                </v-btn>
                                <v-btn 
                                    @click="createNewWorkflow" 
                                    size="large"
                                    prepend-icon="mdi-sticker-plus-outline"
                                    class="action-btn-secondary"
                                    color="brown"
                                    variant="outlined"
                                >
                                    Neuer Workflow
                                </v-btn>
                            </div>
                        </v-col>
                </v-row>
            </v-card-text>

            <!-- Workflow Grid -->
            <v-card-text class="workflows-grid pa-8 pt-0">
                <!-- Loading state -->
                <div v-if="isLoadingWorkflows" class="loading-state text-center py-16">
                    <v-progress-circular 
                        indeterminate 
                        color="brown" 
                        size="64"
                        class="mb-4"
                    />
                    <h3 class="loading-title mb-3">Workflows werden geladen...</h3>
                    <p class="loading-subtitle">Bitte warten Sie einen Moment.</p>
                </div>
                
                <!-- Workflows -->
                <v-row v-else-if="filteredWorkflows.length > 0">
                    <v-col 
                        v-for="workflow in filteredWorkflows" 
                        :key="workflow.id"
                        cols="12" lg="4" xl="3"
                    >
                        <v-card 
                            class="workflow-card" 
                            elevation="0"
                            @click="openWorkflowDetails(workflow.id)"
                        >
                            <div class="workflow-card-header pa-6 pb-0">
                                <div class="d-flex justify-space-between align-start mb-4">
                                    <div class="workflow-info flex-grow-1">
                                        <h3 class="workflow-title mb-2">{{ workflow.name }}</h3>
                                    </div>
                                    <div class="d-flex align-center ga-2">
                                        <v-chip 
                                            :class="`priority-chip priority-chip--${workflow.priority.toLowerCase()}`"
                                            size="small" 
                                            variant="flat"
                                        >
                                            {{ priorityItems.find(item => item.value === workflow.priority)?.title }}
                                        </v-chip>
                                        <v-chip 
                                            :class="`status-chip status-chip--${workflow.status.replace(' ', '-')}`"
                                            size="small"
                                            variant="flat"
                                        >
                                            {{ statusItems.find(item => item.value === workflow.status)?.title }}
                                        </v-chip>
                                    </div>
                                </div>
                            </div>

                            <v-card-text class="workflow-details pa-6 pt-0">
                                <v-list density="compact" class="bg-transparent workflow-meta">
                                    <v-list-item class="px-0 py-2">
                                        <template #prepend>
                                            <v-icon size="16" class="me-3" color="brown">mdi-account-tie</v-icon>
                                        </template>
                                        <div class="d-flex justify-space-between w-100">
                                            <span class="meta-label">Mandant</span>
                                            <span class="meta-value">{{ workflow.client }}</span>
                                        </div>
                                    </v-list-item>
                                    <v-list-item class="px-0 py-2">
                                        <template #prepend>
                                            <v-icon size="16" class="me-3" color="brown">mdi-account-cog</v-icon>
                                        </template>
                                        <div class="d-flex justify-space-between w-100">
                                            <span class="meta-label">Zugewiesen an</span>
                                            <span class="meta-value">{{ workflow.assignedTo }}</span>
                                        </div>
                                    </v-list-item>
                                    <v-list-item class="px-0 py-2">
                                        <template #prepend>
                                            <v-icon size="16" class="me-3" color="brown">mdi-calendar-plus</v-icon>
                                        </template>
                                        <div class="d-flex justify-space-between w-100">
                                            <span class="meta-label">Erstellt</span>
                                            <span class="meta-value">{{ formatDate(workflow.createdAt) }}</span>
                                        </div>
                                    </v-list-item>
                                    <v-list-item v-if="workflow.dueDate" class="px-0 py-2">
                                        <template #prepend>
                                            <v-icon 
                                                size="16" 
                                                class="me-3" 
                                                :color="isOverdue(workflow.dueDate) ? 'error' : 'warning'"
                                            >
                                                mdi-calendar-clock
                                            </v-icon>
                                        </template>
                                        <div class="d-flex justify-space-between w-100">
                                            <span class="meta-label">Fällig</span>
                                            <span 
                                                class="meta-value" 
                                                :class="{ 'text-error font-weight-bold': isOverdue(workflow.dueDate) }"
                                            >
                                                {{ formatDate(workflow.dueDate) }}
                                                <v-icon v-if="isOverdue(workflow.dueDate)" color="error" size="14" class="ms-1">
                                                    mdi-alert-circle
                                                </v-icon>
                                            </span>
                                        </div>
                                    </v-list-item>
                                    <v-list-item class="px-0 py-2">
                                        <template #prepend>
                                            <v-icon size="16" class="me-3" color="info">mdi-file-multiple</v-icon>
                                        </template>
                                        <div class="d-flex justify-space-between w-100">
                                            <span class="meta-label">Dokumente</span>
                                            <span class="meta-value">{{ workflow.documentCount }} Datei(en)</span>
                                        </div>
                                    </v-list-item>
                                </v-list>
                            </v-card-text>

                            <v-card-actions class="workflow-actions pa-4 pt-0">
                                <v-btn
                                    @click.stop="editWorkflow(workflow)"
                                    variant="outlined"
                                    size="small"
                                    prepend-icon="mdi-pencil-outline"
                                    class="action-btn flex-grow-1"
                                >
                                    Bearbeiten
                                </v-btn>
                                <v-btn
                                    @click.stop="viewDocuments(workflow.id)"
                                    variant="outlined"
                                    size="small"
                                    prepend-icon="mdi-file-document-multiple-outline"
                                    class="action-btn flex-grow-1"
                                >
                                    Dokumente
                                </v-btn>
                                <v-btn
                                    @click.stop="openIntelligentProcessing(workflow.id)"
                                    variant="outlined"
                                    size="small"
                                    prepend-icon="mdi-creation"
                                    color="primary"
                                    class="action-btn flex-grow-1"
                                >
                                    KI-Verarbeitung
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-col>
                </v-row>

                <!-- Empty State -->
                <div v-else class="empty-state text-center py-16">
                    <div class="empty-state-icon mb-6">
                        <v-icon size="80" color="grey-lighten-2">mdi-clipboard-text-outline</v-icon>
                    </div>
                    <h3 class="empty-state-title mb-3">
                        {{ searchQuery || statusFilter || priorityFilter ? 'Keine passenden Workflows gefunden' : 'Noch keine Workflows vorhanden' }}
                    </h3>
                    <p class="empty-state-subtitle mb-8">
                        {{ searchQuery || statusFilter || priorityFilter 
                            ? 'Versuchen Sie, die Filter anzupassen oder einen neuen Workflow zu erstellen.' 
                            : 'Erstellen Sie Ihren ersten Workflow, um loszulegen.' 
                        }}
                    </p>
                    <v-btn 
                        @click="createNewWorkflow" 
                        size="large"
                        color="brown"
                        prepend-icon="mdi-plus-circle"
                        class="action-btn-primary"
                    >
                        Ersten Workflow erstellen
                    </v-btn>
                </div>
            </v-card-text>
        </v-card>

        <!-- File Upload Dialog -->
        <!-- Workflow Creation Dialog -->
        <v-dialog v-model="showWorkflowModal" max-width="900" persistent>
            <v-card class="workflow-modal">
                <v-card-title class="workflow-modal-header pa-4">
                    <div class="d-flex justify-end align-center w-100">

                        <v-btn
                            @click="closeWorkflowModal"
                            icon="mdi-close"
                            variant="text"
                            size="small"
                            class="close-btn"
                        />
                    </div>
                </v-card-title>

                <!-- Step Indicator -->
                <v-card-text class="pa-8 pt-0">
                    <v-stepper 
                        v-model="currentStep"
                        alt-labels
                        editable 
                        :items="stepperItems"
                        hide-actions
                        flat
                        class="workflow-stepper mb-0"
                    />

                    <!-- Step 1: File Upload -->
                    <div v-if="currentStep === 1" class="step-content">
                        <div 
                            class="upload-zone"
                            :class="{ 'upload-zone--active': dragover }"
                            @drop="handleFileDrop" 
                            @dragover.prevent="dragover = true" 
                            @dragleave.prevent="dragover = false"
                            @click="triggerFileInput"
                        >
                            <div class="upload-zone-content">
                                <v-icon size="64" class="upload-icon mb-4">mdi-cloud-upload-outline</v-icon>
                                <h3 class="upload-title mb-3">Dateien hier ablegen</h3>
                                <p class="upload-subtitle mb-6">oder klicken zum Auswählen</p>
                                <v-btn 
                                    variant="outlined" 
                                    prepend-icon="mdi-folder-open-outline"
                                    class="upload-btn"
                                    size="large"
                                >
                                    Dateien auswählen
                                </v-btn>
                                <p class="upload-hint mt-4">
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
                        
                        <div v-if="workflowFiles.length > 0" class="upload-files-section mt-8">
                            <div class="files-header mb-4">
                                <h4 class="files-title">Ausgewählte Dateien ({{ workflowFiles.length }})</h4>
                            </div>
                            <div class="files-chips d-flex flex-wrap ga-2">
                                <v-chip
                                    v-for="(file, index) in workflowFiles"
                                    :key="index"
                                    class="file-chip"
                                    variant="tonal"
                                    color="brown"
                                    size="default"
                                    closable
                                    @click:close="removeWorkflowFile(index)"
                                    prepend-icon="mdi-file-document-outline"
                                >
                                    <span class="file-chip-content">
                                        {{ file.name }}
                                        <span class="file-size-small">{{ formatFileSize(file.size) }}</span>
                                    </span>
                                </v-chip>
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Client, Recipient, Worker Selection -->
                    <div v-if="currentStep === 2" class="step-content">
                        <v-row>
                            <!-- Client Selection -->
                            <v-col cols="12" md="4">
                                <h4 class="selection-title mb-4">Mandant auswählen</h4>
                                <v-select
                                    v-model="selectedClient"
                                    :items="clients"
                                    item-title="displayName"
                                    item-value="id"
                                    label="Mandant"
                                    variant="outlined"
                                    density="comfortable"
                                    prepend-inner-icon="mdi-account-tie"
                                    clearable
                                    :loading="isLoadingClients"
                                    class="selection-field"
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

                            <!-- Recipient Selection -->
                            <v-col cols="12" md="4">
                                <h4 class="selection-title mb-4">Empfänger</h4>
                                <v-select
                                    v-model="selectedRecipient"
                                    :items="recipients"
                                    item-title="name"
                                    item-value="id"
                                    label="Empfänger"
                                    variant="outlined"
                                    density="comfortable"
                                    prepend-inner-icon="mdi-email-outline"
                                    clearable
                                    class="selection-field"
                                />
                            </v-col>

                            <!-- Worker Selection -->
                            <v-col cols="12" md="4">
                                <h4 class="selection-title mb-4">Bearbeiter</h4>
                                <v-select
                                    v-model="selectedWorker"
                                    :items="workers"
                                    item-title="name"
                                    item-value="id"
                                    label="Bearbeiter"
                                    variant="outlined"
                                    density="comfortable"
                                    prepend-inner-icon="mdi-account-cog"
                                    clearable
                                    class="selection-field"
                                />
                            </v-col>
                        </v-row>

                        <!-- Workflow Details -->
                        <v-row class="mt-4">
                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="workflowName"
                                    label="Workflow Name"
                                    variant="outlined"
                                    density="comfortable"
                                    prepend-inner-icon="mdi-file-document-edit"
                                    placeholder="z.B. Jahresabschluss 2024"
                                    class="selection-field"
                                />
                            </v-col>
                            <v-col cols="12" md="6">
                                <v-select
                                    v-model="workflowPriority"
                                    :items="priorityItems"
                                    item-title="title"
                                    item-value="value"
                                    label="Priorität"
                                    variant="outlined"
                                    density="comfortable"
                                    prepend-inner-icon="mdi-flag"
                                    class="selection-field"
                                />
                            </v-col>
                        </v-row>

                        <v-row>
                            <v-col cols="12" md="6">
                                <v-text-field
                                    v-model="workflowDueDate"
                                    label="Fälligkeitsdatum (optional)"
                                    variant="outlined"
                                    density="comfortable"
                                    type="date"
                                    prepend-inner-icon="mdi-calendar"
                                    class="selection-field"
                                    hint="Wann soll der Workflow abgeschlossen sein?"
                                    persistent-hint
                                    :error="!isDueDateValid"
                                    :error-messages="dueDateErrorMessage"
                                />
                            </v-col>
                            <v-col cols="12" md="6">
                                <!-- Placeholder for future field or empty space -->
                            </v-col>
                        </v-row>

                        <v-row>
                            <v-col cols="12">
                                <v-textarea
                                    v-model="workflowDescription"
                                    label="Beschreibung (optional)"
                                    variant="outlined"
                                    density="comfortable"
                                    rows="3"
                                    prepend-inner-icon="mdi-text"
                                    placeholder="Beschreibung des Workflows..."
                                    class="selection-field"
                                />
                            </v-col>
                        </v-row>
                    </div>

                    <!-- Step 3: Template Selection -->
                    <div v-if="currentStep === 3" class="step-content">
                        <div class="templates-header mb-6">
                            <h4 class="selection-title mb-4">Dokumentvorlage auswählen</h4>
                            
                            <!-- Template Search -->
                            <v-text-field
                                v-model="templateSearchQuery"
                                label="Vorlage suchen..."
                                prepend-inner-icon="mdi-magnify"
                                variant="outlined"
                                density="comfortable"
                                hide-details
                                clearable
                                class="template-search mb-4"
                                style="max-width: 400px"
                                placeholder="Name, Beschreibung oder Dateityp..."
                            />
                            
                            <!-- Template Stats -->
                            <div class="template-stats mb-4">
                                <v-chip variant="tonal" color="brown" size="small">
                                    {{ filteredTemplates.length }} von {{ documentTemplates.length }} Vorlagen
                                </v-chip>
                                <v-chip v-if="selectedTemplate" variant="tonal" color="success" size="small" class="ms-2">
                                    <v-icon size="14" class="me-1">mdi-check-circle</v-icon>
                                    Ausgewählt
                                </v-chip>
                            </div>
                        </div>
                        
                        <div v-if="isLoadingTemplates" class="loading-templates text-center py-8">
                            <v-progress-circular indeterminate color="brown" size="64" class="mb-4" />
                            <h4 class="loading-title mb-2">Lade Vorlagen...</h4>
                            <p class="loading-subtitle">Bitte warten Sie einen Moment.</p>
                        </div>
                        
                        <div v-else-if="filteredTemplates.length > 0" class="templates-grid">
                            <v-row>
                                <v-col 
                                    v-for="template in filteredTemplates" 
                                    :key="template.id"
                                    cols="12" md="6"
                                >
                                    <v-card 
                                        class="template-card-minimal" 
                                        :class="{ 
                                            'template-card-minimal--selected': selectedTemplate === template.id
                                        }"
                                        @click="selectedTemplate = template.id"
                                        elevation="0"
                                        variant="outlined"
                                    >
                                        <v-card-text class="pa-4">
                                            <div class="d-flex align-center justify-space-between">
                                                <!-- Left content -->
                                                <div class="d-flex align-center ga-3">
                                                    <v-icon 
                                                        :color="getTemplateColor(template)" 
                                                        size="24"
                                                    >
                                                        {{ getTemplateIcon(template) }}
                                                    </v-icon>
                                                    
                                                    <div class="template-content-minimal">
                                                        <h5 class="template-title-minimal mb-1">{{ template.name }}</h5>
                                                        <div class="d-flex align-center ga-2">
                                                            <v-chip 
                                                                :color="getFileTypeColor(template.file_type)" 
                                                                variant="tonal" 
                                                                size="x-small"
                                                                class="template-type-minimal"
                                                            >
                                                                {{ formatFileType(template.file_type) }}
                                                            </v-chip>
                                                            <span v-if="template.placeholders && template.placeholders.length > 0" class="field-count">
                                                                {{ template.placeholders.length }} Felder
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <!-- Right content -->
                                                <v-icon 
                                                    v-if="selectedTemplate === template.id"
                                                    color="success" 
                                                    size="20"
                                                >
                                                    mdi-check-circle
                                                </v-icon>
                                                <v-icon 
                                                    v-else
                                                    color="grey-lighten-1" 
                                                    size="20"
                                                >
                                                    mdi-circle-outline
                                                </v-icon>
                                            </div>
                                        </v-card-text>
                                    </v-card>
                                </v-col>
                            </v-row>
                        </div>
                        
                        <!-- Empty state for search -->
                        <div v-else-if="templateSearchQuery && documentTemplates.length > 0" class="template-empty-search text-center py-8">
                            <div class="empty-search-icon mb-4">
                                <v-icon size="64" color="grey-lighten-2">mdi-file-search-outline</v-icon>
                            </div>
                            <h4 class="empty-search-title mb-3">Keine passenden Vorlagen gefunden</h4>
                            <p class="empty-search-subtitle mb-6">
                                Keine Vorlagen entsprechen Ihrer Suche nach "<strong>{{ templateSearchQuery }}</strong>".
                            </p>
                            <v-btn 
                                @click="templateSearchQuery = ''" 
                                variant="outlined" 
                                color="brown"
                                prepend-icon="mdi-refresh"
                            >
                                Suche zurücksetzen
                            </v-btn>
                        </div>
                        
                        <!-- Empty state for no templates -->
                        <div v-else class="template-empty-state text-center py-8">
                            <div class="empty-state-icon mb-4">
                                <v-icon size="64" color="grey-lighten-2">mdi-file-document-outline</v-icon>
                            </div>
                            <h4 class="empty-state-title mb-3">Keine Dokumentvorlagen verfügbar</h4>
                            <p class="empty-state-subtitle">
                                Es wurden noch keine Dokumentvorlagen erstellt.
                            </p>
                        </div>
                    </div>

                    <!-- Step 4: Summary -->
                    <div v-if="currentStep === 4" class="step-content">
                        <h4 class="selection-title mb-6">Workflow-Zusammenfassung</h4>
                        
                        <v-card variant="outlined" class="summary-card">
                            <v-card-text class="pa-6">
                                <v-row>
                                    <v-col cols="12" md="6">
                                        <h5 class="summary-section-title mb-3">Workflow Details</h5>
                                        <div class="summary-item">
                                            <span class="summary-label">Name:</span>
                                            <span class="summary-value">{{ workflowName || 'Unbenannt' }}</span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-label">Priorität:</span>
                                            <span class="summary-value">
                                                {{ priorityItems.find(p => p.value === workflowPriority)?.title || 'Nicht festgelegt' }}
                                            </span>
                                        </div>
                                        <div v-if="workflowDueDate" class="summary-item">
                                            <span class="summary-label">Fälligkeitsdatum:</span>
                                            <span 
                                                class="summary-value" 
                                                :class="{ 'text-error font-weight-bold': isOverdue(workflowDueDate) }"
                                            >
                                                {{ formatDate(workflowDueDate) }}
                                                <v-icon v-if="isOverdue(workflowDueDate)" color="error" size="14" class="ms-1">
                                                    mdi-alert-circle
                                                </v-icon>
                                            </span>
                                        </div>
                                        <div v-if="workflowDescription" class="summary-item">
                                            <span class="summary-label">Beschreibung:</span>
                                            <span class="summary-value">{{ workflowDescription }}</span>
                                        </div>
                                    </v-col>
                                    
                                    <v-col cols="12" md="6">
                                        <h5 class="summary-section-title mb-3">Zuordnungen</h5>
                                        <div class="summary-item">
                                            <span class="summary-label">Mandant:</span>
                                            <span class="summary-value">
                                                {{ getClientDisplayName(selectedClient) || 'Nicht ausgewählt' }}
                                            </span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-label">Empfänger:</span>
                                            <span class="summary-value">
                                                {{ getRecipientName(selectedRecipient) || 'Nicht ausgewählt' }}
                                            </span>
                                        </div>
                                        <div class="summary-item">
                                            <span class="summary-label">Bearbeiter:</span>
                                            <span class="summary-value">
                                                {{ getWorkerName(selectedWorker) || 'Nicht ausgewählt' }}
                                            </span>
                                        </div>
                                    </v-col>
                                </v-row>
                                
                                <v-divider class="my-4" />
                                
                                <v-row>
                                    <v-col cols="12" md="6">
                                        <h5 class="summary-section-title mb-3">Dateien ({{ workflowFiles.length }})</h5>
                                        <div v-for="file in workflowFiles" :key="file.name" class="summary-file">
                                            <v-icon size="16" class="me-2">mdi-file-document-outline</v-icon>
                                            <span>{{ file.name }}</span>
                                        </div>
                                    </v-col>
                                    
                                    <v-col cols="12" md="6">
                                        <h5 class="summary-section-title mb-3">Dokumentvorlage</h5>
                                        <div v-if="selectedTemplate" class="summary-template">
                                            <v-icon size="16" class="me-2">{{ getTemplateIcon(getSelectedTemplateData()) }}</v-icon>
                                            <span>{{ getSelectedTemplateData()?.name || 'Unbekannt' }}</span>
                                        </div>
                                        <div v-else class="text-grey">
                                            Keine Vorlage ausgewählt
                                        </div>
                                    </v-col>
                                </v-row>
                            </v-card-text>
                        </v-card>
                    </div>
                </v-card-text>

                <!-- Modal Actions -->
                <v-card-actions class="workflow-modal-actions pa-8 pt-0">
                    <v-btn 
                        v-if="currentStep > 1"
                        @click="previousStep" 
                        variant="outlined"
                        size="large"
                        prepend-icon="mdi-arrow-left"
                        class="step-btn"
                    >
                        Zurück
                    </v-btn>
                    <v-spacer />
                    <v-btn 
                        v-if="currentStep < 4"
                        @click="nextStep" 
                        :disabled="!canProceedToNextStep"
                        size="large"
                        class="step-btn"
                        color="brown"
                        append-icon="mdi-arrow-right"
                    >
                        Weiter
                    </v-btn>
                    <v-btn 
                        v-else
                        @click="createWorkflow" 
                        :disabled="!canCreateWorkflow"
                        :loading="isCreatingWorkflow"
                        size="large"
                        class="create-btn"
                        prepend-icon="mdi-check"
                    >
                        Workflow erstellen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        
        <!-- Workflow Edit Modal -->
        <WorkflowEditModal
            v-model="showEditModal"
            :workflow="selectedWorkflow"
            :clients="clients"
            :is-loading-clients="isLoadingClients"
            @workflow-updated="handleWorkflowUpdated"
            @workflow-deleted="handleWorkflowDeleted"
            @show-notification="handleNotification"
        />

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
    </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import store from '@/store/store'
import { DocumentAPI, WorkflowAPI } from '@/services/api'
import WorkflowEditModal from '@/components/WorkflowEditModal.vue'

const router = useRouter()

// Reactive data
const statusFilter = ref('')
const priorityFilter = ref('')
const searchQuery = ref('')
const dragover = ref(false)
const fileInput = ref<HTMLInputElement>()

// Workflow Creation Modal
const showWorkflowModal = ref(false)
const currentStep = ref(1)
const workflowFiles = ref<File[]>([])
const isCreatingWorkflow = ref(false)

// Workflow Edit Modal
const showEditModal = ref(false)
const selectedWorkflow = ref<any>(null)

// Notification system
const showNotificationSnackbar = ref(false)
const notificationText = ref('')
const notificationColor = ref('success')

// Legacy upload modal (keeping for backwards compatibility)
const showUploadModal = ref(false)
const uploadFiles = ref<File[]>([])

// Step data
const selectedClient = ref<number | null>(null)
const selectedRecipient = ref<number | null>(null)
const selectedWorker = ref<number | null>(null)
const selectedTemplate = ref<number | null>(null)
const workflowName = ref('')
const workflowDescription = ref('')
const workflowPriority = ref('medium')
const workflowDueDate = ref('')

// Template search
const templateSearchQuery = ref('')

// Loading states
const isLoadingWorkflows = ref(false)
const isLoadingClients = ref(false)
const isLoadingTemplates = ref(false)

// Data arrays
const clients = ref<any[]>([])
const documentTemplates = ref<any[]>([])

// Mock data for recipients and workers
const recipients = ref([
    { id: 1, name: 'max.mustermann@example.com', email: 'max.mustermann@example.com' },
    { id: 2, name: 'info@beispiel-ag.de', email: 'info@beispiel-ag.de' },
    { id: 3, name: 'kontakt@testfirma.de', email: 'kontakt@testfirma.de' }
])

const workers = ref([
    { id: 1, name: 'Dr. Schmidt', role: 'Senior Berater' },
    { id: 2, name: 'M. Weber', role: 'Steuerberater' },
    { id: 3, name: 'A. Müller', role: 'Buchhalter' },
    { id: 4, name: 'R. Fischer', role: 'Rechtsanwalt' }
])

// Step configuration
const stepperItems = computed(() => [
    { title: 'Dokumente', value: 1 },
    { title: 'Beteiligte', value: 2 },
    { title: 'Vorlage', value: 3 },
    { title: 'Bestätigung', value: 4 }
])

// Items for Vuetify selects
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

// Enhanced mock data for workflows
const workflows = ref<any[]>([])

// Real workflows will be loaded from API

// Computed properties
const filteredWorkflows = computed(() => {
    let filtered = workflows.value

    if (statusFilter.value) {
        filtered = filtered.filter(workflow => workflow.status === statusFilter.value)
    }

    if (priorityFilter.value) {
        filtered = filtered.filter(workflow => workflow.priority === priorityFilter.value)
    }

    if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(workflow => 
            workflow.name.toLowerCase().includes(query) ||
            workflow.client.toLowerCase().includes(query) ||
            workflow.assignedTo.toLowerCase().includes(query)
        )
    }

    return filtered
})

// Filtered templates based on search query
const filteredTemplates = computed(() => {
    if (!templateSearchQuery.value) {
        return documentTemplates.value
    }
    
    const query = templateSearchQuery.value.toLowerCase()
    return documentTemplates.value.filter(template => 
        template.name.toLowerCase().includes(query) ||
        (template.description && template.description.toLowerCase().includes(query)) ||
        formatFileType(template.file_type).toLowerCase().includes(query)
    )
})

// Step validation
const canProceedToNextStep = computed(() => {
    switch (currentStep.value) {
        case 1:
            return workflowFiles.value.length > 0
        case 2:
            return selectedClient.value !== null && workflowName.value.trim() !== ''
        case 3:
            return selectedTemplate.value !== null
        default:
            return false
    }
})

const canCreateWorkflow = computed(() => {
    return selectedClient.value !== null && 
            workflowName.value.trim() !== '' && 
            selectedTemplate.value !== null && 
            workflowFiles.value.length > 0 &&
            isDueDateValid.value
})

// Due date validation
const isDueDateValid = computed(() => {
    return !workflowDueDate.value || !isOverdue(workflowDueDate.value)
})

const dueDateErrorMessage = computed(() => {
    if (workflowDueDate.value && isOverdue(workflowDueDate.value)) {
        return ['Das gewählte Datum liegt in der Vergangenheit']
    }
    return []
})

// Helper functions
const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}

const isOverdue = (dueDateString: string) => {
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

const getTemplateIcon = (template: any) => {
    if (!template?.file_type) return 'mdi-file-document-outline'
    
    const type = template.file_type.toLowerCase()
    if (type.includes('pdf')) return 'mdi-file-pdf-box'
    if (type.includes('word') || type.includes('docx')) return 'mdi-file-word-box'
    if (type.includes('excel') || type.includes('xlsx')) return 'mdi-file-excel-box'
    return 'mdi-file-document-outline'
}

const formatFileType = (fileType: string) => {
    if (!fileType) return 'Unbekannt'
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return 'PDF'
    if (type.includes('word') || type.includes('docx')) return 'Word'
    if (type.includes('excel') || type.includes('xlsx')) return 'Excel'
    return fileType
}

const getClientDisplayName = (clientId: number | null) => {
    if (!clientId) return null
    const client = clients.value.find(c => c.id === clientId)
    return client?.displayName || null
}

const getRecipientName = (recipientId: number | null) => {
    if (!recipientId) return null
    const recipient = recipients.value.find(r => r.id === recipientId)
    return recipient?.name || null
}

const getWorkerName = (workerId: number | null) => {
    if (!workerId) return null
    const worker = workers.value.find(w => w.id === workerId)
    return worker?.name || null
}

const getSelectedTemplateData = () => {
    return documentTemplates.value.find(t => t.id === selectedTemplate.value) || null
}

const getTemplateColor = (template: any) => {
    if (!template?.file_type) return 'grey-lighten-2'
    
    const type = template.file_type.toLowerCase()
    if (type.includes('pdf')) return '#f44336'
    if (type.includes('word') || type.includes('docx')) return '#2196f3'
    if (type.includes('excel') || type.includes('xlsx')) return '#4caf50'
    return 'brown'
}

const getTemplateIconColor = (template: any) => {
    if (!template?.file_type) return 'grey-darken-1'
    
    const type = template.file_type.toLowerCase()
    if (type.includes('pdf')) return 'white'
    if (type.includes('word') || type.includes('docx')) return 'white'
    if (type.includes('excel') || type.includes('xlsx')) return 'white'
    return 'white'
}

const getFileTypeColor = (fileType: string) => {
    if (!fileType) return 'grey'
    
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return 'red'
    if (type.includes('word') || type.includes('docx')) return 'blue'
    if (type.includes('excel') || type.includes('xlsx')) return 'green'
    return 'brown'
}

const getTemplateCategory = (template: any) => {
    if (!template?.name) return 'Dokument'
    
    const name = template.name.toLowerCase()
    if (name.includes('vertrag') || name.includes('contract')) return 'Vertrag'
    if (name.includes('rechnung') || name.includes('invoice')) return 'Rechnung'
    if (name.includes('brief') || name.includes('letter')) return 'Brief'
    if (name.includes('kündigung') || name.includes('termination')) return 'Kündigung'
    if (name.includes('antrag') || name.includes('application')) return 'Antrag'
    return 'Dokument'
}

// Workflow navigation functions
const openWorkflowDetails = (workflowId: number) => {
    // Find the workflow to get its template_id
    const workflow = workflows.value.find(w => w.id === workflowId)
    const templateId = workflow?.template_id
    
    // Pass both workflowId and templateId as query parameters
    if (templateId) {
        router.push(`/documents/filling?workflowId=${workflowId}&templateId=${templateId}`)
    } else {
        router.push(`/documents/filling?workflowId=${workflowId}`)
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

const createNewWorkflow = () => {
    showWorkflowModal.value = true
    currentStep.value = 1
    resetWorkflowData()
    loadClients()
    loadDocumentTemplates()
}

const openAIAgent = () => {
    router.push('/ai-agent')
}

const editWorkflow = async (workflow: any) => {
    try {
        // Загружаем актуальные данные workflow с сервера
        const response = await WorkflowAPI.getWorkOrder(workflow.id)
        const freshWorkflowData = response.data
        
        // Трансформируем данные для UI
        const transformedWorkflow = {
            id: freshWorkflowData.id,
            name: freshWorkflowData.title || freshWorkflowData.name || 'Unbenannt',
            status: mapAPIStatusToDisplay(freshWorkflowData.status),
            client: getClientDisplayName(freshWorkflowData.client_id),
            client_id: freshWorkflowData.client_id,
            assignedTo: freshWorkflowData.assigned_to || 'Nicht zugewiesen',
            createdAt: freshWorkflowData.created_at ? freshWorkflowData.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
            dueDate: freshWorkflowData.due_date ? freshWorkflowData.due_date.split('T')[0] : '',
            documentCount: freshWorkflowData.document_count || 0,
            priority: freshWorkflowData.priority || 'medium',
            template_id: freshWorkflowData.template_id,
            description: freshWorkflowData.description || '',
            // Дополнительные поля для модального окна редактирования
            due_date: freshWorkflowData.due_date ? freshWorkflowData.due_date.split('T')[0] : '',
            assigned_to: freshWorkflowData.assigned_to
        }
        
        selectedWorkflow.value = transformedWorkflow
        showEditModal.value = true
        
    } catch (error) {
        console.error('Error loading workflow details:', error)
        displayNotification('Fehler beim Laden der Workflow-Details. Bitte versuchen Sie es erneut.', 'error')
        
        // Fallback: использовать имеющиеся данные
        selectedWorkflow.value = workflow
        showEditModal.value = true
    }
}

const viewDocuments = (workflowId: number) => {
    router.push(`/workflow/${workflowId}/documents`)
}

const openIntelligentProcessing = (workflowId: number) => {
    router.push(`/workflow/${workflowId}/intelligent-processing`)
}

// Workflow modal functions
const closeWorkflowModal = () => {
    showWorkflowModal.value = false
    resetWorkflowData()
}

const resetWorkflowData = () => {
    currentStep.value = 1
    workflowFiles.value = []
    selectedClient.value = null
    selectedRecipient.value = null
    selectedWorker.value = null
    selectedTemplate.value = null
    workflowName.value = ''
    workflowDescription.value = ''
    workflowPriority.value = 'medium'
    workflowDueDate.value = ''
    templateSearchQuery.value = ''
    dragover.value = false
}

const nextStep = () => {
    if (canProceedToNextStep.value && currentStep.value < 4) {
        currentStep.value++
    }
}

const previousStep = () => {
    if (currentStep.value > 1) {
        currentStep.value--
    }
}

// File handling for workflow   
const triggerFileInput = () => {
    fileInput.value?.click()
}

const handleFileDrop = (e: DragEvent) => {
    e.preventDefault()
    dragover.value = false
    const files = e.dataTransfer?.files
    if (files) {
        addWorkflowFiles(Array.from(files))
    }
}

const handleFileSelect = (e: Event) => {
    const target = e.target as HTMLInputElement
    const files = target.files
    if (files) {
        addWorkflowFiles(Array.from(files))
    }
}

const addWorkflowFiles = (files: File[]) => {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
    const validFiles = files.filter(file => validTypes.includes(file.type))
    workflowFiles.value.push(...validFiles)
}

const removeWorkflowFile = (index: number) => {
    workflowFiles.value.splice(index, 1)
}

// Data loading functions
const loadClients = async () => {
    try {
        isLoadingClients.value = true
        await store.dispatch('client/fetchClients')
        
        const storeClients = store.getters['client/getClients'] || []
        clients.value = storeClients.map((client: any) => ({
            id: client.id,
            displayName: client.client_type === 'natural' 
                ? `${client.title || ''} ${client.first_name || ''} ${client.last_name || ''}`.trim() || client.email || `Person ${client.id}`
                : client.company_name || client.email || `Unternehmen ${client.id}`,
            ...client
        }))
    } catch (error) {
        console.error('Error loading clients:', error)
        // Fallback with mock data if API fails
        clients.value = [
            { id: 1, displayName: 'Max Mustermann GmbH', client_type: 'company' },
            { id: 2, displayName: 'Dr. Hans Müller', client_type: 'natural' },
            { id: 3, displayName: 'Beispiel AG', client_type: 'company' }
        ]
    } finally {
        isLoadingClients.value = false
    }
}

const loadDocumentTemplates = async () => {
    try {
        isLoadingTemplates.value = true
        const response = await DocumentAPI.getTemplates()
        documentTemplates.value = response.data || []
    } catch (error) {
        console.error('Error loading document templates:', error)
        // Fallback with mock data if API fails
        documentTemplates.value = [
            {
                id: 1,
                name: 'Arbeitsvertrag',
                description: 'Standard Arbeitsvertrag Vorlage',
                file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                placeholders: [
                    { name: 'arbeitgeber', type: 'text' },
                    { name: 'arbeitnehmer', type: 'text' },
                    { name: 'beginn', type: 'date' }
                ]
            },
            {
                id: 2,
                name: 'Kündigung',
                description: 'Vorlage für Kündigungsschreiben',
                file_type: 'application/pdf',
                placeholders: [
                    { name: 'name', type: 'text' },
                    { name: 'anschrift', type: 'text' },
                    { name: 'kuendigungsdatum', type: 'date' }
                ]
            },
            {
                id: 3,
                name: 'Rechnung',
                description: 'Standardvorlage für Rechnungen',
                file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                placeholders: [
                    { name: 'kunde', type: 'text' },
                    { name: 'betrag', type: 'number' },
                    { name: 'datum', type: 'date' },
                    { name: 'leistungsbeschreibung', type: 'textarea' }
                ]
            }
        ]
    } finally {
        isLoadingTemplates.value = false
    }
}

// Show notification helper
const displayNotification = (message: string, color: 'success' | 'error' | 'warning' | 'info' = 'success') => {
    notificationText.value = message
    notificationColor.value = color
    showNotificationSnackbar.value = true
}

// Load workflows from API
const loadWorkflows = async () => {
    try {
        isLoadingWorkflows.value = true
        
        const response = await WorkflowAPI.getWorkOrders()
        const workflowsData = response.data || []
        
        // Transform API data to display format  
        workflows.value = await Promise.all(workflowsData.map(async (workflow: any) => {
            // Get client display name
            let clientDisplayName = 'Unbekannt'
            if (workflow.client_id && clients.value.length > 0) {
                const client = clients.value.find(c => c.id === workflow.client_id)
                if (client) {
                    clientDisplayName = client.displayName
                }
            }
            
            // Map API status to display status
            let displayStatus = workflow.status
            switch (workflow.status?.toLowerCase()) {
                case 'open':
                    displayStatus = 'to do'
                    break
                case 'in_progress':
                case 'in progress':
                case 'processing':
                    displayStatus = 'in progress'
                    break
                case 'completed':
                case 'done':
                case 'finished':
                case 'closed':
                    displayStatus = 'done'
                    break
                default:
                    displayStatus = workflow.status || 'to do'
            }
            
            // Get document count
            let documentCount = 0
            try {
                const documentsResponse = await WorkflowAPI.getWorkflowDocuments(workflow.id)
                documentCount = documentsResponse.data?.length || 0
            } catch (error) {
                console.warn(`Error loading document count for workflow ${workflow.id}:`, error)
                documentCount = 0
            }
            
            return {
                id: workflow.id,
                name: workflow.title || 'Unbenannt',
                status: displayStatus,
                client: clientDisplayName,
                assignedTo: workflow.assigned_to || 'Nicht zugewiesen',
                createdAt: workflow.created_at ? workflow.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
                dueDate: workflow.due_date ? workflow.due_date.split('T')[0] : '',
                documentCount: documentCount,
                priority: workflow.priority || 'medium',
                template_id: workflow.template_id  // Add template_id
            }
        }))
        
        // Show success message
        if (workflows.value.length > 0) {
            displayNotification(`${workflows.value.length} Workflow(s) erfolgreich geladen`, 'success')
        }
        
    } catch (error) {
        console.error('Error loading workflows:', error)
        // Keep empty array on error, show user-friendly message
        workflows.value = []
        displayNotification('Fehler beim Laden der Workflows. Bitte versuchen Sie es später erneut.', 'error')
    } finally {
        isLoadingWorkflows.value = false
    }
}

const createWorkflow = async () => {
    if (!canCreateWorkflow.value) return
    
    try {
        isCreatingWorkflow.value = true
        
        // Prepare workflow data for API
        const workflowData = {
            name: workflowName.value,
            description: workflowDescription.value,
            priority: workflowPriority.value,
            client_id: selectedClient.value,
            template_id: selectedTemplate.value,
            due_date: workflowDueDate.value || null,
            assigned_to: selectedWorker.value || null,
            recipient_id: selectedRecipient.value || null
        }
        
        // Create workflow with documents
        const response = await WorkflowAPI.createWorkOrderWithDocuments(workflowData, workflowFiles.value)
        const newWorkflow = response.data
        
        // Reload workflows from API to get updated list
        await loadWorkflows()
        
        // Show success and close modal
        closeWorkflowModal()
        
        displayNotification(`Workflow mit Dokumenten erfolgreich erstellt`, 'success')
        
    } catch (error) {
        console.error('Error creating workflow:', error)
        displayNotification('Fehler beim Erstellen des Workflows. Bitte versuchen Sie es erneut.', 'error')
    } finally {
        isCreatingWorkflow.value = false
    }
}

// Legacy upload modal functions (keeping for backwards compatibility)
const uploadDocuments = () => {
    showUploadModal.value = true
}

const closeUploadModal = () => {
    showUploadModal.value = false
    uploadFiles.value = []
    dragover.value = false
}

const startUpload = async () => {
    // TODO: Implement actual file upload logic
    // Simulate upload process
    for (const file of uploadFiles.value) {
        // Call API to upload file
    }
    
    closeUploadModal()
}

// New handlers for edit modal events
const handleWorkflowUpdated = (updatedWorkflow: any) => {
    // Обновляем локальный массив workflows с новыми данными
    const index = workflows.value.findIndex(w => w.id === updatedWorkflow.id)
    if (index !== -1) {
        // Трансформируем обновленные данные для отображения
        const transformedWorkflow = {
            id: updatedWorkflow.id,
            name: updatedWorkflow.title || updatedWorkflow.name || 'Unbenannt',
            status: mapAPIStatusToDisplay(updatedWorkflow.status),
            client: getClientDisplayName(updatedWorkflow.client_id),
            assignedTo: updatedWorkflow.assigned_to || 'Nicht zugewiesen',
            createdAt: updatedWorkflow.created_at ? updatedWorkflow.created_at.split('T')[0] : workflows.value[index].createdAt,
            dueDate: updatedWorkflow.due_date ? updatedWorkflow.due_date.split('T')[0] : '',
            documentCount: updatedWorkflow.document_count || workflows.value[index].documentCount,
            priority: updatedWorkflow.priority || 'medium',
            template_id: updatedWorkflow.template_id
        }
        
        // Обновляем элемент в массиве
        workflows.value[index] = transformedWorkflow
    } else {
        // Если workflow не найден, перезагружаем все данные
        loadWorkflows()
    }
}

const handleWorkflowDeleted = (workflowId: number) => {
    // Remove workflow from local array
    const index = workflows.value.findIndex(w => w.id === workflowId)
    if (index !== -1) {
        workflows.value.splice(index, 1)
    }
}

// Wrapper for displayNotification to match emit signature
const handleNotification = (message: string, color: 'success' | 'error' | 'warning' | 'info') => {
    displayNotification(message, color)
}

onMounted(() => {
    // Load real data from API
    loadInitialData()
})

// Load all initial data
const loadInitialData = async () => {
    try {
        // Load clients first so we can resolve client names in workflows
        await loadClients()
        
        // Then load workflows
        await loadWorkflows()
        
    } catch (error) {
        console.error('Error loading initial data:', error)
    }
}
</script>

<style scoped>
@import '../assets/views/dashboard.css';
</style>