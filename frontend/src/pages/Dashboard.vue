<template>
  <n-layout has-sider class="h-screen">
    <!-- Sidebar -->
    <template v-if="isDesktop">
      <n-layout-sider
        bordered
        collapse-mode="width"
        :collapsed="isCollapsed"
        :width="siderWidth"
        :collapsed-width="0"
        show-trigger="arrow-circle"
        @collapse="isCollapsed = true"
        @expand="isCollapsed = false"
        class="p-3 relative"
      >
        <div v-if="!isCollapsed">
          <Filters
            :users="users"
            :templates="templates"
            :selected="filters"
            @apply="applyFilters"
            @reset="resetFilters"
          />
        </div>
        <!-- Drag handle -->
        <div
          v-if="!isCollapsed"
          class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-slate-200"
          @mousedown="startResize"
        />
      </n-layout-sider>
    </template>

    <n-layout>
      <div class="p-4">
        <Toolbar
          :query="filters.query || ''"
          :column-visibility="columnVisibility"
          @update:query="onQuery"
          @toggle-filter="isDesktop ? isCollapsed = !isCollapsed : showFilterDrawer = true"
          @update:column-visibility="onUpdateColumnVisibility"
          @create-document="onCreate"
          @open-ai="openAIDrawer"
        />
      </div>

      <div class="px-4 pb-4">
        <DocumentsTable
          :loading="isLoading"
          :error="isError"
          :documents="documents"
          :page="page"
          :page-size="pageSize"
          :total="total"
          :column-visibility="columnVisibility"
          :sorting="sorting"
          :get-client-name="getClientName"
          @update:page="(v:number)=>page=v"
          @update:page-size="onUpdatePageSize"
          @update:sorting="onUpdateSorting"
          @edit="onEdit"
          @download="onDownload"
          @delete="onDelete"
          @create="onCreate"
        />
      </div>
    </n-layout>
  </n-layout>

  <!-- Filters Drawer (mobile) -->
  <n-drawer v-model:show="showFilterDrawer" :width="320" placement="left">
    <n-drawer-content title="Filter">
      <Filters
        :users="users"
        :templates="templates"
        :selected="filters"
        @apply="(f)=>{ applyFilters(f); showFilterDrawer=false; }"
        @reset="resetFilters"
      />
    </n-drawer-content>
  </n-drawer>

  <!-- Create Document Modal -->
  <n-modal v-model:show="showCreateModal" :mask-closable="false">
    <div class="w-full max-w-lg mx-auto rounded-2xl shadow-xl bg-white p-5">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="text-lg font-semibold">Neues Dokument</h3>
          <p class="text-xs text-slate-500">Bitte fülle die folgenden Informationen aus.</p>
        </div>
        <button class="text-slate-400 hover:text-slate-600" @click="closeCreateModal" aria-label="Schließen">✕</button>
      </div>
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="top" class="space-y-1">
        <n-form-item path="name" label="Dokumentenname">
          <n-input v-model:value="createForm.name" placeholder="z. B. Jahresabschluss 2024" />
        </n-form-item>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <n-form-item path="status" label="Status">
            <n-select v-model:value="createForm.status" :options="statusOptions" placeholder="Status wählen" />
          </n-form-item>
          <n-form-item path="deadline" label="Deadline">
            <n-date-picker v-model:value="createForm.deadline" type="date" clearable />
          </n-form-item>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <n-form-item path="owner" label="Owner">
            <n-select
              v-model:value="createForm.owner"
              :options="usersSelectOptions"
              filterable
              tag
              placeholder="Owner auswählen"
            />
          </n-form-item>
          <n-form-item path="clientId" label="Mandant" required>
            <n-select
              v-model:value="createForm.clientId"
              :options="clientSelectOptions"
              filterable
              placeholder="Mandant auswählen *"
              :loading="clientsLoading"
            />
          </n-form-item>
        </div>
        <n-form-item path="template" label="Template" required>
          <n-select
            v-model:value="createForm.template"
            :options="templatesSelectOptions"
            filterable
            placeholder="Template auswählen *"
          />
        </n-form-item>
        <n-form-item path="description" label="Beschreibung">
          <n-input v-model:value="createForm.description" type="textarea" placeholder="Optional: kurze Beschreibung" />
        </n-form-item>
      </n-form>
      <div class="mt-4 flex items-center justify-end gap-2">
        <n-button quaternary @click="closeCreateModal">Abbrechen</n-button>
        <n-button 
          type="primary" 
          :loading="createSubmitting" 
          :disabled="!createForm.name || !createForm.status || !createForm.clientId || !createForm.template"
          @click="submitCreate"
        >
          Anlegen
        </n-button>
      </div>
    </div>
  </n-modal>

  <!-- AI Drawer -->
  <n-drawer v-model:show="showAIDrawer" :width="420" placement="right">
    <n-drawer-content title="KI-Agent">
      <div class="space-y-3">
        <p class="text-sm text-slate-600">Kommende KI-Assistenz…</p>
        <n-input v-model:value="aiInput" placeholder="Frage an die KI…" />
        <div class="rounded border p-3 text-sm h-64 overflow-auto">
          <p class="text-slate-500">Noch kein Chatverlauf vorhanden.</p>
        </div>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
