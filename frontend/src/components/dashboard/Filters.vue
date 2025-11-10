<template>
  <div class="space-y-4">
    <n-collapse :default-expanded-names="['status','user','template','deadline']">
      <n-collapse-item name="status" title="STATUS">
        <div class="grid grid-cols-1 gap-2">
          <n-checkbox-group v-model:value="local.status">
            <n-checkbox v-for="s in statusOptions" :key="s" :value="s">{{ s }}</n-checkbox>
          </n-checkbox-group>
        </div>
      </n-collapse-item>
      <n-collapse-item name="user" title="USER">
        <div class="space-y-2">
          <div v-for="(u, idx) in visibleUsers" :key="u.id">
            <n-checkbox :value="u.name" v-model:checked="checkedUsers[u.name]">{{ u.name }}</n-checkbox>
          </div>
          <button v-if="users.length > 6" class="text-sm text-blue-600" @click="toggleUsers">
            {{ showAllUsers ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
          </button>
        </div>
      </n-collapse-item>
      <n-collapse-item name="template" title="Template">
        <div class="space-y-2">
          <div v-for="(t, idx) in visibleTemplates" :key="t.id">
            <n-checkbox :value="t.name" v-model:checked="checkedTemplates[t.name]">{{ t.name }}</n-checkbox>
          </div>
          <button v-if="templates.length > 6" class="text-sm text-blue-600" @click="toggleTemplates">
            {{ showAllTemplates ? 'Weniger anzeigen' : 'Mehr anzeigen' }}
          </button>
        </div>
      </n-collapse-item>
      <n-collapse-item name="deadline" title="Deadline">
        <n-date-picker v-model:value="deadline" type="daterange" clearable :shortcuts="dateShortcuts" />
      </n-collapse-item>
    </n-collapse>
    <div class="flex gap-2">
      <n-button type="primary" @click="apply">Filter anwenden</n-button>
      <n-button quaternary @click="reset">Zurücksetzen</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Filters: Sidebar/Drawer Filtergruppen mit Mehrfachauswahl.
 */
import { computed, reactive, toRefs, watch } from 'vue';
import { NButton, NCheckbox, NCheckboxGroup, NCollapse, NCollapseItem, NDatePicker } from 'naive-ui';
import type { DocumentsQueryParams } from '@/lib/types';

const props = defineProps<{
  users: Array<{ id: string; name: string }>;
  templates: Array<{ id: string; name: string }>;
  selected: DocumentsQueryParams;
}>();
const emit = defineEmits<{
  (e: 'apply', v: DocumentsQueryParams): void;
  (e: 'reset'): void;
}>();

const local = reactive<DocumentsQueryParams>({
  query: props.selected.query || '',
  status: props.selected.status ? [...props.selected.status] : [],
  owner: props.selected.owner ? [...props.selected.owner] : [],
  template: props.selected.template ? [...props.selected.template] : [],
  deadlineFrom: props.selected.deadlineFrom,
  deadlineTo: props.selected.deadlineTo,
});

watch(() => props.selected, (v) => {
  Object.assign(local, {
    query: v.query || '',
    status: v.status ? [...v.status] : [],
    owner: v.owner ? [...v.owner] : [],
    template: v.template ? [...v.template] : [],
    deadlineFrom: v.deadlineFrom,
    deadlineTo: v.deadlineTo,
  });
}, { deep: true });

const statusOptions = ['Draft', 'To Be Reviewed', 'In Progress', 'Not Started', 'Finished'];

const checkedUsers = reactive<Record<string, boolean>>({});
const checkedTemplates = reactive<Record<string, boolean>>({});
props.selected.owner?.forEach((o) => checkedUsers[o] = true);
props.selected.template?.forEach((t) => checkedTemplates[t] = true);

const showAllUsers = reactive({ v: false });
const showAllTemplates = reactive({ v: false });
const visibleUsers = computed(() => showAllUsers.v ? props.users : props.users.slice(0,6));
const visibleTemplates = computed(() => showAllTemplates.v ? props.templates : props.templates.slice(0,6));
function toggleUsers(){ showAllUsers.v = !showAllUsers.v; }
function toggleTemplates(){ showAllTemplates.v = !showAllTemplates.v; }

const deadline = computed<[number, number] | null>({
  get() {
    if (local.deadlineFrom && local.deadlineTo) {
      return [Date.parse(local.deadlineFrom), Date.parse(local.deadlineTo)];
    }
    return null;
  },
  set(val) {
    if (val && Array.isArray(val) && val.length === 2) {
      local.deadlineFrom = new Date(val[0]).toISOString();
      local.deadlineTo = new Date(val[1]).toISOString();
    } else {
      local.deadlineFrom = undefined;
      local.deadlineTo = undefined;
    }
  }
});

const dateShortcuts = [
  { label: 'Heute', value: [Date.now(), Date.now()] as [number, number] },
  { label: '7 Tage', value: [Date.now(), Date.now() + 7*86400000] as [number, number] },
  { label: '30 Tage', value: [Date.now(), Date.now() + 30*86400000] as [number, number] },
];

function apply() {
  local.owner = Object.keys(checkedUsers).filter(k => checkedUsers[k]);
  local.template = Object.keys(checkedTemplates).filter(k => checkedTemplates[k]);
  emit('apply', { ...local });
}
function reset() {
  Object.assign(local, {
    query: '',
    status: [],
    owner: [],
    template: [],
    deadlineFrom: undefined,
    deadlineTo: undefined,
  });
  Object.keys(checkedUsers).forEach(k => checkedUsers[k] = false);
  Object.keys(checkedTemplates).forEach(k => checkedTemplates[k] = false);
  emit('reset');
}
</script>

<style scoped>
</style>

