<template>
  <div class="client-creation-container">

    <!-- View toggle switch with dropdown -->
    <div class="view-toggle-container">
      <div class="view-toggle">
        <input type="radio" id="list-view" value="list" v-model="viewMode" />
        <label :class="{ active: viewMode === 'list' }" for="list-view">
          <v-icon size="small" class="toggle-icon">mdi-format-list-bulleted</v-icon>
          Mandantenliste
        </label>
        <input type="radio" id="form-view" value="form" v-model="viewMode" />
        <label 
          :class="{ active: viewMode === 'form' }" 
          for="form-view"
          @click="selectFormType()"
        >
          <v-icon size="small" class="toggle-icon">mdi-account-plus</v-icon>
          Erstellen
        </label>
      </div>
    </div>

    <!-- Dynamic content based on selected view -->
    <transition name="fade" mode="out-in">
      <ClientList v-if="viewMode === 'list'" class="list-view" />
      
      <v-card v-else-if="viewMode === 'form' && formSelected" class="form-container">
        <v-card-text>
        <!-- Notification for save status -->
          <div v-if="saveStatus.show" class="status-notification" :class="saveStatus.type">
            {{ saveStatus.message }}
          </div>
    
          <!-- Dynamic input fields -->
          <form class="contact-form">
            <!-- Fields for natural person -->
            <div v-if="selectedType === 'person'" class="fields-container">
              <DynamicMask :placeholders="personPlaceholders" :initial-values="personInitialValues"
                title="Persönliche Informationen" @update:values="updateValues" @validation="handleValidation"
                @submit="handleSubmit" />
            </div>

            <!-- Fields for company -->
            <div v-if="selectedType === 'unternehmen'" class="fields-container">
              <DynamicMask :placeholders="companyPlaceholders" :initial-values="companyInitialValues"
                title="Unternehmensinformationen" @update:values="updateValues" @validation="handleValidation"
                @submit="handleSubmit" />
            </div>
          </form>
        </v-card-text>
      </v-card>
      
      <div v-else-if="viewMode === 'form' && !formSelected" class="form-selection-prompt">
        <p>Bitte wählen Sie eine Formularoption aus</p>
        <v-icon size="large" color="#c2a47b">mdi-arrow-down-bold</v-icon>
        <div class="select-container">
          <div class="select-item" @click="selectFormType('person')">
          <v-icon size="small" class="toggle-icon">mdi-account-tie</v-icon>
          Natürliche Person
        </div>
        <div class="select-item" @click="selectFormType('unternehmen')">
          <v-icon size="small" class="toggle-icon">mdi-domain</v-icon>
          Unternehmen
        </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import DynamicMask from '@/components/DynamicMask.vue'
import ClientList from '@/components/ClientList.vue'
import store from '@/store/store'

const router = useRouter()
const clientData = ref({
  name: '',
  email: '',
  phone: '',
  address: ''
})

// View mode toggle between form and list
const viewMode = ref<string>('list')

const selectedType = ref<string>(''); // Choice between "person" and "unternehmen"
const formSelected = computed(() => selectedType.value !== '');

// Function to select form type from dropdown
const selectFormType = (type: string = '') => {
  selectedType.value = type;
  viewMode.value = 'form';  
};

// Watch viewMode changes to reset selection when switching to list view
// and ensure form selection is shown when switching to form view
watch(viewMode, (newValue) => {
  if (newValue === 'list') {
    // Clear selection when switching to list view
    selectedType.value = '';
  }
});

