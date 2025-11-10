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
      <ClientFilters
        :advisors="advisors"
        :legal-forms="legalForms"
        :clients="allClients"
        :selected="filters"
        @apply="applyFilters"
        @reset="resetFilters"
      />
    </n-layout-sider>

    <n-layout>
      <div class="p-4">
        <ClientToolbar
          :query="filters.query || ''"
          :meta-visibility="visibleMeta"
          :selected-count="selectedIds.size"
          :all-selected="allSelected"
          @update:query="onQuery"
          @toggle-filter="isDesktop ? sidebarCollapsed = !sidebarCollapsed : showFilterDrawer = true"
          @update:meta-visibility="onUpdateMeta"
          @create="openCreate"
          @bulk-delete="bulkDelete"
          @toggle-select-all="toggleSelectAll"
        />
      </div>

      <div class="px-4 pb-4">
        <ClientGrid
          :loading="isLoading"
          :error="isError"
          :items="clients"
          :page="page"
          :page-size="pageSize"
          :total="total"
          :meta-visibility="visibleMeta"
          v-model:selected-ids="selectedIds"
          @update:page="(v:number)=>page=v"
          @update:page-size="onUpdatePageSize"
          @view="onView"
          @delete="onDelete"
        />
      </div>
    </n-layout>
  </n-layout>

  <!-- Mobile Filters -->
  <n-drawer v-model:show="showFilterDrawer" :width="320" placement="left">
    <n-drawer-content title="Filter">
      <ClientFilters
        :advisors="advisors"
        :legal-forms="legalForms"
        :clients="allClients"
        :selected="filters"
        @apply="(f)=>{ applyFilters(f); showFilterDrawer=false; }"
        @reset="resetFilters"
      />
    </n-drawer-content>
  </n-drawer>

  <!-- Create Modal -->
  <CreateClientModal v-model:show="showCreate" :advisors="advisors" :legal-forms="legalForms" @created="refetch" />
</template>

<script setup lang="ts">
/**
 * Clients.vue - Seite für Mandantenverwaltung mit Filter, Toolbar und Grid.
 */
import { computed, inject, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { useBreakpoints } from '@vueuse/core';
import { NDrawer, NDrawerContent, NLayout, NLayoutSider } from 'naive-ui';
import ClientFilters from '@/components/clients/Filters.vue';
import ClientToolbar from '@/components/clients/Toolbar.vue';
import ClientGrid from '@/components/clients/ClientGrid.vue';
import CreateClientModal from '@/components/clients/CreateClientModal.vue';
import { clientsApi } from '@/lib/api';
import type { ClientItem } from '@/lib/types';
import { useClientPrefsStore } from '@/stores/clientPrefs';

const nMessage = inject<any>('nMessage');
const router = useRouter();
const route = useRoute();
const prefs = useClientPrefsStore();

const showFilterDrawer = ref(false);
const showCreate = ref(false);
const sidebarCollapsed = ref(true); // Standardmäßig eingeklappt

const breakpoints = useBreakpoints({ lg: 1024 });
const isDesktop = breakpoints.greaterOrEqual('lg');

// Filters from URL
const filters = reactive<{ query?: string; type?: string[]; advisorId?: string[]; legalForm?: string[] }>({
  query: (route.query.q as string) || '',
  type: ([] as string[]).concat(route.query.type as any || []),
  advisorId: ([] as string[]).concat(route.query.advisorId as any || []),
  legalForm: ([] as string[]).concat(route.query.legalForm as any || []),
});

// Meta visibility
const visibleMeta = ref<Record<string, boolean>>({ ...prefs.visibleMeta });
watch(visibleMeta, (v) => {
  Object.entries(v).forEach(([k, val]) => prefs.setMetaVisible(k, val));
}, { deep: true });

// Pagination
const page = ref(Number(route.query.page || 1));
const pageSize = ref(Number(route.query.pageSize || prefs.pageSize || 12));

// Selection
const selectedIds = ref<Set<string>>(new Set());

// Sync URL
watch([filters, page, pageSize], () => {
  const q: any = {
    q: filters.query,
    type: filters.type,
    advisorId: filters.advisorId,
    legalForm: filters.legalForm,
    page: page.value,
    pageSize: pageSize.value,
  };
  Object.keys(q).forEach((k) => (q[k] === undefined || q[k] === '' || (Array.isArray(q[k]) && q[k].length === 0)) && delete q[k]);
  router.replace({ query: q });
}, { deep: true });

// Advisors + Legal forms
const { data: advisorsData } = useQuery({
  queryKey: ['advisors'],
  queryFn: () => clientsApi.getAdvisors(),
  staleTime: 60_000
});
const { data: legalFormsData } = useQuery({
  queryKey: ['legalForms'],
  queryFn: () => clientsApi.getLegalForms(),
  staleTime: 60_000
});
const advisors = computed(() => advisorsData.value ?? []);
const legalForms = computed(() => legalFormsData.value ?? []);

// Clients list (gefiltert und paginiert)
const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['clients', { ...filters, page: page.value, pageSize: pageSize.value }]),
  queryFn: () => clientsApi.getClients({
    query: filters.query,
    type: filters.type,
    advisorId: filters.advisorId,
    legalForm: filters.legalForm,
    page: page.value,
    pageSize: pageSize.value,
  }),
  keepPreviousData: true
});

