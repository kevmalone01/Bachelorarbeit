<template>
    <v-dialog 
        :model-value="modelValue" 
        @update:model-value="$emit('update:modelValue', $event)"
        max-width="50vw"
        max-height="90vh"
        class="pdf-modal"
    >
        <v-card class="pdf-card">
            <!-- Modal Header -->
            <v-card-title class="d-flex align-center pa-3">
                <span class="text-h6">{{ fileName || 'PDF Dokument' }}</span>
                <v-spacer />
                <v-btn
                    @click="$emit('update:modelValue', false)"
                    icon="mdi-close"
                    variant="text"
                    size="small"
                />
            </v-card-title>

            <v-divider />

            <!-- PDF Content -->
            <v-card-text class="pdf-content pa-0">
                <div v-if="isLoading" class="pdf-loading">
                    <v-progress-circular 
                        indeterminate 
                        color="brown" 
                        size="48"
                        class="mb-3"
                    />
                    <p class="text-body-2">PDF wird geladen...</p>
                </div>
                
                <div v-else-if="error" class="pdf-error">
                    <v-icon size="48" color="error" class="mb-3">mdi-alert-circle-outline</v-icon>
                    <h4 class="mb-2">Fehler beim Laden</h4>
                    <p class="text-body-2 mb-3">{{ error }}</p>
                </div>
                
                <div v-else-if="pdfUrl" class="pdf-container">
                    <iframe
                        :src="pdfUrl"
                        class="pdf-iframe"
                        @load="handlePdfLoad"
                        @error="handlePdfError"
                        title="PDF Document"
                    />
                </div>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

// Props
interface Props {
    modelValue: boolean
    pdfUrl: string
    fileName?: string
    highlightText?: string
}
const props = withDefaults(defineProps<Props>(), {
    highlightText: ''
})

// Emits
const emit = defineEmits<{
    'update:modelValue': [value: boolean]
    download: []
}>()

// Reactive data
const isLoading = ref(false)
const error = ref('')
const loadTimeout = ref<number | null>(null)

// Watch for changes in props.pdfUrl
watch(() => props.pdfUrl, (val) => {
    if (loadTimeout.value) {
        clearTimeout(loadTimeout.value)
        loadTimeout.value = null
    }
    
    if (val) {
        isLoading.value = true
        error.value = ''
        
        loadTimeout.value = setTimeout(() => {
            if (isLoading.value) {
                isLoading.value = false
            }
        }, 100)
    }
}, { immediate: true })

// Handle PDF load success
const handlePdfLoad = () => {
    if (loadTimeout.value) {
        clearTimeout(loadTimeout.value)
        loadTimeout.value = null
    }
    isLoading.value = false
    error.value = ''
}

// Handle PDF error
const handlePdfError = (event: Event) => {
    if (loadTimeout.value) {
        clearTimeout(loadTimeout.value)
        loadTimeout.value = null
    }
    error.value = 'Fehler beim Laden des PDF-Dokuments'
    isLoading.value = false
}

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
    if (!props.modelValue || e.target instanceof HTMLInputElement) return
    
    switch (e.key) {
        case 'Escape':
            e.preventDefault()
            emit('update:modelValue', false)
            break
    }
}

// Watch for modal open/close
watch(() => props.modelValue, (isOpen) => {
    if (isOpen && props.pdfUrl) {
        // Reset state when opening
        error.value = ''
        isLoading.value = true
    }
})

// Lifecycle
onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
    if (loadTimeout.value) {
        clearTimeout(loadTimeout.value)
        loadTimeout.value = null
    }
    // Clean up object URL if needed
    if (props.pdfUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(props.pdfUrl)
    }
})
</script>

<style scoped>
.pdf-modal :deep(.v-overlay__content) {
    display: flex;
    align-items: center;
    justify-content: center;
}

.pdf-card {
    display: flex;
    flex-direction: column;
    max-height: 90vh;
    min-height: 60vh;
    width: 100%;
}

.pdf-content {
    flex: 1;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    background: #f5f5f5;
}

.pdf-loading,
.pdf-error {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem;
}

.pdf-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    padding: 1rem;
}

.pdf-iframe {
    width: 100%;
    height: 70vh;
    border: none;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    background: white;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .pdf-iframe {
        height: 60vh;
    }
}
</style> 