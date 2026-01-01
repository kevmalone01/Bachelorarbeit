<template>
  <div class="document-from-template-view p-6">
    <n-card title="Neues Dokument anlegen" size="large">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item path="templateId" label="Vorlage auswählen *">
          <n-select
            v-model:value="form.templateId"
            :options="templateOptions"
            placeholder="Vorlage auswählen"
            filterable
            :loading="templatesLoading"
            clearable
            @update:value="onTemplateSelected"
          />
        </n-form-item>

        <n-form-item path="clientId" label="Mandant auswählen" required>
          <n-select
            v-model:value="form.clientId"
            :options="clientOptions"
            placeholder="Mandant auswählen *"
            filterable
            :loading="clientsLoading"
            @update:value="onClientSelected"
          />
        </n-form-item>

        <n-form-item v-if="selectedTemplate && selectedClient" label="Vorschau">
          <div class="preview-info">
            <p><strong>Vorlage:</strong> {{ selectedTemplate.name }}</p>
            <p><strong>Mandant:</strong> {{ selectedClient.name || `${selectedClient.firstName} ${selectedClient.lastName}` }}</p>
          </div>
        </n-form-item>
      </n-form>

      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="router.push('/dashboard')">Abbrechen</n-button>
          <n-button
            type="primary"
            :disabled="!form.templateId || !form.clientId"
            :loading="loading"
            @click="handleCreate"
          >
            Dokument erstellen und bearbeiten
          </n-button>
        </div>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { NCard, NForm, NFormItem, NSelect, NButton, createDiscreteApi } from 'naive-ui';
import { documentEditorApi } from '@/lib/api';
import { clientsApi } from '@/lib/api';
import type { DocumentTemplate, ClientItem } from '@/lib/types';

const router = useRouter();
const route = useRoute();
const { message: nMessage } = createDiscreteApi(['message']);

const formRef = ref<any>(null);
const loading = ref(false);
const form = ref({
  templateId: undefined as string | undefined,
  clientId: undefined as string | undefined,
});

// Templates laden
const { data: templates = [], isLoading: templatesLoading } = useQuery({
  queryKey: ['document-templates'],
  queryFn: () => documentEditorApi.getTemplates(),
});

// CRITICAL: Watch templates to ensure no automatic selection happens
watch(
  () => templates.value,
  (newTemplates) => {
    // Don't auto-select first template - let user choose
    console.log('[DocumentFromTemplateView] Templates loaded:', newTemplates.length, 'Current templateId:', form.value.templateId);
  },
  { immediate: true }
);

const templateOptions = computed(() =>
  templates.value.map((t: DocumentTemplate) => ({
    label: t.name,
    value: String(t.id),
  }))
);

const selectedTemplate = computed(() => {
  if (!form.value.templateId) return null;
  return templates.value.find((t: DocumentTemplate) => String(t.id) === form.value.templateId) || null;
});

// Clients laden
const { data: clientsData, isLoading: clientsLoading } = useQuery({
  queryKey: ['clients-for-document'],
  queryFn: () => clientsApi.getClients({ page: 1, pageSize: 1000 }),
});

const clients = computed(() => clientsData.value?.items || []);

const clientOptions = computed(() =>
  clients.value.map((c: ClientItem) => ({
    label: c.type === 'Natürliche Person'
      ? `${c.salutation || ''} ${c.firstName || ''} ${c.lastName || ''}`.trim()
      : c.companyName || 'Unbekannt',
    value: c.id,
  }))
);

const selectedClient = computed(() => {
  if (!form.value.clientId) return null;
  return clients.value.find((c: ClientItem) => c.id === form.value.clientId) || null;
});

const rules = {
  templateId: { 
    required: true, 
    message: 'Bitte wählen Sie eine Vorlage aus', 
    trigger: ['change', 'blur'] 
  },
  clientId: { 
    required: true, 
    message: 'Bitte wählen Sie einen Mandanten aus', 
    trigger: ['change', 'blur'] 
  },
};

function onTemplateSelected(value: string) {
  console.log('[DocumentFromTemplateView] Template selected:', value);
  form.value.templateId = value;
  console.log('[DocumentFromTemplateView] form.templateId after selection:', form.value.templateId);
}

function onClientSelected(value: string) {
  form.value.clientId = value;
}

async function handleCreate() {
  try {
    await formRef.value?.validate();
  } catch (e) {
    console.log('[DocumentFromTemplateView] Form validation failed:', e);
    // Zeige spezifische Fehlermeldung
    if (!form.value.templateId) {
      nMessage.error('Bitte wählen Sie eine Vorlage aus');
    }
    if (!form.value.clientId) {
      nMessage.error('Bitte wählen Sie einen Mandanten aus');
    }
    return;
  }

  // Zusätzliche Prüfung (sollte eigentlich nicht nötig sein, aber sicherheitshalber)
  if (!form.value.templateId || !form.value.clientId) {
    nMessage.error('Bitte wählen Sie eine Vorlage und einen Mandanten aus');
    return;
  }

  loading.value = true;
  try {
    // Navigiere zum Editor mit Template-ID und Client-ID als Query-Parameter
    router.push({
      path: `/editor/${form.value.templateId}`,
      query: {
        clientId: form.value.clientId,
        templateId: form.value.templateId, // CRITICAL: Save templateId in query
        mode: 'document', // Modus: Dokument (nicht Template)
      },
    });
  } catch (error) {
    nMessage.error('Fehler beim Erstellen des Dokuments');
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// Prüfe Query-Parameter für Vorauswahl
// CRITICAL: Only set from query if form is not already set (to avoid overwriting user selection)
watch(
  () => route.query,
  (query, oldQuery) => {
    console.log('[DocumentFromTemplateView] Route query changed:', query, 'Old query:', oldQuery, 'Current form.templateId:', form.value.templateId);
    // Only set templateId from query if form.templateId is not already set
    // This prevents overwriting user selection
    if (query.templateId && typeof query.templateId === 'string' && !form.value.templateId) {
      console.log('[DocumentFromTemplateView] Setting templateId from query:', query.templateId);
      form.value.templateId = query.templateId;
    } else if (query.templateId && typeof query.templateId === 'string' && form.value.templateId) {
      console.log('[DocumentFromTemplateView] NOT setting templateId from query (already set):', form.value.templateId, 'Query has:', query.templateId);
    }
    // Only set clientId from query if form.clientId is not already set
    if (query.clientId && typeof query.clientId === 'string' && !form.value.clientId) {
      console.log('[DocumentFromTemplateView] Setting clientId from query:', query.clientId);
      form.value.clientId = query.clientId;
    }
  },
  { immediate: true }
);

// Watch form.templateId to debug selection issues
watch(
  () => form.value.templateId,
  (newValue, oldValue) => {
    console.log('[DocumentFromTemplateView] form.templateId changed:', oldValue, '->', newValue);
  }
);
</script>

<style scoped>
.document-from-template-view {
  max-width: 800px;
  margin: 0 auto;
}

.preview-info {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.preview-info p {
  margin: 4px 0;
}
</style>

