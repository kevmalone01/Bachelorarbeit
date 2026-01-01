<template>
  <n-drawer
    :show="show"
    @update:show="(v) => !v && $emit('close')"
    :width="600"
    placement="right"
    :mask-closable="false"
  >
    <n-drawer-content title="Vorschau" closable>
      <div class="space-y-4">
        <div class="prose max-w-none" v-html="mergedContent" />
      </div>
      
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-dropdown trigger="click" :options="exportOptions" @select="handleExport">
            <n-button type="primary">
              <template #icon>
                <Download class="w-4 h-4" />
              </template>
              Exportieren
            </n-button>
          </n-dropdown>
          <n-button @click="$emit('close')">Schließen</n-button>
        </div>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { NDrawer, NDrawerContent, NButton, NDropdown } from 'naive-ui';
import { Download } from 'lucide-vue-next';
import { mergeContent } from '@/composables/useDocumentPlaceholders';
import type { FillValues } from '@/lib/types';

const props = defineProps<{
  show: boolean;
  contentHtml: string;
  fillValues: FillValues;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'export', format: 'pdf' | 'docx'): void;
}>();

const mergedContent = computed(() => {
  return mergeContent(props.contentHtml, props.fillValues);
});

const exportOptions = [
  { label: 'Als PDF exportieren', key: 'pdf' },
  { label: 'Als DOCX exportieren', key: 'docx' },
];

function handleExport(key: string) {
  emit('export', key as 'pdf' | 'docx');
}
</script>

<style scoped>
:deep(.prose) {
  @apply text-slate-700;
}

:deep(.prose p) {
  @apply mb-4;
}

:deep(.prose h1) {
  @apply text-2xl font-bold mb-4;
}

:deep(.prose h2) {
  @apply text-xl font-bold mb-3;
}

:deep(.prose ul) {
  @apply list-disc pl-6 mb-4;
}

:deep(.prose ol) {
  @apply list-decimal pl-6 mb-4;
}
</style>