/**
 * Dashboard: Dokumentenübersicht mit Filter-Sidebar, Toolbar und Tabelle.
 */
import { computed, inject, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { useBreakpoints } from '@vueuse/core';
import { NDrawer, NDrawerContent, NLayout, NLayoutSider, NInput, NModal, NForm, NFormItem, NSelect, NDatePicker, NButton, createDiscreteApi } from 'naive-ui';
import Filters from '@/components/dashboard/Filters.vue';
import Toolbar from '@/components/dashboard/Toolbar.vue';
import DocumentsTable from '@/components/dashboard/DocumentsTable.vue';
import { api, clientsApi } from '@/lib/api';
import type { DocumentsQueryParams, DocumentItem, ClientItem } from '@/lib/types';
import { useTablePrefsStore } from '@/stores/tablePrefs';

const nMessage = inject<any>('nMessage');
const router = useRouter();
const route = useRoute();
const prefs = useTablePrefsStore();

const showFilterDrawer = ref(false);
const showAIDrawer = ref(false);
const showCreateModal = ref(false);
const aiInput = ref('');

const breakpoints = useBreakpoints({ lg: 1024 });
const isDesktop = breakpoints.greaterOrEqual('lg');
const isCollapsed = ref(true); // Standardmäßig eingeklappt
const siderWidth = ref(280);
let isResizing = false;
let startX = 0;
let startW = 280;
function startResize(e: MouseEvent) {
  isResizing = true;
  startX = e.clientX;
  startW = siderWidth.value;
  window.addEventListener('mousemove', onResize);
  window.addEventListener('mouseup', stopResize, { once: true });
}
function onResize(e: MouseEvent) {
  if (!isResizing) return;
  const delta = e.clientX - startX;
  const next = Math.min(420, Math.max(220, startW + delta));
  siderWidth.value = next;
}
function stopResize() {
  isResizing = false;
  window.removeEventListener('mousemove', onResize);
}

// Filters from URL
const filters = reactive<DocumentsQueryParams>({
  query: (route.query.query as string) || '',
  status: ([] as string[]).concat(route.query.status as any || []),
  owner: ([] as string[]).concat(route.query.owner as any || []),
  template: ([] as string[]).concat(route.query.template as any || []),
  deadlineFrom: (route.query.deadlineFrom as string) || undefined,
  deadlineTo: (route.query.deadlineTo as string) || undefined,
  page: Number(route.query.page || 1),
  pageSize: prefs.pageSize || 20,
  sortBy: (route.query.sortBy as string) || undefined,
  sortDir: (route.query.sortDir as any) || undefined,
});

const columnVisibility = ref<Record<string, boolean>>({ ...prefs.visibleColumns });
watch(columnVisibility, (v) => {
  Object.entries(v).forEach(([k, val]) => prefs.setColumnVisible(k, val));
}, { deep: true });

const page = ref(filters.page || 1);
const pageSize = ref(filters.pageSize || prefs.pageSize || 20);
const sorting = ref<{ id: string; desc: boolean } | null>(filters.sortBy ? { id: filters.sortBy!, desc: filters.sortDir === 'desc' } : null);

// Sync URL
watch([filters, page, pageSize, sorting], () => {
  const q: any = {
    ...filters,
    page: page.value,
    pageSize: pageSize.value,
    sortBy: sorting.value?.id,
    sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
  };
  Object.keys(q).forEach((k) => (q[k] === undefined || q[k] === '' || (Array.isArray(q[k]) && q[k].length === 0)) && delete q[k]);
  router.replace({ query: q });
}, { deep: true });

// Data
const { data: docsData, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['documents', { ...filters, page: page.value, pageSize: pageSize.value, sorting: sorting.value }]),
  queryFn: async () => {
    console.log('[Dashboard] Fetching documents with params:', {
      ...filters,
      page: page.value,
      pageSize: pageSize.value,
      sortBy: sorting.value?.id,
      sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
    });
    const result = await api.getDocuments({
      ...filters,
      page: page.value,
      pageSize: pageSize.value,
      sortBy: sorting.value?.id,
      sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
    });
    console.log('[Dashboard] Documents loaded:', result?.items?.length || 0, 'total:', result?.total || 0);
    return result;
  },
  refetchOnWindowFocus: false,
});

