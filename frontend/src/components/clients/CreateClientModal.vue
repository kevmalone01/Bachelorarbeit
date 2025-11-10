<template>
  <n-modal
    v-model:show="showProxy"
    :mask-closable="false"
    :block-scroll="true"
    :style="{ maxWidth: '900px' }"
    :content-style="{ maxHeight: '80vh', overflowY: 'auto' }"
  >
    <n-card title="Neuer Mandant" :bordered="false" size="large" class="flex flex-col">
      <template #header-extra>
        <n-button quaternary circle @click="close">
          <template #icon>
            <span class="text-xl">×</span>
          </template>
        </n-button>
      </template>
      
      <div class="flex-1 pr-2">
        <n-form ref="formRef" :model="form" :rules="rules" label-placement="top" class="space-y-8">
          <!-- Basis-Informationen -->
          <div>
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Basis-Informationen</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item path="type" label="Typ *">
                <n-select v-model:value="form.type" :options="typeOptions" @update:value="onTypeChange" />
              </n-form-item>
              <n-form-item path="advisorId" label="Berater *">
                <n-select v-model:value="form.advisorId" :options="advisorOptions" filterable placeholder="Berater auswählen" />
              </n-form-item>
              <n-form-item path="mandateManager" label="Mandatsmanager">
                <n-input v-model:value="form.mandateManager" placeholder="Mandatsmanager" />
              </n-form-item>
              <n-form-item path="mandateResponsible" label="Mandatsverantwortlicher">
                <n-input v-model:value="form.mandateResponsible" placeholder="Mandatsverantwortlicher" />
              </n-form-item>
            </div>
          </div>

          <!-- Personendaten (Natürliche Person) -->
          <div v-if="form.type === 'Natürliche Person'">
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Personendaten</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item path="salutation" label="Anrede">
                <n-select v-model:value="form.salutation" :options="salutationOptions" clearable placeholder="Anrede" />
              </n-form-item>
              <n-form-item path="title" label="Titel">
                <n-input v-model:value="form.title" placeholder="z.B. Dr., Prof." />
              </n-form-item>
              <n-form-item path="firstName" label="Vorname *">
                <n-input v-model:value="form.firstName" placeholder="Vorname" />
              </n-form-item>
              <n-form-item path="lastName" label="Nachname *">
                <n-input v-model:value="form.lastName" placeholder="Nachname" />
              </n-form-item>
              <n-form-item path="birthDate" label="Geburtsdatum">
                <n-date-picker v-model:value="form.birthDate" type="date" value-format="yyyy-MM-dd" placeholder="Geburtsdatum" />
              </n-form-item>
            </div>
          </div>

          <!-- Firmendaten (Unternehmen) -->
          <div v-if="form.type === 'Gewerbe'">
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Firmendaten</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item path="companyName" label="Firma *">
                <n-input v-model:value="form.companyName" placeholder="Firmenname" />
              </n-form-item>
              <n-form-item path="legalForm" label="Rechtsform *">
                <n-select v-model:value="form.legalForm" :options="legalOptions" placeholder="Rechtsform auswählen" />
              </n-form-item>
            </div>
          </div>

          <!-- Adresse -->
          <div>
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Adresse</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item path="street" label="Straße">
                <n-input v-model:value="form.street" placeholder="Straße" />
              </n-form-item>
              <n-form-item path="number" label="Nr.">
                <n-input v-model:value="form.number" placeholder="Hausnummer" />
              </n-form-item>
              <n-form-item path="zip" label="PLZ">
                <n-input v-model:value="form.zip" placeholder="PLZ" />
              </n-form-item>
              <n-form-item path="city" label="Ort">
                <n-input v-model:value="form.city" placeholder="Ort" />
              </n-form-item>
            </div>
          </div>

          <!-- Kontakt & Steuerdaten -->
          <div>
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Kontakt & Steuerdaten</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item path="email" label="E-Mail">
                <n-input v-model:value="form.email" type="email" placeholder="email@example.com" />
              </n-form-item>
              <n-form-item path="taxNumber" label="Steuernummer">
                <n-input v-model:value="form.taxNumber" placeholder="Steuernummer" />
              </n-form-item>
              <n-form-item v-if="form.type === 'Natürliche Person'" path="taxId" label="Steuer-ID">
                <n-input v-model:value="form.taxId" placeholder="Steuer-ID" />
              </n-form-item>
              <n-form-item v-if="form.type === 'Gewerbe'" path="vatId" label="UST-ID">
                <n-input v-model:value="form.vatId" placeholder="UST-ID" />
              </n-form-item>
              <n-form-item path="taxCourt" label="Finanzgericht">
                <n-input v-model:value="form.taxCourt" placeholder="Finanzgericht" />
              </n-form-item>
            </div>
          </div>

          <!-- Finanzamt -->
          <div>
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Finanzamt</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <n-form-item label="PLZ">
                <n-input v-model:value="form.taxOfficeZip" placeholder="PLZ" />
              </n-form-item>
              <n-form-item label="Ort">
                <n-input v-model:value="form.taxOfficeCity" placeholder="Ort" />
              </n-form-item>
              <n-form-item label="Straße">
                <n-input v-model:value="form.taxOfficeStreet" placeholder="Straße" />
              </n-form-item>
              <n-form-item label="Nr.">
                <n-input v-model:value="form.taxOfficeNumber" placeholder="Hausnummer" />
              </n-form-item>
              <n-form-item label="E-Mail">
                <n-input v-model:value="form.taxOfficeEmail" type="email" placeholder="email@example.com" />
              </n-form-item>
              <n-form-item label="Fax">
                <n-input v-model:value="form.taxOfficeFax" placeholder="Fax" />
              </n-form-item>
              <n-form-item label="Anrede Ansprechpartner">
                <n-select v-model:value="form.taxOfficeContactSalutation" :options="salutationOptions" clearable placeholder="Anrede" />
              </n-form-item>
              <n-form-item label="Nachname Ansprechpartner">
                <n-input v-model:value="form.taxOfficeContactLastName" placeholder="Nachname" />
              </n-form-item>
              <n-form-item label="Telefon Ansprechpartner">
                <n-input v-model:value="form.taxOfficeContactPhone" placeholder="Telefon" />
              </n-form-item>
            </div>
          </div>

          <!-- Beteiligte (nur für Unternehmen) -->
          <div v-if="form.type === 'Gewerbe'">
            <h3 class="text-lg font-semibold mb-4 text-gray-800">Beteiligte</h3>
            <div class="space-y-4">
              <div v-for="(participant, idx) in form.participants" :key="idx" class="border rounded-lg p-4 bg-gray-50">
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-medium text-sm">Beteiligter {{ idx + 1 }}</h4>
                  <n-button size="small" quaternary type="error" @click="removeParticipant(idx)">
                    Entfernen
                  </n-button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <n-form-item :path="`participants.${idx}.firstName`" label="Vorname *">
                    <n-input v-model:value="participant.firstName" placeholder="Vorname" />
                  </n-form-item>
                  <n-form-item :path="`participants.${idx}.lastName`" label="Nachname *">
                    <n-input v-model:value="participant.lastName" placeholder="Nachname" />
                  </n-form-item>
                  <n-form-item :path="`participants.${idx}.role`" label="Rolle *">
                    <n-select 
                      v-model:value="participant.role" 
                      :options="getRoleOptions(form.legalForm)" 
                      placeholder="Rolle auswählen" 
                    />
                  </n-form-item>
                </div>
              </div>
              <n-button dashed block @click="addParticipant">
                + Beteiligten hinzufügen
              </n-button>
            </div>
          </div>
        </n-form>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <n-button @click="close">Abbrechen</n-button>
          <n-button type="primary" :loading="submitting" @click="submit">Anlegen</n-button>
        </div>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup lang="ts">
