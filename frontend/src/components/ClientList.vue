<template>
    <div class="client-list-container">
        <div class="controls">
            <div class="search-container">
                <v-icon class="search-icon" color="brown">mdi-magnify</v-icon>
                <input type="text" v-model="searchQuery" placeholder="Mandanten suchen..." class="search-input" />
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

        <div v-else-if="!filteredClients.length" class="no-clients">
            <v-icon size="x-large" color="#c2a47b">mdi-account-multiple-outline</v-icon>
            <p>Keine Mandanten gefunden.</p>
        </div>

        <div v-else class="client-list">
            <div v-for="client in filteredClients" :key="client.id" class="client-card">
                <div class="card-content">
                    <div class="card-header">
                        <div class="header-left">
                            <div class="client-avatar" :class="client.client_type === 'natural' ? 'person-avatar' : 'company-avatar'">
                                <v-icon :color="client.client_type === 'natural' ? '#4caf50' : '#2196f3'" size="large">
                                    {{ client.client_type === 'natural' ? 'mdi-account-tie' : 'mdi-domain' }}
                                </v-icon>
                            </div>
                            <div class="client-title">
                                <h3>{{ getClientName(client) }}</h3>
                                <span class="client-type" :class="client.client_type">
                                    {{ client.client_type === 'natural' ? 'Natürliche Person' : 'Unternehmen' }}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <div class="client-info">
                            <div v-if="client.client_type === 'natural'">
                                <div class="info-row">
                                    <v-icon size="small" color="#555">mdi-account-outline</v-icon>
                                    <p><span>Name:</span> {{ client.title || '' }} {{ client.first_name || '' }} {{ client.last_name || '' }}</p>
                                </div>
                                <div v-if="client.birth_date" class="info-row">
                                    <v-icon size="small" color="#555">mdi-calendar</v-icon>
                                    <p><span>Geburtsdatum:</span> {{ formatDate(client.birth_date) }}</p>
                                </div>
                            </div>
                            <div v-else>
                                <div class="info-row">
                                    <v-icon size="small" color="#555">mdi-domain</v-icon>
                                    <p><span>Firmenname:</span> {{ client.company_name }}</p>
                                </div>
                                <div v-if="client.legal_form" class="info-row">
                                    <v-icon size="small" color="#555">mdi-file-document-outline</v-icon>
                                    <p><span>Rechtsform:</span> {{ client.legal_form }}</p>
                                </div>
                            </div>
                            <div v-if="client.email" class="info-row">
                                <v-icon size="small" color="#555">mdi-email-outline</v-icon>
                                <p><span>Email:</span> {{ client.email }}</p>
                            </div>
                            <div v-if="client.tax_number" class="info-row">
                                <v-icon size="small" color="#555">mdi-file-document-outline</v-icon>
                                <p><span>Steuernummer:</span> {{ client.tax_number }}</p>
                            </div>
                            <div v-if="client.address_city" class="info-row">
                                <v-icon size="small" color="#555">mdi-map-marker-outline</v-icon>
                                <p>
                                    <span>Adresse:</span>
                                    {{ client.address_street || '' }} {{ client.address_number || '' }},
                                    {{ client.address_zip || '' }} {{ client.address_city || '' }}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div class="card-actions">
                        <v-btn @click="viewClient(client.id)" class="btn-view" variant="outlined" size="small">
                            <v-icon size="small" class="action-icon">mdi-eye</v-icon>
                            Ansehen
                        </v-btn>
                        <v-btn @click="confirmDelete(client)" class="btn-delete" variant="tonal" color="error" size="small">
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
                    Mandant löschen
                </v-card-title>
                <v-card-text class="dialog-content">
                    Sind Sie sicher, dass Sie <strong>{{ clientToDelete ? getClientName(clientToDelete) : '' }}</strong> löschen möchten? 
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
                        @click="deleteClient" 
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

        <!-- Client Details/Edit Dialog -->
        <v-dialog v-model="showClientDialog" max-width="600">
            <v-card v-if="editableClient">
                <v-card-title class="dialog-title">
                    <v-icon class="mr-2">{{ editableClient.client_type === 'natural' ? 'mdi-account-tie' : 'mdi-domain' }}</v-icon>
                    {{ getClientName(editableClient) }}
                </v-card-title>
                <v-card-text class="dialog-content">
                    <Mask
                        :placeholders="getClientPlaceholders(editableClient)"
                        :values="editableClient"
                        :readonly="false"
                        @update:values="onMaskUpdate"
                        :title="'Mandantendetails'"
                    />
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="cancelEdit">Zurücksetzen</v-btn>
                    <v-btn color="success" variant="tonal" :loading="isSaving" @click="saveClientChanges(editableClient)">Speichern</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import store from '@/store/store';
