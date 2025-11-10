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
                                    @click="createNewWorkflow" 
                                    size="large"
                                    class="action-btn-secondary"
                                    prepend-icon="mdi-plus-circle"
                                >
                                    Neuer Workflow
                                </v-btn>
                            </div>
                        </v-col>
                </v-row>
            </v-card-text>

            <!-- Workflow Backlog -->
            <v-card-text class="workflows-backlog pa-8 pt-0">
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
                
                <!-- Backlog Columns -->
                <div v-else-if="filteredWorkflows.length > 0" class="backlog-board">
                    <!-- To Do Column -->
                    <div 
                        class="backlog-column"
                        :class="{ 'column-drag-over': dragOverColumn === 'to do' }"
                        @dragover="handleDragOver($event, 'to do')"
                        @dragleave="handleDragLeave"
                        @drop="handleDrop($event, 'to do')"
                    >
                        <div class="column-header">
                            <div class="column-title">
                                <v-icon class="column-icon me-2" color="warning">mdi-clock-outline</v-icon>
                                <h4>Zu erledigen</h4>
                            </div>
                            <v-chip 
                                variant="tonal" 
                                color="warning" 
                                size="small"
                                class="count-chip"
                            >
                                {{ getWorkflowsByStatus('to do').length }}
                            </v-chip>
                        </div>
                        <div class="column-content">
                            <div 
                                v-for="workflow in getWorkflowsByStatus('to do')" 
                                :key="workflow.id"
                                class="backlog-item"
                                :class="{ 'item-dragging': draggedWorkflow?.id === workflow.id }"
                                draggable="true"
                                @dragstart="handleDragStart($event, workflow)"
                                @dragend="handleDragEnd"
                                @click="openWorkflowDetails(workflow.id)"
                            >
                                <div class="item-header">
                                    <div class="item-title-section">
                                        <h5 class="item-title">{{ workflow.name }}</h5>
                                        <v-chip 
                                            :class="`priority-chip priority-chip--${workflow.priority.toLowerCase()}`"
                                            size="x-small" 
                                            variant="flat"
                                        >
                                            {{ priorityItems.find(item => item.value === workflow.priority)?.title }}
                                        </v-chip>
                                    </div>
                                </div>
                                
                                <div class="item-content">
                                    <div class="item-meta">
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-tie</v-icon>
                                            <span class="meta-text">{{ workflow.client }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-cog</v-icon>
                                            <span class="meta-text">{{ workflow.assignedTo }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-calendar-plus</v-icon>
                                            <span class="meta-text">{{ formatDate(workflow.createdAt) }}</span>
                                        </div>
                                        <div v-if="workflow.dueDate" class="meta-item">
                                            <v-icon 
                                                size="14" 
                                                class="meta-icon"
                                                :color="isOverdue(workflow.dueDate) ? 'error' : 'warning'"
                                            >
                                                mdi-calendar-clock
                                            </v-icon>
                                            <span 
                                                class="meta-text" 
                                                :class="{ 'text-error font-weight-bold': isOverdue(workflow.dueDate) }"
                                            >
                                                {{ formatDate(workflow.dueDate) }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="item-actions">
                                    <v-btn
                                        @click.stop="editWorkflow(workflow)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-pencil-outline"
                                        class="action-btn-mini"
                                    />
                                    <v-btn
                                        @click.stop="viewDocuments(workflow.id)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-file-document-multiple-outline"
                                        class="action-btn-mini"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- In Progress Column -->
                    <div 
                        class="backlog-column"
                        :class="{ 'column-drag-over': dragOverColumn === 'in progress' }"
                        @dragover="handleDragOver($event, 'in progress')"
                        @dragleave="handleDragLeave"
                        @drop="handleDrop($event, 'in progress')"
                    >
                        <div class="column-header">
                            <div class="column-title">
                                <v-icon class="column-icon me-2" color="info">mdi-clock-fast</v-icon>
                                <h4>In Arbeit</h4>
                            </div>
                            <v-chip 
                                variant="tonal" 
                                color="info" 
                                size="small"
                                class="count-chip"
                            >
                                {{ getWorkflowsByStatus('in progress').length }}
                            </v-chip>
                        </div>
                        <div class="column-content">
                            <div 
                                v-for="workflow in getWorkflowsByStatus('in progress')" 
                                :key="workflow.id"
                                class="backlog-item"
                                :class="{ 'item-dragging': draggedWorkflow?.id === workflow.id }"
                                draggable="true"
                                @dragstart="handleDragStart($event, workflow)"
                                @dragend="handleDragEnd"
                                @click="openWorkflowDetails(workflow.id)"
                            >
                                <div class="item-header">
                                    <div class="item-title-section">
                                        <h5 class="item-title">{{ workflow.name }}</h5>
                                        <v-chip 
                                            :class="`priority-chip priority-chip--${workflow.priority.toLowerCase()}`"
                                            size="x-small" 
                                            variant="flat"
                                        >
                                            {{ priorityItems.find(item => item.value === workflow.priority)?.title }}
                                        </v-chip>
                                    </div>
                                </div>
                                
                                <div class="item-content">
                                    <div class="item-meta">
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-tie</v-icon>
                                            <span class="meta-text">{{ workflow.client }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-cog</v-icon>
                                            <span class="meta-text">{{ workflow.assignedTo }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-calendar-plus</v-icon>
                                            <span class="meta-text">{{ formatDate(workflow.createdAt) }}</span>
                                        </div>
                                        <div v-if="workflow.dueDate" class="meta-item">
                                            <v-icon 
                                                size="14" 
                                                class="meta-icon"
                                                :color="isOverdue(workflow.dueDate) ? 'error' : 'warning'"
                                            >
                                                mdi-calendar-clock
                                            </v-icon>
                                            <span 
                                                class="meta-text" 
                                                :class="{ 'text-error font-weight-bold': isOverdue(workflow.dueDate) }"
                                            >
                                                {{ formatDate(workflow.dueDate) }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="item-actions">
                                    <v-btn
                                        @click.stop="editWorkflow(workflow)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-pencil-outline"
                                        class="action-btn-mini"
                                    />
                                    <v-btn
                                        @click.stop="viewDocuments(workflow.id)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-file-document-multiple-outline"
                                        class="action-btn-mini"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Done Column -->
                    <div 
                        class="backlog-column"
                        :class="{ 'column-drag-over': dragOverColumn === 'done' }"
                        @dragover="handleDragOver($event, 'done')"
                        @dragleave="handleDragLeave"
                        @drop="handleDrop($event, 'done')"
                    >
                        <div class="column-header">
                            <div class="column-title">
                                <v-icon class="column-icon me-2" color="success">mdi-check-circle-outline</v-icon>
                                <h4>Abgeschlossen</h4>
                            </div>
                            <v-chip 
                                variant="tonal" 
                                color="success" 
                                size="small"
                                class="count-chip"
                            >
                                {{ getWorkflowsByStatus('done').length }}
                            </v-chip>
                        </div>
                        <div class="column-content">
                            <div 
                                v-for="workflow in getWorkflowsByStatus('done')" 
                                :key="workflow.id"
                                class="backlog-item backlog-item--completed"
                                :class="{ 'item-dragging': draggedWorkflow?.id === workflow.id }"
                                draggable="true"
                                @dragstart="handleDragStart($event, workflow)"
                                @dragend="handleDragEnd"
                                @click="openWorkflowDetails(workflow.id)"
                            >
                                <div class="item-header">
                                    <div class="item-title-section">
                                        <h5 class="item-title">{{ workflow.name }}</h5>
                                        <v-chip 
                                            :class="`priority-chip priority-chip--${workflow.priority.toLowerCase()}`"
                                            size="x-small" 
                                            variant="flat"
                                        >
                                            {{ priorityItems.find(item => item.value === workflow.priority)?.title }}
                                        </v-chip>
                                    </div>
                                </div>
                                
                                <div class="item-content">
                                    <div class="item-meta">
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-tie</v-icon>
                                            <span class="meta-text">{{ workflow.client }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-account-cog</v-icon>
                                            <span class="meta-text">{{ workflow.assignedTo }}</span>
                                        </div>
                                        <div class="meta-item">
                                            <v-icon size="14" class="meta-icon">mdi-calendar-plus</v-icon>
                                            <span class="meta-text">{{ formatDate(workflow.createdAt) }}</span>
                                        </div>
                                        <div v-if="workflow.dueDate" class="meta-item">
                                            <v-icon 
                                                size="14" 
                                                class="meta-icon"
                                                :color="isOverdue(workflow.dueDate) ? 'error' : 'warning'"
                                            >
                                                mdi-calendar-clock
                                            </v-icon>
                                            <span 
                                                class="meta-text" 
                                                :class="{ 'text-error font-weight-bold': isOverdue(workflow.dueDate) }"
                                            >
                                                {{ formatDate(workflow.dueDate) }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="item-actions">
                                    <v-btn
                                        @click.stop="editWorkflow(workflow)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-pencil-outline"
                                        class="action-btn-mini"
                                    />
                                    <v-btn
                                        @click.stop="viewDocuments(workflow.id)"
                                        variant="text"
                                        size="small"
                                        icon="mdi-file-document-multiple-outline"
                                        class="action-btn-mini"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

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

// Drag and Drop state
const draggedWorkflow = ref<any>(null)
const dragOverColumn = ref<string | null>(null)
const isDragging = ref(false)

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

// Get workflows by status for backlog columns
const getWorkflowsByStatus = (status: string) => {
    return filteredWorkflows.value.filter(workflow => workflow.status === status)
}

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
           workflowFiles.value.length > 0
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
    // Prevent navigation if we're in the middle of dragging
    if (isDragging.value) {
        return
    }
    
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

const createNewWorkflow = () => {
    showWorkflowModal.value = true
    currentStep.value = 1
    resetWorkflowData()
    loadClients()
    loadDocumentTemplates()
}

const editWorkflow = (workflow: any) => {
    selectedWorkflow.value = workflow
    showEditModal.value = true
}

const viewDocuments = (workflowId: number) => {
    router.push(`/workflow/${workflowId}/documents`)
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
        workflows.value = workflowsData.map((workflow: any) => {
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
            
            return {
                id: workflow.id,
                name: workflow.title || 'Unbenannt',
                status: displayStatus,
                client: clientDisplayName,
                assignedTo: 'Nicht zugewiesen', // TODO: Get from tax_advisor_id
                createdAt: workflow.created_at ? workflow.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
                dueDate: workflow.due_date ? workflow.due_date.split('T')[0] : '',
                documentCount: 0, // TODO: Get document count from API
                priority: workflow.priority || 'medium',
                template_id: workflow.template_id  // Add template_id
            }
        })
        
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
            // Note: recipient and template will be handled separately in a more complete implementation
            // For now, we're just creating the basic workflow
        }
        
        // Call real API to create workflow
        const response = await WorkflowAPI.createWorkOrder(workflowData)
        const newWorkflow = response.data
        
        // Reload workflows from API to get updated list
        await loadWorkflows()
        
        // Show success and close modal
        closeWorkflowModal()
        
        displayNotification('Workflow erfolgreich erstellt!', 'success')
        
        // TODO: Handle file uploads separately
        
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
    // Reload workflows to get updated data
    loadWorkflows()
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

// Drag and Drop functions
const handleDragStart = (e: DragEvent, workflow: any) => {
    isDragging.value = true
    draggedWorkflow.value = workflow
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', workflow.id.toString())
    }
}

const handleDragEnd = () => {
    setTimeout(() => {
        isDragging.value = false
    }, 100) // Small delay to prevent click after drag
    draggedWorkflow.value = null
    dragOverColumn.value = null
}

const handleDragOver = (e: DragEvent, status: string) => {
    e.preventDefault()
    if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'move'
    }
    dragOverColumn.value = status
}

const handleDragLeave = () => {
    dragOverColumn.value = null
}

const handleDrop = async (e: DragEvent, targetStatus: string) => {
    e.preventDefault()
    dragOverColumn.value = null
    
    if (!draggedWorkflow.value) return
    
    const workflow = draggedWorkflow.value
    const oldStatus = workflow.status
    
    // Don't do anything if dropping on the same status
    if (oldStatus === targetStatus) {
        draggedWorkflow.value = null
        return
    }
    
    try {
        // Optimistically update the UI
        const workflowIndex = workflows.value.findIndex(w => w.id === workflow.id)
        if (workflowIndex !== -1) {
            workflows.value[workflowIndex].status = targetStatus
        }
        
        // Call API to update workflow status
        const updateData = { status: targetStatus }
        await WorkflowAPI.updateWorkOrder(workflow.id, updateData)
        
        // Show success message
        const statusName = statusItems.value.find(item => item.value === targetStatus)?.title || targetStatus
        displayNotification(`Workflow "${workflow.name}" wurde zu "${statusName}" verschoben`, 'success')
        
    } catch (error) {
        console.error('Error updating workflow status:', error)
        
        // Revert the optimistic update
        const workflowIndex = workflows.value.findIndex(w => w.id === workflow.id)
        if (workflowIndex !== -1) {
            workflows.value[workflowIndex].status = oldStatus
        }
        
        displayNotification('Fehler beim Verschieben des Workflows', 'error')
    } finally {
        draggedWorkflow.value = null
    }
}

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
/* Modern Dashboard Styling */
.dashboard-container {
    min-height: 100vh;
    padding: 2rem 1.5rem;
}

/* Header Section */
.header-section {
    position: relative;
    overflow: hidden;
}

.header-card {
    color: white;
    border-radius: 20px;
    position: relative;
    overflow: hidden;
}

.header-card::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 200px;
    border-radius: 50%;
    transform: translate(50%, -50%);
}

.status-indicator {
    width: 8px;
    height: 8px;
    background: #94754a;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.display-title {
    font-size: 3rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
    letter-spacing: -0.02em !important;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle-text {
    font-size: 1.125rem !important;
    color: #d4c4b0 !important;
    font-weight: 400 !important;
}

.action-btn-primary {
    color: white !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
    padding: 0 2rem !important;
    box-shadow: 0 8px 25px rgba(148, 117, 74, 0.25) !important;
    transition: all 0.3s ease !important;
}

.action-btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 35px rgba(148, 117, 74, 0.35) !important;
}

.action-btn-secondary {
    border: 1.5px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
    backdrop-filter: blur(10px) !important;
}

.upload-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
    padding: 0 2rem !important;
}

.cancel-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

/* Workflows Section */
.workflows-card {
    background: white;
    border-radius: 20px;
    border: 1px solid #e8ddd1;
    overflow: hidden;
}   

.section-title {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #4a3528 !important;
}

.count-chip {
    font-weight: 600 !important;
    text-transform: none !important;
}

.filter-select, .search-field {
    border-radius: 12px;
}

/* Workflow Cards */
.workflows-grid .v-row {
    margin: 0 -12px;
}

.workflow-card {
    background: white;
    border: 1px solid #e8ddd1;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    position: relative;
}

.workflow-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 25px 50px rgba(148, 117, 74, 0.1) !important;
    border-color: #d4c4b0;
}

.workflow-card:hover::before {
    transform: scaleX(1);
}

.workflow-title {
    font-size: 1.125rem !important;
    font-weight: 700 !important;
    color: #4a3528 !important;
    line-height: 1.3 !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
    hyphens: auto !important;
    max-width: 100%;
}

.workflow-client {
    color: #6b5d4f !important;
    font-weight: 500 !important;
}

.priority-chip {
    font-weight: 600 !important;
    text-transform: none !important;
    border-radius: 8px !important;
}

.priority-chip--high {
    background: linear-gradient(135deg, #f5e6e6 0%, #ecd4d4 100%) !important;
    color: #a04040 !important;
}

.priority-chip--medium {
    background: linear-gradient(135deg, #f2ead9 0%, #e8ddd1 100%) !important;
    color: #94754a !important;
}

.priority-chip--low {
    background: linear-gradient(135deg, #e8eed1 0%, #d4e0b0 100%) !important;
    color: #6b7a3d !important;
}

.status-chip {
    font-weight: 600 !important;
    text-transform: none !important;
    border-radius: 8px !important;
}

.status-chip--to-do {
    background: linear-gradient(135deg, #f2ead9 0%, #e8ddd1 100%) !important;
    color: #94754a !important;
}

.status-chip--in-progress {
    background: linear-gradient(135deg, #f6e4bc 0%, #f8cfa2 100%) !important;
    color: #8b6837 !important;
}

.status-chip--done {
    background: linear-gradient(135deg, #e8eed1 0%, #d4e0b0 100%) !important;
    color: #6b7a3d !important;
}

.assignee-info {
    gap: 0.5rem;
}

.assignee-name {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #6b5d4f !important;
}

.workflow-meta .v-list-item {
    min-height: auto !important;
}

.meta-label {
    font-size: 0.875rem !important;
    color: #6b5d4f !important;
    font-weight: 500 !important;
}

.meta-value {
    font-size: 0.875rem !important;
    color: #4a3528 !important;
    font-weight: 600 !important;
}

.workflow-actions .action-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 8px !important;
    text-transform: none !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.workflow-actions .action-btn:hover {
    transform: translateY(-1px) !important;
}

/* Empty State */
.empty-state {
    padding: 4rem 2rem;
}

.empty-state-title {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.empty-state-subtitle {
    color: #6b5d4f !important;
    font-size: 1rem !important;
}

/* Upload Modal */
.upload-modal {
    border-radius: 20px !important;
    overflow: hidden;
}

.modal-title {
    font-size: 1.5rem !important;
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


.files-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.files-chips {
    gap: 1rem !important;
}

.file-chip {
    max-width: 300px !important;
    height: auto !important;
    padding: 0.25rem 0.75rem !important;
    border-radius: 12px !important;
    border: 1px solid rgba(148, 117, 74, 0.3) !important;
    transition: all 0.2s ease !important;
}

.file-chip:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(148, 117, 74, 0.2) !important;
}

.file-chip-content {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    font-weight: 500 !important;
    color: #4a3528 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    max-width: 200px !important;
}

.file-size-small {
    font-size: 0.75rem !important;
    color: #8a7b6d !important;
    font-weight: 400 !important;
}

/* Responsive Design */
@media (max-width: 1280px) {
    .display-title {
        font-size: 2.5rem !important;
    }
}

@media (max-width: 960px) {
    .dashboard-container {
        padding: 1rem;
    }
    
    .display-title {
        font-size: 2rem !important;
    }
    
    .action-buttons {
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .analytics-section .v-row {
        margin: 0 -6px;
    }
    
    .workflows-grid .v-row {
        margin: 0 -6px;
    }
}

@media (max-width: 600px) {
    .header-card .v-row {
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .workflows-header .d-flex {
        flex-direction: column;
        gap: 1rem;
        align-items: flex-start !important;
    }
    
    .filters-section .v-row {
        flex-direction: column;
        gap: 1rem;
    }
    
    .analytics-value {
        font-size: 2rem !important;
    }
}

/* Custom utility classes */
.ga-3 > *:not(:last-child) {
    margin-right: 12px;
}

.ga-4 > *:not(:last-child) {
    margin-right: 16px;
}

.ga-6 > *:not(:last-child) {
    margin-right: 24px;
}

/* Loading State */
.loading-state {
    padding: 4rem 2rem;
}

.loading-title {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.loading-subtitle {
    color: #6b5d4f !important;
    font-size: 1rem !important;
}

/* Workflow Creation Modal Styles */
.workflow-modal {
    border-radius: 20px !important;
    overflow: hidden;
    max-height: 90vh;
}

.workflow-stepper {
    background: transparent !important;
    box-shadow: none !important;
}

.selection-title {
    font-size: 1.125rem !important;
    font-weight: 600 !important;
}

.selection-field {
    border-radius: 12px;
}

.template-card {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 16px !important;
    border: 2px solid transparent;
}

.template-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(148, 117, 74, 0.15) !important;
}

.template-card--selected {
    box-shadow: 0 8px 25px rgba(148, 117, 74, 0.25) !important;
}

.template-title-enhanced {
    font-size: 1.125rem !important;
    font-weight: 700 !important;
    color: #4a3528 !important;
    line-height: 1.3 !important;
    margin-bottom: 0.5rem !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
    hyphens: auto !important;
    max-width: 100%;
}

.template-type {
    font-size: 0.75rem !important;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    margin-top: 2px;
    display: inline-block;
}

.template-description {
    font-size: 0.875rem !important;
    color: #6b5d4f !important;
    line-height: 1.4;
}

.summary-card {
    border-color: #d4c4b0 !important;
}

.summary-section-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
    margin-bottom: 1rem;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}

.summary-label {
    font-weight: 500;
    color: #6b5d4f;
}

.summary-value {
    font-weight: 600;
    color: #4a3528;
}

.summary-file {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: #4a3528;
}

.summary-template {
    display: flex;
    align-items: center;
    font-size: 0.875rem;
    color: #4a3528;
    font-weight: 500;
}

.step-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.create-btn {
    border: 1px solid #94754a !important;
    color: #94754a !important;
    border-radius: 12px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.create-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(148, 117, 74, 0.3) !important;
}

/* Minimal Template Selection Styles */
.templates-header {
    border-bottom: 1px solid #e8ddd1;
    padding-bottom: 1.5rem;
}

.template-search {
    border-radius: 12px;
}

.template-stats {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.templates-grid {
    margin-top: 1.5rem;
}

.template-card-minimal {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 12px !important;
    border: 1px solid #e8ddd1 !important;
}

.template-card-minimal:hover {
    border-color: #94754a !important;
    box-shadow: 0 4px 12px rgba(148, 117, 74, 0.1) !important;
}

.template-card-minimal--selected {
    border-color: #4caf50 !important;
    background: linear-gradient(135deg, #f8fff8 0%, #f5f9f5 100%) !important;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15) !important;
}

.template-content-minimal {
    flex-grow: 1;
}

.template-title-minimal {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
    line-height: 1.3 !important;
    margin: 0;
}

.template-type-minimal {
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    font-size: 0.6rem !important;
    height: 20px !important;
}

.field-count {
    font-size: 0.75rem !important;
    color: #6b5d4f !important;
    font-weight: 500 !important;
}

/* Loading and Empty States */
.loading-templates {
    padding: 4rem 2rem;
}

.loading-title {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.loading-subtitle {
    color: #6b5d4f !important;
    font-size: 1rem !important;
}

.template-empty-search,
.template-empty-state {
    padding: 4rem 2rem;
}

.empty-search-title,
.empty-state-title {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
}

.empty-search-subtitle,
.empty-state-subtitle {
    color: #6b5d4f !important;
    font-size: 1rem !important;
    line-height: 1.5;
}

/* Responsive Design for Templates */
@media (max-width: 960px) {
    .template-card-enhanced {
        margin-bottom: 1.5rem;
    }
    
    .template-action-overlay {
        opacity: 1;
        transform: translateY(0);
        position: relative;
        background: transparent;
        padding: 1rem 0 0;
    }
}

@media (max-width: 600px) {
    .templates-header {
        text-align: center;
    }
    
    .template-search {
        max-width: 100% !important;
    }
    
    .template-stats {
        justify-content: center;
    }
}

/* Responsive adjustments for minimal cards */
@media (max-width: 768px) {
    .templates-grid .v-col {
        flex: 0 0 100%;
        max-width: 100%;
    }
    
    .template-card-minimal .d-flex.justify-space-between {
        gap: 1rem;
    }
    
    .template-content-minimal {
        min-width: 0;
    }
    
    .template-title-minimal {
        word-break: break-word;
    }
}

/* Backlog Board Styles */
.workflows-backlog {
    overflow-x: auto;
}

.backlog-board {
    display: flex;
    gap: 2rem;
    min-height: 600px;
    padding: 1rem 0;
}

.backlog-column {
    flex: 1;
    min-width: 320px;
    background: #fafafa;
    border-radius: 16px;
    border: 1px solid #e8ddd1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.column-header {
    background: white;
    padding: 1.5rem 1.5rem 1rem;
    border-bottom: 1px solid #e8ddd1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.column-title {
    display: flex;
    align-items: center;
}

.column-title h4 {
    font-size: 1.125rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
    margin: 0;
}

.column-icon {
    flex-shrink: 0;
}

.column-content {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.backlog-item {
    background: white;
    border: 1px solid #e8ddd1;
    border-radius: 12px;
    padding: 1.25rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    gap: 1rem;
    position: relative;
    overflow: hidden;
}

.backlog-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #94754a 0%, #b8926a 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.backlog-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 35px rgba(148, 117, 74, 0.15) !important;
    border-color: #d4c4b0;
}

.backlog-item:hover::before {
    opacity: 1;
}

.backlog-item--completed {
    opacity: 0.85;
}

.backlog-item--completed::before {
    background: linear-gradient(90deg, #4caf50 0%, #66bb6a 100%);
}

.backlog-item--completed:hover {
    opacity: 1;
}

.item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
}

.item-title-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
    min-width: 0;
}

.item-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #4a3528 !important;
    margin: 0;
    line-height: 1.3;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}

.item-content {
    flex: 1;
}

.item-meta {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.meta-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
}

.meta-icon {
    color: #94754a !important;
    flex-shrink: 0;
}

.meta-text {
    color: #6b5d4f;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.item-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.backlog-item:hover .item-actions {
    opacity: 1;
}

.action-btn-mini {
    color: #94754a !important;
    transition: all 0.2s ease !important;
}

.action-btn-mini:hover {
    background: rgba(148, 117, 74, 0.1) !important;
    transform: scale(1.1);
}

/* Drag and Drop Styles */
.backlog-item[draggable="true"] {
    cursor: grab;
}

.backlog-item[draggable="true"]:active {
    cursor: grabbing;
}

.item-dragging {
    opacity: 0.5 !important;
    transform: rotate(2deg) scale(0.95) !important;
    z-index: 1000 !important;
    box-shadow: 0 20px 40px rgba(148, 117, 74, 0.3) !important;
}

.column-drag-over {
    background: rgba(148, 117, 74, 0.05) !important;
    border: 2px dashed #94754a !important;
    transform: scale(1.02) !important;
    transition: all 0.3s ease !important;
}

.column-drag-over .column-header {
    background: rgba(148, 117, 74, 0.1) !important;
}

.column-drag-over .column-content {
    background: rgba(148, 117, 74, 0.03) !important;
}

/* Drag placeholder */
.backlog-item.drag-placeholder {
    border: 2px dashed #94754a;
    background: rgba(148, 117, 74, 0.1);
    opacity: 0.6;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94754a;
    font-weight: 600;
}

/* Touch devices support */
@media (hover: none) and (pointer: coarse) {
    .item-actions {
        opacity: 1 !important;
    }
    
    .backlog-item {
        user-select: none;
        -webkit-user-select: none;
        -webkit-touch-callout: none;
    }
}

/* Mobile Responsive */
@media (max-width: 1200px) {
    .backlog-board {
        gap: 1.5rem;
    }
    
    .backlog-column {
        min-width: 280px;
    }
}

@media (max-width: 960px) {
    .workflows-backlog {
        padding: 1rem 0.5rem !important;
    }
    
    .backlog-board {
        flex-direction: column;
        gap: 1.5rem;
        min-height: auto;
    }
    
    .backlog-column {
        min-width: 100%;
        max-height: 400px;
    }
    
    .column-content {
        max-height: 320px;
    }
}

@media (max-width: 600px) {
    .column-header {
        padding: 1rem;
        flex-direction: column;
        gap: 0.75rem;
        align-items: flex-start;
    }
    
    .backlog-item {
        padding: 1rem;
    }
    
    .item-header {
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .item-actions {
        opacity: 1;
        justify-content: flex-start;
    }
    
    .meta-item {
        font-size: 0.8rem;
    }
}
</style>