<template>
  <div class="sticky top-0 z-50 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between w-full shadow-sm">
    <div class="flex items-center gap-3 flex-1">
      <n-input
        v-model:value="localName"
        placeholder="Template-Name"
        class="max-w-md"
        @blur="handleNameChange"
        @keyup.enter="handleNameChange"
      />
      <n-tag v-if="isDirty" type="warning" size="small">Ungespeichert</n-tag>
    </div>
    
    <div class="flex items-center gap-2">
      <n-dropdown trigger="click" :options="exportOptions" @select="handleExport">
        <n-button type="primary">
          <template #icon>
            <Download class="w-4 h-4" />
          </template>
          Export
        </n-button>
      </n-dropdown>
      
      <n-button type="primary" :loading="saving" @click="$emit('save')">
        <template #icon>
          <Save class="w-4 h-4" />
        </template>
        Speichern
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { NButton, NInput, NTag, NDropdown } from 'naive-ui';
import { Download, Save } from 'lucide-vue-next';

const props = defineProps<{
  templateName: string;
  isDirty: boolean;
  saving?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:templateName', v: string): void;
  (e: 'export', format: 'pdf' | 'docx'): void;
  (e: 'save'): void;
}>();

const localName = ref(props.templateName);

watch(() => props.templateName, (newName) => {
  localName.value = newName;
});

function handleNameChange() {
  emit('update:templateName', localName.value);
}

const exportOptions = [
  { label: 'Als PDF exportieren', key: 'pdf' },
  { label: 'Als DOCX exportieren', key: 'docx' },
];

function handleExport(key: string) {
  emit('export', key as 'pdf' | 'docx');
}
</script>

<style scoped>
</style>

