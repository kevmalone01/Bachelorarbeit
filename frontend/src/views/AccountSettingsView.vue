<template>
    <v-container fluid class="settings-container">
        <div class="settings-wrapper">
            <v-row no-gutters class="settings-main">
                <!-- Left Navigation Sidebar -->
                <v-col cols="12" md="3" class="sidebar-col">
                    <div class="settings-sidebar">
                        <div class="sidebar-content">
                            <div class="nav-section">
                                <v-btn 
                                    @click="activeSection = 'account'" 
                                    :class="['nav-btn', { 'nav-btn--active': activeSection === 'account' }]"
                                    variant="text"
                                    block
                                >
                                    <template v-slot:prepend>
                                        <v-icon class="nav-icon" color="brown">mdi-account-circle-outline</v-icon>
                                    </template>
                                    <span class="nav-text">Profil</span>
                                </v-btn>

                                <v-btn 
                                    @click="activeSection = 'system'" 
                                    :class="['nav-btn', { 'nav-btn--active': activeSection === 'system' }]"
                                    variant="text"
                                    block
                                >
                                    <template v-slot:prepend>
                                        <v-icon class="nav-icon" color="brown">mdi-cog-outline</v-icon>
                                    </template>
                                    <span class="nav-text">Einstellungen</span>
                                </v-btn>

                                <v-divider></v-divider>

                                <v-btn 
                                    class="nav-btn"
                                    href="https://docs.ai-doc.de"
                                    target="_blank"
                                    variant="text"
                                    block
                                >
                                    <template v-slot:prepend>
                                        <v-icon class="nav-icon" color="brown">mdi-book-open-outline</v-icon>
                                    </template>
                                    <span class="nav-text">Docs</span>
                                </v-btn>
                            </div>
                        </div>
                    </div>
                </v-col>

                <!-- Main Content Area -->
                <v-col cols="12" md="9" class="content-col">
                    <div class="content-area">
                        <!-- Loading State -->
                        <div v-if="loading" class="loading-state">
                            <v-progress-circular 
                                indeterminate 
                                color="brown" 
                                size="48"
                                width="3"
                                class="mb-4"
                            />
                            <div class="loading-text">Laden...</div>
                        </div>

                        <!-- Success/Error Messages -->
                        <v-alert 
                            v-if="message" 
                            :type="messageType === 'success' ? 'success' : 'error'" 
                            variant="tonal"
                            closable 
                            @click:close="message = ''" 
                            class="message-alert mb-6"
                        >
                            {{ message }}
                        </v-alert>

                        <!-- Account Section -->
                        <div v-if="!loading && activeSection === 'account'" class="section-content">
                            <!-- <div class="section-header mb-6">
                                <h2 class="section-title">Persönliche Daten</h2>
                                <p class="section-description">Ihre Kontoinformationen und Präferenzen</p>
                            </div> -->

                            <div class="profile-card">
                                <div class="card-content">
                                    <v-row class="profile-fields">
                                        <v-col cols="12" md="6">
                                            <div class="field-group">
                                                <label class="field-label">Benutzername</label>
                                                <v-text-field 
                                                    v-model="userSettings.name" 
                                                    disabled
                                                    variant="outlined" 
                                                    readonly
                                                    class="profile-field"
                                                />
                                            </div>
                                        </v-col>

                                        <v-col cols="12" md="6">
                                            <div class="field-group">
                                                <label class="field-label">E-Mail-Adresse</label>
                                                <v-text-field 
                                                    v-model="userSettings.email" 
                                                    disabled
                                                    variant="outlined" 
                                                    readonly
                                                    class="profile-field"
                                                />
                                            </div>
                                        </v-col>

                                        <v-col cols="12" md="6">
                                            <div class="field-group">
                                                <label class="field-label">Benutzerrolle</label>
                                                <v-select 
                                                    v-model="userSettings.role" 
                                                    :items="[
                                                        { title: 'Benutzer', value: 'user' },
                                                        { title: 'Administrator', value: 'admin' },
                                                        { title: 'Steuerberater', value: 'tax_advisor' }
                                                    ]" 
                                                    disabled 
                                                    variant="outlined" 
                                                    readonly
                                                    class="profile-field"
                                                />
                                            </div>
                                        </v-col>

                                        <v-col cols="12" md="6">
                                            <div class="field-group">
                                                <label class="field-label">Sprache der Benutzeroberfläche</label>
                                                <v-select 
                                                    v-model="userSettings.language"
                                                    :items="[
                                                        { title: 'Deutsch', value: 'de' },
                                                        { title: 'English', value: 'en' },
                                                        { title: 'Français', value: 'fr' }
                                                    ]" 
                                                    disabled 
                                                    variant="outlined" 
                                                    readonly
                                                    class="profile-field"
                                                />
                                            </div>
                                        </v-col>
                                    </v-row>
                                </div>
                            </div>
                        </div>

                        <!-- System Section -->
                        <div v-if="!loading && activeSection === 'system'" class="section-content">
                            <!-- <div class="section-header mb-6">
                                <h2 class="section-title">Systemkonfiguration</h2>
                                <p class="section-description">KI-Engine und Modelleinstellungen</p>
                            </div> -->

                            <!-- Ollama Status Card -->
                            <div class="system-card mb-6">
                                <div class="card-header">
                                    <div class="card-title-group">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <v-icon size="48" color="brown">
                                                <svg fill="currentColor" fill-rule="evenodd" height="1em" style="flex:none;line-height:1" viewBox="0 0 24 24" width="1em" xmlns="http://www.w3.org/2000/svg"><title>Ollama</title><path d="M7.905 1.09c.216.085.411.225.588.41.295.306.544.744.734 1.263.191.522.315 1.1.362 1.68a5.054 5.054 0 012.049-.636l.051-.004c.87-.07 1.73.087 2.48.474.101.053.2.11.297.17.05-.569.172-1.134.36-1.644.19-.52.439-.957.733-1.264a1.67 1.67 0 01.589-.41c.257-.1.53-.118.796-.042.401.114.745.368 1.016.737.248.337.434.769.561 1.287.23.934.27 2.163.115 3.645l.053.04.026.019c.757.576 1.284 1.397 1.563 2.35.435 1.487.216 3.155-.534 4.088l-.018.021.002.003c.417.762.67 1.567.724 2.4l.002.03c.064 1.065-.2 2.137-.814 3.19l-.007.01.01.024c.472 1.157.62 2.322.438 3.486l-.006.039a.651.651 0 01-.747.536.648.648 0 01-.54-.742c.167-1.033.01-2.069-.48-3.123a.643.643 0 01.04-.617l.004-.006c.604-.924.854-1.83.8-2.72-.046-.779-.325-1.544-.8-2.273a.644.644 0 01.18-.886l.009-.006c.243-.159.467-.565.58-1.12a4.229 4.229 0 00-.095-1.974c-.205-.7-.58-1.284-1.105-1.683-.595-.454-1.383-.673-2.38-.61a.653.653 0 01-.632-.371c-.314-.665-.772-1.141-1.343-1.436a3.288 3.288 0 00-1.772-.332c-1.245.099-2.343.801-2.67 1.686a.652.652 0 01-.61.425c-1.067.002-1.893.252-2.497.703-.522.39-.878.935-1.066 1.588a4.07 4.07 0 00-.068 1.886c.112.558.331 1.02.582 1.269l.008.007c.212.207.257.53.109.785-.36.622-.629 1.549-.673 2.44-.05 1.018.186 1.902.719 2.536l.016.019a.643.643 0 01.095.69c-.576 1.236-.753 2.252-.562 3.052a.652.652 0 01-1.269.298c-.243-1.018-.078-2.184.473-3.498l.014-.035-.008-.012a4.339 4.339 0 01-.598-1.309l-.005-.019a5.764 5.764 0 01-.177-1.785c.044-.91.278-1.842.622-2.59l.012-.026-.002-.002c-.293-.418-.51-.953-.63-1.545l-.005-.024a5.352 5.352 0 01.093-2.49c.262-.915.777-1.701 1.536-2.269.06-.045.123-.09.186-.132-.159-1.493-.119-2.73.112-3.67.127-.518.314-.95.562-1.287.27-.368.614-.622 1.015-.737.266-.076.54-.059.797.042zm4.116 9.09c.936 0 1.8.313 2.446.855.63.527 1.005 1.235 1.005 1.94 0 .888-.406 1.58-1.133 2.022-.62.375-1.451.557-2.403.557-1.009 0-1.871-.259-2.493-.734-.617-.47-.963-1.13-.963-1.845 0-.707.398-1.417 1.056-1.946.668-.537 1.55-.849 2.485-.849zm0 .896a3.07 3.07 0 00-1.916.65c-.461.37-.722.835-.722 1.25 0 .428.21.829.61 1.134.455.347 1.124.548 1.943.548.799 0 1.473-.147 1.932-.426.463-.28.7-.686.7-1.257 0-.423-.246-.89-.683-1.256-.484-.405-1.14-.643-1.864-.643zm.662 1.21l.004.004c.12.151.095.37-.056.49l-.292.23v.446a.375.375 0 01-.376.373.375.375 0 01-.376-.373v-.46l-.271-.218a.347.347 0 01-.052-.49.353.353 0 01.494-.051l.215.172.22-.174a.353.353 0 01.49.051zm-5.04-1.919c.478 0 .867.39.867.871a.87.87 0 01-.868.871.87.87 0 01-.867-.87.87.87 0 01.867-.872zm8.706 0c.48 0 .868.39.868.871a.87.87 0 01-.868.871.87.87 0 01-.867-.87.87.87 0 01.867-.872zM7.44 2.3l-.003.002a.659.659 0 00-.285.238l-.005.006c-.138.189-.258.467-.348.832-.17.692-.216 1.631-.124 2.782.43-.128.899-.208 1.404-.237l.01-.001.019-.034c.046-.082.095-.161.148-.239.123-.771.022-1.692-.253-2.444-.134-.364-.297-.65-.453-.813a.628.628 0 00-.107-.09L7.44 2.3zm9.174.04l-.002.001a.628.628 0 00-.107.09c-.156.163-.32.45-.453.814-.29.794-.387 1.776-.23 2.572l.058.097.008.014h.03a5.184 5.184 0 011.466.212c.086-1.124.038-2.043-.128-2.722-.09-.365-.21-.643-.349-.832l-.004-.006a.659.659 0 00-.285-.239h-.004z"></path></svg>
                                            </v-icon>
                                            <h3 class="card-title">Ollama Engine</h3>
                                        </div>
                                        <p class="card-subtitle">Status und Konfiguration der KI-Engine</p>
                                    </div>
                                    <v-btn 
                                        @click="checkOllamaStatus" 
                                        :loading="checkingStatus" 
                                        size="42" 
                                        class="refresh-btn"
                                        prepend-icon="mdi-refresh"
                                    >
                                    </v-btn>
                                </div>

                                <div class="card-content">
                                    <div class="status-section mb-4">
                                        <div class="status-info">
                                            <v-chip 
                                                :color="ollamaStatus.installed ? 'success' : 'error'"
                                                variant="tonal" 
                                                size="large" 
                                                class="status-chip"
                                            >
                                                <v-icon start size="small">
                                                    {{ ollamaStatus.installed ? 'mdi-check-circle' : 'mdi-close-circle' }}
                                                </v-icon>
                                                {{ ollamaStatus.installed ? 'Aktiv' : 'Nicht installiert' }}
                                            </v-chip>

                                            <div v-if="ollamaStatus.version" class="version-info">
                                                <span class="version-label">Version</span>
                                                <span class="version-value">{{ ollamaStatus.version }}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <v-btn 
                                        v-if="!ollamaStatus.installed" 
                                        @click="downloadOllamaInstaller" 
                                        color="brown"
                                        variant="outlined"
                                        prepend-icon="mdi-download" 
                                        size="large"
                                        class="install-btn"
                                    >
                                        Ollama herunterladen
                                    </v-btn>
                                </div>
                            </div>

                            <!-- Model Selection Cards -->
                            <div class="models-section">
                                <h3 class="models-title mb-4">Modellauswahl</h3>
                                
                                <v-row class="models-grid">
                                    <v-col cols="12" lg="12">
                                        <div class="model-card">
                                            <div class="model-header">
                                                <div class="model-icon-wrapper">
                                                    <v-icon class="model-icon" size="24" color="brown">mdi-text-box-search-outline</v-icon>
                                                </div>
                                                <div class="model-info">
                                                    <h4 class="model-title">Textanalyse</h4>
                                                    <p class="model-description">Modell für die Analyse von Textdokumenten</p>
                                                </div>
                                            </div>
                                            
                                            <div class="model-selector">
                                                <v-select 
                                                    v-model="userSettings.preferred_text_model"
                                                    label="Modell auswählen" 
                                                    :items="availableModels.text.map(m => ({
                                                        title: `${m.name} (${formatFileSize(m.size)})`,
                                                        value: m.name
                                                    }))" 
                                                    :disabled="saving" 
                                                    variant="outlined" 
                                                    clearable
                                                    class="model-field"
                                                />
                                            </div>
                                        </div>
                                    </v-col>

                                    <v-col cols="12" lg="12">
                                        <div class="model-card">
                                            <div class="model-header">
                                                <div class="model-icon-wrapper">
                                                    <v-icon class="model-icon" size="24" color="brown">mdi-image-outline</v-icon>
                                                </div>
                                                <div class="model-info">
                                                    <h4 class="model-title">Bildanalyse</h4>
                                                    <p class="model-description">Modell für Bildanalyse und OCR</p>
                                                </div>
                                            </div>
                                            
                                            <div class="model-selector">
                                                <v-select 
                                                    v-model="userSettings.preferred_image_model"
                                                    label="Modell auswählen" 
                                                    :items="availableModels.image.map(m => ({
                                                        title: `${m.name} (${formatFileSize(m.size)})`,
                                                        value: m.name
                                                    }))" 
                                                    :disabled="saving" 
                                                    variant="outlined" 
                                                    clearable
                                                    class="model-field"
                                                />
                                            </div>
                                        </div>
                                    </v-col>
                                </v-row>
                            </div>
                        </div>

                        <!-- Save Button -->
                        <!-- <div v-if="!loading" class="save-section">
                            <v-btn 
                                @click="saveSettings" 
                                :loading="saving" 
                                color="primary" 
                                size="large"
                                prepend-icon="mdi-content-save" 
                                class="save-btn"
                            >
                                {{ saving ? 'Speichern...' : 'Änderungen speichern' }}
                            </v-btn>
                        </div> -->
                    </div>
                </v-col>
            </v-row>
        </div>

        <!-- Installer Modal -->
        <v-dialog v-model="showInstaller" max-width="700px" persistent class="installer-dialog">
            <v-card class="installer-card">
                <v-card-title class="installer-header">
                    <span class="installer-title">Ollama Installation</span>
                    <v-btn 
                        @click="showInstaller = false" 
                        icon="mdi-close" 
                        variant="text" 
                        size="small"
                        class="close-btn"
                    />
                </v-card-title>

                <v-card-text class="installer-content">
                    <p class="installer-description">
                        Wählen Sie ein Leistungsprofil und folgen Sie den Anweisungen zur Installation von Ollama
                    </p>

                    <div v-if="installerInfo" class="profiles-section mb-6">
                        <v-row>
                            <v-col 
                                v-for="(profile, key) in installerInfo.performance_profiles" 
                                :key="key" 
                                cols="12" md="4"
                            >
                                <div 
                                    @click="selectedProfile = key"
                                    :class="[
                                        'profile-card', 
                                        { 'profile-card--selected': selectedProfile === key }
                                    ]"
                                >
                                    <div class="profile-content">
                                        <h4 class="profile-name">{{ profile.name }}</h4>
                                        <p class="profile-description">{{ profile.description }}</p>
                                        <div class="profile-specs">
                                            <div class="spec-item">
                                                <span class="spec-label">RAM:</span>
                                                <span class="spec-value">{{ profile.min_ram }}</span>
                                            </div>
                                            <div class="spec-item">
                                                <span class="spec-label">Speicher:</span>
                                                <span class="spec-value">{{ profile.min_storage }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </v-col>
                        </v-row>
                    </div>

                    <div v-if="installerInfo" class="steps-section">
                        <h4 class="steps-title">Installationsschritte:</h4>
                        <ol class="steps-list">
                            <li v-for="step in installerInfo.installation_steps" :key="step" class="step-item">
                                {{ step }}
                            </li>
                        </ol>
                    </div>
                </v-card-text>

                <v-card-actions v-if="installerInfo" class="installer-actions">
                    <v-btn 
                        @click="showInstaller = false" 
                        variant="outlined"
                        class="cancel-btn"
                    >
                        Abbrechen
                    </v-btn>
                    <v-btn 
                        :href="installerInfo.download_url" 
                        target="_blank" 
                        @click="showInstaller = false"
                        color="primary" 
                        prepend-icon="mdi-download"
                        class="download-btn"
                    >
                        Installer herunterladen
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UserAPI } from '@/services/api'
import type { User, OllamaStatus, AvailableModels, RecommendedModels, InstallerInfo, RecommendedModel } from '@/types/user'


