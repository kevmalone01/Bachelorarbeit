<template>
  <div class="document-creation-container" style="padding: 0; margin: 0;">
    <!-- Upload state: Show upload zone if no document loaded -->
    <div v-if="!hasDocument" class="upload-container">
          <div 
            class="upload-zone"
            :class="{ 'upload-zone--active': dragover }"
            @drop="handleFileDrop" 
            @dragover.prevent="dragover = true" 
            @dragleave.prevent="dragover = false"
            @click="triggerFileInput"
          >
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
          
          <!-- Hidden file input -->
          <input 
            ref="fileInput" 
            type="file" 
            accept=".pdf,.docx" 
            style="display: none"
            @change="handleFileUpload" 
          />
          
          <!-- Upload progress -->
          <v-progress-linear 
            v-if="isUploading" 
            color="brown" 
            :model-value="uploadProgress" 
            height="15" 
            style="margin-top: 10px; border-radius: 10px;"
          >
            <template v-slot:default>
              <strong>{{ Math.ceil(uploadProgress) }}%</strong>
            </template>
          </v-progress-linear>
        </div>
        
        <!-- Editor state: Show editor if document is loaded -->
        <div v-else class="editor-container">
          <EditorTopbar
            :template-name="editor.templateName.value"
            :is-dirty="editor.isDirty.value"
            :saving="saving"
            @update:template-name="editor.templateName.value = $event"
            @preview="showPreview = true"
            @export="handleExport"
            @save="handleSave"
          />
          
          <div class="flex-1 flex overflow-hidden min-h-0">
            <!-- Left Panel -->
            <div class="w-80 bg-white border-r border-slate-200 flex flex-col min-h-0">
              <LeftPanelTabs
                :active-tab="activeTab"
                @update:active-tab="activeTab = $event"
              >
                <SettingsPanel
                  v-if="activeTab === 'settings'"
                  :placeholders="editor.placeholders.value"
                  :db-fields="dbFields"
                  :linked-client-groups="linkedClientGroups"
                  @update:placeholders="editor.placeholders.value = $event"
                  @update:linked-client-groups="linkedClientGroups = $event"
                  @rescan="handleRescan"
                  @save="handleSave"
                />
                
                <FormPanel
                  v-else
                  :placeholders="editor.placeholders.value"
                  :fill-values="editor.fillValues.value"
                  @update:fill-values="handleUpdateFillValues"
                  @reset="editor.resetFillValues()"
                />
              </LeftPanelTabs>
            </div>
            
            <!-- Main Editor Area -->
            <div class="flex-1 bg-white flex flex-col overflow-auto">
              <EditorCanvas
                :content-html="editor.contentHtml.value"
                :placeholders="editor.placeholders.value"
                :fill-values="editor.fillValues.value"
                @update:content-html="editor.contentHtml.value = $event"
                @placeholder-click="handlePlaceholderClick"
              />
            </div>
          </div>
          
          <!-- Preview Drawer -->
          <PreviewDrawer
            :show="showPreview"
            :content-html="editor.contentHtml.value"
            :fill-values="editor.fillValues.value"
            @close="showPreview = false"
            @export="handleExport"
          />
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
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useQuery, useMutation } from '@tanstack/vue-query';
import { createDiscreteApi } from 'naive-ui';
import mammoth from 'mammoth';
import EditorTopbar from '@/components/editor/EditorTopbar.vue';
import LeftPanelTabs from '@/components/editor/LeftPanelTabs.vue';
import SettingsPanel from '@/components/editor/SettingsPanel.vue';
import FormPanel from '@/components/editor/FormPanel.vue';
import EditorCanvas from '@/components/editor/EditorCanvas.vue';
import PreviewDrawer from '@/components/editor/PreviewDrawer.vue';
import { useTemplateEditor } from '@/composables/useTemplateEditor';
import { extractPlaceholders } from '@/composables/useDocumentPlaceholders';
import { documentEditorApi } from '@/lib/api';
import type { DocumentTemplate, DbField, FillValues } from '@/lib/types';
import { DocumentAPI } from '@/services/api';