/**
 * CreateClientModal - Dialog zur Anlage eines Mandanten mit allen Feldern.
 */
import { computed, ref, watch } from 'vue';
import { NButton, NCard, NDatePicker, NForm, NFormItem, NInput, NModal, NSelect } from 'naive-ui';
import type { Advisor, LegalForm, ParticipantRole } from '@/lib/types';
import { clientsApi } from '@/lib/api';

const props = defineProps<{
  show: boolean;
  advisors: Advisor[];
  legalForms: LegalForm[];
}>();
const emit = defineEmits<{ (e:'update:show', v:boolean): void; (e:'created'): void }>();
const showProxy = computed({
  get: () => props.show,
  set: (v: boolean) => emit('update:show', v)
});

const formRef = ref<any>(null);
const submitting = ref(false);

const form = ref<any>({
  type: 'Natürliche Person',
  advisorId: '',
  mandateManager: '',
  mandateResponsible: '',
  // Personendaten
  salutation: '',
  title: '',
  firstName: '',
  lastName: '',
  birthDate: null,
  // Firmendaten
  companyName: '',
  legalForm: undefined,
  // Adresse
  street: '',
  number: '',
  zip: '',
  city: '',
  // Kontakt & Steuer
  email: '',
  taxNumber: '',
  taxId: '',
  vatId: '',
  taxCourt: '',
  // Finanzamt
  taxOfficeZip: '',
  taxOfficeCity: '',
  taxOfficeStreet: '',
  taxOfficeNumber: '',
  taxOfficeEmail: '',
  taxOfficeFax: '',
  taxOfficeContactSalutation: '',
  taxOfficeContactLastName: '',
  taxOfficeContactPhone: '',
  // Beteiligte
  participants: [] as Array<{ firstName: string; lastName: string; role: ParticipantRole | undefined }>
});