// Reactive data
const activeSection = ref<'account' | 'system' | 'models'>('account')
const loading = ref(true)
const saving = ref(false)
const checkingStatus = ref(false)
const showInstaller = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const warnings = ref<string[]>([])
const selectedPerformance = ref<keyof RecommendedModels>('medium')
const selectedProfile = ref<keyof InstallerInfo['performance_profiles']>('medium')

// User settings
const userSettings = ref<User>({
    id: 1, // TODO: Get from auth
    name: '',
    email: '',
    role: 'user',
    language: 'de',
    preferred_text_model: '',
    preferred_image_model: ''
})

// Ollama data
const ollamaStatus = ref<OllamaStatus>({
    installed: false,
    version: null,
    error: null
})

const availableModels = ref<AvailableModels>({
    text: [],
    image: []
})

const recommendedModels = ref<RecommendedModels | null>(null)
const installerInfo = ref<InstallerInfo | null>(null)

// Methods
const getPerformanceLevelName = (level: string) => {
    const names: Record<string, string> = {
        low: 'Basis',
        medium: 'Standard',
        high: 'Hohe Leistung'
    }
    return names[level] || level
}

const loadUserSettings = async () => {
    try {
        const response = await UserAPI.getUserSettings(userSettings.value.id)
        Object.assign(userSettings.value, response.data)
    } catch (error) {
        console.error('Error loading user settings:', error)
    }
}

