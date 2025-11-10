<template>
    <div class="document-list-container">
        <div class="controls">
            <div class="search-container">
                <v-icon class="search-icon" color="brown">mdi-magnify</v-icon>
                <input type="text" v-model="searchQuery" placeholder="Dokumente suchen..." class="search-input" />
            </div>
        </div>

        <div v-if="isLoading" class="loading-indicator">
            <v-progress-circular indeterminate color="#c2a47b"></v-progress-circular>
            <span>Daten werden geladen...</span>
        </div>

        <div v-else-if="error" class="error-message">
            <v-icon color="error" size="large">mdi-alert-circle</v-icon>
            <span>{{ error }}</span>
        </div>

        <div v-else-if="!filteredDocuments.length" class="no-documents">
            <v-icon size="x-large" color="#c2a47b">mdi-file-document-outline</v-icon>
            <p>Keine Dokumente gefunden.</p>
        </div>

        <div v-else class="document-list">
            <div v-for="document in filteredDocuments" :key="document.id" class="document-card">
                <div class="card-content">
                    <div class="card-header">
                        <div class="header-left">
                            <div class="document-avatar">
                                <v-icon color="#8B4513" size="large">
                                    {{ getFileTypeIcon(document) }}
                                </v-icon>
                            </div>
                            <div class="document-title">
                                <h3>{{ document.name }}</h3>
                                <span class="document-type">
                                    {{ formatFileType(document.file_type) }}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <div class="document-info">
                            <div class="info-row" v-if="document.description">
                                <v-icon size="small" color="#555">mdi-text-box-outline</v-icon>
                                <p>{{ document.description }}</p>
                            </div>
                            <div class="info-row">
                                <v-icon size="small" color="#555">mdi-calendar</v-icon>
                                <p><span>Erstellt am:</span> {{ formatDate(document.created_at) }}</p>
                            </div>
                            <div class="info-row" v-if="document.placeholders && document.placeholders.length > 0">
                                <v-icon size="small" color="#555">mdi-form-select</v-icon>
                                <p><span>Platzhalter:</span> {{ document.placeholders.length }}</p>
                            </div>
                        </div>
                    </div>

                    <div class="card-actions">
                        <v-btn @click="viewDocument(document)" class="btn-view" variant="outlined" size="small">
                            <v-icon size="small" class="action-icon">mdi-eye</v-icon>
                            Ansehen
                        </v-btn>
                        <v-btn @click="confirmDelete(document)" class="btn-delete" variant="tonal" color="error" size="small">
                            <v-icon size="small" class="action-icon">mdi-delete</v-icon>
                            Löschen
                        </v-btn>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete confirmation dialog -->
        <v-dialog v-model="deleteDialog" max-width="400">
            <v-card>
                <v-card-title class="dialog-title">
                    <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
                    Dokument löschen
                </v-card-title>
                <v-card-text class="dialog-content">
                    Sind Sie sicher, dass Sie <strong>{{ documentToDelete ? documentToDelete.name : '' }}</strong> löschen möchten? 
                    Diese Aktion kann nicht rückgängig gemacht werden.
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey-darken-1" variant="text" @click="deleteDialog = false">
                        Abbrechen
                    </v-btn>
                    <v-btn 
                        color="error" 
                        variant="tonal" 
                        @click="deleteDocument" 
                        :loading="isDeleting"
                        :disabled="isDeleting">
                        Löschen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Status notification -->
        <v-snackbar
            v-model="snackbar.show"
            :color="snackbar.color"
            :timeout="3000"
            location="top"
        >
            {{ snackbar.text }}
            <template v-slot:actions>
                <v-btn variant="text" @click="snackbar.show = false">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
            </template>
        </v-snackbar>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { DocumentAPI } from '@/services/api';

// Props и emits для коммуникации с родительским компонентом
const emit = defineEmits(['view-document']);

const searchQuery = ref('');
const isLoading = ref(true);
const error = ref('');
const documents = ref<any[]>([]);

// Delete confirmation
const deleteDialog = ref(false);
const documentToDelete = ref<any>(null);
const isDeleting = ref(false);

// Snackbar notification
const snackbar = ref({
    show: false,
    color: 'success',
    text: ''
});

// Filter documents by search query
const filteredDocuments = computed(() => {
    if (!searchQuery.value) return documents.value;

    const query = searchQuery.value.toLowerCase();
    return documents.value.filter((doc: any) => {
        return (
            (doc.name && doc.name.toLowerCase().includes(query)) ||
            (doc.description && doc.description.toLowerCase().includes(query))
        );
    });
});

// Format date
const formatDate = (dateString: string) => {
    try {
        if (!dateString) return 'Unbekannt';
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('de-DE').format(date);
    } catch (e) {
        return dateString || 'Unbekannt';
    }
};

// Get icon based on file type
const getFileTypeIcon = (document: any) => {
    const type = document.file_type?.toLowerCase() || '';
    
    if (type.includes('pdf')) {
        return 'mdi-file-pdf-box';
    } else if (type.includes('word') || type.includes('docx')) {
        return 'mdi-file-word-box';
    } else if (type.includes('excel') || type.includes('xlsx')) {
        return 'mdi-file-excel-box';
    } else {
        return 'mdi-file-document-outline';
    }
};

// Format file type for display
const formatFileType = (fileType: string) => {
    if (!fileType) return 'Unbekannt';
    
    const type = fileType.toLowerCase();
    if (type.includes('pdf')) {
        return 'PDF';
    } else if (type.includes('word') || type.includes('docx')) {
        return 'Word';
    } else if (type.includes('excel') || type.includes('xlsx')) {
        return 'Excel';
    } else {
        return fileType;
    }
};