const router = useRouter();
const { message: nMessage } = createDiscreteApi(['message']);

// File upload
const fileInput = ref<HTMLInputElement | null>(null);
const uploadedDocument = ref<File | null>(null);
const isUploading = ref(false);
const uploadProgress = ref(0);
const dragover = ref(false);
const documentId = ref<number | undefined>(undefined);

// Editor state
const activeTab = ref<'settings' | 'form'>('settings');
const showPreview = ref(false);
const saving = ref(false);
const linkedClientGroups = ref<string[]>([]);

// Load DB fields
const { data: dbFields = [] } = useQuery({
  queryKey: ['db-fields'],
  queryFn: () => documentEditorApi.getDbFields(),
});

// Initialize editor
const editor = useTemplateEditor();

// Computed
const hasDocument = computed(() => !!uploadedDocument.value || !!documentId.value);

// Snackbar
const snackbar = ref({
  show: false,
  text: '',
  color: 'success' as 'success' | 'error' | 'warning' | 'info',
});

function showNotification(text: string, color: 'success' | 'error' | 'warning' | 'info') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

// File upload handlers
function triggerFileInput() {
  fileInput.value?.click();
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    await processFile(target.files[0]);
  }
}

async function handleFileDrop(event: DragEvent) {
  dragover.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    await processFile(event.dataTransfer.files[0]);
  }
}

async function processFile(file: File) {
  // Check file type
  if (!file.type.includes('pdf') && !file.name.endsWith('.docx')) {
    showNotification('Nur PDF und DOCX Dateien werden unterstützt', 'error');
    return;
  }

  isUploading.value = true;
  uploadProgress.value = 0;

  try {
    // Simulate upload progress
    const uploadInterval = setInterval(() => {
      uploadProgress.value += 2;
      if (uploadProgress.value >= 100) {
        clearInterval(uploadInterval);
      }
    }, 100);

    if (file.name.endsWith('.docx')) {
      // Store uploaded file first so the editor container is rendered
      uploadedDocument.value = file;
      
      // Convert DOCX to HTML using Promise
      const htmlContent = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = async (e) => {
          try {
            const arrayBuffer = e.target?.result as ArrayBuffer;
            const result = await mammoth.convertToHtml({ arrayBuffer });
            resolve(result.value);
          } catch (error) {
            reject(error);
          }
        };
        reader.onerror = () => reject(new Error('Fehler beim Lesen der Datei'));
        reader.readAsArrayBuffer(file);
      });

      // Extract placeholders from HTML
      const extracted = extractPlaceholders(htmlContent);
      
      console.log('Document loaded:', {
        htmlLength: htmlContent.length,
        placeholders: extracted.length,
        htmlPreview: htmlContent.substring(0, 200)
      });
      
      // Update editor with content and placeholders
      // Wait for editor component to be mounted
      await nextTick();
      await nextTick(); // Double tick to ensure editor is ready
      
      // Set content - ensure it's valid HTML
      const cleanHtml = htmlContent.trim() || '<p></p>';
      editor.contentHtml.value = cleanHtml;
      editor.placeholders.value = extracted;
      editor.templateName.value = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
      editor.markSaved();
      
      // Force editor update after another tick
      await nextTick();
      console.log('Editor content set:', {
        contentLength: editor.contentHtml.value.length,
        preview: editor.contentHtml.value.substring(0, 200)
      });
      
      clearInterval(uploadInterval);
      uploadProgress.value = 100;
      
      setTimeout(() => {
        isUploading.value = false;
        showNotification(`Dokument erfolgreich hochgeladen. ${extracted.length} Platzhalter gefunden.`, 'success');
      }, 500);
    } else {
      // PDF: For now, show error
      clearInterval(uploadInterval);
      isUploading.value = false;
      showNotification('PDF-Dateien werden derzeit nicht unterstützt. Bitte verwenden Sie DOCX.', 'error');
    }
  } catch (error) {
    isUploading.value = false;
    showNotification('Fehler beim Hochladen des Dokuments', 'error');
    console.error('Upload error:', error);
  }
}