const loadAvailableModels = async () => {
    try {
        const response = await UserAPI.getAvailableModels()
        const data = response.data

        ollamaStatus.value = data.ollama_status
        availableModels.value = data.available_models
        recommendedModels.value = data.recommended_models
    } catch (error) {
        console.error('Error loading available models:', error)
        ollamaStatus.value = { installed: false, version: null, error: 'Ошибка проверки статуса Ollama' }
    }
}

const loadInstallerInfo = async () => {
    try {
        const response = await UserAPI.getOllamaInstallerInfo()
        installerInfo.value = response.data
    } catch (error) {
        console.error('Error loading installer info:', error)
    }
}

const saveSettings = async () => {
    saving.value = true
    warnings.value = []

    try {
        const response = await UserAPI.updateUserSettings(userSettings.value.id, userSettings.value)

        if (response.data.warnings) {
            warnings.value = response.data.warnings
        }

        showMessage('Settings saved successfully', 'success')
    } catch (error) {
        console.error('Error saving settings:', error)
        showMessage('Error saving settings', 'error')
    } finally {
        saving.value = false
    }
}

const checkOllamaStatus = async () => {
    checkingStatus.value = true
    try {
        await loadAvailableModels()
        showMessage('Ollama status updated', 'success')
    } catch (error) {
        showMessage('Error updating Ollama status', 'error')
    } finally {
        checkingStatus.value = false
    }
}

