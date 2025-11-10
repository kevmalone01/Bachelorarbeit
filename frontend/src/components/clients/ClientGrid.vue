<template>
  <div class="space-y-4">
    <div v-if="loading" class="flex justify-center py-10">
      <n-spin size="large" />
    </div>
    <div v-else-if="error">
      <n-empty description="Fehler beim Laden" />
    </div>
    <div v-else>
      <template v-if="items.length">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
          <ClientCard
            v-for="item in items"
            :key="item.id"
            :item="item"
            :meta-visibility="metaVisibility"
            :selected="selectedIds.has(item.id)"
            @view="$emit('view', item)"
            @delete="$emit('delete', item.id)"
            @toggle-select="toggle(item.id)"
          />
        </div>
      </template>
      <n-empty v-else description="Keine Mandanten gefunden">
        <template #extra>
          <n-button type="primary" @click="$emit('create')">Create new Client</n-button>
        </template>
      </n-empty>
    </div>

    <div class="flex justify-end items-center gap-3 py-2">
      <label class="text-sm text-slate-600">Pro Seite</label>
      <select class="border rounded px-2 py-1" :value="pageSize" @change="$emit('update:page-size', +($event.target as HTMLSelectElement).value)">
        <option :value="12">12</option>
        <option :value="24">24</option>
        <option :value="48">48</option>
      </select>
      <n-pagination :page="page" :page-size="pageSize" :item-count="total" @update:page="$emit('update:page', $event)" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ClientGrid - Grid und Paginierung für Mandantenkarten.
 */
import { NButton, NEmpty, NPagination, NSpin } from 'naive-ui';
import type { ClientItem } from '@/lib/types';
import ClientCard from './ClientCard.vue';

const props = defineProps<{
  items: ClientItem[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  total: number;
  metaVisibility: Record<string, boolean>;
  selectedIds: Set<string>;
}>();
const emit = defineEmits<{
  (e:'update:page', v:number): void;
  (e:'update:page-size', v:number): void;
  (e:'view', item: ClientItem): void;
  (e:'delete', id: string): void;
  (e:'create'): void;
  (e:'update:selected-ids', v:Set<string>): void;
}>();

function toggle(id: string) {
  const next = new Set(props.selectedIds);
  if (next.has(id)) next.delete(id); else next.add(id);
  emit('update:selected-ids', next);
}
</script>

<style scoped>
.grid > * {
  display: flex;
  height: 100%;
}

.grid {
  align-items: stretch;
}
</style>

