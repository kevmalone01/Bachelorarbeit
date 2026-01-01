<template>
  <div class="p-4 space-y-4">
    <div>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-slate-900">Erkannte Platzhalter</h3>
        <n-button size="small" secondary @click="handleRescan">
          <template #icon>
            <Highlighter class="w-4 h-4" />
          </template>
          Erneut scannen
        </n-button>
      </div>
      
      <div v-if="placeholders.length === 0" class="text-center py-8 text-slate-500">
        <p>Keine Platzhalter gefunden.</p>
        <p class="text-sm mt-2">Klicken Sie auf "Erneut scannen" um Platzhalter im Dokument zu finden.</p>
      </div>
      
      <div v-else class="space-y-3">
        <div
          v-for="(placeholder, index) in placeholders"
          :key="placeholder.key"
          class="p-4 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
        >
          <div class="flex items-start justify-between gap-3 mb-3">
            <div class="flex items-center gap-2 flex-1">
              <span class="font-semibold text-slate-900">{{ placeholder.key }}</span>
              <n-tag size="small" :type="getTypeColor(placeholder.type)">
                {{ placeholder.type }}
              </n-tag>
            </div>
            
            <n-button
              quaternary
              size="small"
              @click="showPlaceholderDetails(placeholder)"
              title="Details anzeigen"
            >
              <template #icon>
                <Database class="w-4 h-4" />
              </template>
            </n-button>
          </div>
          
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1.5">Anzeigename</label>
              <n-input
                :value="placeholder.label"
                size="small"
                placeholder="Anzeigename eingeben"
                @update:value="(v) => handleUpdatePlaceholder(placeholder.key, { label: v })"
                @blur="handleUpdatePlaceholder(placeholder.key, { label: placeholder.label })"
              />
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1.5">Typ</label>
                <n-select
                  :value="placeholder.type"
                  :options="typeOptions"
                  size="small"
                  placeholder="Typ auswählen"
                  @update:value="(v) => handleUpdatePlaceholder(placeholder.key, { type: v })"
                />
              </div>
              
              <div>
                <label class="block text-xs font-medium text-slate-600 mb-1.5">DB-Feld</label>
                <n-select
                  :value="placeholder.mappedFieldId"
                  :options="dbFieldOptions"
                  filterable
                  size="small"
                  placeholder="DB-Feld zuordnen"
                  @update:value="(v) => {
                    console.log('[SettingsPanel] DB-Feld selected:', v, 'for placeholder:', placeholder.key);
                    handleUpdatePlaceholder(placeholder.key, { mappedFieldId: v });
                  }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="pt-6 border-t border-slate-200">
      <h3 class="text-lg font-semibold mb-3 text-slate-900">Verknüpfte Mandanten</h3>
      
      <div class="space-y-3">
        
        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1.5">Einzelne Mandanten</label>
          <n-select
            v-model:value="linkedClients"
            multiple
            filterable
            :options="clientOptions"
            placeholder="Mandanten auswählen"
            :loading="clientsLoading"
            @update:value="handleLinkedClientsUpdate"
          />
          <p class="text-xs text-slate-500 mt-1">Die Daten des ersten ausgewählten Mandanten werden automatisch übernommen</p>
        </div>
      </div>
    </div>
    
    <div class="pt-6">
      <n-button type="primary" block size="medium" @click="$emit('save')">
        Änderungen speichern
      </n-button>
    </div>
    
    <!-- Placeholder Details Modal -->
    <n-modal v-model:show="showDetailsModal" preset="card" title="Platzhalter-Details" style="width: 600px">
      <n-form v-if="selectedPlaceholder" :model="selectedPlaceholder" label-placement="top">
        <n-form-item label="Schlüssel">
          <n-input v-model:value="selectedPlaceholder.key" disabled />
        </n-form-item>
        <n-form-item label="Typ">
          <n-select v-model:value="selectedPlaceholder.type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="Standardwert">
          <n-input v-model:value="selectedPlaceholder.defaultValue" />
        </n-form-item>
        <n-form-item label="Pflichtfeld">
          <n-switch v-model:value="selectedPlaceholder.required" />
        </n-form-item>
        <n-form-item label="Beschreibung">
          <n-input
            v-model:value="selectedPlaceholder.description"
            type="textarea"
            :rows="3"
            placeholder="Optionale Beschreibung"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showDetailsModal = false">Abbrechen</n-button>
          <n-button type="primary" @click="savePlaceholderDetails">Speichern</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { NButton, NSelect, NInput, NTag, NModal, NForm, NFormItem, NSwitch } from 'naive-ui';