const selectRecommendedModel = (model: RecommendedModel) => {
    if (model.type === 'text') {
        userSettings.value.preferred_text_model = model.name
    } else if (model.type === 'image') {
        userSettings.value.preferred_image_model = model.name
    }
    showMessage(`Model ${model.name} selected`, 'success')
}

const showMessage = (text: string, type: 'success' | 'error') => {
    message.value = text
    messageType.value = type
    setTimeout(() => {
        message.value = ''
    }, 5000)
}

const formatFileSize = (bytes: number) => {
    if (!bytes) return 'Unknown'

    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const downloadOllamaInstaller = () => {
    try {
        const link = document.createElement('a')
        link.href = '/ollamaInstaller.exe'
        link.download = 'ollamaInstaller.exe'
        link.style.display = 'none'
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        showMessage('Ollama installer download started', 'success')
    } catch (error) {
        console.error('Error downloading installer:', error)
        showMessage('Error downloading installer', 'error')
    }
}

// Lifecycle
onMounted(async () => {
    loading.value = true

    try {
        await Promise.all([
            loadUserSettings(),
            loadAvailableModels(),
            loadInstallerInfo()
        ])
    } catch (error) {
        console.error('Error initializing account settings:', error)
    } finally {
        loading.value = false
    }
})
</script>

<style scoped>
/* Color Variables - Professional Law Firm Palette */

/* Main Container */
.settings-container {
    min-height: 100vh;
    padding: 2rem 1rem;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.settings-wrapper {
    max-width: 1100px;
    margin: 0 auto;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
    border-radius: 24px;
    background: #fff;
}

/* Main Layout */
.settings-main {
    border-radius: 16px;
    overflow: hidden;
}

/* Sidebar */

.settings-sidebar {
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
    height: 100%;
    min-height: 700px;
    position: relative;
}

.sidebar-content {
    padding: 2rem 1.5rem;
    height: 100%;
}

.sidebar-title {
    color: var(--neutral-white);
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 2rem;
    text-align: center;
    letter-spacing: 0.05em;
}

.nav-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.nav-btn {
    justify-content: flex-start !important;
    padding: 1rem 1.25rem !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    background: transparent !important;
    min-height: 56px !important;
}

.nav-btn:hover {
    background: #94754a22 !important;
    color: var(--neutral-white) !important;
    transform: translateX(4px);
}

.nav-btn--active {
    background: #94754a22 !important;
    font-weight: 600 !important;
}

.nav-btn--active:hover {
    transform: translateX(2px);
}

.nav-icon {
    margin-right: 0.25rem !important;
    font-size: 1.35rem !important;
}

.nav-text {
    font-size: 1rem;
    letter-spacing: 0.025em;
}

/* Content Area */
.content-col {
}

.content-area {
    /* display: flex; */
    /* flex-direction: column; */
    /* justify-content: center; */
    padding: 3rem 2.5rem;
    height: 100%;
    min-height: 700px;
}

/* Loading State */
.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 400px;
}

.loading-text {
    font-size: 1.125rem;
    font-weight: 500;
}

/* Messages */
.message-alert {
    border-radius: 12px !important;
    border: none !important;
    font-weight: 500 !important;
}

/* Section Headers */
.section-header {
    padding-bottom: 1.5rem;
}

.section-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: -0.025em;
}