// Placeholders & Initial values – Person
const personPlaceholders = ref([
  { name: 'mandatsmanager', type: 'text', required: false },
  { name: 'mandatsverantwortlicher', type: 'text', required: false },
  { name: 'anrede', type: 'select', options: ['Herr', 'Frau', 'Divers'], required: false },
  { name: 'titel', type: 'select', options: ['', 'Dr.', 'Prof.', 'Prof. Dr.'], required: false },
  {
    name: 'vorname',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[A-Za-zÄäÖöÜüß\\s-]{2,50}$',
      errorMessage: 'Vorname darf nur Buchstaben enthalten und muss zwischen 2 und 50 Zeichen lang sein.'
    }
  },
  {
    name: 'nachname',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[A-Za-zÄäÖöÜüß\\s-]{2,50}$',
      errorMessage: 'Nachname darf nur Buchstaben enthalten und muss zwischen 2 und 50 Zeichen lang sein.'
    }
  },
  { name: 'geburtsdatum', type: 'date', required: false },
  { name: 'strasse', type: 'text', required: false },
  { name: 'nr.', type: 'text', required: false },
  {
    name: 'plz',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[0-9]{5}$',
      errorMessage: 'PLZ muss 5 Ziffern enthalten'
    }
  },
  { name: 'ort', type: 'text', required: false },
  {
    name: 'e-Mail',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,6}$',
      errorMessage: 'Die eingegebene E-Mail-Adresse ist ungültig.'
    }
  },
  {
    name: 'steuernummer',
    type: 'text',
    required: false,
    validation: {
      pattern: '(\\d{3}/\\d{3}/\\d{5}|\\d{10,13})$',
      errorMessage: 'Steuernummer muss entweder 123/456/78901 oder zwischen 10-13 Ziffern enthalten.'
    }
  },
  { name: 'steuer-ID', type: 'text', required: false,
    validation: {
      pattern: '^[0-9]{11}$',
      errorMessage: 'USt-ID muss 11 Ziffern enthalten.'
    }
  },
  { name: 'finanzamt', type: 'text', required: false },
  { name: 'ort (Finanzamt)', type: 'text', required: false },
  { name: 'strasse (Finanzamt)', type: 'text', required: false },
  { name: 'nr. (Finanzamt)', type: 'text', required: false },
  { name: 'e-mail (Finanzamt)', type: 'text', required: false },
  { name: 'fax (Finanzamt)', type: 'text', required: false },
  { name: 'anrede ansprechpartner', type: 'text', required: false },
  { name: 'nachname ansprechpartner', type: 'text', required: false },
  {
    name: 'telefon ansprechpartner',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[\\d\\+\\-\\s\\/]{6,20}$',
      errorMessage: 'Telefonnummer darf nur Ziffern und + - / enthalten.'
    }
  },
  { name: 'finanzgericht', type: 'text', required: false },
]);

const musterPlaceholders = ref({
  "mandatsmanager": "Herr Müller",
  "mandatsverantwortlicher": "Frau Müller",
  "anrede": "Herr",
  "titel": "Dr.",
  "vorname": "Max",
  "nachname": "Mustermann",
  "geburtsdatum": "1990-01-01",
  "strasse": "Musterstraße",
  "nr.": "123",
  "plz": "12345",
  "ort": "Musterstadt",
  "e-mail": "max.mustermann@example.com",
  "steuernummer": "12345678901",
  "steuer-ID": "12345678910",
  "finanzamt": "Musterfinanzamt",
  "ort (Finanzamt)": "Musterstadt",
  "strasse (Finanzamt)": "Musterstraße",
  "nr. (Finanzamt)": "123",
  "e-mail (Finanzamt)": "max.mustermann@example.com",
  "fax (Finanzamt)": "0123456789",
  "anrede ansprechpartner": "Herr",
  "nachname ansprechpartner": "Mustermann",
  "telefon ansprechpartner": "0123456789",
  "finanzgericht": "Musterfinanzgericht",
  "beteiligte": "Musterbeteiligte"
});

const personInitialValues = ref({
  mandatsmanager: '',
  mandatsverantwortlicher: '',
  anrede: '',
  titel: '',
  vorname: '',
  nachname: '',
  geburtsdatum: '',
  strasse: '',
  'nr.': '',
  plz: '',
  ort: '',
  'ort (Finanzamt)': '',
  'strasse (Finanzamt)': '',
  'nr. (Finanzamt)': '',
  'e-mail (Finanzamt)': '',
  'fax (Finanzamt)': '',
  'anrede ansprechpartner': '',
  'nachname ansprechpartner': '',
  'e-Mail': '',
  steuernummer: '',
  'steuer-ID': '',
  finanzamt: '',
  finanzgericht: '',
  'telefon ansprechpartner': ''
});

