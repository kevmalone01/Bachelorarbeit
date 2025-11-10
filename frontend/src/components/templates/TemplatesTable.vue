<template>
  <div ref="tableContainer" class="w-full overflow-auto">
    <div class="min-w-[1000px]">
      <table class="w-full border-separate border-spacing-0" style="table-layout: fixed;">
        <thead class="sticky top-0 bg-white z-10">
          <tr class="text-left">
            <th class="px-3 py-2 border-b" style="width: 50px;">
              <input type="checkbox" :checked="allSelected" @change="toggleAll" aria-label="Alle auswählen" />
            </th>
            <th 
              v-for="col in orderedColumns" 
              :key="col.id" 
              class="px-3 py-2 border-b select-none relative"
              :style="{ width: columnWidths[col.id] + 'px', minWidth: minColumnWidths[col.id] + 'px' }"
              :draggable="true"
              @dragstart="onDragStart($event, col.id)"
              @dragover.prevent="onDragOver($event, col.id)"
              @drop="onDrop($event, col.id)"
              @dragend="onDragEnd"
            >
              <div class="flex items-center gap-1">
                <div v-if="col.id === 'actions'" class="inline-flex items-center gap-1 flex-1">
                  <GripVertical class="w-4 h-4 text-slate-400 cursor-move" />
                  {{ col.label }}
                </div>
                <button 
                  v-else
                  class="inline-flex items-center gap-1 flex-1" 
                  @click="toggleSort(col.id)" 
                  @mousedown.stop
                  :aria-label="`Sortiere nach ${col.label}`"
                >
                  <GripVertical class="w-4 h-4 text-slate-400 cursor-move" />
                  {{ col.label }}
                  <ArrowUpDown class="w-3.5 h-3.5 text-slate-500" />
                </button>
              </div>
              <div
                class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-blue-500 bg-transparent"
                @mousedown.stop="startResize($event, col.id)"
              ></div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td class="px-3 py-4 text-slate-500" :colspan="visibleColCount + 1">Lade…</td>
          </tr>
          <tr v-else-if="error">
            <td class="px-3 py-4 text-red-600" :colspan="visibleColCount + 1">Fehler beim Laden</td>
          </tr>
          <tr v-else-if="templates.length === 0">
            <td class="px-3 py-6 text-slate-600" :colspan="visibleColCount + 1">
              Keine Vorlagen gefunden.
              <n-button type="primary" class="ml-2" @click="$emit('create')">Create Template</n-button>
            </td>
          </tr>
          <tr v-for="row in templates" :key="row.id" class="odd:bg-slate-50">
            <td class="px-3 py-2 border-b">
              <input type="checkbox" :checked="selected[row.id]" @change="toggleSelect(row.id)" :aria-label="`Auswählen ${row.title}`" />
            </td>
            <td 
              v-for="col in orderedColumns" 
              :key="col.id"
              class="px-3 py-2 border-b overflow-hidden text-ellipsis"
              :style="{ width: columnWidths[col.id] + 'px' }"
            >
              <template v-if="col.id === 'createdAt'">
                {{ formatDate(row.createdAt) }}
              </template>
              <template v-else-if="col.id === 'creator'">
                {{ row.creator }}
              </template>
              <template v-else-if="col.id === 'title'">
                {{ row.title }}
              </template>
              <template v-else-if="col.id === 'history'">
                <n-button size="small" quaternary @click="showHistory(row)">
                  {{ row.history.length }} {{ row.history.length === 1 ? 'Änderung' : 'Änderungen' }}
                </n-button>
              </template>
              <template v-else-if="col.id === 'type'">
                <n-tag size="small">{{ row.type }}</n-tag>
              </template>
              <template v-else-if="col.id === 'actions'">
                <div class="flex gap-2">
                  <n-button size="small" @click="$emit('edit', row)">
                    <Pencil class="w-3.5 h-3.5 mr-1" /> Edit
                  </n-button>
                  <n-button size="small" @click="$emit('download', row)">
                    <Download class="w-3.5 h-3.5 mr-1" /> Download
                  </n-button>
                </div>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex justify-end items-center gap-3 py-3">
      <label class="text-sm text-slate-600">Pro Seite</label>
      <select class="border rounded px-2 py-1" :value="pageSize" @change="$emit('update:page-size', +($event.target as HTMLSelectElement).value)">
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
      </select>
      <div class="text-sm text-slate-600">
        Seite {{ page }} / {{ totalPages }}
      </div>
      <n-button size="small" :disabled="page<=1" @click="$emit('update:page', page-1)">Zurück</n-button>
      <n-button size="small" :disabled="page>=totalPages" @click="$emit('update:page', page+1)">Weiter</n-button>
    </div>
  </div>

  <!-- History Modal -->
  <n-modal v-model:show="showHistoryModal" :mask-closable="true">
    <n-card v-if="selectedTemplate" title="Änderungshistorie" :bordered="false" size="large" class="max-w-2xl mx-auto">
      <template #header-extra>
        <n-button quaternary circle @click="showHistoryModal = false">
          <template #icon>
            <span class="text-xl">×</span>
          </template>
        </n-button>
      </template>
      <div class="space-y-3">
        <div v-for="item in selectedTemplate.history" :key="item.id" class="border-l-2 border-blue-500 pl-4 py-2">
          <div class="flex items-center justify-between mb-1">
            <span class="font-semibold">{{ item.user }}</span>
            <span class="text-sm text-slate-500">{{ formatDate(item.date) }}</span>
          </div>
          <p class="text-sm text-slate-600">{{ item.change }}</p>
        </div>
        <div v-if="selectedTemplate.history.length === 0" class="text-slate-500 text-center py-4">
          Keine Änderungshistorie vorhanden.
        </div>
      </div>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