import Mask from './Mask.vue';

const router = useRouter();
const searchQuery = ref('');
const isLoading = computed(() => store.getters['client/isLoading']);
const error = computed(() => store.getters['client/getError']);
const clients = computed(() => store.getters['client/getClients']);

// Delete confirmation
const deleteDialog = ref(false);
const clientToDelete = ref<any>(null);
const isDeleting = ref(false);

// Snackbar notification
const snackbar = ref({
    show: false,
    color: 'success',
    text: ''
});

// Modal state for viewing/editing client
type EditableClient = Record<string, any> | null;
const showClientDialog = ref(false);
const editableClient = ref<EditableClient>(null);
const isSaving = ref(false);

// Mapping from client object keys to user-friendly German labels
const fieldLabelMap: Record<string, string> = {
    // Person
    first_name: 'Vorname',
    last_name: 'Nachname',
    title: 'Titel',
    birth_date: 'Geburtsdatum',
    email: 'E-Mail',
    tax_number: 'Steuernummer',
    tax_id: 'Steuer-ID',
    address_street: 'Straße',
    address_number: 'Hausnummer',
    address_zip: 'PLZ',
    address_city: 'Ort',
    salutation: 'Anrede',
    mandate_manager: 'Mandatsmanager',
    mandate_responsible: 'Mandatsverantwortlicher',
    tax_court: 'Finanzgericht',
    // Company
    company_name: 'Firmenname',
    legal_form: 'Rechtsform',
    vat_id: 'USt-ID',
    // Tax office
    tax_office: 'Finanzamt',
    tax_office_city: 'Ort (Finanzamt)',
    tax_office_street: 'Straße (Finanzamt)',
    tax_office_number: 'Hausnummer (Finanzamt)',
    tax_office_zip: 'PLZ (Finanzamt)',
    tax_office_email: 'E-Mail (Finanzamt)',
    tax_office_fax: 'Fax (Finanzamt)',
    // Contact
    contact_salutation: 'Anrede Ansprechpartner',
    contact_last_name: 'Nachname Ansprechpartner',
    contact_phone: 'Telefon Ansprechpartner',
    contact_email: 'E-Mail Ansprechpartner',
    contact_fax: 'Fax Ansprechpartner',
    // Other
    created_at: 'Erstellt am',
    updated_at: 'Aktualisiert am',
};