// Placeholders & Initial values – Company
const companyPlaceholders = ref([
  { name: 'firmenname', type: 'text', required: false },
  { name: 'mandatsmanager', type: 'text', required: false },
  { name: 'mandatsverantwortlicher', type: 'text', required: false },
  { name: 'umsatz', type: 'number', required: false },
  { name: 'mitarbeiteranzahl', type: 'number', required: false },
  { name: 'rechtsform', type: 'text', required: false },
  {
    name: 'plz',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[0-9]{5}$',
      errorMessage: 'PLZ muss 5 Ziffern enthalten'
    }
  },
  {
    name: 'ort',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[A-Za-zÄäÖöÜüß\\s-]{2,50}$',
      errorMessage: 'Ort darf nur Buchstaben enthalten.'
    }
  },
  { name: 'straße', type: 'text', required: false },
  { name: 'nr.', type: 'text', required: false },
  {
    name: 'e-mail',
    type: 'text',
    required: false,
    validation: {
      pattern: '^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,6}$',
      errorMessage: 'Die eingegebene E-Mail-Adresse ist ungültig.'
    }
  },
  {
    name: 'steuernummer',
    type: 'text',
    required: false,
    validation: {
      pattern: '(\\d{3}/\\d{3}/\\d{5}|\\d{10,13})$',
      errorMessage: 'Steuernummer muss entweder 123/456/78901 oder zwischen 10-13 Ziffern enthalten.'
    }
  },
  {
    name: 'ust-id',
    type: 'text',
    required: false,
    validation: {
      pattern: '^DE[0-9]{9}$',
      errorMessage: 'USt-ID muss mit "DE" beginnen und 9 Ziffern enthalten (z. B. DE123456789).'
    }
  },
  { name: 'finanzamt', type: 'text', required: false },
  { name: 'finanzgericht', type: 'text', required: false },
  { name: 'beteiligte', type: 'text', required: false },
]);

const companyInitialValues = ref({
  firmenname: '',
  mandatsmanager: '',
  mandatsverantwortlicher: '',
  umsatz: 0,
  mitarbeiteranzahl: 0,
  rechtsform: '',
  plz: '',
  ort: '',
  straße: '',
  'nr.': '',
  'e-mail': '',
  steuernummer: '',
  'ust-id': '',
  finanzamt: '',
  finanzgericht: '',
  beteiligte: ''
});

// Message about save status
const saveStatus = ref<{
  show: boolean,
  type: 'success' | 'error',
  message: string
}>({
  show: false,
  type: 'success',
  message: ''
})

// Loading state
const isLoading = ref(false)

// Convert data to API format
const preparePersonData = (values: Record<string, any>) => {
  return {
    client_type: 'natural',
    mandate_manager: values.mandatsmanager || '',
    mandate_responsible: values.mandatsverantwortlicher || '',
    salutation: values.anrede ? values.anrede.toUpperCase() : null,
    title: values.titel || '',
    first_name: values.vorname || '',
    last_name: values.nachname || '',
    birth_date: values.geburtsdatum || null,
    address_street: values.strasse || '',
    address_number: values['nr.'] || '',
    address_zip: values.plz || '',
    address_city: values.ort || '',
    email: values['e-Mail'] || '',
    tax_number: values.steuernummer || '',
    tax_id: values['steuer-ID'] || '',
    tax_office: values.finanzamt || '',
    tax_office_city: values['ort (Finanzamt)'] || '',
    tax_office_street: values['strasse (Finanzamt)'] || '',
    tax_office_number: values['nr. (Finanzamt)'] || '',
    tax_office_email: values['e-mail (Finanzamt)'] || '',
    tax_office_fax: values['fax (Finanzamt)'] || '',
    contact_salutation: values['anrede ansprechpartner'] ? values['anrede ansprechpartner'].toUpperCase() : null,
    contact_last_name: values['nachname ansprechpartner'] || '',
    contact_phone: values['telefon ansprechpartner'] || '',
    tax_court: values.finanzgericht || ''
  }
}

const prepareCompanyData = (values: Record<string, any>) => {
  // Convert legal form to ENUM format
  let legalFormValue = null;
  if (values.rechtsform) {
    // Remove spaces and convert to uppercase
    const normalizedForm = values.rechtsform.replace(/\s+/g, '').toUpperCase();
    // Map of visual values to ENUM values
    const legalFormMap: Record<string, string> = {
      'GMBH': 'GMBH',
      'AG': 'AG',
      'OHG': 'OHG',
      'UG': 'UG',
      'KG': 'KG',
      'GBR': 'GBR',
      'EINZELFIRMA': 'EINZELFIRMA'
    };
    legalFormValue = legalFormMap[normalizedForm] || normalizedForm;
  }

  return {
    client_type: 'company',
    company_name: values.firmenname || '',
    mandate_manager: values.mandatsmanager || '',
    mandate_responsible: values.mandatsverantwortlicher || '',
    legal_form: legalFormValue,
    address_zip: values.plz || '',
    address_city: values.ort || '',
    address_street: values.straße || '',
    address_number: values['nr.'] || '',
    email: values['e-mail'] || '',
    tax_number: values.steuernummer || '',
    vat_id: values['ust-id'] || '',
    tax_office: values.finanzamt || '',
    tax_court: values.finanzgericht || '',
    contact_salutation: values['anrede ansprechpartner'] ? values['anrede ansprechpartner'].toUpperCase() : 'HERR',
    contact_last_name: values['nachname ansprechpartner'] || '',
    contact_phone: values['telefon ansprechpartner'] || '',
    contact_email: values['e-mail'] || '' // Use company's main email
  }
}