const documents = computed(() => {
  const items = docsData.value?.items ?? [];
  console.log('[Dashboard] Computed documents:', items.length, 'items');
  return items;
});
const total = computed(() => {
  const totalValue = docsData.value?.total ?? 0;
  console.log('[Dashboard] Computed total:', totalValue);
  return totalValue;
});

// Auxiliary data
const { data: usersData } = useQuery({
  queryKey: ['users'],
  queryFn: () => api.getUsers(),
  refetchOnWindowFocus: false,
});
const users = computed(() => usersData.value ?? []);

const { data: templatesData } = useQuery({
  queryKey: ['templates'],
  queryFn: () => api.getTemplates(),
  refetchOnWindowFocus: false,
});
const templates = computed(() => templatesData.value ?? []);

// Clients für Mandantenauswahl laden
const { data: clientsData, isLoading: clientsLoading } = useQuery({
  queryKey: ['clients-for-document-creation'],
  queryFn: () => clientsApi.getClients({ page: 1, pageSize: 1000 }),
  refetchOnWindowFocus: false,
});
const clients = computed(() => clientsData.value?.items || []);
const clientSelectOptions = computed(() =>
  clients.value.map((c: ClientItem) => ({
    label: c.type === 'Natürliche Person'
      ? `${c.salutation || ''} ${c.firstName || ''} ${c.lastName || ''}`.trim()
      : c.companyName || 'Unbekannt',
    value: c.id,
  }))
);

// Funktion zum Ermitteln des Client-Namens aus der ID
function getClientName(clientId: string | undefined): string {
  if (!clientId) return '—';
  const client = clients.value.find((c: ClientItem) => c.id === clientId);
  if (!client) return clientId; // Fallback: ID anzeigen, wenn Client nicht gefunden
  return client.type === 'Natürliche Person'
    ? `${client.salutation || ''} ${client.firstName || ''} ${client.lastName || ''}`.trim()
    : client.companyName || 'Unbekannt';
}

function onQuery(v: string) {
  filters.query = v;
}
function onUpdateColumnVisibility(v: Record<string, boolean>) {
  columnVisibility.value = { ...v };
}
function onUpdatePageSize(v: number) {
  pageSize.value = v;
  prefs.setPageSize(v);
}
function onUpdateSorting(v: { id: string; desc: boolean } | null) {
  sorting.value = v;
}
function applyFilters(f: DocumentsQueryParams) {
  Object.assign(filters, f);
  page.value = 1;
  refetch();
}
function resetFilters() {
  Object.assign(filters, {
    query: '',
    status: [],
    owner: [],
    template: [],
    deadlineFrom: undefined,
    deadlineTo: undefined,
  });
  page.value = 1;
  refetch();
}
function onCreate() {
  showCreateModal.value = true;
}
function onEdit(row: DocumentItem) {
  console.log('[Dashboard] Edit clicked for document:', row.id, row.name);
  // Navigate to document editor
  router.push(`/editor/${row.id}`);
}
function onDownload(row: DocumentItem) {
  nMessage?.success(`Download gestartet: ${row.name}`);
}
async function onDelete(row: DocumentItem) {
  const { dialog } = createDiscreteApi(['dialog']);
  dialog.warning({
    title: 'Dokument löschen',
    content: `Möchten Sie das Dokument "${row.name}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`,
    positiveText: 'Löschen',
    negativeText: 'Abbrechen',
    onPositiveClick: async () => {
      try {
        await api.deleteDocument(row.id);
        nMessage?.success('Dokument gelöscht');
        refetch();
      } catch (e: any) {
        nMessage?.error(e.message || 'Fehler beim Löschen');
      }
    }
  });
}
function openAIDrawer() {
  showAIDrawer.value = true;
}

