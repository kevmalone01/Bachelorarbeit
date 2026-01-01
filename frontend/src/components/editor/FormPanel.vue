<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-lg font-semibold">Formular</h3>
      <n-button size="small" quaternary @click="handleReset">
        Alle zurücksetzen
      </n-button>
    </div>
    
    <div v-if="placeholders.length === 0" class="text-center py-8 text-slate-500">
      <p>Keine Platzhalter vorhanden.</p>
      <p class="text-sm mt-2">Gehen Sie zu EINSTELLUNGEN um Platzhalter zu erkennen.</p>
    </div>
    
    <n-form v-else :model="fillValues" label-placement="top" class="space-y-4">
      <n-form-item
        v-for="placeholder in placeholders"
        :key="placeholder.key"
        :label="placeholder.label || placeholder.key"
        :required="placeholder.required"
      >
        <!-- Text Input -->
        <n-input
          v-if="placeholder.type === 'text'"
          :value="fillValues[placeholder.key]"
          :placeholder="`Geben Sie ${placeholder.label || placeholder.key} ein`"
          @update:value="(v) => {
            console.log('[FormPanel] Text input update for key:', placeholder.key, 'value:', v, 'current fillValues:', fillValues[placeholder.key]);
            handleValueChange(placeholder.key, v);
          }"
        />
        
        <!-- Multiline Input -->
        <n-input
          v-else-if="placeholder.type === 'multiline'"
          :value="fillValues[placeholder.key]"
          type="textarea"
          :rows="4"
          :placeholder="`Geben Sie ${placeholder.label || placeholder.key} ein`"
          @update:value="(v) => handleValueChange(placeholder.key, v)"
        />
        
        <!-- Number Input -->
        <n-input-number
          v-else-if="placeholder.type === 'number'"
          :value="fillValues[placeholder.key] !== undefined && fillValues[placeholder.key] !== null ? Number(fillValues[placeholder.key]) : undefined"
          :placeholder="`Geben Sie ${placeholder.label || placeholder.key} ein`"
          @update:value="(v) => {
            console.log('[FormPanel] Number input update for key:', placeholder.key, 'value:', v, 'type:', typeof v, 'current fillValues:', fillValues[placeholder.key]);
            handleValueChange(placeholder.key, v);
          }"
        />
        
        <!-- Date Picker -->
        <n-date-picker
          v-else-if="placeholder.type === 'date'"
          :value="fillValues[placeholder.key]"
          type="date"
          value-format="yyyy-MM-dd"
          clearable
          @update:value="(v) => {
            console.log('[FormPanel] Date input update for key:', placeholder.key, 'value:', v, 'type:', typeof v);
            // Format date value to yyyy-MM-dd if it's a timestamp or Date object
            let formattedValue = v;
            if (v) {
              if (typeof v === 'number') {
                // Timestamp - convert to yyyy-MM-dd
                const date = new Date(v);
                formattedValue = date.toISOString().split('T')[0];
                console.log('[FormPanel] Converted timestamp to date string:', formattedValue);
              } else if (v instanceof Date) {
                // Date object - convert to yyyy-MM-dd
                formattedValue = v.toISOString().split('T')[0];
                console.log('[FormPanel] Converted Date object to date string:', formattedValue);
              } else if (typeof v === 'string' && !/^\d{4}-\d{2}-\d{2}$/.test(v)) {
                // String that's not in yyyy-MM-dd format - try to parse and format
                const date = new Date(v);
                if (!isNaN(date.getTime())) {
                  formattedValue = date.toISOString().split('T')[0];
                  console.log('[FormPanel] Converted date string to yyyy-MM-dd:', formattedValue);
                }
              }
            }
            handleValueChange(placeholder.key, formattedValue);
          }"
        />
        
        <!-- Dropdown Select -->
        <n-select
          v-else-if="placeholder.type === 'dropdown'"
          v-model:value="fillValues[placeholder.key]"
          :options="getDropdownOptions(placeholder)"
          :placeholder="`Wählen Sie ${placeholder.label || placeholder.key}`"
          @update:value="(v) => handleValueChange(placeholder.key, v)"
        />
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { NForm, NFormItem, NInput, NInputNumber, NDatePicker, NSelect, NButton } from 'naive-ui';
import type { Placeholder, FillValues } from '@/lib/types';

const props = defineProps<{
  placeholders: Placeholder[];
  fillValues: FillValues;
}>();

const emit = defineEmits<{
  (e: 'update:fillValues', v: FillValues): void;
  (e: 'reset'): void;
}>();

const fillValues = ref<FillValues>({ ...props.fillValues });

watch(() => props.fillValues, (newValues) => {
  console.log('[FormPanel] fillValues updated from props:', newValues);
  console.log('[FormPanel] Props fillValues keys:', Object.keys(newValues || {}));
  console.log('[FormPanel] Props fillValues values:', Object.entries(newValues || {}).map(([k, v]) => `${k}: ${v}`).join(', '));
  fillValues.value = { ...newValues };
  console.log('[FormPanel] fillValues after update:', fillValues.value);
  console.log('[FormPanel] Local fillValues keys:', Object.keys(fillValues.value || {}));
  console.log('[FormPanel] Local fillValues values:', Object.entries(fillValues.value || {}).map(([k, v]) => `${k}: ${v}`).join(', '));
  
  // Debug: Log all placeholder keys and their corresponding fillValues
  props.placeholders.forEach((p: any) => {
    const key = p.key || p.name;
    const value = fillValues.value[key];
    console.log(`[FormPanel] Placeholder key: "${key}", fillValue:`, value, 'type:', typeof value);
  });
}, { deep: true, immediate: true });

function handleValueChange(key: string, value: any) {
  const updated = { ...fillValues.value, [key]: value };
  fillValues.value = updated;
  emit('update:fillValues', updated);
}

function handleReset() {
  emit('reset');
}

function getDropdownOptions(placeholder: Placeholder) {
  // If placeholder has options from DB field mapping, use those
  // Otherwise return empty array (should be configured in settings)
  return [];
}
</script>

<style scoped>
</style>