// Methods
const updateValues = (values: Record<string, any>) => {
};

const handleValidation = (isValid: boolean) => {
};

const handleSubmit = async (values: Record<string, any>) => {
  try {
    isLoading.value = true;
    
    // Convert data to API format
    const clientData = selectedType.value === 'person' 
      ? preparePersonData(values)
      : prepareCompanyData(values);
    
    // Save data to server
    await store.dispatch('client/createClient', clientData);
    
    // Show notification about successful save
    saveStatus.value = {
      show: true,
      type: 'success',
      message: 'Mandant erfolgreich gespeichert!'
    };
    
    // Hide notification after 3 seconds
    setTimeout(() => {
      saveStatus.value.show = false;
      // Redirect to client list after successful save
      viewMode.value = 'list';
      selectedType.value = '';
    }, 1500);
    
  } catch (error) {
    console.error('Error saving client:', error);
    saveStatus.value = {
      show: true,
      type: 'error',
      message: 'Fehler beim Speichern des Mandanten'
    };
    
    // Hide notification after 5 seconds
    setTimeout(() => {
      saveStatus.value.show = false;
    }, 5000);
  } finally {
    isLoading.value = false;
  }
};

// Навигация
const goToClientList = () => {
  router.push('/clients');
};

onMounted(() => {
  // document.addEventListener('click', closeDropdown);
  
  // personInitialValues.value = {
  //   mandatsmanager: musterPlaceholders.value.mandatsmanager || '',
  //   mandatsverantwortlicher: musterPlaceholders.value.mandatsverantwortlicher || '',
  //   anrede: musterPlaceholders.value.anrede || '',
  //   titel: musterPlaceholders.value.titel || '',
  //   vorname: musterPlaceholders.value.vorname || '',
  //   nachname: musterPlaceholders.value.nachname || '',
  //   geburtsdatum: musterPlaceholders.value.geburtsdatum || '',
  //   strasse: musterPlaceholders.value.strasse || '',
  //   'nr.': musterPlaceholders.value['nr.'] || '',
  //   plz: musterPlaceholders.value.plz || '',
  //   ort: musterPlaceholders.value.ort || '',
  //   'ort (Finanzamt)': musterPlaceholders.value['ort (Finanzamt)'] || '',
  //   'strasse (Finanzamt)': musterPlaceholders.value['strasse (Finanzamt)'] || '',
  //   'nr. (Finanzamt)': musterPlaceholders.value['nr. (Finanzamt)'] || '',
  //   'e-mail (Finanzamt)': musterPlaceholders.value['e-mail (Finanzamt)'] || '',
  //   'fax (Finanzamt)': musterPlaceholders.value['fax (Finanzamt)'] || '',
  //   'anrede ansprechpartner': musterPlaceholders.value['anrede ansprechpartner'] || '',
  //   'nachname ansprechpartner': musterPlaceholders.value['nachname ansprechpartner'] || '',
  //   'e-Mail': musterPlaceholders.value['e-mail'] || '',
  //   steuernummer: musterPlaceholders.value.steuernummer || '',
  //   'steuer-ID': musterPlaceholders.value['steuer-ID'] || '',
  //   finanzamt: musterPlaceholders.value.finanzamt || '',
  //   finanzgericht: musterPlaceholders.value.finanzgericht || '',
  //   'telefon ansprechpartner': musterPlaceholders.value['telefon ansprechpartner'] || '',
  // };

  // companyInitialValues.value = {
  //   firmenname: 'Muster GmbH',
  //   mandatsmanager: musterPlaceholders.value.mandatsmanager || '',
  //   mandatsverantwortlicher: musterPlaceholders.value.mandatsverantwortlicher || '',
  //   umsatz: 1000000,
  //   mitarbeiteranzahl: 25,
  //   rechtsform: 'GmbH',
  //   plz: musterPlaceholders.value.plz || '',
  //   ort: musterPlaceholders.value.ort || '',
  //   straße: musterPlaceholders.value.strasse || '',
  //   'nr.': musterPlaceholders.value['nr.'] || '',
  //   'e-mail': musterPlaceholders.value['e-mail'] || '',
  //   steuernummer: musterPlaceholders.value.steuernummer || '',
  //   'ust-id': 'DE123456789',
  //   finanzamt: musterPlaceholders.value.finanzamt || '',
  //   finanzgericht: musterPlaceholders.value.finanzgericht || '',
  //   beteiligte: musterPlaceholders.value.beteiligte || ''
  // };
});

