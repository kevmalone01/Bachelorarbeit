<template>
  <div class="space-y-4">
    <n-collapse :default-expanded-names="['type','advisor','legalForm']">
      <n-collapse-item name="type" title="Clients">
        <n-checkbox-group v-model:value="local.type">
          <div class="grid grid-cols-1 gap-2">
            <n-checkbox value="Natürliche Person">Natürliche Person</n-checkbox>
            <n-checkbox value="Gewerbe">Gewerbe</n-checkbox>
          </div>
        </n-checkbox-group>
      </n-collapse-item>
      <n-collapse-item name="advisor" title="Berater">
        <div class="space-y-2">
          <div v-for="a in visibleAdvisors" :key="a.id">
            <n-checkbox :value="a.id" v-model:checked="checkedAdvisors[a.id]">{{ a.name }}</n-checkbox>
          </div>
          <button v-if="advisors.length>6" class="text-sm text-blue-600" @click="toggleAdvisors">
            {{ showAllAdvisors ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
          </button>
        </div>
      </n-collapse-item>
      <n-collapse-item name="legalForm" title="Rechtsform">
        <div class="space-y-2">
          <div v-for="(lf, idx) in availableLegalForms" :key="lf">
            <n-checkbox :value="lf" v-model:checked="checkedLegal[lf]">{{ lf }}</n-checkbox>
          </div>
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
 * Filters für Mandantenliste: Typ, Berater, Rechtsform.
 */
import { computed, reactive, watch, onMounted } from 'vue';
import { NButton, NCheckbox, NCheckboxGroup, NCollapse, NCollapseItem } from 'naive-ui';
import { useDebounceFn } from '@vueuse/core';
import type { Advisor, LegalForm } from '@/lib/types';

const props = defineProps<{
  advisors: Advisor[];
  legalForms: LegalForm[];
  clients?: Array<{ legalForm?: string }>; // Clients-Daten für Filterung
  selected: { query?: string; type?: string[]; advisorId?: string[]; legalForm?: string[] };
}>();
const emit = defineEmits<{ (e:'apply', v:any):void; (e:'reset'):void }>();

// Initialisiere Filter: Standardmäßig alles ausgewählt, außer wenn URL-Parameter vorhanden sind
const local = reactive({ 
  type: props.selected.type && props.selected.type.length > 0 
    ? [...props.selected.type] 
    : ['Natürliche Person', 'Gewerbe'] as string[] 
});

const checkedAdvisors = reactive<Record<string, boolean>>({});
const checkedLegal = reactive<Record<string, boolean>>({});

// Initialisiere Berater: Standardmäßig alle ausgewählt
function initializeAdvisors() {
  props.advisors.forEach(a => {
    if (props.selected.advisorId && props.selected.advisorId.length > 0) {
      checkedAdvisors[a.id] = props.selected.advisorId.includes(a.id);
    } else {
      checkedAdvisors[a.id] = true; // Standardmäßig ausgewählt
    }
  });
}

// Initialisiere Rechtsformen: Standardmäßig alle ausgewählt
function initializeLegalForms() {
  availableLegalForms.value.forEach(lf => {
    if (props.selected.legalForm && props.selected.legalForm.length > 0) {
      checkedLegal[lf] = props.selected.legalForm.includes(lf);
    } else {
      checkedLegal[lf] = true; // Standardmäßig ausgewählt
    }
  });
}

// Watch für props.selected.type
watch(() => props.selected.type, (v) => {
  local.type = v && v.length > 0 ? [...v] : ['Natürliche Person', 'Gewerbe'];
});

const showAllAdvisors = reactive({ v:false });
const visibleAdvisors = computed(() => showAllAdvisors.v ? props.advisors : props.advisors.slice(0,6));
function toggleAdvisors(){ showAllAdvisors.v=!showAllAdvisors.v; }

// Nur Rechtsformen anzeigen, die in den Clients vorkommen
const availableLegalForms = computed(() => {
  // Wenn keine Clients übergeben wurden, zeige alle Rechtsformen
  if (!props.clients || props.clients.length === 0) {
    return props.legalForms;
  }
  
  // Sammle alle vorhandenen Rechtsformen direkt aus den Clients
  const existingLegalForms = new Set<string>();
  props.clients.forEach(client => {
    if (client && client.legalForm && typeof client.legalForm === 'string' && client.legalForm.trim()) {
      existingLegalForms.add(client.legalForm.trim());
    }
  });
  
  // Wenn keine Rechtsformen gefunden wurden, zeige alle (Fallback)
  if (existingLegalForms.size === 0) {
    return props.legalForms;
  }
  
  // Konvertiere zu Array und sortiere
  const formsArray = Array.from(existingLegalForms).sort();
  
  // Erstelle ein Mapping von kurzen zu langen Formen
  const formMapping: Record<string, string> = {
    'GmbH': 'Gesellschaft mit beschränkter Haftung (GmbH)',
    'UG': 'Unternehmergesellschaft (UG)',
    'AG': 'Aktiengesellschaft (AG)',
    'GmbH & Co. KG': 'GmbH & Co. KG',
    'KG': 'Kommanditgesellschaft (KG)',
    'OHG': 'Offene Handelsgesellschaft (OHG)',
    'PartG': 'Partnerschaftsgesellschaft (PartG)',
    'Einzelunternehmen': 'Einzelunternehmen',
    'GbR': 'Gesellschaft bürgerlichen Rechts (GbR)',
    'Stiftung': 'Stiftung'
  };
  
  // Versuche, die extrahierten Formen mit der legalForms-Liste zu matchen
  const matched = formsArray.map(extracted => {
    // 1. Exakte Übereinstimmung
    const exact = props.legalForms.find(lf => lf === extracted);
    if (exact) return exact;
    
    // 2. Verwende Mapping falls vorhanden
    const mapped = formMapping[extracted];
    if (mapped && props.legalForms.includes(mapped)) {
      return mapped;
    }
    
    // 3. Suche nach Übereinstimmung in Klammern am Ende (z.B. "(GmbH)")
    const bracketMatch = props.legalForms.find(lf => {
      const match = lf.match(/\(([^)]+)\)$/);
      return match && match[1] === extracted;
    });
    if (bracketMatch) return bracketMatch;
    
    // 4. Suche nach Übereinstimmung im Text
    const containsMatch = props.legalForms.find(lf => lf.includes(extracted));
    if (containsMatch) return containsMatch;
    
    // 5. Falls keine Übereinstimmung, verwende die extrahierte Form direkt
    return extracted;
  });
  
  // Entferne Duplikate
  return Array.from(new Set(matched));
});

// Automatische Filteranwendung mit Debounce
const emitFilters = useDebounceFn(() => {
  const advisorId = Object.keys(checkedAdvisors).filter(k => checkedAdvisors[k]);
  const legalForm = Object.keys(checkedLegal).filter(k => checkedLegal[k]);
  // Stelle sicher, dass type ein Array ist und nicht leer
  const type = Array.isArray(local.type) && local.type.length > 0 
    ? local.type 
    : ['Natürliche Person', 'Gewerbe'];
  emit('apply', { type, advisorId, legalForm });
}, 300);

// Watch für automatische Filteranwendung bei Änderungen
watch(() => local.type, () => {
  emitFilters();
}, { deep: true });

watch(checkedAdvisors, () => {
  emitFilters();
}, { deep: true });

watch(checkedLegal, () => {
  emitFilters();
}, { deep: true });

// Watch für availableLegalForms, um Rechtsformen zu initialisieren, wenn sie verfügbar werden
watch(availableLegalForms, () => {
  initializeLegalForms();
}, { immediate: true });

// Initialisiere beim Mounten
onMounted(() => {
  initializeAdvisors();
  initializeLegalForms();
  // Wende Filter automatisch an beim ersten Laden
  // Kurze Verzögerung, damit alle Initialisierungen abgeschlossen sind
  setTimeout(() => {
    emitFilters();
  }, 200);
});

function reset() {
  local.type = ['Natürliche Person', 'Gewerbe'];
  props.advisors.forEach(a => {
    checkedAdvisors[a.id] = true;
  });
  availableLegalForms.value.forEach(lf => {
    checkedLegal[lf] = true;
  });
  emitFilters(); // Automatisch anwenden
}
</script>

<style scoped>
</style>