import { Highlighter, Database } from 'lucide-vue-next';
import { useQuery } from '@tanstack/vue-query';
import { clientsApi } from '@/lib/api';
import type { Placeholder, PlaceholderType, DbField, ClientItem } from '@/lib/types';

const props = defineProps<{
  placeholders: Placeholder[];
  dbFields: DbField[];
  linkedClients?: string[];
  fillValues?: Record<string, any>;
  currentClient?: ClientItem | null;
}>();

const emit = defineEmits<{
  (e: 'update:placeholders', v: Placeholder[]): void;
  (e: 'update:linkedClients', v: string[]): void;
  (e: 'update:fillValue', key: string, value: any): void;
  (e: 'rescan'): void;
  (e: 'save'): void;
}>();

const showDetailsModal = ref(false);
const selectedPlaceholder = ref<Placeholder | null>(null);

const typeOptions = [
  { label: 'Text', value: 'text' },
  { label: 'Zahl', value: 'number' },
  { label: 'Datum', value: 'date' },
  { label: 'Auswahl', value: 'dropdown' },
  { label: 'Mehrzeilig', value: 'multiline' },
];

const dbFieldOptions = computed(() => {
  return props.dbFields.map(field => ({
    label: field.label || field.key || `${field.entity}: ${field.id}`, // Zeige den vollständigen Label-Namen
    value: field.id,
  }));
});

const linkedClients = ref(props.linkedClients || []);

// Clients laden
const { data: clientsData, isLoading: clientsLoading } = useQuery({
  queryKey: ['clients-for-linking'],
  queryFn: () => clientsApi.getClients({ page: 1, pageSize: 1000 }),
  refetchOnWindowFocus: false,
});

const clients = computed(() => clientsData.value?.items || []);

const clientOptions = computed(() => {
  return clients.value.map((c: ClientItem) => ({
    label: c.type === 'Natürliche Person'
      ? `${c.salutation || ''} ${c.firstName || ''} ${c.lastName || ''}`.trim() || 'Unbekannt'
      : c.companyName || 'Unbekannt',
    value: c.id,
  }));
});

function handleLinkedClientsUpdate(value: string[]) {
  linkedClients.value = value;
  emit('update:linkedClients', value);
}

function getTypeColor(type: PlaceholderType): 'default' | 'success' | 'info' | 'warning' | 'error' {
  const colors: Record<PlaceholderType, 'default' | 'success' | 'info' | 'warning' | 'error'> = {
    text: 'default',
    number: 'success',
    date: 'info',
    dropdown: 'warning',
    multiline: 'error',
  };
  return colors[type] || 'default';
}

