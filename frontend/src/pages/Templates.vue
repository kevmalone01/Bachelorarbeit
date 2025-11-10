<template>
  <n-layout has-sider class="h-screen">
    <!-- Sidebar Desktop -->
    <n-layout-sider
      v-if="isDesktop"
      bordered
      collapse-mode="width"
      :width="280"
      :collapsed="sidebarCollapsed"
      :collapsed-width="0"
      show-trigger="arrow-circle"
      @collapse="sidebarCollapsed = true"
      @expand="sidebarCollapsed = false"
      class="p-3"
    >
      <TemplateFilters
        :creators="creators"
        :types="types"
        :selected="filters"
        @apply="applyFilters"
        @reset="resetFilters"
      />
    </n-layout-sider>

    <n-layout>
      <div class="p-4">
        <TemplateToolbar
          :query="filters.query || ''"
          :column-visibility="visibleColumns"
          :selected-count="selectedIds.size"
          @update:query="onQuery"
          @toggle-filter="isDesktop ? sidebarCollapsed = !sidebarCollapsed : showFilterDrawer = true"
          @update:column-visibility="onUpdateColumnVisibility"
          @create-template="openCreate"
          @delete-selected="handleDeleteSelected"
        />
      </div>

      <div class="px-4 pb-4">
        <TemplatesTable
          :loading="isLoading"
          :error="isError"
          :templates="templates"
          :page="page"
          :page-size="pageSize"
          :total="total"
          :column-visibility="visibleColumns"
          :sorting="sorting"
          :selected-ids="selectedIds"
          @update:page="(v:number)=>page=v"
          @update:page-size="onUpdatePageSize"
          @update:sorting="onUpdateSorting"
          @update:selected-ids="selectedIds = $event"
          @create="openCreate"
          @edit="onEdit"
          @download="onDownload"
        />
      </div>
    </n-layout>
  </n-layout>

  <!-- Mobile Filters -->
  <n-drawer v-model:show="showFilterDrawer" :width="320" placement="left">
    <n-drawer-content title="Filter">
      <TemplateFilters
        :creators="creators"
        :types="types"
        :selected="filters"
        @apply="(f)=>{ applyFilters(f); showFilterDrawer=false; }"
        @reset="resetFilters"
      />
    </n-drawer-content>
  </n-drawer>

  <!-- Create Template Modal -->
  <n-modal v-model:show="showCreateModal" :mask-closable="false">
    <n-card title="Neue Vorlage" :bordered="false" size="large" class="max-w-lg mx-auto">
      <template #header-extra>
        <n-button quaternary circle @click="closeCreateModal">
          <template #icon>
            <span class="text-xl">×</span>
          </template>
        </n-button>
      </template>
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="top">
        <n-form-item path="title" label="Titel *">
          <n-input v-model:value="createForm.title" placeholder="Titel der Vorlage" />
        </n-form-item>
        <n-form-item path="note" label="Notiz">
          <n-input v-model:value="createForm.note" type="textarea" placeholder="Optionale Notiz zur Vorlage" :rows="3" />
        </n-form-item>
        <n-form-item path="type" label="Vorlagenart *">
          <n-select v-model:value="createForm.type" :options="typeOptions" placeholder="Vorlagenart auswählen" />
        </n-form-item>
        <n-form-item path="creator" label="Ersteller *">
          <n-select v-model:value="createForm.creator" :options="creatorOptions" filterable placeholder="Ersteller auswählen" />
        </n-form-item>
        <n-form-item label="Word-Datei hochladen">
          <n-upload
            v-model:file-list="fileList"
            :max="1"
            accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            @change="handleFileChange"
          >
            <n-upload-dragger>
              <div class="text-center py-4">
                <p class="text-sm text-slate-600">Klicken oder Datei hierher ziehen</p>
                <p class="text-xs text-slate-400 mt-1">Nur .doc und .docx Dateien</p>
              </div>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <n-button @click="closeCreateModal">Abbrechen</n-button>
          <n-button type="primary" :loading="createSubmitting" @click="submitCreate">Anlegen</n-button>
        </div>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
/**
 * Templates.vue - Seite für Vorlagenverwaltung mit Filter, Toolbar und Tabelle.
 */