/**
 * TemplatesTable: Tabelle mit Checkboxen, Sortierung, Sticky Header, Paginierung, Resize und Drag & Drop.
 */
import { computed, reactive, ref, onUnmounted } from 'vue';
import { NBadge, NButton, NCard, NModal, NTag } from 'naive-ui';
import type { TemplateItem } from '@/lib/types';
import { ArrowUpDown, GripVertical, Pencil, Download } from 'lucide-vue-next';
import { useTablePrefsStore } from '@/stores/tablePrefs';

const props = defineProps<{
  templates: TemplateItem[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  total: number;
  columnVisibility: Record<string, boolean>;
  sorting: { id: string; desc: boolean } | null;
  selectedIds?: Set<string>;
}>();
const emit = defineEmits<{
  (e: 'update:page', v: number): void;
  (e: 'update:page-size', v: number): void;
  (e: 'update:sorting', v: { id: string; desc: boolean } | null): void;
  (e: 'create'): void;
  (e: 'edit', row: TemplateItem): void;
  (e: 'download', row: TemplateItem): void;
  (e: 'update:selected-ids', v: Set<string>): void;
}>();

const prefs = useTablePrefsStore();

const allColumns = [
  { id: 'createdAt', label: 'Erstellungsdatum' },
  { id: 'creator', label: 'Ersteller' },
  { id: 'title', label: 'Vorlagenname' },
  { id: 'type', label: 'Vorlagenart' },
  { id: 'history', label: 'Änderungshistorie' },
  { id: 'actions', label: 'Actions' },
];

// Spalten-Reihenfolge und -Breiten aus Store (separate Keys für Templates)
const columnOrder = computed(() => prefs.templateColumnOrder);
const columnWidths = computed(() => prefs.templateColumnWidths);

// Gefilterte und sortierte Spalten
const orderedColumns = computed(() => {
  const visible = allColumns.filter(c => props.columnVisibility[c.id] !== false);
  // Stelle sicher, dass alle sichtbaren Spalten in der Reihenfolge sind
  const currentOrder = [...columnOrder.value];
  const visibleIds = visible.map(c => c.id);
  const missingIds = visibleIds.filter(id => !currentOrder.includes(id));
  // Füge fehlende Spalten am Ende hinzu
  const completeOrder = [...currentOrder, ...missingIds];
  
  // Sortiere nach gespeicherter Reihenfolge
  const orderMap = new Map(completeOrder.map((id, idx) => [id, idx]));
  return visible.sort((a, b) => {
    const aIdx = orderMap.get(a.id) ?? 999;
    const bIdx = orderMap.get(b.id) ?? 999;
    return aIdx - bIdx;
  });
});

const visibleColCount = computed(() => orderedColumns.value.length);

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / (props.pageSize || 20))));

const selected = computed(() => {
  const result: Record<string, boolean> = {};
  props.templates.forEach(t => {
    result[t.id] = props.selectedIds?.has(t.id) || false;
  });
  return result;
});

const allSelected = computed(() => props.templates.length > 0 && props.templates.every(t => props.selectedIds?.has(t.id)));