const typeOptions = [
  { label: 'Natürliche Person', value: 'Natürliche Person' },
  { label: 'Gewerbe', value: 'Gewerbe' },
];

const salutationOptions = [
  { label: 'Herr', value: 'Herr' },
  { label: 'Frau', value: 'Frau' },
  { label: 'Divers', value: 'Divers' },
];

const advisorOptions = computed(() => props.advisors.map(a => ({ label: a.name, value: a.id })));
const legalOptions = computed(() => props.legalForms.map(l => ({ label: l, value: l })));

// Rollen basierend auf Rechtsform
function getRoleOptions(legalForm?: string): Array<{ label: string; value: ParticipantRole }> {
  if (!legalForm) return [];
  
  const roleMap: Record<string, ParticipantRole[]> = {
    'Einzelunternehmen': ['Einzelunternehmer'],
    'Aktiengesellschaft (AG)': ['Aktionär', 'Vorstand'],
    'Gesellschaft bürgerlichen Rechts (GbR)': ['Gesellschafter', 'Geschäftsführender Gesellschafter'],
    'Gesellschaft mit beschränkter Haftung (GmbH)': ['Geschäftsführer', 'Gesellschafter', 'Geschäftsführender Gesellschafter'],
    'GmbH & Co. KG': ['Komplementär', 'Kommanditist'],
    'Kommanditgesellschaft (KG)': ['Komplementär', 'Kommanditist'],
    'Offene Handelsgesellschaft (OHG)': ['Gesellschafter'],
    'Partnerschaftsgesellschaft (PartG)': ['Partner', 'Geschäftsführender Partner'],
    'Unternehmergesellschaft (UG)': ['Gesellschafter', 'Geschäftsführender Gesellschafter'],
    'Stiftung': ['Vorstand', 'Stifter', 'Destinatär'],
  };
  
  const roles = roleMap[legalForm] || [];
  return roles.map(r => ({ label: r, value: r }));
}

function addParticipant() {
  form.value.participants.push({ firstName: '', lastName: '', role: undefined });
}

function removeParticipant(idx: number) {
  form.value.participants.splice(idx, 1);
}

function onTypeChange() {
  // Reset form when type changes
  if (form.value.type === 'Natürliche Person') {
    form.value.companyName = '';
    form.value.legalForm = undefined;
    form.value.vatId = '';
    form.value.participants = [];
  } else {
    form.value.firstName = '';
    form.value.lastName = '';
    form.value.salutation = '';
    form.value.title = '';
    form.value.birthDate = null;
    form.value.taxId = '';
  }
}

