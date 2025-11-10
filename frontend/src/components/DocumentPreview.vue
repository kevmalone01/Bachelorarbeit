<template>
    <div class="document-preview-component">
        <v-card class="preview-card">
            <v-card-title class="d-flex align-center justify-space-between">
                <!-- <span class="preview-title">{{ title }}</span> -->
                <div class="view-mode-toggle">
                    <v-radio-group v-model="viewMode" inline color="brown" class="mt-0">
                        <v-radio label="Text" value="text" density="compact" hide-details></v-radio>
                        <v-radio label="PDF" value="pdf" density="compact" hide-details></v-radio>
                    </v-radio-group>
                </div>
                <div class="preview-actions" v-if="viewMode === 'pdf'">
                    <v-btn color="brown" icon="mdi-file-download" variant="outlined"
                        @click="downloadDocument" tooltip="Download Document">
                    </v-btn>
                    <v-btn  color="brown" icon="mdi-open-in-app" variant="outlined"
                        @click="openInNewWindow" tooltip="Open in New Window">
                    </v-btn>
                    <v-btn v-if="isClosable" icon="mdi-close" @click="$emit('close')"></v-btn>
                </div>
            </v-card-title>

            <v-card-text class="preview-container">
                <div v-if="isLoading" class="loading-state">
                    <v-progress-circular indeterminate color="brown"></v-progress-circular>
                    <p>Generiere Vorschau...</p>
                </div>
                
                <div v-else-if="error" class="error-state">
                    <v-icon size="48" color="error">mdi-alert-circle-outline</v-icon>
                    <p>{{ error }}</p>
                </div>
                
                <div v-else-if="!showPreview && viewMode !== 'text'" class="empty-state">
                    <v-icon size="48" color="grey">mdi-file-document-outline</v-icon>
                    <p>Keine Vorschau verfügbar. Füllen Sie das Formular aus und generieren Sie eine Vorschau.</p>
                </div>
                
                <div v-else class="preview-content">
                    <!-- Text Preview Mode -->
                    <div v-if="viewMode === 'text'" class="text-preview-container">
                        <div v-if="isLoadingTextPreview" class="loading-state">
                            <v-progress-circular indeterminate color="brown"></v-progress-circular>
                            <p>Text wird generiert...</p>
                        </div>
                        <div v-else class="text-preview-content">
                            <div v-if="documentText" v-html="highlightedTextPreview"></div>
                            <div v-else class="empty-text-state">
                                <v-icon size="48" color="grey">mdi-text-box-outline</v-icon>
                                <p>Kein Textinhalt verfügbar.</p>
                            </div>
                        </div>
                    </div>
                
                    <!-- PDF Viewer with navigation -->
                    <div v-else-if="previewBlobUrl && previewMimeType === 'application/pdf' && pdf" class="pdf-viewer">
                        <!-- PDF Content -->
                        <div class="pdf-document-container">
                            <VuePDF 
                                :pdf="pdf"
                                :page="currentPage"
                                :scale="scale"
                                text-layer
                                annotation-layer
                                :highlight-text="highlightText"
                                :highlight-options="highlightOptions"
                                @loaded="handlePageLoaded"
                                @error="handlePdfError"
                            />
                        </div>
                        <!-- PDF Controls -->
                        <div class="pdf-controls">
                            <div class="controls-group">
                                <!-- Page Navigation -->
                                <div class="page-navigation">
                                    <v-btn 
                                        color="brown" 
                                        icon="mdi-chevron-left" 
                                        variant="text"
                                        @click="currentPage = Math.max(1, currentPage - 1)" 
                                        :disabled="currentPage === 1">
                                    </v-btn>
                                    
                                    <div class="page-info">
                                        <span class="current-page">{{ currentPage }}</span>
                                        <span class="page-separator">/</span>
                                        <span class="total-pages">{{ totalPages }}</span>
                                    </div>
                                    
                                    <v-btn 
                                        color="brown" 
                                        icon="mdi-chevron-right" 
                                        variant="text"
                                        @click="currentPage = Math.min(totalPages, currentPage + 1)" 
                                        :disabled="currentPage === totalPages">
                                    </v-btn>
                                </div>

                                <!-- Zoom Controls -->
                                <div class="zoom-controls">
                                    <v-btn 
                                        color="brown" 
                                        icon="mdi-magnify-minus" 
                                        variant="text"
                                        @click="scale = Math.max(0.5, scale - 0.25)" 
                                        :disabled="scale <= 0.5">
                                    </v-btn>
                                    <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
                                    <v-btn 
                                        color="brown" 
                                        icon="mdi-magnify-plus" 
                                        variant="text"
                                        @click="scale = Math.min(3, scale + 0.25)" 
                                        :disabled="scale >= 3">
                                    </v-btn>
                                </div>
                            </div>

                            <!-- Search -->
                            <v-text-field
                                v-model="highlightText"
                                class="search-input"
                                density="compact"
                                hide-details
                                placeholder="Search..."
                                prepend-inner-icon="mdi-magnify"
                                clearable
                                variant="outlined"
                            ></v-text-field>
                        </div>
                    </div>
                    
                    <!-- Fallback for other document types -->
                    <div v-else class="preview-fallback">
                        <v-icon size="64" color="brown">mdi-file-document-outline</v-icon>
                        <p>Dokument erstellt, aber Vorschau nicht verfügbar. Füllen Sie das Formular aus und generieren Sie eine Vorschau.</p>
                    </div>
                </div>
            </v-card-text>
        </v-card>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, watch, onBeforeUnmount, onMounted } from 'vue';
