<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header mit Zurück-Button -->
      <div class="mb-6 flex items-center gap-4">
        <n-button quaternary @click="router.push('/clients')">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Zurück zur Übersicht
        </n-button>
        <div class="flex-1"></div>
        <n-button v-if="!isEditing" type="primary" @click="startEdit">
          <Edit class="w-4 h-4 mr-2" />
          Bearbeiten
        </n-button>
        <template v-else>
          <n-button @click="cancelEdit">
            Abbrechen
          </n-button>
          <n-button type="primary" :loading="isSaving" @click="saveChanges">
            Speichern
          </n-button>
        </template>
        <n-button type="error" @click="handleDelete" :disabled="isEditing">
          <Trash2 class="w-4 h-4 mr-2" />
          Löschen
        </n-button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex justify-center py-20">
        <n-spin size="large" />
      </div>

      <!-- Error -->
      <n-alert v-else-if="isError" type="error" title="Fehler">
        Mandant konnte nicht geladen werden.
      </n-alert>

      <!-- Content -->
      <div v-else-if="client" class="space-y-6">
        <!-- Basis-Informationen -->
        <n-card title="Basis-Informationen" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Typ</label>
              <div class="mt-1">
                <n-tag :type="client.type === 'Gewerbe' ? 'success' : 'info'" size="medium">
                  {{ client.type }}
                </n-tag>
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Berater</label>
              <p class="mt-1 text-gray-900">{{ client.advisorName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Mandatsmanager</label>
              <n-input v-if="isEditing" v-model:value="editableClient.mandateManager" placeholder="Mandatsmanager" />
              <p v-else class="mt-1 text-gray-900">{{ client.mandateManager || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Mandatsverantwortlicher</label>
              <n-input v-if="isEditing" v-model:value="editableClient.mandateResponsible" placeholder="Mandatsverantwortlicher" />
              <p v-else class="mt-1 text-gray-900">{{ client.mandateResponsible || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Erstellt am</label>
              <p class="mt-1 text-gray-900">{{ formatDate(client.createdAt) }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Zuletzt aktualisiert</label>
              <p class="mt-1 text-gray-900">{{ formatDate(client.updatedAt) }}</p>
            </div>
          </div>
        </n-card>

        <!-- Personendaten (Natürliche Person) -->
        <n-card v-if="client.type === 'Natürliche Person'" title="Personendaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Anrede</label>
              <n-select v-if="isEditing" v-model:value="editableClient.salutation" :options="salutationOptions" clearable placeholder="Anrede" />
              <p v-else class="mt-1 text-gray-900">{{ client.salutation || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Titel</label>
              <n-input v-if="isEditing" v-model:value="editableClient.title" placeholder="z.B. Dr., Prof." />
              <p v-else class="mt-1 text-gray-900">{{ client.title || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Vorname</label>
              <n-input v-if="isEditing" v-model:value="editableClient.firstName" placeholder="Vorname" />
              <p v-else class="mt-1 text-gray-900 font-semibold">{{ client.firstName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nachname</label>
              <n-input v-if="isEditing" v-model:value="editableClient.lastName" placeholder="Nachname" />
              <p v-else class="mt-1 text-gray-900 font-semibold">{{ client.lastName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Geburtsdatum</label>
              <n-date-picker v-if="isEditing" v-model:value="editableClient.birthDate" type="date" value-format="yyyy-MM-dd" placeholder="Geburtsdatum" />
              <p v-else class="mt-1 text-gray-900">{{ formatDate(client.birthDate) }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Geburtsort</label>
              <n-input v-if="isEditing" v-model:value="editableClient.birthPlace" placeholder="Geburtsort" />
              <p v-else class="mt-1 text-gray-900">{{ client.birthPlace || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Staatsangehörigkeit</label>
              <n-input v-if="isEditing" v-model:value="editableClient.nationality" placeholder="z.B. Deutsch" />
              <p v-else class="mt-1 text-gray-900">{{ client.nationality || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Firmendaten (Unternehmen) -->
        <n-card v-if="client.type === 'Gewerbe'" title="Firmendaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Firma</label>
              <n-input v-if="isEditing" v-model:value="editableClient.companyName" placeholder="Firmenname" />
              <p v-else class="mt-1 text-gray-900 font-semibold text-lg">{{ client.companyName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Rechtsform</label>
              <n-select v-if="isEditing" v-model:value="editableClient.legalForm" :options="legalFormOptions" placeholder="Rechtsform auswählen" />
              <div v-else class="mt-1">
                <n-tag size="medium" v-if="client.legalForm">{{ client.legalForm }}</n-tag>
                <span v-else class="text-gray-500">-</span>
              </div>
            </div>
          </div>
        </n-card>

        <!-- Adresse -->
        <n-card title="Adresse" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Straße</label>
              <n-input v-if="isEditing" v-model:value="editableClient.street" placeholder="Straße" />
              <p v-else class="mt-1 text-gray-900">{{ client.street || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nr.</label>
              <n-input v-if="isEditing" v-model:value="editableClient.number" placeholder="Hausnummer" />
              <p v-else class="mt-1 text-gray-900">{{ client.number || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">PLZ</label>
              <n-input v-if="isEditing" v-model:value="editableClient.zip" placeholder="PLZ" />
              <p v-else class="mt-1 text-gray-900">{{ client.zip || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Ort</label>
              <n-input v-if="isEditing" v-model:value="editableClient.city" placeholder="Ort" />
              <p v-else class="mt-1 text-gray-900">{{ client.city || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Kontakt & Steuerdaten -->
        <n-card title="Kontakt & Steuerdaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">E-Mail</label>
              <n-input v-if="isEditing" v-model:value="editableClient.email" type="email" placeholder="email@example.com" />
              <p v-else class="mt-1 text-gray-900">{{ client.email || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Steuernummer</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxNumber" placeholder="Steuernummer" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxNumber || '-' }}</p>
            </div>
            <div v-if="client.type === 'Natürliche Person'">
              <label class="text-sm font-medium text-gray-600">Steuer-ID</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxId" placeholder="Steuer-ID" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxId || '-' }}</p>
            </div>
            <div v-if="client.type === 'Gewerbe'">
              <label class="text-sm font-medium text-gray-600">UST-ID</label>
              <n-input v-if="isEditing" v-model:value="editableClient.vatId" placeholder="UST-ID" />
              <p v-else class="mt-1 text-gray-900">{{ client.vatId || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Finanzgericht</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxCourt" placeholder="Finanzgericht" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxCourt || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Finanzamt -->
        <n-card v-if="client.taxOffice || isEditing" title="Finanzamt" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">PLZ</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeZip" placeholder="PLZ" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.zip || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Ort</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeCity" placeholder="Ort" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.city || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Straße</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeStreet" placeholder="Straße" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.street || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nr.</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeNumber" placeholder="Hausnummer" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.number || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">E-Mail</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeEmail" type="email" placeholder="email@example.com" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.email || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Fax</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeFax" placeholder="Fax" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.fax || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Anrede Ansprechpartner</label>
              <n-select v-if="isEditing" v-model:value="editableClient.taxOfficeContactSalutation" :options="salutationOptions" clearable placeholder="Anrede" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.contactSalutation || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nachname Ansprechpartner</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeContactLastName" placeholder="Nachname" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.contactLastName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Telefon Ansprechpartner</label>
              <n-input v-if="isEditing" v-model:value="editableClient.taxOfficeContactPhone" placeholder="Telefon" />
              <p v-else class="mt-1 text-gray-900">{{ client.taxOffice?.contactPhone || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Beteiligte (nur für Unternehmen) -->
        <n-card v-if="client.type === 'Gewerbe' && client.participants && client.participants.length > 0" title="Beteiligte" class="shadow-sm">
          <div class="space-y-4">
            <div v-for="participant in client.participants" :key="participant.id" class="border-b pb-4 last:border-0">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label class="text-sm font-medium text-gray-600">Name</label>
                  <p class="mt-1 text-gray-900 font-semibold">{{ participant.firstName }} {{ participant.lastName }}</p>
                </div>
                <div>
                  <label class="text-sm font-medium text-gray-600">Rolle</label>
                  <div class="mt-1">
                    <n-tag type="info" size="medium">{{ participant.role }}</n-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!client.participants || client.participants.length === 0" class="text-gray-500 text-sm py-4">
            Keine Beteiligten vorhanden.
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ClientDetail - Detailansicht für einen einzelnen Mandanten mit allen Feldern.
 */
import { computed, inject, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { NButton, NCard, NTag, NSpin, NAlert, NInput, NSelect, NDatePicker, createDiscreteApi } from 'naive-ui';
import { ArrowLeft, Trash2, Edit } from 'lucide-vue-next';
import { clientsApi } from '@/lib/api';
import type { ClientItem } from '@/lib/types';

const route = useRoute();
const router = useRouter();
const { message, dialog } = createDiscreteApi(['message', 'dialog']);
const queryClient = useQueryClient();

const clientId = computed(() => route.params.id as string);

// Client laden
const { data: client, isLoading, isError } = useQuery({
  queryKey: ['client', clientId.value],
  queryFn: () => clientsApi.getClient(clientId.value),
  enabled: !!clientId.value
});

// Bearbeitungsmodus
const isEditing = ref(false);
const isSaving = ref(false);
const editableClient = ref<Partial<ClientItem> | null>(null);

// Optionen für Selects
const salutationOptions = [
  { label: 'Herr', value: 'Herr' },
  { label: 'Frau', value: 'Frau' },
  { label: 'Divers', value: 'Divers' }
];

const legalFormOptions = [
  { label: 'Gesellschaft mit beschränkter Haftung (GmbH)', value: 'Gesellschaft mit beschränkter Haftung (GmbH)' },
  { label: 'Aktiengesellschaft (AG)', value: 'Aktiengesellschaft (AG)' },
  { label: 'Offene Handelsgesellschaft (OHG)', value: 'Offene Handelsgesellschaft (OHG)' },
  { label: 'Unternehmergesellschaft (UG)', value: 'Unternehmergesellschaft (UG)' },
  { label: 'Kommanditgesellschaft (KG)', value: 'Kommanditgesellschaft (KG)' },
  { label: 'Gesellschaft bürgerlichen Rechts (GbR)', value: 'Gesellschaft bürgerlichen Rechts (GbR)' },
  { label: 'Einzelunternehmen', value: 'Einzelunternehmen' }
];

function startEdit() {
  if (client.value) {
    editableClient.value = { 
      ...client.value,
      // Ensure salutation is always included, even if null/undefined
      salutation: client.value.salutation || null,
      // Ensure birthPlace and nationality are included
      birthPlace: client.value.birthPlace || '',
      nationality: client.value.nationality || '',
      // Map taxOffice fields to flat structure for editing
      taxOfficeZip: client.value.taxOffice?.zip || '',
      taxOfficeCity: client.value.taxOffice?.city || '',
      taxOfficeStreet: client.value.taxOffice?.street || '',
      taxOfficeNumber: client.value.taxOffice?.number || '',
      taxOfficeEmail: client.value.taxOffice?.email || '',
      taxOfficeFax: client.value.taxOffice?.fax || '',
      taxOfficeContactSalutation: client.value.taxOffice?.contactSalutation || '',
      taxOfficeContactLastName: client.value.taxOffice?.contactLastName || '',
      taxOfficeContactPhone: client.value.taxOffice?.contactPhone || '',
    };
    console.log('[ClientDetail] Started editing, editableClient:', editableClient.value);
    isEditing.value = true;
  }
}

function cancelEdit() {
  editableClient.value = null;
  isEditing.value = false;
}

// Update mutation
const updateMutation = useMutation({
  mutationFn: (data: Partial<ClientItem>) => clientsApi.updateClient(clientId.value, data),
  onSuccess: (response) => {
    console.log('[ClientDetail] Update response:', response);
    console.log('[ClientDetail] Salutation in response:', response?.salutation);
    message.success('Mandantendaten erfolgreich aktualisiert');
    queryClient.invalidateQueries({ queryKey: ['client', clientId.value] });
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    isEditing.value = false;
    editableClient.value = null;
  },
  onError: (error) => {
    console.error('[ClientDetail] Update error:', error);
    message.error('Fehler beim Aktualisieren der Mandantendaten');
  }
});

async function saveChanges() {
  if (!editableClient.value || !client.value) return;
  
  isSaving.value = true;
  try {
    // Ensure type is included in the payload
    const payload = {
      ...editableClient.value,
      type: client.value.type, // Always include the client type
      // Explicitly include birthPlace and nationality to ensure they're sent
      birthPlace: editableClient.value.birthPlace || '',
      nationality: editableClient.value.nationality || '',
    };
    console.log('[ClientDetail] Saving changes with payload:', payload);
    console.log('[ClientDetail] birthPlace in payload:', payload.birthPlace);
    console.log('[ClientDetail] nationality in payload:', payload.nationality);
    await updateMutation.mutateAsync(payload);
  } finally {
    isSaving.value = false;
  }
}

// Löschen
const deleteMutation = useMutation({
  mutationFn: (id: string) => clientsApi.deleteClient(id),
  onSuccess: () => {
    message.success('Mandant gelöscht');
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    router.push('/clients');
  },
  onError: () => {
    message.error('Fehler beim Löschen');
  }
});

function handleDelete() {
  if (!client.value) return;
  dialog.warning({
    title: 'Mandant löschen',
    content: `Möchten Sie den Mandanten "${client.value.companyName || (client.value.firstName + ' ' + client.value.lastName)}" wirklich löschen?`,
    positiveText: 'Löschen',
    negativeText: 'Abbrechen',
    onPositiveClick: () => deleteMutation.mutate(client.value!.id)
  });
}

function formatDate(iso?: string): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}
</script>

<style scoped>
</style>
