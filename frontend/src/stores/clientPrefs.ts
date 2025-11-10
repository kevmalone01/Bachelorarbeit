import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export interface ClientPrefsState {
  visibleMeta: Record<string, boolean>;
  pageSize: number;
}

export const useClientPrefsStore = defineStore('clientPrefs', {
  state: (): ClientPrefsState => ({
    visibleMeta: useStorage<Record<string, boolean>>('clients.visibleMeta', {
      companyName: true,
      address: true,
      advisor: true,
      legalForm: true,
      createdAt: false
    }),
    pageSize: useStorage<number>('clients.pageSize', 12) as unknown as number,
  }),
  actions: {
    setMetaVisible(key: string, visible: boolean) {
      this.visibleMeta[key] = visible;
    },
    setPageSize(size: number) {
      this.pageSize = size;
    }
  }
});