// Editor handlers
function handleRescan() {
  const extracted = extractPlaceholders(editor.contentHtml.value);
  editor.placeholders.value = extracted;
  editor.markSaved();
  showNotification(`${extracted.length} Platzhalter gefunden`, 'success');
}

function handlePlaceholderClick(key: string) {
  activeTab.value = 'form';
}

function handleUpdateFillValues(values: FillValues) {
  Object.keys(values).forEach(key => {
    editor.updateFillValue(key, values[key]);
  });
}

// Save mutation
const saveMutation = useMutation({
  mutationFn: async () => {
    const data = editor.getTemplateData();
    
    if (documentId.value) {
      // Update existing template
      await documentEditorApi.updateTemplate(
        String(documentId.value),
        {
          name: editor.templateName.value,
          contentHtml: editor.contentHtml.value,
          placeholders: editor.placeholders.value,
          linkedClientGroupIds: linkedClientGroups.value || []
        }
      );
    } else if (uploadedDocument.value) {
      // Create new template
      const response = await documentEditorApi.saveTemplate(
        uploadedDocument.value,
        editor.templateName.value,
        editor.contentHtml.value,
        editor.placeholders.value,
        linkedClientGroups.value || []
      );
      
      if (response.id) {
        documentId.value = response.id;
      }
    } else {
      throw new Error('Kein Dokument hochgeladen');
    }
    
    return { ok: true };
  },
  onSuccess: () => {
    editor.markSaved();
    showNotification('Template gespeichert', 'success');
    saving.value = false;
  },
  onError: () => {
    showNotification('Fehler beim Speichern', 'error');
    saving.value = false;
  },
});

function handleSave() {
  saving.value = true;
  saveMutation.mutate();
}

async function handleExport(format: 'pdf' | 'docx') {
  try {
    if (documentId.value) {
      const blob = await documentEditorApi.exportTemplate(
        String(documentId.value),
        editor.fillValues.value,
        format
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${editor.templateName.value}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showNotification('Export erfolgreich', 'success');
    } else {
      showNotification('Bitte speichern Sie das Template zuerst', 'warning');
    }
  } catch (error) {
    showNotification('Fehler beim Export', 'error');
  }
}

// Handle view document from list
async function handleViewDocument(document: any) {
  try {
    documentId.value = document.id;
    editor.templateName.value = document.name || '';
    
    // Load template
    const template = await documentEditorApi.getTemplate(String(document.id));
    editor.contentHtml.value = template.contentHtml;
    editor.placeholders.value = template.placeholders || [];
    linkedClientGroups.value = template.linkedClientGroupIds || [];
    editor.markSaved();
    
    // Try to load the original document file
    try {
      const fileResponse = await DocumentAPI.getDocumentFile(document.id);
      const blob = fileResponse.data;
      const filename = `${document.name}.${document.file_type?.includes('pdf') ? 'pdf' : 'docx'}`;
      const file = new File([blob], filename, { 
        type: document.file_type || 'application/octet-stream' 
      });
      uploadedDocument.value = file;
    } catch (fileError) {
      console.warn('Could not load original document file:', fileError);
    }
    
    showNotification(`Template "${document.name}" geladen`, 'success');
  } catch (error) {
    console.error('Error loading document:', error);
    showNotification('Fehler beim Laden des Dokuments', 'error');
  }
}
</script>

<style scoped>
.document-creation-container {
  padding: 0 !important;
  margin: 0 !important;
  min-height: 100vh;
  width: 100vw;
  max-width: 100%;
}


/* Upload container */
.upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
  padding: 2rem;
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
  width: 100%;
  max-width: 600px;
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

/* Editor container */
.editor-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  background: #fff;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .editor-container {
    height: auto;
    min-height: 600px;
  }
}
</style>
