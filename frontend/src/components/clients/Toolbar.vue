<template>
  <div class="flex flex-wrap items-center gap-3">
    <n-button quaternary @click="$emit('toggle-filter')">
      <Filter class="w-4 h-4 mr-1" /> Filter
    </n-button>
    <n-input :value="query" @update:value="onInput" placeholder="Suchen…" class="w-full max-w-md">
      <template #prefix>
        <Search class="w-4 h-4 text-slate-500" />
      </template>
    </n-input>

    <n-button quaternary @click="$emit('toggle-select-all')">
      {{ allSelected ? 'Alle abwählen' : 'Alle auswählen' }}
    </n-button>

    <div class="ml-auto flex items-center gap-2">
      <n-dropdown v-if="selectedCount>0" trigger="click" :options="bulkOptions" @select="onBulk">
        <n-button>Bulk</n-button>
      </n-dropdown>
      <n-button type="primary" @click="$emit('create')"><Plus class="w-4 h-4 mr-1" /> Create new Client</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Toolbar: Suche, Spaltenpicker (Karten-Metadaten), Create, optionale Bulk-Aktionen.
 */
import { NButton, NDropdown, NInput } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import { Search, Filter, Plus } from 'lucide-vue-next';

const props = defineProps<{
  query: string;
  metaVisibility: Record<string, boolean>;
  selectedCount: number;
  allSelected: boolean;
}>();
const emit = defineEmits<{
  (e:'toggle-filter'): void;
  (e:'update:query', v:string): void;
  (e:'update:meta-visibility', v:Record<string, boolean>): void;
  (e:'create'): void;
  (e:'bulk-delete'): void;
  (e:'toggle-select-all'): void;
}>();

const onInput = useDebounceFn((v: string) => emit('update:query', v), 300);

const bulkOptions = [
  { key: 'delete', label: 'Löschen' },
];
function onBulk(key: string) {
  if (key === 'delete') emit('bulk-delete');
}
</script>

<style scoped>
</style>