onUnmounted(() => {
  // Fix: remove reference to undefined closeDropdown function
  // document.removeEventListener('click', closeDropdown);
});
</script>

<style scoped>
/* Container-Stil */
.client-creation-container {
  padding: 1.5rem;
  min-height: calc(100vh - 100px);
}

/* View toggle styles */
.view-toggle-container {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.view-toggle {
  display: flex;
  background: #fff;
  border-radius: 40px;
  overflow: hidden;
  width: 350px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

.view-toggle label {
  flex: 1;
  text-align: center;
  min-height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 15px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.view-toggle label.active {
  background: #c2a47b;
  color: #fff;
  font-weight: 500;
}

.view-toggle input[type="radio"] {
  display: none;
}

.toggle-icon {
  margin-right: 5px;
  color: #c2a47b;
}

.view-toggle label.active .toggle-icon {
  color: #fff;
}

/* Form Container */
.form-container {
  max-width: 900px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.07);
  overflow: hidden;
  background-color: transparent;
}

/* List view styles */
.list-view {
  margin-top: 20px;
}

/* Toggle Switch Style */
.toggle-switch {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff;
  overflow: hidden;
  width: 350px;
  margin: 0 auto 32px auto;
  box-shadow: 0 2px 8px rgba(194, 164, 123, 0.08);
}

.toggle-switch label {
  flex: 1;
  text-align: center;
  min-height: 45px;
  height: 45px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 0 0;
  font-size: 14px;
  font-weight: 400;
  color: #c2a47b;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  border: 1px solid #c2a47b;
  border-top-left-radius: 40px;
  border-bottom-left-radius: 40px;
  letter-spacing: 0.2px;
  line-height: 1.1;
  white-space: normal;
  font-family: 'Inter', Arial, sans-serif;
}

.toggle-switch label:last-child {
  border-top-left-radius: 0px;
  border-bottom-left-radius: 0px;
  border-top-right-radius: 40px;
  border-bottom-right-radius: 40px;
}

.toggle-switch label {
  color: #a2a2a2;
  font-weight: 400;
  box-shadow: 0 2px 8px rgba(194, 164, 123, 0.10);
}

.toggle-switch label.active {
  background: #c2a47b;
  color: #fff;
  font-weight: 400;
  box-shadow: 0 2px 8px rgba(194, 164, 123, 0.10);
}

.toggle-switch .checkmark {
  font-size: 20px;
  margin-bottom: 0;
}

.toggle-switch input[type="radio"] {
  display: none;
}

/* Fields Container */
.fields-container {
  background-color: #fcfcfc;
  padding: 25px;
  margin-bottom: 30px;
  border-radius: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 25px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e4e8;
}

/* Animation transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Responsive adaptations */
@media (max-width: 768px) {
  .toggle-switch, .view-toggle {
    width: 100%;
    max-width: 440px;
  }
  
  .toggle-switch label, .view-toggle label {
    font-size: 14px;
  }
}

/* Animation */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.contact-form {
  animation: fadeIn 0.3s ease-in-out;
}

/* Status notification */
.status-notification {
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  text-align: center;
  font-weight: 500;
}

.success {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}

.error {
  background-color: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 1.5rem;
  color: #333;
  margin: 0;
}

/* Form selection prompt */
.form-selection-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 50px;
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.07);
  max-width: 500px;
  height: 275px;
  margin: 0 auto;
}

.form-selection-prompt p {
  margin-top: 10px;
  color: #666;
  font-size: 16px;
  text-align: center;
}

.select-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
}

.select-item {
  padding: 12px 15px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s;
    margin: 10px;
    border: 2px solid #c2a47b;
    border-radius: 25px;
    width: 200px;
}

.select-item:hover {
  background-color: #f5f5f5;
}

.select-item .toggle-icon {
  margin-right: 8px;
  color: #c2a47b;
}
</style>