function prettifyLabel(key: string): string {
    // Fallback: Replace underscores with spaces, capitalize first letter
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Filter clients by search query
const filteredClients = computed(() => {
    if (!searchQuery.value) return clients.value;

    const query = searchQuery.value.toLowerCase();
    return clients.value.filter((client: any) => {
        if (client.client_type === 'natural') {
            return (
                (client.first_name && client.first_name.toLowerCase().includes(query)) ||
                (client.last_name && client.last_name.toLowerCase().includes(query)) ||
                (client.email && client.email.toLowerCase().includes(query)) ||
                (client.tax_number && client.tax_number.toLowerCase().includes(query))
            );
        } else {
            return (
                (client.company_name && client.company_name.toLowerCase().includes(query)) ||
                (client.email && client.email.toLowerCase().includes(query)) ||
                (client.tax_number && client.tax_number.toLowerCase().includes(query)) ||
                (client.vat_id && client.vat_id.toLowerCase().includes(query))
            );
        }
    });
});

// Get client name for display
const getClientName = (client: any) => {
    if (client.client_type === 'natural') {
        return `${client.title || ''} ${client.first_name || ''} ${client.last_name || ''}`.trim() || 'Nicht angegeben';
    } else {
        return client.company_name || 'Nicht angegeben';
    }
};

// Format date
const formatDate = (dateString: string) => {
    try {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(date);
    } catch (e) {
        return dateString;
    }
};

const openClientDialog = (client: any) => {
    editableClient.value = JSON.parse(JSON.stringify(client));
    showClientDialog.value = true;
};

const closeClientDialog = () => {
    showClientDialog.value = false;
    editableClient.value = null;
};

const getClientPlaceholders = (client: any) => {
    if (!client) return [];
    // Define the allowed placeholders and their German labels for each client type
    const personPlaceholders = [
        { name: 'salutation', label: 'Anrede' },
        { name: 'mandate_manager', label: 'Mandatsmanager' },
        { name: 'mandate_responsible', label: 'Mandatsverantwortlicher' },
        { name: 'title', label: 'Titel' },
        { name: 'first_name', label: 'Vorname' },
        { name: 'last_name', label: 'Nachname' },
        { name: 'birth_date', label: 'Geburtsdatum', type: 'date' },
        { name: 'address_street', label: 'Straße' },
        { name: 'address_number', label: 'Nr.' },
        { name: 'address_zip', label: 'PLZ' },
        { name: 'address_city', label: 'Ort' },
        { name: 'email', label: 'E-Mail' },
        { name: 'tax_number', label: 'Steuernummer' },
        { name: 'tax_id', label: 'Steuer-ID' },
        { name: 'tax_office', label: 'Finanzamt' },
        { name: 'tax_office_city', label: 'Ort (Finanzamt)' },
        { name: 'tax_office_street', label: 'Straße (Finanzamt)' },
        { name: 'tax_office_number', label: 'Nr. (Finanzamt)' },
        { name: 'tax_office_email', label: 'E-Mail (Finanzamt)' },
        { name: 'tax_office_fax', label: 'Fax (Finanzamt)' },
        { name: 'contact_salutation', label: 'Anrede Ansprechpartner' },
        { name: 'contact_last_name', label: 'Nachname Ansprechpartner' },
        { name: 'contact_phone', label: 'Telefon Ansprechpartner' },
        { name: 'tax_court', label: 'Finanzgericht' },
    ];
    const companyPlaceholders = [
        { name: 'company_name', label: 'Firmenname' },
        { name: 'mandate_manager', label: 'Mandatsmanager' },
        { name: 'mandate_responsible', label: 'Mandatsverantwortlicher' },
        { name: 'revenue', label: 'Umsatz', type: 'number' },
        { name: 'employee_count', label: 'Mitarbeiteranzahl', type: 'number' },
        { name: 'legal_form', label: 'Rechtsform' },
        { name: 'address_zip', label: 'PLZ' },
        { name: 'address_city', label: 'Ort' },
        { name: 'address_street', label: 'Straße' },
        { name: 'address_number', label: 'Nr.' },
        { name: 'email', label: 'E-Mail' },
        { name: 'tax_number', label: 'Steuernummer' },
        { name: 'vat_id', label: 'Ust-id' },
        { name: 'tax_office', label: 'Finanzamt' },
        { name: 'tax_court', label: 'Finanzgericht' },
        { name: 'stakeholders', label: 'Beteiligte' },
    ];
    const isPerson = client.client_type === 'natural';
    const allowed = isPerson ? personPlaceholders : companyPlaceholders;
    return allowed.map(ph => {
        let type = ph.type || 'text';
        return {
            name: ph.name,
            type,
            label: ph.label,
            required: false
        };
    });
};

const saveClientChanges = async (values?: any) => {
    if (!editableClient.value) return;
    try {
        isSaving.value = true;
        // If values are passed, use them, otherwise use the editableClient
        const data = values || editableClient.value;
        await store.dispatch('client/updateClient', { clientId: editableClient.value.id, clientData: data });
        snackbar.value = {
            show: true,
            color: 'success',
            text: 'Mandantendaten wurden erfolgreich gespeichert.'
        };
        closeClientDialog();
    } catch (error) {
        snackbar.value = {
            show: true,
            color: 'error',
            text: 'Fehler beim Speichern der Mandantendaten.'
        };
    } finally {
        isSaving.value = false;
    }
};

const viewClient = (clientId: number) => {
    const client = clients.value.find((c: any) => c.id === clientId);
    if (client) {
        openClientDialog(client);
    }
};

// Open delete confirmation dialog
const confirmDelete = (client: any) => {
    clientToDelete.value = client;
    deleteDialog.value = true;
};

// Delete client
const deleteClient = async () => {
    if (!clientToDelete.value) return;
    
    try {
        isDeleting.value = true;
        await store.dispatch('client/deleteClient', clientToDelete.value.id);
        
        // Show success notification
        snackbar.value = {
            show: true,
            color: 'success',
            text: `Mandant "${getClientName(clientToDelete.value)}" wurde erfolgreich gelöscht.`
        };
        
        // Close dialog
        deleteDialog.value = false;
        clientToDelete.value = null;
    } catch (error) {
        console.error(`Error deleting client: ${clientToDelete.value.id}`, error);
        snackbar.value = {
            show: true,
            color: 'error',
            text: 'Fehler beim Löschen des Mandanten.'
        };
    } finally {
        isDeleting.value = false;
    }
};

// Get client list when component is mounted
onMounted(async () => {
    await store.dispatch('client/fetchClients');
});

// Expose functions for template
// @ts-ignore
defineExpose({
    getClientPlaceholders,
    saveClientChanges
});

// Helper to map client object to prettified labels and values for Mask
function getClientMaskValues(client: any) {
    const result: Record<string, any> = {};
    for (const key in client) {
        if (Object.prototype.hasOwnProperty.call(client, key)) {
            // Use fieldLabelMap if available, else prettify
            const label = fieldLabelMap[key] || prettifyLabel(key);
            let value = client[key];
            // Format date fields
            if (key.includes('date') && value) {
                value = formatDate(value);
            }
            result[label] = value;
        }
    }
    return result;
}

function onMaskUpdate(values: any) {
    if (editableClient.value) {
        Object.assign(editableClient.value, values);
    }
}

function cancelEdit() {
    // Reset editableClient to original values and exit edit mode
    if (editableClient.value && clients.value) {
        const original = clients.value.find((c: any) => c.id === editableClient.value?.id);
        if (original) {
            editableClient.value = JSON.parse(JSON.stringify(original));
        }
    }
}
</script>

<style scoped>
.client-list-container {
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
.no-clients {
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

.client-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1.5rem;
}

.client-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    display: flex;
    border-color: transparent;
}

.client-card:hover {
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

.client-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.person-avatar {
    background-color: rgba(76, 175, 80, 0.1);
}

.company-avatar {
    background-color: rgba(33, 150, 243, 0.1);
}

.client-title {
    display: flex;
    flex-direction: column;
}

.client-title h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #333;
}

.client-type {
    width: 115px;
    text-align: center;
    font-size: 0.75rem;
    border-radius: 4px;
    color: white;
    padding: 0.2rem 0.5rem;
    margin-top: 4px;
    display: inline-block;
    font-weight: 500;
}

.client-type.natural {
    background: linear-gradient(135deg, #4caf4fac 0%, #4caf4fbf 100%) !important;
    color: white !important;
}

.client-type.company {
    background: linear-gradient(135deg, #2195f3a3 0%, #2195f3bf 100%) !important;
    color: white !important;
}

.card-body {
    padding: 0 1.5rem 1rem 1.5rem;
    flex: 1;
}

.client-info {
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

.btn-edit {
    background-color: #c2a47b;
    color: white;
}

.btn-delete {
    background-color: rgba(244, 67, 54, 0.08);
}

.btn-view:hover {
    border-color: #bbb;
    background-color: #f5f5f5;
}

.btn-edit:hover {
    background-color: #b39069;
}

.btn-delete:hover {
    background-color: rgba(244, 67, 54, 0.12);
}

a {
    color: #c2a47b;
    text-decoration: none;
    cursor: pointer;
}

a:hover {
    text-decoration: underline;
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

.v-card-actions {
    padding: 0 1.5rem 1rem 1.5rem !important;
}

/* Responsive styles */
@media (max-width: 600px) {
    .search-container {
        width: 100%;
    }
    
    .client-list {
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