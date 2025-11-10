<template>
  <div class="space-y-4">
    <n-collapse :default-expanded-names="['creator', 'type', 'date']">
      <n-collapse-item name="creator" title="Ersteller">
        <div class="space-y-2">
          <div v-for="c in creators" :key="c.id">
            <n-checkbox :value="c.name" v-model:checked="checkedCreators[c.name]">{{ c.name }}</n-checkbox>
          </div>
        </div>
      </n-collapse-item>
      <n-collapse-item name="type" title="Vorlagenart">
        <n-checkbox-group v-model:value="local.type">
          <div class="grid grid-cols-1 gap-2">
            <n-checkbox v-for="t in types" :key="t" :value="t">{{ t }}</n-checkbox>
          </div>
        </n-checkbox-group>
      </n-collapse-item>
      <n-collapse-item name="date" title="Erstellungsdatum">
        <div class="space-y-2">
          <n-date-picker
            v-model:value="dateRange"
            type="daterange"
            clearable
            value-format="yyyy-MM-dd"
            placeholder="Von - Bis"
          />
        </div>
      </n-collapse-item>
    </n-collapse>
    <div class="flex gap-2">
      <n-button quaternary @click="reset">Alle auswählen</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Filters für Vorlagenliste: Ersteller, Vorlagenart, Erstellungsdatum.
 */
import { ref, reactive, watch, onMounted } from 'vue';
import { NButton, NCheckbox, NCheckboxGroup, NCollapse, NCollapseItem, NDatePicker } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import type { TemplateType } from '@/lib/types';

const props = defineProps<{
  creators: Array<{ id: string; name: string }>;
  types: TemplateType[];
  selected: { query?: string; creator?: string[]; type?: string[]; createdAtFrom?: string; createdAtTo?: string };
}>();
const emit = defineEmits<{ (e:'apply', v:any):void; (e:'reset'):void }>();

const local = reactive({ 
  type: props.selected.type && props.selected.type.length > 0 
    ? [...props.selected.type] 
    : [...props.types] as string[] 
});

const checkedCreators = reactive<Record<string, boolean>>({});
const dateRange = ref<[number, number] | null>(null);

// Initialisiere Ersteller: Standardmäßig alle ausgewählt
function initializeCreators() {
  props.creators.forEach(c => {
    if (props.selected.creator && props.selected.creator.length > 0) {
      checkedCreators[c.name] = props.selected.creator.includes(c.name);
    } else {
      checkedCreators[c.name] = true; // Standardmäßig ausgewählt
    }
  });
}

// Initialisiere Datum
function initializeDate() {
  if (props.selected.createdAtFrom && props.selected.createdAtTo) {
    dateRange.value = [
      new Date(props.selected.createdAtFrom).getTime(),
      new Date(props.selected.createdAtTo).getTime()
    ];
  } else {
    dateRange.value = null;
  }
}

// Watch für props.selected
watch(() => props.selected, () => {
  local.type = props.selected.type && props.selected.type.length > 0 
    ? [...props.selected.type] 
    : [...props.types];
  initializeCreators();
  initializeDate();
}, { deep: true });

// Automatische Filteranwendung mit Debounce
const emitFilters = useDebounceFn(() => {
  const creator = Object.keys(checkedCreators).filter(k => checkedCreators[k]);
  const type = local.type;
  let createdAtFrom: string | undefined;
  let createdAtTo: string | undefined;
  
  if (dateRange.value) {
    createdAtFrom = new Date(dateRange.value[0]).toISOString().split('T')[0];
    createdAtTo = new Date(dateRange.value[1]).toISOString().split('T')[0];
  }
  
  emit('apply', { creator, type, createdAtFrom, createdAtTo });
}, 300);

// Watch für automatische Filteranwendung bei Änderungen
watch(() => local.type, () => {
  emitFilters();
}, { deep: true });

watch(checkedCreators, () => {
  emitFilters();
}, { deep: true });

watch(dateRange, () => {
  emitFilters();
});

// Initialisiere beim Mounten
onMounted(() => {
  initializeCreators();
  initializeDate();
  setTimeout(() => {
    emitFilters();
  }, 200);
});

function reset() {
  local.type = [...props.types];
  props.creators.forEach(c => {
    checkedCreators[c.name] = true;
  });
  dateRange.value = null;
  emitFilters();
}
</script>

<style scoped>
</style>