import type { PropType } from 'vue';
import { DocumentAPI } from '@/services/api';
import { VuePDF, usePDF } from '@tato30/vue-pdf';
import '@tato30/vue-pdf/style.css';
import mammoth from 'mammoth';

interface PreviewData {
    preview_data: string;
    mime_type: string;
    filename: string;
}

export default defineComponent({
    name: 'DocumentPreview',
    
    components: {
        VuePDF
    },
    
    props: {
        documentId: {
            type: Number,
            required: false,
            default: undefined
        },
        placeholderValues: {
            type: Object as PropType<Record<string, any>>,
            required: true
        },
        title: {
            type: String,
            default: 'Dokument-Vorschau'
        },
        autoGenerate: {
            type: Boolean,
            default: false
        },
        isClosable: {
            type: Boolean,
            default: false
        },
        documentFile: {
            type: Object as PropType<File | null>,
            required: false,
            default: null
        },
        initialViewMode: {
            type: String,
            default: 'pdf',
            validator: (value: string) => ['pdf', 'text'].includes(value)
        }
    },
    
    emits: ['preview-generated', 'error', 'close', 'view-mode-change'],
    
    setup(props, { emit }) {
        const isLoading = ref(false);
        const error = ref<string | null>(null);
        const previewData = ref<PreviewData | null>(null);
        const showPreview = ref(false);
        const previewBlobUrl = ref<string | null>(null);
        const viewMode = ref(props.initialViewMode);
        
        // PDF viewer specific state
        const currentPage = ref(1);
        const currentPageInput = ref('1');
        const totalPages = ref(1);
        const scale = ref(1.0);
        
        // Text highlighting state
        const highlightText = ref('');
        const highlightOptions = ref({
            completeWords: false,
        });
        
        // Initialize PDF viewer
        const pdfUrl = ref<string | null>(null);
        const { pdf, pages } = usePDF(pdfUrl);
        
        // Text preview state
        const isLoadingTextPreview = ref(false);
        const documentText = ref('');
        
        // Watch for changes in previewBlobUrl to update pdfUrl
        watch(previewBlobUrl, (val) => {
            if (val) {
                pdfUrl.value = val;
            }
        });
        
        // Watch for changes in pages to update totalPages
        watch(pages, (val) => {
            if (val) {
                totalPages.value = val;
            }
        });
        
        // Watch for changes in viewMode
        watch(viewMode, (newMode) => {
            emit('view-mode-change', newMode);
            
            if (newMode === 'text') {
                if (!documentText.value && (previewData.value || props.documentFile)) {
                    extractTextContent();
                }
                showPreview.value = true;
            }
        });
        
        // Ensure text content is extracted on mount if in text mode
        onMounted(() => {
            if (viewMode.value === 'text' && (props.documentFile || props.documentId) && !documentText.value) {
                extractTextContent();
            }
        });
        
        // Extract text content from the document file or preview data
        let extractTextDebounceTimer: number | null = null;
        const extractTextContent = async () => {
            if (isLoadingTextPreview.value) return;
            
            // Clear any existing timer
            if (extractTextDebounceTimer !== null) {
                clearTimeout(extractTextDebounceTimer);
            }

            isLoadingTextPreview.value = true;

            extractTextDebounceTimer = setTimeout(async () => {
                try {
                    let text = '';
                    if (props.documentFile) {
                        // Extract from original document
                        text = await readFileContent(props.documentFile);
                    } else if (props.documentId) {
                        // Try to get text content from API
                        try {
                            const response = await DocumentAPI.getDocumentText(props.documentId);
                            text = response.data.text || 'Kein Text verfügbar.';
                        } catch (apiError) {
                            console.warn('Could not get text from API, trying preview data:', apiError);
                            // Fallback to preview data if available
                            if (previewData.value && previewData.value.preview_data) {
                                const blob = base64ToBlob(previewData.value.preview_data, previewData.value.mime_type);
                                const file = new File([blob], previewData.value.filename, { type: previewData.value.mime_type });
                                text = await readFileContent(file);
                            } else {
                                text = 'Text konnte nicht geladen werden. Bitte wechseln Sie zur PDF-Ansicht.';
                            }
                        }
                    } else if (previewData.value && previewData.value.preview_data) {
                        // Extract from preview data
                        const blob = base64ToBlob(previewData.value.preview_data, previewData.value.mime_type);
                        const file = new File([blob], previewData.value.filename, { type: previewData.value.mime_type });
                        text = await readFileContent(file);
                    } else {
                        text = 'Kein Dokument verfügbar für die Textanzeige.';
                    }
                    
                    // Clean up text - remove excessive line breaks
                    documentText.value = text.replace(/\n\n\n+/g, '\n\n');
                } catch (error) {
                    console.error('Error extracting text content:', error);
                    documentText.value = 'Fehler beim Extrahieren des Textes aus dem Dokument.';
                } finally {
                    isLoadingTextPreview.value = false;
                    extractTextDebounceTimer = null;
                }
                }, 500);
            
            showPreview.value = true; // Always show preview when extracting text
        };
        
        // Helper function to read text content from a file
        const readFileContent = (file: File): Promise<string> => {
            return new Promise((resolve, reject) => {
                if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
                    // For PDFs, we currently have a limitation
                    resolve("PDF-Textextraktion ist in dieser Vorschau nicht implementiert. Bitte wechseln Sie zur PDF-Ansicht für eine vollständige Darstellung.");
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
        
        // Computed property for highlighted text preview
        const highlightedTextPreview = computed(() => {
            if (!documentText.value) return '';
            
            let result = documentText.value;
            
            // Get the list of placeholder keys from the placeholderValues prop
            const placeholderKeys = Object.keys(props.placeholderValues);
            
            // Sort keys by length (longest first) to avoid replacing parts of longer placeholders
            const sortedKeys = [...placeholderKeys].sort((a, b) => b.length - a.length);
            
            // Replace each placeholder with its value or highlight it
            for (const key of sortedKeys) {
                const placeholderPattern = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
                const value = props.placeholderValues[key] || `{{${key}}}`;
                
                if (value === `{{${key}}}`) {
                    // Placeholder not filled - highlight in yellow
                    result = result.replace(
                        placeholderPattern, 
                        `<span class="highlight-placeholder unfilled">{{${key}}}</span>`
                    );
                } else {
                    // Placeholder filled - highlight in green
                    result = result.replace(
                        placeholderPattern, 
                        `<span class="highlight-placeholder filled">${value}</span>`
                    );
                }
            }
            
            // Format line breaks
            result = result.replace(/\n/g, '<br>');
            
            return result;
        });
        
        // Handle page input changes
        const handlePageInputChange = () => {
            const pageNum = parseInt(currentPageInput.value);
            if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages.value) {
                currentPage.value = pageNum;
            } else {
                // Reset to current page if input is invalid
                currentPageInput.value = currentPage.value.toString();
            }
        };
        
        // Handle page loaded event
        const handlePageLoaded = (info: any) => {
            // If we have page info from loaded event, update total pages
            if (info && typeof info.pagesCount === 'number') {
                totalPages.value = info.pagesCount;
            }
        };
        
        // Update currentPageInput when currentPage changes
        watch(currentPage, (newPage) => {
            currentPageInput.value = newPage.toString();
        });
        
        // Convert base64 to Blob
        const base64ToBlob = (base64Data: string, contentType: string): Blob => {
            try {
                const byteCharacters = atob(base64Data);
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
                
                return new Blob(byteArrays, { type: contentType });
            } catch (e) {
                console.error('Error converting base64 to blob:', e);
                throw e;
            }
        };
        
        const handlePdfError = (pdfError: any) => {
            console.error('PDF loading error:', pdfError);
            error.value = 'Fehler beim Laden des PDF-Dokuments';
        };
        
        // Create Blob URL from preview data
        const createBlobUrl = async () => {
            // Clean up old state
            if (previewBlobUrl.value) {
                URL.revokeObjectURL(previewBlobUrl.value);
                previewBlobUrl.value = null;
            }

            if (!previewData.value || !previewData.value.preview_data) return;

            try {
                const blob = base64ToBlob(previewData.value.preview_data, previewData.value.mime_type);
                previewBlobUrl.value = URL.createObjectURL(blob);
            } catch (err) {
                console.error('Error creating blob URL:', err);
                error.value = 'Fehler beim Erstellen der Vorschau';
            }
        };
        
        // Computed for MIME type
        const previewMimeType = computed(() => {
            return previewData.value?.mime_type || '';
        });
        
        // Computed for file name
        const previewFileName = computed(() => {
            return previewData.value?.filename || 'document.pdf';
        });
        
        // Generate preview
        const generatePreview = async () => {
            if ((!props.documentId && !props.documentFile) || Object.keys(props.placeholderValues).length === 0) {
                return;
            }
            
            // Switch to PDF mode when generating preview
            if (viewMode.value !== 'pdf') {
                viewMode.value = 'pdf';
            }
            
            isLoading.value = true;
            error.value = null;
            
            try {
                let response;
                
                // If we have a file but no document ID, use the temp preview endpoint
                if (props.documentFile && !props.documentId) {
                    response = await DocumentAPI.getTemporaryPreview(
                        props.documentFile, 
                        props.placeholderValues
                    );
                } else if (props.documentId) {
                    // Otherwise use the regular document preview endpoint
                    response = await DocumentAPI.getDocumentPreview(
                        props.documentId,
                        props.placeholderValues
                    );
                } else {
                    throw new Error('No document ID or file provided');
                }
                
                previewData.value = response.data;
                
                // Create blob URL from the preview data
                await createBlobUrl();
                
                showPreview.value = true;
                
                // If we're in text view mode, extract the text content
                if (viewMode.value === 'text') {
                    extractTextContent();
                }
                
                emit('preview-generated', previewData.value);
            } catch (err: any) {
                const errorMessage = err.response?.data?.error || 'Fehler bei der Generierung der Vorschau';
                error.value = errorMessage;
                emit('error', errorMessage);
            } finally {
                isLoading.value = false;
            }
        };
        
        // Switch to PDF mode programmatically
        const switchToPdfMode = () => {
            viewMode.value = 'pdf';
        };
        
        // Switch to text mode programmatically
        const switchToTextMode = () => {
            viewMode.value = 'text';
        };
        
        // Update placeholder name - Method to be called from parent when a placeholder is renamed
        const updatePlaceholderName = (oldName: string, newName: string) => {
            // For DocumentPreview component, we need to regenerate the preview
            // if we detect that a placeholder changed name
            if (oldName !== newName && showPreview.value) {
                generatePreview();
            }
            
            // Also update the document text if we have it
            if (oldName !== newName && documentText.value) {
                updatePlaceholderInDocumentText(oldName, newName);
            }
        };
        
        // Update placeholder names in document text
        const updatePlaceholderInDocumentText = (oldName: string, newName: string) => {
            if (!documentText.value) return;
            
            // Replace all occurrences of the old placeholder with the new one
            const oldPlaceholderPattern = new RegExp(`\\{\\{${oldName}\\}\\}`, 'g');
            documentText.value = documentText.value.replace(oldPlaceholderPattern, `{{${newName}}}`);
        };
        
        // Download document
        const downloadDocument = async () => {
            try {
                if (previewBlobUrl.value && previewData.value) {
                    // Use existing blob URL for download
                    const a = document.createElement('a');
                    a.href = previewBlobUrl.value;
                    a.download = previewData.value.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                } else if (props.documentId) {
                    window.open(`/api/documents/download/${props.documentId}`, '_blank');
                }
            } catch (err) {
                console.error('Error downloading document:', err);
                error.value = 'Fehler beim Herunterladen des Dokuments';
            }
        };
        
        // Open preview in new window
        const openInNewWindow = () => {
            if (previewBlobUrl.value) {
                window.open(previewBlobUrl.value, '_blank');
            }
        };
        
        // Watch for changes in document ID, document file or placeholder values
        watch([() => props.documentId, () => props.documentFile, () => props.placeholderValues], (newValues, oldValues) => {
            const [newDocumentId, newDocumentFile, newPlaceholderValues] = newValues;
            const [oldDocumentId, oldDocumentFile, oldPlaceholderValues] = oldValues || [null, null, {}];
            
            // Check if document changed (not just placeholder values)
            const documentChanged = newDocumentId !== oldDocumentId || newDocumentFile !== oldDocumentFile;
            
            if (props.autoGenerate) {
                generatePreview();
            } else if (documentChanged) {
                // Only reset when document actually changes, not just placeholder values
                showPreview.value = false;
                previewData.value = null;
                
                // Clean up any existing blob URLs
                if (previewBlobUrl.value) {
                    URL.revokeObjectURL(previewBlobUrl.value);
                    previewBlobUrl.value = null;
                }
                
                // Reset PDF state
                currentPage.value = 1;
                currentPageInput.value = '1';
                totalPages.value = 1;
                
                // Reset text state only when document changes
                documentText.value = '';
                
                // Extract text content when document changes
                if (newDocumentFile || newDocumentId) {
                    if (viewMode.value === 'text') {
                        extractTextContent();
                    }
                }
            } else {
                // Only placeholder values changed, keep preview but update text highlighting
                if (viewMode.value === 'text' && !documentText.value && (newDocumentId || newDocumentFile)) {
                    // Extract text if we don't have it yet
                    extractTextContent();
                }
            }
        }, { deep: true });
        
        onBeforeUnmount(() => {
            if (previewBlobUrl.value) {
                URL.revokeObjectURL(previewBlobUrl.value);
            }
        });
        
        // Auto-generate on mount if configured
        if (props.autoGenerate) {
            generatePreview();
        }
        
        // Extract text on initial mount if document file is available
        if (props.documentFile) {
            extractTextContent();
        }
        
        return {
            isLoading,
            error,
            showPreview,
            previewBlobUrl,
            previewMimeType,
            previewFileName,
            generatePreview,
            updatePlaceholderName,
            downloadDocument,
            openInNewWindow,
            pdf,
            currentPage,
            currentPageInput,
            totalPages,
            scale,
            handlePageInputChange,
            handlePageLoaded,
            handlePdfError,
            highlightText,
            highlightOptions,
            viewMode,
            isLoadingTextPreview,
            highlightedTextPreview,
            documentText,
            switchToPdfMode,
            switchToTextMode,
        };
    }
});
</script>

<style scoped>
.document-preview-component {
    display: flex;
    flex-direction: column;
    height: 95%;
}

.preview-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    border-radius: 8px;
    overflow: hidden;
}

.preview-container {
    flex: 1;
    min-height: 400px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f5f7fa;
    padding: 0 !important;
}

.preview-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    max-width: 25%;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
}

