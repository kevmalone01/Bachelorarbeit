<template>
  <div class="h-full card-wrapper">
    <n-card size="small" class="equal-card flex flex-col hover:shadow-lg transition-all duration-200" @click="onView" :segmented="{ content: true, footer: true }">
      <template #header>
        <div class="flex items-center gap-3 pb-2">
          <input type="checkbox" class="mt-0.5" :checked="selected" @click.stop="toggleSelect" aria-label="Auswählen" />
          <component :is="iconComp" class="w-5 h-5 text-[#0077B6]" />
          <h3 class="font-semibold text-base flex-1">{{ title }}</h3>
          <span 
            class="type-badge"
            :class="item.type === 'Gewerbe' ? 'type-badge-company' : 'type-badge-person'"
            :style="item.type === 'Gewerbe' ? { backgroundColor: '#6ee7b7', color: '#065f46' } : { backgroundColor: '#93c5fd', color: '#1e40af' }"
          >
            {{ item.type }}
          </span>
        </div>
      </template>

      <div class="space-y-2.5 text-sm flex-grow min-h-0 py-1">
        <div v-if="metaVisibility.companyName && item.companyName" class="text-slate-700">
          <span class="font-semibold text-slate-600">Firma:</span> {{ item.companyName }}
        </div>
        <div v-if="metaVisibility.address" class="text-slate-700">
          <span class="font-semibold text-slate-600">Adresse:</span> {{ item.street }}, {{ item.zip }} {{ item.city }}
        </div>
        <div v-if="metaVisibility.advisor && item.advisorName" class="text-slate-700">
          <span class="font-semibold text-slate-600">Berater:</span> {{ item.advisorName }}
        </div>
        <div v-if="metaVisibility.legalForm && item.legalForm" class="text-slate-700">
          <span class="font-semibold text-slate-600">Rechtsform:</span> <n-tag size="small">{{ item.legalForm }}</n-tag>
        </div>
        <div v-if="metaVisibility.createdAt" class="text-slate-500 text-xs pt-1">
          Erstellt: {{ new Date(item.createdAt).toLocaleDateString() }}
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2 mt-auto pt-2 border-t border-gray-200">
          <n-button size="small" quaternary @click.stop="onView"><Eye class="w-4 h-4 mr-1" /> Ansehen</n-button>
          <n-button size="small" type="error" class="delete-button" @click.stop="$emit('delete', item.id)"><Trash2 class="w-4 h-4 mr-1" /> Löschen</n-button>
        </div>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
/**
 * ClientCard - einzelne Mandantenkarte mit Meta-Infos.
 */
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NCard, NTag } from 'naive-ui';
import type { ClientItem } from '@/lib/types';
import { User, Building2, Eye, Trash2 } from 'lucide-vue-next';

const props = defineProps<{
  item: ClientItem;
  metaVisibility: Record<string, boolean>;
  selected?: boolean;
}>();
const emit = defineEmits<{ (e:'delete', id:string): void; (e:'toggle-select'): void }>();

const router = useRouter();
const title = computed(() => props.item.companyName || `${props.item.firstName || ''} ${props.item.lastName || ''}`.trim());
const iconComp = computed(() => props.item.type === 'Gewerbe' ? Building2 : User);

function onView() { 
  router.push(`/clients/${props.item.id}`);
}
function toggleSelect() { emit('toggle-select'); }
</script>

<style scoped>
.card-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 3px; /* Platz für den äußeren Rahmen */
  border: 2px solid #e5e7eb !important; /* Grauer Rahmen */
  border-radius: 10px !important;
  background: #f9fafb; /* Sehr hellgrauer Hintergrund */
  transition: all 0.2s ease;
  min-height: 286px; /* Höhe der Karte (280px) + Padding (6px) */
}

.card-wrapper:hover {
  border-color: #d1d5db !important; /* Etwas dunklerer Grau beim Hover */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

/* Fixe Kartenhöhe für einheitliche Grids (alle Karten gleich hoch) */
.equal-card {
  height: 280px !important; /* fixe Gesamthöhe der Karte - ausreichend für Unternehmenskarten */
  min-height: 280px !important;
  max-height: 280px !important;
  border: 2px solid #0077B6 !important; /* Blauer Rahmen */
  border-radius: 8px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  background: white !important;
}

.equal-card:hover {
  border-color: #005a8a !important; /* Dunklerer Blau beim Hover */
  box-shadow: 0 4px 12px rgba(0, 119, 182, 0.15) !important;
}

:deep(.n-card) {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  border: none !important; /* Entferne Standard-Border */
}

:deep(.n-card-header) {
  padding: 12px 16px !important;
  border-bottom: 1px solid #e5e7eb !important;
  background: white !important;
  overflow: visible !important;
}

:deep(.n-card-body) {
  flex: 1 1 auto !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  padding: 12px 16px !important;
  background: white !important;
}

:deep(.n-card__content) {
  flex: 1 1 auto !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  overflow: hidden; /* verhindert Höhenwachstum durch zusätzliche Zeilen */
  padding: 12px 16px !important;
  background: white !important;
}

:deep(.n-card__footer) {
  margin-top: auto !important;
  flex-shrink: 0 !important;
  padding: 12px 16px !important;
  background: #f9fafb !important; /* Hellgrauer Footer-Hintergrund */
  border-top: 1px solid #e5e7eb !important;
}

.type-badge {
  display: inline-block !important;
  flex-shrink: 0 !important;
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  line-height: 1.5 !important;
  padding: 4px 12px !important;
  border-radius: 4px !important;
  white-space: nowrap !important;
  min-width: fit-content !important;
}

.type-badge-person {
  background-color: #93c5fd !important; /* Blasseres Blau */
  color: #1e40af !important; /* Dunkelblaue Schrift */
}

.type-badge-company {
  background-color: #6ee7b7 !important; /* Blasseres Grün */
  color: #065f46 !important; /* Dunkelgrüne Schrift */
}

.delete-button {
  background-color: #FF5454 !important; /* Rot */
  color: white !important;
  border: none !important;
}

.delete-button:hover {
  background-color: #e63939 !important; /* Dunkleres Rot beim Hover */
}

:deep(.delete-button .n-button__content) {
  color: white !important;
}
</style>

