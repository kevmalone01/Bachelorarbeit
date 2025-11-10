<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header mit Zurück-Button -->
      <div class="mb-6 flex items-center gap-4">
        <n-button quaternary @click="router.push('/clients')">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Zurück zur Übersicht
        </n-button>
        <div class="flex-1"></div>
        <n-button type="error" @click="handleDelete">
          <Trash2 class="w-4 h-4 mr-2" />
          Löschen
        </n-button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex justify-center py-20">
        <n-spin size="large" />
      </div>

      <!-- Error -->
      <n-alert v-else-if="isError" type="error" title="Fehler">
        Mandant konnte nicht geladen werden.
      </n-alert>

      <!-- Content -->
      <div v-else-if="client" class="space-y-6">
        <!-- Basis-Informationen -->
        <n-card title="Basis-Informationen" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Typ</label>
              <div class="mt-1">
                <n-tag :type="client.type === 'Gewerbe' ? 'success' : 'info'" size="medium">
                  {{ client.type }}
                </n-tag>
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Berater</label>
              <p class="mt-1 text-gray-900">{{ client.advisorName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Mandatsmanager</label>
              <p class="mt-1 text-gray-900">{{ client.mandateManager || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Mandatsverantwortlicher</label>
              <p class="mt-1 text-gray-900">{{ client.mandateResponsible || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Erstellt am</label>
              <p class="mt-1 text-gray-900">{{ formatDate(client.createdAt) }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Zuletzt aktualisiert</label>
              <p class="mt-1 text-gray-900">{{ formatDate(client.updatedAt) }}</p>
            </div>
          </div>
        </n-card>

        <!-- Personendaten (Natürliche Person) -->
        <n-card v-if="client.type === 'Natürliche Person'" title="Personendaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Anrede</label>
              <p class="mt-1 text-gray-900">{{ client.salutation || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Titel</label>
              <p class="mt-1 text-gray-900">{{ client.title || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Vorname</label>
              <p class="mt-1 text-gray-900 font-semibold">{{ client.firstName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nachname</label>
              <p class="mt-1 text-gray-900 font-semibold">{{ client.lastName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Geburtsdatum</label>
              <p class="mt-1 text-gray-900">{{ formatDate(client.birthDate) }}</p>
            </div>
          </div>
        </n-card>

        <!-- Firmendaten (Unternehmen) -->
        <n-card v-if="client.type === 'Gewerbe'" title="Firmendaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Firma</label>
              <p class="mt-1 text-gray-900 font-semibold text-lg">{{ client.companyName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Rechtsform</label>
              <div class="mt-1">
                <n-tag size="medium" v-if="client.legalForm">{{ client.legalForm }}</n-tag>
                <span v-else class="text-gray-500">-</span>
              </div>
            </div>
          </div>
        </n-card>

        <!-- Adresse -->
        <n-card title="Adresse" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">Straße</label>
              <p class="mt-1 text-gray-900">{{ client.street || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nr.</label>
              <p class="mt-1 text-gray-900">{{ client.number || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">PLZ</label>
              <p class="mt-1 text-gray-900">{{ client.zip || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Ort</label>
              <p class="mt-1 text-gray-900">{{ client.city || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Kontakt & Steuerdaten -->
        <n-card title="Kontakt & Steuerdaten" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">E-Mail</label>
              <p class="mt-1 text-gray-900">{{ client.email || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Steuernummer</label>
              <p class="mt-1 text-gray-900">{{ client.taxNumber || '-' }}</p>
            </div>
            <div v-if="client.type === 'Natürliche Person'">
              <label class="text-sm font-medium text-gray-600">Steuer-ID</label>
              <p class="mt-1 text-gray-900">{{ client.taxId || '-' }}</p>
            </div>
            <div v-if="client.type === 'Gewerbe'">
              <label class="text-sm font-medium text-gray-600">UST-ID</label>
              <p class="mt-1 text-gray-900">{{ client.vatId || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Finanzgericht</label>
              <p class="mt-1 text-gray-900">{{ client.taxCourt || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Finanzamt -->
        <n-card v-if="client.taxOffice" title="Finanzamt" class="shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="text-sm font-medium text-gray-600">PLZ</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.zip || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Ort</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.city || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Straße</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.street || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nr.</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.number || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">E-Mail</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.email || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Fax</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.fax || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Anrede Ansprechpartner</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.contactSalutation || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Nachname Ansprechpartner</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.contactLastName || '-' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-600">Telefon Ansprechpartner</label>
              <p class="mt-1 text-gray-900">{{ client.taxOffice.contactPhone || '-' }}</p>
            </div>
          </div>
        </n-card>

        <!-- Beteiligte (nur für Unternehmen) -->
        <n-card v-if="client.type === 'Gewerbe' && client.participants && client.participants.length > 0" title="Beteiligte" class="shadow-sm">
          <div class="space-y-4">
            <div v-for="participant in client.participants" :key="participant.id" class="border-b pb-4 last:border-0">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label class="text-sm font-medium text-gray-600">Name</label>
                  <p class="mt-1 text-gray-900 font-semibold">{{ participant.firstName }} {{ participant.lastName }}</p>
                </div>
                <div>
                  <label class="text-sm font-medium text-gray-600">Rolle</label>
                  <div class="mt-1">
                    <n-tag type="info" size="medium">{{ participant.role }}</n-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!client.participants || client.participants.length === 0" class="text-gray-500 text-sm py-4">
            Keine Beteiligten vorhanden.
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ClientDetail - Detailansicht für einen einzelnen Mandanten mit allen Feldern.
 */
import { computed, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { NButton, NCard, NTag, NSpin, NAlert, createDiscreteApi } from 'naive-ui';
import { ArrowLeft, Trash2 } from 'lucide-vue-next';
import { clientsApi } from '@/lib/api';
import type { ClientItem } from '@/lib/types';

const route = useRoute();
const router = useRouter();
const { message, dialog } = createDiscreteApi(['message', 'dialog']);
const queryClient = useQueryClient();

const clientId = computed(() => route.params.id as string);

// Client laden
const { data: client, isLoading, isError } = useQuery({
  queryKey: ['client', clientId.value],
  queryFn: () => clientsApi.getClient(clientId.value),
  enabled: !!clientId.value
});

// Löschen
const deleteMutation = useMutation({
  mutationFn: (id: string) => clientsApi.deleteClient(id),
  onSuccess: () => {
    message.success('Mandant gelöscht');
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    router.push('/clients');
  },
  onError: () => {
    message.error('Fehler beim Löschen');
  }
});

function handleDelete() {
  if (!client.value) return;
  dialog.warning({
    title: 'Mandant löschen',
    content: `Möchten Sie den Mandanten "${client.value.companyName || (client.value.firstName + ' ' + client.value.lastName)}" wirklich löschen?`,
    positiveText: 'Löschen',
    negativeText: 'Abbrechen',
    onPositiveClick: () => deleteMutation.mutate(client.value!.id)
  });
}

function formatDate(iso?: string): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}
</script>

<style scoped>
</style>