function toggleAll(ev: Event) {
  const checked = (ev.target as HTMLInputElement).checked;
  const newSet = new Set(props.selectedIds || []);
  if (checked) {
    props.templates.forEach(t => newSet.add(t.id));
  } else {
    props.templates.forEach(t => newSet.delete(t.id));
  }
  emit('update:selected-ids', newSet);
}

function toggleSelect(templateId: string) {
  const newSet = new Set(props.selectedIds || []);
  if (newSet.has(templateId)) {
    newSet.delete(templateId);
  } else {
    newSet.add(templateId);
  }
  emit('update:selected-ids', newSet);
}

// History Modal
const showHistoryModal = ref(false);
const selectedTemplate = ref<TemplateItem | null>(null);

function showHistory(template: TemplateItem) {
  selectedTemplate.value = template;
  showHistoryModal.value = true;
}

// Resize-Funktionalität
const tableContainer = ref<HTMLElement | null>(null);
let isResizing = false;
let resizingColumnId: string | null = null;
let startX = 0;
let startWidth = 0;
let adjacentColumnId: string | null = null;
let adjacentStartWidth = 0;

// Berechne verfügbare Breite für Spalten (Container-Breite minus Checkbox-Spalte)
const availableWidth = computed(() => {
  if (!tableContainer.value) return 1000; // Fallback
  return tableContainer.value.clientWidth - 50; // 50px für Checkbox-Spalte
});

// Berechne aktuelle Gesamtbreite aller sichtbaren Spalten
const totalColumnWidth = computed(() => {
  return orderedColumns.value.reduce((sum, col) => {
    return sum + (columnWidths.value[col.id] || 120);
  }, 0);
});

// Berechne Mindestbreite basierend auf Überschrift
function getMinColumnWidth(columnId: string, label: string): number {
  // Verwende Canvas, um die Textbreite zu messen
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  if (!context) return 100; // Fallback
  
  // Verwende eine ähnliche Schriftart wie in der Tabelle
  context.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
  
  // Messe die Textbreite
  const textWidth = context.measureText(label).width;
  
  // Füge Padding für Icons und Spacing hinzu
  // GripVertical (16px) + ArrowUpDown (14px) + Padding (24px) = ~54px
  // Für Actions-Spalte: nur GripVertical + Padding = ~40px
  const iconWidth = columnId === 'actions' ? 40 : 54;
  
  return Math.ceil(textWidth + iconWidth + 20); // +20px für zusätzliches Padding
}

// Berechne Mindestbreiten für alle Spalten
const minColumnWidths = computed(() => {
  const mins: Record<string, number> = {};
  allColumns.forEach(col => {
    mins[col.id] = getMinColumnWidth(col.id, col.label);
  });
  return mins;
});

function startResize(e: MouseEvent, columnId: string) {
  e.preventDefault();
  e.stopPropagation();
  isResizing = true;
  resizingColumnId = columnId;
  startX = e.clientX;
  startWidth = columnWidths.value[columnId] || 120;
  
  // Finde die benachbarte Spalte (rechts)
  const currentIndex = orderedColumns.value.findIndex(col => col.id === columnId);
  const nextColumn = currentIndex >= 0 && currentIndex < orderedColumns.value.length - 1
    ? orderedColumns.value[currentIndex + 1]
    : null;
  
  // Speichere die benachbarte Spalte und ihre Startbreite
  if (nextColumn) {
    adjacentColumnId = nextColumn.id;
    adjacentStartWidth = columnWidths.value[nextColumn.id] || 120;
  } else {
    adjacentColumnId = null;
    adjacentStartWidth = 0;
  }
  
  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
}