.preview-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.pdf-viewer {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.pdf-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background-color: white;
    border-bottom: 1px solid #e0e0e0;
    gap: 16px;
}

.controls-group {
    display: flex;
    align-items: center;
    gap: 24px;
}

.page-navigation {
    display: flex;
    align-items: center;
    gap: 8px;
}

.page-info {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 14px;
    color: #5c6b7a;
    min-width: 60px;
    justify-content: center;
}

.current-page {
    font-weight: 500;
}

.page-separator {
    color: #9e9e9e;
}

.zoom-controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.zoom-level {
    font-size: 14px;
    color: #5c6b7a;
    min-width: 40px;
    text-align: center;
}

.search-input {
    width: 240px;
}

.pdf-document-container {
    flex: 1;
    overflow: auto;
    display: flex;
    justify-content: center;
    background-color: #f0f0f0;
    position: relative;
}

.pdf-document {
    margin: 16px auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    background: white;
}

.preview-iframe {
    width: 100%;
    height: 100%;
    border: none;
    background: white;
}

.loading-state,
.error-state,
.empty-state,
.preview-fallback {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #5c6b7a;
}

.loading-state p,
.error-state p,
.empty-state p {
    margin-top: 1rem;
    max-width: 320px;
    line-height: 1.6;
}

.error-state {
    color: #f44336;
}

.view-mode-toggle {
    display: flex;
    flex-direction: row;
    gap: 16px;
    align-items: center;
    border-radius: 8px;
    padding: 4px 8px;
}

.preview-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

.preview-fallback {
    height: 100%;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 2rem;
}

.preview-fallback p {
    margin: 1rem 0;
}

/* Text preview styles */
.text-preview-container {
    flex: 1;
    overflow: auto;
    width: 100%;
    height: 100%;
    background-color: white;
    padding: 1.5rem;
}

.text-preview-content {
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    color: #333;
}

.empty-text-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #5c6b7a;
    height: 100%;
}

.empty-text-state p {
    margin-top: 1rem;
    max-width: 320px;
    line-height: 1.6;
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

/* Mobile styles */
@media (max-width: 600px) {
    .pdf-controls {
        flex-direction: column;
        gap: 12px;
    }

    .controls-group {
        width: 100%;
        justify-content: space-between;
    }

    .search-input {
        width: 100%;
    }
    
    .view-mode-toggle {
        flex-direction: column;
        gap: 4px;
    }
}
</style> 