// Create Document flow
type CreateForm = {
  name: string;
  status: 'Draft' | 'To Be Reviewed' | 'In Progress' | 'Not Started' | 'Finished' | '';
  owner?: string;
  clientId?: string; // Changed from mandant to clientId
  template?: string;
  deadline?: number | null; // timestamp
  description?: string;
};
const createFormRef = ref<any>(null);
const statusOptions = [
  { label: 'Draft', value: 'Draft' },
  { label: 'To Be Reviewed', value: 'To Be Reviewed' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Not Started', value: 'Not Started' },
  { label: 'Finished', value: 'Finished' },
];
const usersSelectOptions = computed(() => users.value.map(u => ({ label: u.name, value: u.name })));
const templatesSelectOptions = computed(() => templates.value.map(t => ({ label: t.name, value: String(t.id) })));
const createForm = reactive<CreateForm>({
  name: '',
  status: 'Draft',
  owner: '',
  clientId: undefined,
  template: '',
  deadline: null,
  description: '',
});
const createRules = {
  name: { required: true, message: 'Name ist erforderlich', trigger: 'blur' },
  status: { required: true, message: 'Status ist erforderlich', trigger: 'change' },
  clientId: { required: true, message: 'Bitte wählen Sie einen Mandanten aus', trigger: ['change', 'blur'] },
  template: { required: true, message: 'Bitte wählen Sie ein Template aus', trigger: ['change', 'blur'] },
};
const createSubmitting = ref(false);

function closeCreateModal() {
  showCreateModal.value = false;
}

async function submitCreate() {
  try {
    await createFormRef.value?.validate();
  } catch (e) {
    console.log('[Dashboard] Form validation failed:', e);
    // Zeige spezifische Fehlermeldungen
    if (!createForm.clientId) {
      nMessage?.error('Bitte wählen Sie einen Mandanten aus');
    }
    if (!createForm.template) {
      nMessage?.error('Bitte wählen Sie ein Template aus');
    }
    return;
  }
  
  createSubmitting.value = true;
  try {
    const createdClientId = createForm.clientId; // Speichere clientId vor dem Reset
    const createdTemplate = createForm.template; // Speichere template vor dem Reset
    
    const result = await api.createDocument({
      title: createForm.name.trim(),
      status: 'draft', // Backend verwendet lowercase
      document_type: createForm.template || undefined,
      content: createForm.description || '',
      client_id: createForm.clientId ? Number(createForm.clientId) : undefined,
    } as any);
    nMessage?.success('Dokument erstellt');
    closeCreateModal();
    // Reset
    createForm.name = '';
    createForm.status = 'Draft';
    createForm.owner = '';
    createForm.clientId = undefined;
    createForm.template = '';
    createForm.deadline = null;
    createForm.description = '';
    refetch();
    
    // Navigiere zum Editor mit dem erstellten Dokument und clientId
    if (result && result.id && createdTemplate) {
      router.push({
        path: `/editor/${createdTemplate}`,
        query: {
          documentId: String(result.id),
          mode: 'document',
          ...(createdClientId ? { clientId: String(createdClientId) } : {}),
          templateId: String(createdTemplate),
        },
      });
    }
  } catch (e:any) {
    nMessage?.error(e.message || 'Erstellen fehlgeschlagen');
  } finally {
    createSubmitting.value = false;
  }
}
</script>

<style scoped>
</style>