const rules = {
  type: { required: true, message: 'Bitte Typ wählen', trigger: 'change' },
  advisorId: { required: true, message: 'Bitte Berater auswählen', trigger: 'change' },
  firstName: {
    validator: (_: any, v: string) => form.value.type === 'Natürliche Person' ? !!v : true,
    message: 'Vorname erforderlich', trigger: 'blur'
  },
  lastName: {
    validator: (_: any, v: string) => form.value.type === 'Natürliche Person' ? !!v : true,
    message: 'Nachname erforderlich', trigger: 'blur'
  },
  companyName: {
    validator: (_: any, v: string) => form.value.type === 'Gewerbe' ? !!v : true,
    message: 'Unternehmensname erforderlich', trigger: 'blur'
  },
  legalForm: {
    validator: (_: any, v: string) => form.value.type === 'Gewerbe' ? !!v : true,
    message: 'Rechtsform erforderlich', trigger: 'change'
  },
};

function resetForm() {
  form.value = {
    type: 'Natürliche Person',
    advisorId: '',
    mandateManager: '',
    mandateResponsible: '',
    salutation: '',
    title: '',
    firstName: '',
    lastName: '',
    birthDate: null,
    companyName: '',
    legalForm: undefined,
    street: '',
    number: '',
    zip: '',
    city: '',
    email: '',
    taxNumber: '',
    taxId: '',
    vatId: '',
    taxCourt: '',
    taxOfficeZip: '',
    taxOfficeCity: '',
    taxOfficeStreet: '',
    taxOfficeNumber: '',
    taxOfficeEmail: '',
    taxOfficeFax: '',
    taxOfficeContactSalutation: '',
    taxOfficeContactLastName: '',
    taxOfficeContactPhone: '',
    participants: []
  };
}

function close() {
  resetForm();
  emit('update:show', false);
}

async function submit() {
  try {
    await formRef.value?.validate();
  } catch (e) {
    return;
  }
  
  submitting.value = true;
  try {
    // Transform form data to API format
    const payload: any = {
      type: form.value.type,
      advisorId: form.value.advisorId,
      mandateManager: form.value.mandateManager,
      mandateResponsible: form.value.mandateResponsible,
      street: form.value.street,
      number: form.value.number,
      zip: form.value.zip,
      city: form.value.city,
      email: form.value.email,
      taxNumber: form.value.taxNumber,
      taxCourt: form.value.taxCourt,
    };

    if (form.value.type === 'Natürliche Person') {
      payload.salutation = form.value.salutation;
      payload.title = form.value.title;
      payload.firstName = form.value.firstName;
      payload.lastName = form.value.lastName;
      payload.birthDate = form.value.birthDate;
      payload.taxId = form.value.taxId;
    } else {
      payload.companyName = form.value.companyName;
      payload.legalForm = form.value.legalForm;
      payload.vatId = form.value.vatId;
      if (form.value.participants && form.value.participants.length > 0) {
        payload.participants = form.value.participants.map((p: any, idx: number) => ({
          personId: `new-${idx}`, // Placeholder, backend should assign real IDs
          firstName: p.firstName,
          lastName: p.lastName,
          role: p.role
        }));
      }
    }

    // Tax office
    if (form.value.taxOfficeZip || form.value.taxOfficeCity || form.value.taxOfficeStreet) {
      payload.taxOffice = {
        zip: form.value.taxOfficeZip,
        city: form.value.taxOfficeCity,
        street: form.value.taxOfficeStreet,
        number: form.value.taxOfficeNumber,
        email: form.value.taxOfficeEmail,
        fax: form.value.taxOfficeFax,
        contactSalutation: form.value.taxOfficeContactSalutation,
        contactLastName: form.value.taxOfficeContactLastName,
        contactPhone: form.value.taxOfficeContactPhone,
      };
    }

    await clientsApi.createClient(payload);
    emit('created');
    close();
  } finally {
    submitting.value = false;
  }
}

// Reset form when modal closes
watch(() => props.show, (newVal) => {
  if (!newVal) {
    resetForm();
  }
});
</script>

<style scoped>
</style>