const clients = computed<ClientItem[]>(() => data.value?.items ?? []);
const total = computed<number>(() => data.value?.total ?? 0);

// Prüfen, ob alle aktuell angezeigten Clients ausgewählt sind
const allSelected = computed(() => {
  if (clients.value.length === 0) return false;
  return clients.value.every(c => selectedIds.value.has(c.id));
});

// Alle Clients für Filterung (ohne Filter/Pagination, um verfügbare Rechtsformen zu bestimmen)
const { data: allClientsData } = useQuery({
  queryKey: ['clients-all'],
  queryFn: async () => {
    // Lade alle Clients ohne Filter
    const result = await clientsApi.getClients({ page: 1, pageSize: 10000 });
    return result;
  },
  staleTime: 60_000
});
const allClients = computed<ClientItem[]>(() => {
  const items = allClientsData.value?.items ?? [];
  return items;
});

function onQuery(v: string) { filters.query = v; page.value = 1; }
function onUpdateMeta(v: Record<string, boolean>) { visibleMeta.value = { ...v }; }
function onUpdatePageSize(v: number) { pageSize.value = v; prefs.setPageSize(v); }
function applyFilters(f: { query?: string; type?: string[]; advisorId?: string[]; legalForm?: string[] }) {
  Object.assign(filters, f); page.value = 1; refetch();
}
function resetFilters() {
  Object.assign(filters, { query: '', type: [], advisorId: [], legalForm: [] }); page.value = 1; refetch();
}
function onView(item: ClientItem) { router.push(`/clients/${item.id}`); }
async function onDelete(id: string) {
  await clientsApi.deleteClient(id); nMessage?.success('Mandant gelöscht'); refetch();
}
async function bulkDelete() {
  if (!selectedIds.value.size) return;
  for (const id of selectedIds.value) { await clientsApi.deleteClient(id); }
  selectedIds.value.clear();
  nMessage?.success('Auswahl gelöscht');
  refetch();
}
function toggleSelectAll() {
  if (allSelected.value) {
    // Alle abwählen: Entferne alle IDs der aktuell angezeigten Clients
    const currentIds = new Set(clients.value.map(c => c.id));
    const newSet = new Set(selectedIds.value);
    currentIds.forEach(id => newSet.delete(id));
    selectedIds.value = newSet;
  } else {
    // Alle auswählen: Füge alle IDs der aktuell angezeigten Clients hinzu
    const allIds = new Set(selectedIds.value);
    clients.value.forEach(c => allIds.add(c.id));
    selectedIds.value = allIds;
  }
}
function openCreate() { showCreate.value = true; }
</script>

<style scoped>
</style>

