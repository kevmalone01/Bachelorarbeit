<template>
  <div class="flex flex-col h-full min-h-0">
    <n-tabs
      v-model:value="localActiveTab"
      type="line"
      @update:value="onUpdate"
      class="border-b border-slate-200"
    >
      <n-tab name="settings">
        <span class="tab-label">Einstellungen</span>
      </n-tab>

      <n-tab name="form">
        <span class="tab-label">Formular</span>
      </n-tab>
    </n-tabs>

    <div class="flex-1 overflow-y-auto min-h-0">
      <slot :activeTab="localActiveTab" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { NTabs, NTab } from 'naive-ui';

const props = defineProps<{
  activeTab: 'settings' | 'form';
}>();

const emit = defineEmits<{
  (e: 'update:activeTab', v: 'settings' | 'form'): void;
}>();

const localActiveTab = ref<'settings' | 'form'>(props.activeTab);

watch(
  () => props.activeTab,
  (newVal) => {
    localActiveTab.value = newVal;
  }
);

function onUpdate(v: 'settings' | 'form') {
  localActiveTab.value = v;
  emit('update:activeTab', v);
}
</script>

<style scoped>
/* --------------------------------------------- */
/* TAB LABEL – jetzt GRÖSSER + FETT */
/* --------------------------------------------- */
.tab-label {
  font-size: 14px;          /* vorher 12px */
  font-weight: 600;         /* fett */
  color: #374151;           /* slate-700 */
}

/* Tabs-Gruppe zentrieren */
:deep(.n-tabs-nav-scroll-content) {
  display: flex;
  justify-content: center;
}

/* Tab-Padding */
:deep(.n-tabs-tab) {
  padding-left: 20px !important;
  padding-right: 20px !important;
}

/* globale Balken deaktivieren */
:deep(.n-tabs-bar) {
  background-color: transparent !important;
  height: 0 !important;
}

/* aktive Tab-Leiste */
:deep(.n-tabs-tab--active .n-tabs-tab__bar) {
  background-color: #1e40af !important;
  height: 2px !important;
  width: 100% !important;
  border-radius: 2px;
  transform: translateY(1px);
}

/* aktiver Tab Text */
:deep(.n-tabs-tab--active .tab-label) {
  color: #1e40af !important;
}

/* Hover */
:deep(.n-tabs-tab:hover .tab-label) {
  color: #1e40af !important;
}
</style>