import { computed, inject, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { useBreakpoints } from '@vueuse/core';
import { NDrawer, NDrawerContent, NLayout, NLayoutSider, NButton, NCard, NForm, NFormItem, NInput, NModal, NSelect, NUpload, NUploadDragger, createDiscreteApi } from 'naive-ui';
import TemplateFilters from '@/components/templates/Filters.vue';
import TemplateToolbar from '@/components/templates/Toolbar.vue';
import TemplatesTable from '@/components/templates/TemplatesTable.vue';
import { templatesApi } from '@/lib/api';
import type { TemplateItem, TemplatesQueryParams } from '@/lib/types';
import { useTablePrefsStore } from '@/stores/tablePrefs';

const nMessage = inject<any>('nMessage');
const { dialog } = createDiscreteApi(['dialog']);
const router = useRouter();
const route = useRoute();
const prefs = useTablePrefsStore();
const queryClient = useQueryClient();

const showFilterDrawer = ref(false);
const showCreateModal = ref(false);
const sidebarCollapsed = ref(true); // Standardmäßig eingeklappt
const selectedIds = ref<Set<string>>(new Set());

const breakpoints = useBreakpoints({ lg: 1024 });
const isDesktop = breakpoints.greaterOrEqual('lg');

// Filters from URL
const filters = reactive<TemplatesQueryParams>({
  query: (route.query.query as string) || '',
  creator: ([] as string[]).concat(route.query.creator as any || []),
  type: ([] as string[]).concat(route.query.type as any || []),
  createdAtFrom: (route.query.createdAtFrom as string) || undefined,
  createdAtTo: (route.query.createdAtTo as string) || undefined,
  page: Number(route.query.page || 1),
  pageSize: prefs.pageSize || 20,
  sortBy: (route.query.sortBy as string) || undefined,
  sortDir: (route.query.sortDir as any) || undefined,
});

// Column visibility
const visibleColumns = ref<Record<string, boolean>>({ ...prefs.templateVisibleColumns });
watch(visibleColumns, (v) => {
  Object.entries(v).forEach(([k, val]) => prefs.setTemplateColumnVisible(k, val));
}, { deep: true });

// Pagination
const page = ref(filters.page || 1);
const pageSize = ref(filters.pageSize || prefs.pageSize || 20);
const sorting = ref<{ id: string; desc: boolean } | null>(filters.sortBy ? { id: filters.sortBy!, desc: filters.sortDir === 'desc' } : null);

// Sync URL
watch([filters, page, pageSize, sorting], () => {
  const q: any = {
    query: filters.query,
    creator: filters.creator,
    type: filters.type,
    createdAtFrom: filters.createdAtFrom,
    createdAtTo: filters.createdAtTo,
    page: page.value,
    pageSize: pageSize.value,
    sortBy: sorting.value?.id,
    sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
  };
  Object.keys(q).forEach((k) => (q[k] === undefined || q[k] === '' || (Array.isArray(q[k]) && q[k].length === 0)) && delete q[k]);
  router.replace({ query: q });
}, { deep: true });

// Data
const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['templates', { ...filters, page: page.value, pageSize: pageSize.value, sorting: sorting.value }]),
  queryFn: () => templatesApi.getTemplates({
    ...filters,
    page: page.value,
    pageSize: pageSize.value,
    sortBy: sorting.value?.id,
    sortDir: sorting.value ? (sorting.value.desc ? 'desc' : 'asc') : undefined,
  }),
  keepPreviousData: true
});

const templates = computed<TemplateItem[]>(() => data.value?.items ?? []);
const total = computed<number>(() => data.value?.total ?? 0);

// Auxiliary data
const { data: creatorsData } = useQuery({
  queryKey: ['template-creators'],
  queryFn: () => templatesApi.getCreators(),
  staleTime: 60_000
});
const creators = computed(() => creatorsData.value ?? []);

const { data: typesData } = useQuery({
  queryKey: ['template-types'],
  queryFn: () => templatesApi.getTemplateTypes(),
  staleTime: 60_000
});
const types = computed(() => typesData.value ?? []);