function onResize(e: MouseEvent) {
  if (!isResizing || !resizingColumnId) return;
  const delta = e.clientX - startX;
  const requestedWidth = startWidth + delta;
  
  // Mindestbreite basierend auf Überschrift
  const minWidth = minColumnWidths.value[resizingColumnId] || 100;
  let newWidth = Math.max(minWidth, requestedWidth);
  
  if (adjacentColumnId) {
    // Berechne die Differenz
    const widthDiff = newWidth - startWidth;
    const adjacentMinWidth = minColumnWidths.value[adjacentColumnId] || 100;
    
    // Passe die benachbarte Spalte an
    let adjacentNewWidth = adjacentStartWidth - widthDiff;
    
    // Stelle sicher, dass die benachbarte Spalte nicht unter ihre Mindestbreite fällt
    if (adjacentNewWidth < adjacentMinWidth) {
      adjacentNewWidth = adjacentMinWidth;
      // Passe die aktuelle Spalte entsprechend an
      newWidth = startWidth + (adjacentStartWidth - adjacentMinWidth);
      newWidth = Math.max(minWidth, newWidth);
    }
    
    // Aktualisiere beide Spalten
    prefs.setTemplateColumnWidth(resizingColumnId, newWidth);
    prefs.setTemplateColumnWidth(adjacentColumnId, adjacentNewWidth);
  } else {
    // Wenn es keine benachbarte Spalte gibt (letzte Spalte), verhalte dich wie vorher
    // Berechne die neue Gesamtbreite
    const currentTotal = totalColumnWidth.value;
    const currentWidth = columnWidths.value[resizingColumnId] || 120;
    const newTotal = currentTotal - currentWidth + newWidth;
    
    // Wenn die neue Gesamtbreite die verfügbare Breite überschreitet, begrenze die Spaltenbreite
    if (newTotal > availableWidth.value) {
      const maxAllowedWidth = availableWidth.value - (currentTotal - currentWidth);
      newWidth = Math.max(minWidth, Math.min(newWidth, maxAllowedWidth));
    }
    
    prefs.setTemplateColumnWidth(resizingColumnId, newWidth);
  }
}

function stopResize() {
  isResizing = false;
  resizingColumnId = null;
  adjacentColumnId = null;
  adjacentStartWidth = 0;
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
});

// Drag & Drop-Funktionalität
let draggedColumnId: string | null = null;
let dragOverColumnId: string | null = null;

function onDragStart(e: DragEvent, columnId: string) {
  // Verhindere Drag, wenn auf dem Resize-Handle geklickt wird
  const target = e.target as HTMLElement;
  if (target.closest('.cursor-col-resize')) {
    e.preventDefault();
    return;
  }
  
  draggedColumnId = columnId;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', columnId);
  }
  const th = target.closest('th');
  if (th) {
    th.style.opacity = '0.5';
  }
}

function onDragOver(e: DragEvent, columnId: string) {
  if (!draggedColumnId || draggedColumnId === columnId) return;
  e.preventDefault();
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move';
  }
  dragOverColumnId = columnId;
}

function onDrop(e: DragEvent, columnId: string) {
  e.preventDefault();
  if (!draggedColumnId || draggedColumnId === columnId) return;
  
  // Verwende die aktuelle Reihenfolge der sichtbaren Spalten
  const currentVisibleOrder = orderedColumns.value.map(col => col.id);
  const draggedIndex = currentVisibleOrder.indexOf(draggedColumnId);
  const targetIndex = currentVisibleOrder.indexOf(columnId);
  
  if (draggedIndex !== -1 && targetIndex !== -1 && draggedIndex !== targetIndex) {
    // Entferne die gezogene Spalte zuerst
    currentVisibleOrder.splice(draggedIndex, 1);
    // Berechne die neue Position
    // Wenn nach rechts verschoben (draggedIndex < targetIndex), ist targetIndex jetzt um 1 reduziert
    // Wenn nach links verschoben (draggedIndex > targetIndex), bleibt targetIndex gleich
    const newIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
    // Füge sie an der neuen Position ein
    currentVisibleOrder.splice(newIndex, 0, draggedColumnId);
    
    // Stelle sicher, dass alle Spalten in der neuen Reihenfolge enthalten sind
    // Füge fehlende Spalten am Ende hinzu
    const allColumnIds = allColumns.map(col => col.id);
    const missingColumns = allColumnIds.filter(id => !currentVisibleOrder.includes(id));
    const newOrder = [...currentVisibleOrder, ...missingColumns];
    
    prefs.setTemplateColumnOrder(newOrder);
  }
  
  dragOverColumnId = null;
}

function onDragEnd(e: DragEvent) {
  (e.target as HTMLElement).style.opacity = '1';
  draggedColumnId = null;
  dragOverColumnId = null;
}

function formatDate(iso?: string) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function toggleSort(id: string) {
  if (!props.sorting || props.sorting.id !== id) {
    emit('update:sorting', { id, desc: false });
  } else if (!props.sorting.desc) {
    emit('update:sorting', { id, desc: true });
  } else {
    emit('update:sorting', null);
  }
}
</script>

<style scoped>
th[draggable="true"] {
  cursor: move;
}

th[draggable="true"]:hover {
  background-color: #f3f4f6;
}
</style>