.section-description {
    font-size: 1rem;
    line-height: 1.6;
}

/* Profile Card */
.profile-card {

    border-radius: 16px;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: box-shadow 0.3s ease;
}

.profile-card:hover {
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.2);
}

.card-content {
    padding: 2rem;
}

.field-group {
    margin-bottom: 0.5rem;
}

.field-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    letter-spacing: 0.025em;
    text-transform: uppercase;
}

/* System Cards */
.system-card {
    border-radius: 16px;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: box-shadow 0.3s ease;
}

.system-card:hover {
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 2rem 2rem 1rem 2rem;
}

.card-title-group {
    flex: 1;
}

.card-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    letter-spacing: -0.025em;
}

.card-subtitle {
    font-size: 0.875rem;
    line-height: 1.5;
}

.refresh-btn {
    /* width: 36px !important; */
    /* height: 36px !important; */
    /* border: 2px solid #94754a75 !important; */
    border-radius: 8px !important;
}

/* Status Section */
.status-section {
    border-radius: 20px;
    background: #f8f9fa;
    padding: 2rem;
}

.status-info {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
}

.status-chip {
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.875rem !important;
}

.version-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.version-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.version-value {
    font-size: 1rem;
    font-weight: 600;
}

.error-alert {
    border-radius: 12px !important;
    border: none !important;
}

