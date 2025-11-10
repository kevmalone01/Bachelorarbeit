<template>
  <div class="flex flex-wrap items-center gap-3">
    <n-button quaternary @click="$emit('toggle-filter')">
      <Filter class="w-4 h-4 mr-1" /> Filter
    </n-button>
    <n-input
      :value="query"
      @update:value="onInput"
      placeholder="Suchen…"
      class="w-full max-w-md"
    >
      <template #prefix>
        <Search class="w-4 h-4 text-slate-500" />
      </template>
    </n-input>

    <n-dropdown 
      trigger="click" 
      :options="dropdownOptions" 
      :key="JSON.stringify(columnVisibility)"
      @select="onToggleColumn"
    >
      <n-button quaternary circle>
        <template #icon>
          <Settings class="w-4 h-4" />
        </template>
      </n-button>
    </n-dropdown>

    <div class="ml-auto flex items-center gap-2">
      <n-button type="primary" @click="$emit('create-document')">Create Document</n-button>
      <n-button @click="$emit('open-ai')"><Sparkles class="w-4 h-4 mr-1" /> AI-Agent</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Toolbar: Suche mit Debounce, Spalten-Picker, Action-Buttons.
 */
import { computed } from 'vue';
import { NButton, NDropdown, NInput } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import { Search, Filter, Sparkles, Settings } from 'lucide-vue-next';

const props = defineProps<{
  query: string;
  columnVisibility: Record<string, boolean>;
}>();
const emit = defineEmits<{
  (e: 'update:query', v: string): void;
  (e: 'update:column-visibility', v: Record<string, boolean>): void;
  (e: 'toggle-filter'): void;
  (e: 'create-document'): void;
  (e: 'open-ai'): void;
}>();

const onInput = useDebounceFn((v: string) => emit('update:query', v), 300);

const dropdownOptions = computed(() => {
  const map: Array<[key: string, label: string]> = [
    ['modified','Modified'],
    ['name','Document Name'],
    ['status','Status'],
    ['owner','Owner'],
    ['mandant','Mandant'],
    ['deadline','Deadline'],
    ['actions','Actions'],
  ];
  return map.map(([key, label]) => ({
    key,
    label: `${props.columnVisibility[key] !== false ? '✓ ' : ''}${label}`,
  }));
});

function onToggleColumn(key: string) {
  const current = props.columnVisibility[key];
  // In DocumentsTable wird `columnVisibility[key] !== false` verwendet
  // Das bedeutet: true oder undefined = sichtbar, false = versteckt
  // Wenn aktuell sichtbar (true oder undefined), dann verstecken (false)
  // Wenn aktuell versteckt (false), dann anzeigen (true)
  const isVisible = current !== false;
  const next = { ...props.columnVisibility, [key]: isVisible ? false : true };
  emit('update:column-visibility', next);
}
</script>

<style scoped>
</style>