function onQuery(v: string) {
  filters.query = v;
  page.value = 1;
}
function onUpdateColumnVisibility(v: Record<string, boolean>) {
  visibleColumns.value = { ...v };
}
function onUpdatePageSize(v: number) {
  pageSize.value = v;
  prefs.setPageSize(v);
}
function onUpdateSorting(v: { id: string; desc: boolean } | null) {
  sorting.value = v;
}
function applyFilters(f: TemplatesQueryParams) {
  Object.assign(filters, f);
  page.value = 1;
  refetch();
}
function resetFilters() {
  Object.assign(filters, {
    query: '',
    creator: [],
    type: [],
    createdAtFrom: undefined,
    createdAtTo: undefined,
  });
  page.value = 1;
  refetch();
}
function openCreate() {
  showCreateModal.value = true;
}

function onEdit(item: TemplateItem) {
  nMessage?.info(`Vorlage bearbeiten: ${item.title}`);
  // TODO: Öffne Edit-Modal oder navigiere zu Edit-Seite
}

function onDownload(item: TemplateItem) {
  if (item.fileUrl) {
    window.open(item.fileUrl, '_blank');
  } else {
    nMessage?.warning('Keine Datei verfügbar');
  }
}

// Create Template flow
const createFormRef = ref<any>(null);
const createSubmitting = ref(false);
const fileList = ref<any[]>([]);
const selectedFile = ref<File | null>(null);

const createForm = reactive({
  title: '',
  note: '',
  type: undefined as string | undefined,
  creator: undefined as string | undefined,
});

const typeOptions = computed(() => types.value.map(t => ({ label: t, value: t })));
const creatorOptions = computed(() => creators.value.map(c => ({ label: c.name, value: c.id })));

const createRules = {
  title: { required: true, message: 'Titel ist erforderlich', trigger: 'blur' },
  type: { required: true, message: 'Vorlagenart ist erforderlich', trigger: 'change' },
  creator: { required: true, message: 'Ersteller ist erforderlich', trigger: 'change' },
};

function handleFileChange(options: { fileList: any[] }) {
  fileList.value = options.fileList;
  if (options.fileList.length > 0) {
    selectedFile.value = options.fileList[0].file as File;
  } else {
    selectedFile.value = null;
  }
}

function closeCreateModal() {
  showCreateModal.value = false;
  createForm.title = '';
  createForm.note = '';
  createForm.type = undefined;
  createForm.creator = undefined;
  fileList.value = [];
  selectedFile.value = null;
}

async function submitCreate() {
  try {
    await createFormRef.value?.validate();
  } catch (e) {
    return;
  }

  createSubmitting.value = true;
  try {
    const creatorName = creators.value.find(c => c.id === createForm.creator)?.name || '';
    await templatesApi.createTemplate({
      title: createForm.title.trim(),
      note: createForm.note.trim() || undefined,
      type: createForm.type as any,
      creator: creatorName,
      file: selectedFile.value || undefined,
    });
    nMessage?.success('Vorlage erstellt');
    closeCreateModal();
    refetch();
  } catch (e: any) {
    nMessage?.error('Erstellen fehlgeschlagen');
  } finally {
    createSubmitting.value = false;
  }
}

// Delete Mutation
const deleteMutation = useMutation({
  mutationFn: (id: string) => templatesApi.deleteTemplate(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['templates'] });
  }
});

async function handleDeleteSelected() {
  if (selectedIds.value.size === 0) return;
  
  const count = selectedIds.value.size;
  const result = await dialog.warning({
    title: 'Vorlagen löschen',
    content: `Möchten Sie wirklich ${count} ${count === 1 ? 'Vorlage' : 'Vorlagen'} löschen? Diese Aktion kann nicht rückgängig gemacht werden.`,
    positiveText: 'Löschen',
    negativeText: 'Abbrechen',
    positiveButtonProps: { type: 'error' }
  });
  
  if (result === 'positive') {
    const idsToDelete = Array.from(selectedIds.value);
    try {
      await Promise.all(idsToDelete.map(id => deleteMutation.mutateAsync(id)));
      nMessage?.success(`${count} ${count === 1 ? 'Vorlage' : 'Vorlagen'} gelöscht`);
      selectedIds.value.clear();
      refetch();
    } catch (e: any) {
      nMessage?.error('Löschen fehlgeschlagen');
    }
  }
}
</script>

<style scoped>
</style>

