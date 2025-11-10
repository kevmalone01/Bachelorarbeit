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
          @update:page="(v:number)=>page=v"
          @update:page-size="onUpdatePageSize"
          @update:sorting="onUpdateSorting"
          @edit="onEdit"
          @download="onDownload"
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
          <n-form-item path="mandant" label="Mandant">
            <n-input v-model:value="createForm.mandant" placeholder="z. B. Müller AG" />
          </n-form-item>
        </div>
        <n-form-item path="template" label="Template">
          <n-select
            v-model:value="createForm.template"
            :options="templatesSelectOptions"
            filterable
            clearable
            placeholder="Template auswählen (optional)"
          />
        </n-form-item>
        <n-form-item path="description" label="Beschreibung">
          <n-input v-model:value="createForm.description" type="textarea" placeholder="Optional: kurze Beschreibung" />
        </n-form-item>
      </n-form>
      <div class="mt-4 flex items-center justify-end gap-2">
        <n-button quaternary @click="closeCreateModal">Abbrechen</n-button>
        <n-button type="primary" :loading="createSubmitting" @click="submitCreate">Anlegen</n-button>
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
import { NDrawer, NDrawerContent, NLayout, NLayoutSider, NInput, NModal, NForm, NFormItem, NSelect, NDatePicker, NButton } from 'naive-ui';
import Filters from '@/components/dashboard/Filters.vue';
import Toolbar from '@/components/dashboard/Toolbar.vue';
import DocumentsTable from '@/components/dashboard/DocumentsTable.vue';
import { api } from '@/lib/api';
import type { DocumentsQueryParams, DocumentItem } from '@/lib/types';
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
    // Placeholder: if backend not ready, provide dummy data
    try {
      return await api.getDocuments({
        ...filters,
        page: page.value,
        pageSize: pageSize.value,
        sortBy: sorting.value?.id,
        sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
      });
    } catch {
      const items: DocumentItem[] = Array.from({ length: 10 }).map((_, i) => ({
        id: String(i + 1),
        modified: new Date(Date.now() - i * 86400000).toISOString(),
        name: `Beispiel-Dokument ${i + 1}`,
        status: (['Draft', 'To Be Reviewed', 'In Progress', 'Not Started', 'Finished'] as const)[i % 5],
        owner: i % 2 ? 'Anna Schmidt' : 'Max Mustermann',
        mandant: i % 2 ? 'Meyer GmbH' : 'Müller AG',
        deadline: new Date(Date.now() + (i + 1) * 86400000).toISOString(),
        template: i % 3 ? 'Standard' : 'Vertrag A',
      }));
      return { items, page: page.value, pageSize: pageSize.value, total: 100 };
    }
  },
  refetchOnWindowFocus: false,
});

const documents = computed(() => docsData.value?.items ?? []);
const total = computed(() => docsData.value?.total ?? 0);

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
  nMessage?.info(`Dokument bearbeiten: ${row.name}`);
}
function onDownload(row: DocumentItem) {
  nMessage?.success(`Download gestartet: ${row.name}`);
}
function openAIDrawer() {
  showAIDrawer.value = true;
}

// Create Document flow
type CreateForm = {
  name: string;
  status: 'Draft' | 'To Be Reviewed' | 'In Progress' | 'Not Started' | 'Finished' | '';
  owner?: string;
  mandant?: string;
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
const templatesSelectOptions = computed(() => templates.value.map(t => ({ label: t.name, value: t.name })));
const createForm = reactive<CreateForm>({
  name: '',
  status: 'Draft',
  owner: '',
  mandant: '',
  template: '',
  deadline: null,
  description: '',
});
const createRules = {
  name: { required: true, message: 'Name ist erforderlich', trigger: 'blur' },
  status: { required: true, message: 'Status ist erforderlich', trigger: 'change' },
};
const createSubmitting = ref(false);

function closeCreateModal() {
  showCreateModal.value = false;
}

async function submitCreate() {
  await createFormRef.value?.validate();
  createSubmitting.value = true;
  try {
    await api.createDocument({
      title: createForm.name.trim(),
      status: 'draft', // Backend verwendet lowercase
      document_type: createForm.template || undefined,
      content: createForm.description || '',
      // Bei Bedarf zusätzlich client_id / tax_advisor_id senden
    } as any);
    nMessage?.success('Dokument erstellt');
    closeCreateModal();
    // Reset
    createForm.name = '';
    createForm.status = 'Draft';
    createForm.owner = '';
    createForm.mandant = '';
    createForm.template = '';
    createForm.deadline = null;
    createForm.description = '';
    refetch();
  } catch (e:any) {
    nMessage?.error('Erstellen fehlgeschlagen');
  } finally {
    createSubmitting.value = false;
  }
}
</script>

<style scoped>
</style>

