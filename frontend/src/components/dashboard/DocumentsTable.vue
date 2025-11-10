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
                  :aria-label="`Sortiere nach ${col.label}`"
                >
                  <GripVertical class="w-4 h-4 text-slate-400 cursor-move" />
                  {{ col.label }}
                  <ArrowUpDown class="w-3.5 h-3.5 text-slate-500" />
                </button>
              </div>
              <div
                class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-blue-500 bg-transparent"
                @mousedown="startResize($event, col.id)"
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
          <tr v-else-if="documents.length === 0">
            <td class="px-3 py-6 text-slate-600" :colspan="visibleColCount + 1">
              Keine Dokumente gefunden.
              <n-button type="primary" class="ml-2" @click="$emit('create')">Create Document</n-button>
            </td>
          </tr>
          <tr v-for="row in documents" :key="row.id" class="odd:bg-slate-50">
            <td class="px-3 py-2 border-b">
              <input type="checkbox" v-model="selected[row.id]" :aria-label="`Auswählen ${row.name}`" />
            </td>
            <td 
              v-for="col in orderedColumns" 
              :key="col.id"
              class="px-3 py-2 border-b overflow-hidden text-ellipsis"
              :style="{ width: columnWidths[col.id] + 'px' }"
            >
              <template v-if="col.id === 'modified'">
                {{ formatDate(row.modified) }}
              </template>
              <template v-else-if="col.id === 'name'">
                {{ row.name }}
              </template>
              <template v-else-if="col.id === 'status'">
                <n-badge :type="statusType(row.status)" :value="row.status" />
              </template>
              <template v-else-if="col.id === 'owner'">
                {{ row.owner }}
              </template>
              <template v-else-if="col.id === 'mandant'">
                {{ row.mandant || '—' }}
              </template>
              <template v-else-if="col.id === 'deadline'">
                {{ row.deadline ? formatDate(row.deadline) : '—' }}
              </template>
              <template v-else-if="col.id === 'actions'">
                <div class="flex gap-2">
                  <n-button size="small" @click="$emit('edit', row)"><Pencil class="w-3.5 h-3.5 mr-1" /> Edit</n-button>
                  <n-button size="small" @click="$emit('download', row)"><Download class="w-3.5 h-3.5 mr-1" /> Download</n-button>
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
</template>

<script setup lang="ts">
/**
 * DocumentsTable: Tabelle mit Checkboxen, Sortierung, Sticky Header, Paginierung, Resize und Drag & Drop.
 */
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue';
import { NBadge, NButton } from 'naive-ui';
import type { DocumentItem } from '@/lib/types';
import { ArrowUpDown, Pencil, Download, GripVertical } from 'lucide-vue-next';
import { useTablePrefsStore } from '@/stores/tablePrefs';

const props = defineProps<{
  documents: DocumentItem[];
  loading: boolean;
  error: boolean;
  page: number;
  pageSize: number;
  total: number;
  columnVisibility: Record<string, boolean>;
  sorting: { id: string; desc: boolean } | null;
}>();
const emit = defineEmits<{
  (e: 'update:page', v: number): void;
  (e: 'update:page-size', v: number): void;
  (e: 'update:sorting', v: { id: string; desc: boolean } | null): void;
  (e: 'edit', row: DocumentItem): void;
  (e: 'download', row: DocumentItem): void;
  (e: 'create'): void;
}>();

const prefs = useTablePrefsStore();

const allColumns = [
  { id: 'modified', label: 'Modified' },
  { id: 'name', label: 'Document Name' },
  { id: 'status', label: 'Status' },
  { id: 'owner', label: 'Owner' },
  { id: 'mandant', label: 'Mandant' },
  { id: 'deadline', label: 'Deadline' },
  { id: 'actions', label: 'Actions' },
];

// Spalten-Reihenfolge und -Breiten aus Store
const columnOrder = computed(() => prefs.columnOrder);
const columnWidths = computed(() => prefs.columnWidths);

// Gefilterte und sortierte Spalten
const orderedColumns = computed(() => {
  const visible = allColumns.filter(c => props.columnVisibility[c.id] !== false);
  // Sortiere nach gespeicherter Reihenfolge
  const orderMap = new Map(columnOrder.value.map((id, idx) => [id, idx]));
  return visible.sort((a, b) => {
    const aIdx = orderMap.get(a.id) ?? 999;
    const bIdx = orderMap.get(b.id) ?? 999;
    return aIdx - bIdx;
  });
});

const visibleColCount = computed(() => orderedColumns.value.length);

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / (props.pageSize || 20))));

const selected = reactive<Record<string, boolean>>({});
const allSelected = computed(() => props.documents.length > 0 && props.documents.every(d => selected[d.id]));
function toggleAll(ev: Event) {
  const checked = (ev.target as HTMLInputElement).checked;
  props.documents.forEach(d => selected[d.id] = checked);
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
    prefs.setColumnWidth(resizingColumnId, newWidth);
    prefs.setColumnWidth(adjacentColumnId, adjacentNewWidth);
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
    
    prefs.setColumnWidth(resizingColumnId, newWidth);
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
  draggedColumnId = columnId;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', columnId);
  }
  (e.target as HTMLElement).style.opacity = '0.5';
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
  
  const currentOrder = [...columnOrder.value];
  const draggedIndex = currentOrder.indexOf(draggedColumnId);
  const targetIndex = currentOrder.indexOf(columnId);
  
  if (draggedIndex !== -1 && targetIndex !== -1 && draggedIndex !== targetIndex) {
    // Entferne die gezogene Spalte zuerst
    currentOrder.splice(draggedIndex, 1);
    // Berechne die neue Position
    // Wenn nach rechts verschoben (draggedIndex < targetIndex), ist targetIndex jetzt um 1 reduziert
    // Wenn nach links verschoben (draggedIndex > targetIndex), bleibt targetIndex gleich
    const newIndex = draggedIndex < targetIndex ? targetIndex : targetIndex;
    // Füge sie an der neuen Position ein
    currentOrder.splice(newIndex, 0, draggedColumnId);
    prefs.setColumnOrder(currentOrder);
  }
  
  dragOverColumnId = null;
}

function onDragEnd(e: DragEvent) {
  (e.target as HTMLElement).style.opacity = '1';
  draggedColumnId = null;
  dragOverColumnId = null;
}

function statusType(status: DocumentItem['status']) {
  switch (status) {
    case 'Draft': return 'default';
    case 'To Be Reviewed': return 'warning';
    case 'In Progress': return 'info';
    case 'Not Started': return 'tertiary';
    case 'Finished': return 'success';
    default: return 'default';
  }
}
function formatDate(iso?: string) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString();
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