function handleUpdatePlaceholder(key: string, updates: Partial<Placeholder>) {
  console.log('[SettingsPanel] handleUpdatePlaceholder:', key, updates);
  console.log('[SettingsPanel] Current placeholders before update:', props.placeholders);
  const updated = props.placeholders.map(p => {
    if (p.key === key) {
      const newPlaceholder = { ...p, ...updates };
      console.log('[SettingsPanel] Updated placeholder:', newPlaceholder);
      console.log('[SettingsPanel] mappedFieldId in new placeholder:', newPlaceholder.mappedFieldId);
      return newPlaceholder;
    }
    return p;
  });
  console.log('[SettingsPanel] All updated placeholders:', updated);
  updated.forEach((p: any) => {
    console.log(`[SettingsPanel] Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}`);
  });
  console.log('[SettingsPanel] Emitting updated placeholders:', updated);
  emit('update:placeholders', updated);
  
  // Wenn ein DB-Feld zugeordnet wurde, automatisch den Wert aus dem verknüpften Mandanten oder aktuellen Client übernehmen
  if (updates.mappedFieldId) {
    console.log('[SettingsPanel] DB-Feld zugeordnet:', updates.mappedFieldId, 'für Platzhalter:', key);
    const placeholder = updated.find(p => p.key === key);
    if (placeholder) {
      const dbField = props.dbFields.find(f => f.id === updates.mappedFieldId);
      console.log('[SettingsPanel] DB-Feld gefunden:', dbField);
      if (dbField) {
        // Zuerst versuchen, verknüpften Mandanten zu verwenden
        let clientToUse: ClientItem | null = null;
        if (linkedClients.value.length > 0 && clients.value.length > 0) {
          clientToUse = clients.value.find((c: ClientItem) => c.id === linkedClients.value[0]) || null;
          console.log('[SettingsPanel] Verknüpfter Mandant gefunden:', clientToUse?.id);
        }
        // Falls kein verknüpfter Mandant, verwende aktuellen Client (z.B. aus Dokument-Modus)
        if (!clientToUse && props.currentClient) {
          clientToUse = props.currentClient;
          console.log('[SettingsPanel] Aktueller Client verwendet:', clientToUse?.id);
        }
        
        if (clientToUse) {
          const value = getValueFromDbField(dbField, clientToUse);
          console.log('[SettingsPanel] Wert extrahiert:', value, 'für DB-Feld:', dbField.key);
          if (value !== null && value !== undefined && value !== '') {
            console.log('[SettingsPanel] Sende update:fillValue Event:', key, value);
            emit('update:fillValue', key, value);
          } else {
            console.warn('[SettingsPanel] Kein Wert gefunden für DB-Feld:', dbField.key);
          }
        } else {
          console.warn('[SettingsPanel] Kein Client verfügbar für Datenübernahme');
        }
      } else {
        console.warn('[SettingsPanel] DB-Feld nicht gefunden für ID:', updates.mappedFieldId);
      }
    }
  }
}

// Funktion zum Extrahieren des Werts aus einem DB-Feld basierend auf dem Mandanten
function getValueFromDbField(dbField: DbField, client: ClientItem): any {
  const dbFieldKey = dbField.key;
  
  // Mandant-Felder
  if (dbFieldKey.startsWith('mandant.')) {
    const fieldName = dbFieldKey.replace('mandant.', '');
    
    if (client.type === 'Natürliche Person') {
      switch (fieldName) {
        case 'name':
          return `${client.firstName || ''} ${client.lastName || ''}`.trim();
        case 'vorname':
          return client.firstName;
        case 'nachname':
          return client.lastName;
        case 'anrede':
          return client.salutation;
        case 'titel':
          return client.title;
        case 'steuernummer':
          return client.taxNumber;
        case 'steuerId':
          return client.taxId;
        case 'email':
          return client.email;
        case 'geburtstag':
          return client.birthDate;
      }
    } else {
      switch (fieldName) {
        case 'name':
        case 'firmenname':
          return client.companyName;
        case 'rechtsform':
          return client.legalForm;
        case 'umsatzsteuerId':
          return client.vatId;
        case 'steuernummer':
          return client.taxNumber;
        case 'email':
          return client.email;
        case 'ansprechpartner':
          return `${client.contactSalutation || ''} ${client.contactLastName || ''}`.trim();
      }
    }
  }
  
  // Adresse-Felder
  if (dbFieldKey.startsWith('adresse.')) {
    const fieldName = dbFieldKey.replace('adresse.', '');
    switch (fieldName) {
      case 'strasse':
        return client.street;
      case 'nummer':
        return client.number;
      case 'plz':
        return client.zip;
      case 'ort':
        return client.city;
    }
  }
  
  // Finanzamt-Felder
  if (dbFieldKey.startsWith('finanzamt.')) {
    const fieldName = dbFieldKey.replace('finanzamt.', '');
    switch (fieldName) {
      case 'name':
        return client.taxOffice;
      case 'strasse':
        return (client.taxOffice as any)?.street || null;
      case 'plz':
        return (client.taxOffice as any)?.zip || null;
      case 'ort':
        return (client.taxOffice as any)?.city || null;
      case 'email':
        return (client.taxOffice as any)?.email || null;
    }
  }
  
  return null;
}

function handleRescan() {
  emit('rescan');
}

function showPlaceholderDetails(placeholder: Placeholder) {
  selectedPlaceholder.value = { ...placeholder };
  showDetailsModal.value = true;
}

function savePlaceholderDetails() {
  if (selectedPlaceholder.value) {
    handleUpdatePlaceholder(selectedPlaceholder.value.key, selectedPlaceholder.value);
    showDetailsModal.value = false;
  }
}
</script>

<style scoped>
</style>