// View document details - emit event to parent to switch to creation view
const viewDocument = (document: any) => {
    emit('view-document', document);
};

// Open delete confirmation dialog
const confirmDelete = (document: any) => {
    documentToDelete.value = document;
    deleteDialog.value = true;
};

// Delete document
const deleteDocument = async () => {
    if (!documentToDelete.value) return;
    
    try {
        isDeleting.value = true;
        
        // Call real API to delete document
        await DocumentAPI.deleteTemplate(documentToDelete.value.id);
        
        // Remove from local array
        documents.value = documents.value.filter(doc => doc.id !== documentToDelete.value.id);
        
        // Show success notification
        snackbar.value = {
            show: true,
            color: 'success',
            text: `Dokument "${documentToDelete.value.name}" wurde erfolgreich gelöscht.`
        };
        
        // Close dialog
        deleteDialog.value = false;
        documentToDelete.value = null;
        isDeleting.value = false;
        
    } catch (error: any) {
        console.error(`Error deleting document: ${documentToDelete.value.id}`, error);
        snackbar.value = {
            show: true,
            color: 'error',
            text: 'Fehler beim Löschen des Dokuments: ' + (error.response?.data?.error || error.message || 'Unbekannter Fehler')
        };
        isDeleting.value = false;
    }
};

// Fetch document templates from API
const fetchDocuments = async () => {
    isLoading.value = true;
    error.value = '';
    
    try {
        const response = await DocumentAPI.getTemplates();
        documents.value = response.data;
    } catch (err: any) {
        console.error('Error fetching documents:', err);
        error.value = 'Fehler beim Laden der Dokumente: ' + (err.response?.data?.error || err.message || 'Unbekannter Fehler');
        
        // Fallback - показываем mock данные если API не работает
        documents.value = [
            {
                id: 1,
                name: 'Arbeitsvertrag',
                description: 'Standard Arbeitsvertrag Vorlage',
                file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                created_at: '2023-05-15T10:30:00Z',
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
                created_at: '2023-06-20T14:15:00Z',
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
                created_at: '2023-07-05T09:45:00Z',
                placeholders: [
                    { name: 'kunde', type: 'text' },
                    { name: 'betrag', type: 'number' },
                    { name: 'datum', type: 'date' },
                    { name: 'leistungsbeschreibung', type: 'textarea' }
                ]
            }
        ];
    } finally {
        isLoading.value = false;
    }
};

// Fetch documents when component is mounted
onMounted(() => {
    fetchDocuments();
});

// Expose fetchDocuments method for external refresh
defineExpose({
    fetchDocuments
});
</script>

<style scoped>
.document-list-container {
    max-width: 1200px;
    margin: 0 auto;
}

.controls {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-bottom: 2rem;
}

.search-container {
    position: relative;
    width: 100%;
    display: flex;
    align-items: center;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    overflow: hidden;
}

.search-icon {
    position: absolute;
    left: 12px;
    color: #777;
}

.search-input {
    width: 100%;
    padding: 12px 12px 12px 40px;
    border: none;
    font-size: 14px;
    outline: none;
    transition: box-shadow 0.3s ease;
}

.search-input:focus {
    box-shadow: 0 0 0 2px rgba(194, 164, 123, 0.2);
}

.loading-indicator,
.error-message,
.no-documents {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    gap: 1rem;
    text-align: center;
    color: #666;
    background-color: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.error-message {
    color: #d32f2f;
}

.document-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1.5rem;
}

.document-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    display: flex;
    border-color: transparent;
}

.document-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.card-header {
    padding: 1.2rem 1.5rem 0.8rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.document-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(139, 69, 19, 0.1);
}

.document-title {
    display: flex;
    flex-direction: column;
}

.document-title h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
}

.document-type {
    font-size: 0.75rem;
    width: 3rem;
    text-align: center;
    border-radius: 12px;
    background-color: rgba(194, 164, 123, 0.1);
    color: #777;
    padding: 0.2rem 0.5rem;
    margin-top: 4px;
    display: inline-block;
    font-weight: 500;
}

.card-body {
    padding: 0 1.5rem 1rem 1.5rem;
    flex: 1;
}

.document-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.info-row {
    display: flex;
    align-items: flex-start;
    gap: 8px;
}

.info-row p {
    margin: 0;
    font-size: 0.9rem;
    color: #555;
    line-height: 1.5;
}

.info-row span {
    font-weight: 600;
    color: #444;
}

.card-actions {
    display: flex;
    padding: 1rem 1.5rem;
    background: #f9f9f9;
    border-top: 1px solid #eee;
    gap: 12px;
    justify-content: flex-end;
}

.action-icon {
    margin-right: 4px;
}

.btn-view {
    color: #555;
    border-color: #ddd;
}

.btn-delete {
    background-color: rgba(244, 67, 54, 0.08);
}

.btn-view:hover {
    border-color: #bbb;
    background-color: #f5f5f5;
}

.btn-delete:hover {
    background-color: rgba(244, 67, 54, 0.12);
}

/* Dialog styling */
.dialog-title {
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    padding: 1.5rem 1.5rem 0.5rem 1.5rem;
}

.dialog-content {
    padding: 0 1.5rem 0 1.5rem !important;
    font-size: 1rem;
    color: #333;
    line-height: 1.6;
}

/* Responsive styles */
@media (max-width: 600px) {
    .search-container {
        width: 100%;
    }
    
    .document-list {
        grid-template-columns: 1fr;
    }
    
    .card-actions {
        flex-direction: row;
        flex-wrap: wrap;
    }
    
    .info-row {
        flex-direction: row;
    }
}
</style> 