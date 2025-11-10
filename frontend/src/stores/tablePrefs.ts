import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export interface TablePrefsState {
  visibleColumns: Record<string, boolean>;
  pageSize: number;
  columnWidths: Record<string, number>;
  columnOrder: string[];
  // Template-spezifische Einstellungen
  templateVisibleColumns: Record<string, boolean>;
  templateColumnWidths: Record<string, number>;
  templateColumnOrder: string[];
}

const defaultColumnOrder = ['modified', 'name', 'status', 'owner', 'mandant', 'deadline', 'actions'];
const defaultColumnWidths: Record<string, number> = {
  modified: 120,
  name: 200,
  status: 120,
  owner: 150,
  mandant: 150,
  deadline: 120,
  actions: 180,
};

const defaultTemplateColumnOrder = ['title', 'createdAt', 'creator', 'type', 'history', 'actions'];
const defaultTemplateColumnWidths: Record<string, number> = {
  createdAt: 150,
  creator: 150,
  title: 300,
  type: 150,
  history: 150,
  actions: 180,
};

export const useTablePrefsStore = defineStore('tablePrefs', {
  state: (): TablePrefsState => ({
    visibleColumns: useStorage<Record<string, boolean>>('docs.visibleColumns', {
      select: true,
      modified: true,
      name: true,
      status: true,
      owner: true,
      mandant: true,
      deadline: true,
      actions: true,
    }),
    pageSize: useStorage<number>('docs.pageSize', 20) as unknown as number,
    columnWidths: useStorage<Record<string, number>>('docs.columnWidths', defaultColumnWidths),
    columnOrder: useStorage<string[]>('docs.columnOrder', defaultColumnOrder),
    templateVisibleColumns: useStorage<Record<string, boolean>>('templates.visibleColumns', {
      createdAt: true,
      creator: true,
      title: true,
      type: true,
      history: true,
      actions: true,
    }),
    templateColumnWidths: useStorage<Record<string, number>>('templates.columnWidths', defaultTemplateColumnWidths),
    templateColumnOrder: useStorage<string[]>('templates.columnOrder', defaultTemplateColumnOrder),
  }),
  actions: {
    setColumnVisible(key: string, visible: boolean) {
      this.visibleColumns[key] = visible;
    },
    setPageSize(size: number) {
      this.pageSize = size;
    },
    setColumnWidth(key: string, width: number) {
      this.columnWidths[key] = width;
    },
    setColumnOrder(order: string[]) {
      this.columnOrder = order;
    },
    setTemplateColumnVisible(key: string, visible: boolean) {
      this.templateVisibleColumns[key] = visible;
    },
    setTemplateColumnWidth(key: string, width: number) {
      this.templateColumnWidths[key] = width;
    },
    setTemplateColumnOrder(order: string[]) {
      this.templateColumnOrder = order;
    }
  }
});