.install-btn {
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    text-transform: none !important;
}

.install-btn:hover {
    transform: translateY(-2px);
}

/* Models Section */
.models-section {
    padding: 2rem 2rem 2rem 2rem;
    box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
    border-radius: 16px;
}

.models-title {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.025em;
}

.model-card {
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    height: 100%;
}

.model-card:hover {
    transform: translateY(-2px);
}

.model-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.model-icon-wrapper {
    padding: 0.75rem;
    border-radius: 10px;
    flex-shrink: 0;
}

.model-icon {
}

.model-info {
    flex: 1;
}

.model-title {
    font-size: 1.125rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    letter-spacing: -0.025em;
}

.model-description {
    font-size: 0.875rem;
    line-height: 1.5;
}

/* Save Section */
.save-section {
    text-align: center;
    margin-top: 3rem;
    padding-top: 2rem;
}

.save-btn {
    background: #94754a99 !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 1rem 3rem !important;
    font-size: 1rem !important;
    text-transform: none !important;
    letter-spacing: 0.025em !important;
}

.save-btn:hover {
    transform: translateY(-2px);
}

/* Installer Dialog */
.installer-dialog {
    z-index: 2000;
}

.installer-card {
    border-radius: 16px !important;
}

.installer-header {
    padding: 1.5rem 2rem !important;
    border-radius: 16px 16px 0 0 !important;
}

.installer-title {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.025em;
}

.close-btn {
}

.installer-content {
    padding: 2rem !important;
}

.installer-description {
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 2rem;
}

.profiles-section {
    margin-bottom: 2rem;
}

.profile-card {
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
}

.profile-card:hover {
    transform: translateY(-2px);
}

.profile-card--selected {
}

.profile-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.profile-name {
    font-size: 1.125rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.profile-description {
    font-size: 0.875rem;
    line-height: 1.5;
    margin-bottom: 1rem;
    flex: 1;
}

.profile-specs {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.spec-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.spec-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.spec-value {
    font-size: 0.875rem;
    font-weight: 600;
}

.steps-section {
    margin-top: 1.5rem;
}

.steps-title {
    font-size: 1.125rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.steps-list {
    padding-left: 1.5rem;
}

.step-item {
    font-size: 0.875rem;
    line-height: 1.6;
    margin-bottom: 0.75rem;
}

.installer-actions {
    padding: 1.5rem 2rem !important;
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
}

.cancel-btn {
    border-radius: 8px !important;
    font-weight: 500 !important;
    text-transform: none !important;
}

.download-btn {
    font-weight: 600 !important;
    border-radius: 8px !important;
    text-transform: none !important;
}

.download-btn:hover {
    transform: translateY(-1px);
}

/* Form Field Overrides */
:deep(.profile-field .v-field) {
    border-radius: 8px !important;
}

:deep(.profile-field .v-field--focused) {
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1) !important;
}

:deep(.model-field .v-field) {
    border-radius: 8px !important;
}

:deep(.model-field .v-field--focused) {
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1) !important;
}

/* Responsive Design */
@media (max-width: 960px) {
    .settings-container {
        padding: 1rem 0.5rem;
    }

    .page-title {
        font-size: 2rem;
    }

    .settings-main {
        border-radius: 12px;
        flex-direction: column;
    }

    .sidebar-col {
    }

    .settings-sidebar {
        min-height: auto;
        border-radius: 12px 12px 0 0;
    }

    .sidebar-content {
        padding: 1.5rem;
    }

    .nav-section {
        flex-direction: row;
        overflow-x: auto;
        gap: 0.5rem;
    }

    .nav-btn {
        flex-shrink: 0;
        min-width: 120px;
    }

    .content-area {
        padding: 2rem 1.5rem;
        border-radius: 0 0 12px 12px;
    }

    .card-header {
        flex-direction: column;
        gap: 1rem;
        align-items: flex-start;
    }

    .models-grid {
        gap: 1rem;
    }
}

@media (max-width: 600px) {
    .settings-container {
        padding: 0.5rem;
    }

    .page-title {
        font-size: 1.75rem;
    }

    .content-area {
        padding: 1.5rem 1rem;
    }

    .card-content,
    .status-section,
    .models-section {
        padding: 1.5rem;
    }

    .profile-fields {
        margin: 0;
    }

    .status-info {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
    }

    .nav-section {
        flex-direction: column;
    }

    .nav-btn {
        min-width: auto;
    }
}

/* Smooth Transitions */
* {
    transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

/* Focus States for Accessibility */
:deep(.v-btn:focus-visible) {
    outline-offset: 2px;
}

:deep(.v-field--focused) {
    outline-offset: 2px;
}

/* Print Styles */
@media print {
    .settings-container {
        background: white !important;
        box-shadow: none !important;
    }
    
    .save-section,
    .installer-dialog {
        display: none !important;
    }
}
</style>
