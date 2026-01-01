<template>
  <div class="document-editor h-screen w-screen overflow-hidden flex flex-col bg-white">
    <!-- Fehler / Loading -->
    <div v-if="!templateId && !routeId" class="flex items-center justify-center h-full">
      <div class="px-4 py-2 rounded bg-red-100 text-red-800">
        Fehler: Keine Template-ID gefunden. Route: {{ route.path }}
      </div>
    </div>

    <div v-else-if="(isLoading || checkingRouteId || documentLoading) && !documentData && !template" class="flex items-center justify-center flex-1">
      <n-spin size="large">
        <div class="text-slate-600 mt-4">Lade {{ routeIdDocument?.isDocument ? 'Dokument' : 'Template' }}...</div>
      </n-spin>
    </div>

    <div v-else-if="templateError && !documentData" class="flex items-center justify-center flex-1">
      <div class="px-4 py-2 rounded bg-red-100 text-red-800">
        Fehler beim Laden des Templates: {{ templateError }}
        <n-button class="ml-2" @click="router.push('/document-creation')">
          Zur Dokument-Erstellung
        </n-button>
      </div>
    </div>

    <template v-else>
      <!-- Sticky Toolbar -->
      <EditorTopbar
        :template-name="editor.templateName.value"
        :is-dirty="editor.isDirty.value"
        :saving="saving"
        @update:template-name="editor.templateName.value = $event"
        @export="handleExport"
        @save="handleSave"
      />

      <!-- Main Content: Sidebar + Editor -->
      <div class="flex flex-1 min-h-0 overflow-hidden">
        <!-- Left Sidebar: Einstellungen / Formular -->
        <div class="w-[320px] bg-white border-r border-slate-200 flex flex-col overflow-hidden">
          <LeftPanelTabs
            :active-tab="activeTab"
            @update:active-tab="activeTab = $event"
          >
            <SettingsPanel
              v-if="activeTab === 'settings'"
              :placeholders="editor.placeholders.value"
              :db-fields="dbFields || []"
              :linked-clients="linkedClients"
              :fill-values="editor.fillValues.value"
              :current-client="client || null"
              @update:placeholders="(v) => { 
                console.log('[DocumentEditor] Placeholders updated event received:', v);
                v.forEach((p: any) => {
                  console.log(`[DocumentEditor] Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}, type=${p.type}, label=${p.label}`);
                });
                // WICHTIG: Direkt zuweisen, damit die mappedFieldId erhalten bleibt
                // Stelle sicher, dass wir ein neues Array erstellen, nicht nur die Referenz ändern
                editor.placeholders.value = [...v];
                console.log('[DocumentEditor] Placeholders assigned to editor.placeholders.value');
                console.log('[DocumentEditor] Verifying assignment - editor.placeholders.value:', editor.placeholders.value);
                editor.placeholders.value.forEach((p: any) => {
                  console.log(`[DocumentEditor] After assignment - Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}`);
                });
                // Zusätzlich: Prüfe nach 100ms, ob die mappedFieldId noch vorhanden ist
                setTimeout(() => {
                  console.log('[DocumentEditor] Placeholders after 100ms:', editor.placeholders.value);
                  editor.placeholders.value.forEach((p: any) => {
                    console.log(`[DocumentEditor] After 100ms - Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}`);
                  });
                }, 100);
              }"
              @update:linked-clients="handleLinkedClientsUpdate"
              @update:fill-value="(key, value) => { console.log('[DocumentEditor] update:fillValue received:', key, value); editor.updateFillValue(key, value); }"
              @rescan="handleRescan"
              @save="handleSavePlaceholders"
            />

            <FormPanel
              v-else
              :placeholders="editor.placeholders.value"
              :fill-values="editor.fillValues.value"
              @update:fill-values="handleUpdateFillValues"
              @reset="editor.resetFillValues()"
            />
          </LeftPanelTabs>
        </div>

        <!-- Right Editor Area -->
        <div class="flex-1 min-h-0 overflow-hidden bg-white flex flex-col">
          <EditorCanvas
            class="flex-1 min-h-0"
            :content-html="editor.contentHtml.value"
            :placeholders="editor.placeholders.value"
            :fill-values="editor.fillValues.value"
            @update:content-html="editor.contentHtml.value = $event"
            @placeholder-click="handlePlaceholderClick"
          />
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import { useRoute, useRouter } from 'vue-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { NSpin, createDiscreteApi } from 'naive-ui';
import EditorTopbar from '@/components/editor/EditorTopbar.vue';
import LeftPanelTabs from '@/components/editor/LeftPanelTabs.vue';
import SettingsPanel from '@/components/editor/SettingsPanel.vue';
import FormPanel from '@/components/editor/FormPanel.vue';
import EditorCanvas from '@/components/editor/EditorCanvas.vue';
import { useTemplateEditor } from '@/composables/useTemplateEditor';
import { documentEditorApi, clientsApi } from '@/lib/api';
import { DocumentAPI } from '@/services/api';
import { extractPlaceholders } from '@/composables/useDocumentPlaceholders';
import mammoth from 'mammoth';
import type { DbField } from '@/lib/types';

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const routeId = route.params.id as string;
const documentId = route.query.documentId as string | undefined; // ID des Dokuments (falls bereits erstellt)
// clientId aus URL oder aus geladenem Dokument
const clientIdFromQuery = route.query.clientId as string | undefined;
const templateIdFromQuery = route.query.templateId as string | undefined; // Template-ID aus Query (wichtig für Dokument-Modus)
const isDocumentMode = route.query.mode === 'document';

// Computed clientId: aus URL oder aus geladenem Dokument
const clientId = computed(() => {
  return clientIdFromQuery || documentData.value?.clientId || (documentData.value as any)?.client_id || undefined;
});

// CRITICAL: Determine if routeId is a document ID or template ID
// If isDocumentMode is not set, we need to check if routeId is a document or template
// Strategy: Try to load as document first, if it's a document, set isDocumentMode and currentDocumentId
const { data: routeIdDocument, isLoading: checkingRouteId } = useQuery({
  queryKey: ['check-route-id', routeId],
  queryFn: async () => {
    // Try to get as document first
    try {
      const doc = await documentEditorApi.getDocument(routeId);
      // If successful and it's not a template, it's a document
      return { isDocument: true, id: routeId };
    } catch {
      // If it fails, it might be a template
      return { isDocument: false, id: routeId };
    }
  },
  enabled: !isDocumentMode && !!routeId, // Only check if mode is not explicitly set
  retry: false,
});

// Determine actual templateId and currentDocumentId
// CRITICAL: If templateId is in query (from document mode), use it
// Otherwise, if routeId is a document, we'll use routeId as a fallback templateId to allow loading
// The actual template will be determined after the document is loaded
const templateId = computed(() => {
  // CRITICAL: If templateId is in query, use it (this is set when creating a document from a template)
  if (templateIdFromQuery) {
    return templateIdFromQuery;
  }
  if (isDocumentMode) {
    // In document mode, routeId should be template ID
    return routeId;
  } else if (routeIdDocument.value?.isDocument) {
    // Route ID is a document ID
    // Use routeId as fallback so we can at least try to load something
    // The document query will handle the actual loading
    return routeId;
  } else {
    // Route ID is template ID
    return routeId;
  }
});

const { message: nMessage, dialog: nDialog } = createDiscreteApi(['message', 'dialog']);

// Dokument-ID (entweder aus Query, routeId wenn es ein Dokument ist, oder wird beim ersten Speichern erstellt)
const currentDocumentId = ref<string | undefined>(
  documentId || (routeIdDocument.value?.isDocument ? routeId : undefined)
);

const activeTab = ref<'settings' | 'form'>(isDocumentMode ? 'form' : 'settings');
const saving = ref(false);
const linkedClients = ref<string[]>([]);

// Dokument laden (wenn routeId ein Dokument ist oder documentId gesetzt ist)
const { data: documentData, isLoading: documentLoading } = useQuery({
  queryKey: ['document', currentDocumentId.value || routeId],
  queryFn: () => {
    const docId = currentDocumentId.value || routeId;
    console.log('[DocumentEditor] Loading document with ID:', docId);
    return documentEditorApi.getDocument(docId);
  },
  enabled: computed(() => {
    // Always try to load document if routeId is set
    // We'll determine if it's actually a document after loading
    const enabled = !!routeId;
    console.log('[DocumentEditor] Document query enabled:', enabled, 'routeId:', routeId);
    return enabled;
  }),
  retry: false,
  onSuccess: (data) => {
    if (!data) return;
    
    // Prüfen, ob das geladene Dokument ein Template ist
    const isTemplate = (data as any).is_template === true || (data as any).isTemplate === true;
    const docClientId = (data as any).clientId || (data as any).client_id;
    const docId = String((data as any).id || routeId);
    
    console.log('[DocumentEditor] Document loaded - isTemplate:', isTemplate, 'clientId:', docClientId, 'docId:', docId, 'current clientId in URL:', clientId.value);
    
    // Wenn es kein Template ist, URL immer aktualisieren mit mode=document und clientId
    if (!isTemplate) {
      const docTitle = (data as any).title || (data as any).name;
      const docTemplateId = (data as any).template_id || (data as any).templateId || route.query.templateId;
      
      // Setze den Dokument-Namen als templateName, damit er in der Topbar angezeigt wird
      if (docTitle) {
        editor.templateName.value = docTitle;
        console.log('[DocumentEditor] Set document name as templateName:', docTitle);
      }
      
      const needsUpdate = !isDocumentMode || (docClientId && docClientId !== clientId.value) || (!clientId.value && docClientId);
      
      if (needsUpdate) {
        console.log('[DocumentEditor] Updating URL with document mode and clientId:', docClientId);
        router.replace({
          ...route,
          query: {
            ...route.query,
            mode: 'document',
            documentId: docId,
            ...(docClientId ? { clientId: String(docClientId) } : {}),
            ...(docTemplateId ? { templateId: String(docTemplateId) } : {}),
          },
        });
      }
      
      // Automatisch den Mandanten als verknüpften Mandanten hinzufügen, wenn vorhanden
      const docClientIdStr = String(docClientId);
      if (docClientId && !linkedClients.value.includes(docClientIdStr)) {
        console.log('[DocumentEditor] Automatically adding clientId from document to linkedClients:', docClientIdStr);
        // Verwende handleLinkedClientsUpdate, damit die UI korrekt aktualisiert wird
        // Warten, bis allClients geladen sind
        setTimeout(() => {
          handleLinkedClientsUpdate([...linkedClients.value, docClientIdStr]);
        }, 300);
      }
    }
  },
});

// Template laden
// CRITICAL: If templateIdFromQuery is present, we should always load the template
// (even if routeId is a document ID, because we know the correct template ID from the query)
// Wenn routeId ein Dokument ist, versuchen wir NICHT, getTemplate aufzurufen (weil das das Dokument zurückgibt)
// Stattdessen verwenden wir templateByFilePath, um die Vorlage zu finden
// Wenn routeId eine Vorlage ist oder isDocumentMode gesetzt ist, laden wir die Vorlage direkt
const shouldLoadTemplate = computed(() => {
  // CRITICAL: If templateIdFromQuery is present, always load the template
  // This ensures we load the correct template even if routeId is a document ID
  if (templateIdFromQuery) {
    return true;
  }
  if (isDocumentMode) {
    return true; // In document mode, routeId should be template ID
  } else if (routeIdDocument.value?.isDocument) {
    // Route ID is document ID - DON'T call getTemplate, it will return the document
    return false; // We'll use templateByFilePath instead
  } else if (documentData.value && Number(documentData.value.id) === Number(routeId)) {
    // If we have a document with matching ID, don't load template (it would return the document)
    return false;
  } else {
    return true; // Route ID is template ID
  }
});

const { data: template, isLoading, error: templateError } = useQuery({
  queryKey: ['template', templateId.value],
  queryFn: () => {
    // CRITICAL: Use templateId.value (which includes templateIdFromQuery) instead of routeId
    // This ensures we load the correct template even if routeId is a document ID
    const idToLoad = templateId.value;
    console.log('[DocumentEditor] Loading template with ID:', idToLoad, 'templateIdFromQuery:', templateIdFromQuery, 'routeId:', routeId);
    return documentEditorApi.getTemplate(idToLoad);
  },
  enabled: computed(() => {
    const enabled = shouldLoadTemplate.value && !!templateId.value;
    console.log('[DocumentEditor] Template query enabled:', enabled, 'shouldLoadTemplate:', shouldLoadTemplate.value, 'templateId:', templateId.value, 'templateIdFromQuery:', templateIdFromQuery, 'routeId:', routeId);
    if (templateIdFromQuery && templateId.value !== templateIdFromQuery) {
      console.warn('[DocumentEditor] WARNING: templateId.value does not match templateIdFromQuery! templateId.value:', templateId.value, 'templateIdFromQuery:', templateIdFromQuery);
    }
    return enabled;
  }),
  retry: false,
});

// Wenn ein Dokument geladen wird, versuchen wir, die Vorlage über file_path zu finden
const documentFilePath = computed(() => {
  const path = documentData.value?.filePath || (documentData.value as any)?.file_path || null;
  console.log('[DocumentEditor] Document filePath:', path, 'Document:', documentData.value);
  return path;
});

// Wenn ein Dokument geladen wird, versuchen wir, die Vorlage zu finden
// Zuerst über file_path, dann über Titel oder andere Attribute
const { data: templateByFilePath, isLoading: loadingTemplateByFilePath } = useQuery({
  queryKey: computed(() => ['template-for-document', documentData.value?.id, documentFilePath.value]),
  queryFn: async () => {
    if (!documentData.value) {
      console.log('[DocumentEditor] No document loaded, cannot find template');
      return null;
    }
    
    console.log('[DocumentEditor] Searching for template for document:', documentData.value.id);
    // Get all templates
    const templates = await documentEditorApi.getTemplates();
    console.log('[DocumentEditor] Found templates:', templates.length);
    
    // Strategy 1: Find by file_path if available
    if (documentFilePath.value) {
      console.log('[DocumentEditor] Searching for template with filePath:', documentFilePath.value);
      const foundByPath = templates.find((t: any) => {
        const tPath = t.filePath || (t as any).file_path;
        console.log('[DocumentEditor] Comparing template', t.id, 'filePath:', tPath, 'with document filePath:', documentFilePath.value);
        return tPath === documentFilePath.value;
      });
      if (foundByPath) {
        console.log('[DocumentEditor] Found template by filePath:', foundByPath.id);
        return foundByPath;
      }
    }
    
    // Strategy 2: Find by title (documents created from templates often have similar titles)
    const docTitle = documentData.value.name || (documentData.value as any).title;
    if (docTitle) {
      console.log('[DocumentEditor] Searching for template with similar title:', docTitle);
      // Try exact match first
      let found = templates.find((t: any) => t.name === docTitle || (t as any).title === docTitle);
      if (found) {
        console.log('[DocumentEditor] Found template by exact title match:', found.id);
        return found;
      }
      // Try partial match (document title might have been modified)
      found = templates.find((t: any) => {
        const tTitle = t.name || (t as any).title;
        return tTitle && docTitle && (tTitle.includes(docTitle) || docTitle.includes(tTitle));
      });
      if (found) {
        console.log('[DocumentEditor] Found template by partial title match:', found.id);
        return found;
      }
    }
    
    // Strategy 3: If templateIdFromQuery is present, use it (CRITICAL: This is the correct template ID)
    // This ensures we use the correct template that was selected, even if routeId is a document ID
    if (templateIdFromQuery) {
      const templateById = templates.find((t: any) => String(t.id) === String(templateIdFromQuery));
      if (templateById) {
        console.log('[DocumentEditor] Found template by templateIdFromQuery:', templateById.id);
        return templateById;
      }
    }
    
    // Strategy 3b: If isDocumentMode is set, use the template ID from routeId
    // This ensures we use the correct template that was selected
    if (isDocumentMode && routeId) {
      const templateById = templates.find((t: any) => String(t.id) === String(routeId));
      if (templateById) {
        console.log('[DocumentEditor] Found template by routeId (document mode):', templateById.id);
        return templateById;
      }
    }
    
    // Strategy 4: If no match found, return the first template (fallback)
    // This is not ideal, but better than nothing
    if (templates.length > 0) {
      console.warn('[DocumentEditor] No template found by filePath, title, or routeId, using first template as fallback:', templates[0].id);
      return templates[0];
    }
    
    console.log('[DocumentEditor] No template found');
    return null;
  },
  enabled: computed(() => {
    // CRITICAL: Don't enable if templateIdFromQuery is present - we already have the correct template via template query
    if (templateIdFromQuery) {
      console.log('[DocumentEditor] templateByFilePath query disabled: templateIdFromQuery present:', templateIdFromQuery);
      return false;
    }
    
    // Don't enable if isDocumentMode is set - we already have the template via template query
    if (isDocumentMode) {
      console.log('[DocumentEditor] templateByFilePath query disabled (document mode, using template query instead)');
      return false;
    }
    
    // Enable if we have a document loaded
    // We'll check if it's actually a document by comparing IDs
    const hasDocument = !!documentData.value;
    const isDoc = hasDocument && documentData.value && Number(documentData.value.id) === Number(routeId);
    const enabled = hasDocument && isDoc;
    console.log('[DocumentEditor] templateByFilePath query enabled:', enabled, 'hasDocument:', hasDocument, 'document.id:', documentData.value?.id, 'routeId:', routeId, 'isDoc:', isDoc);
    return enabled;
  }),
  retry: false,
});

// Clients für Verknüpfung laden
const { data: allClientsData } = useQuery({
  queryKey: ['all-clients-for-linking'],
  queryFn: () => clientsApi.getClients({ page: 1, pageSize: 1000 }),
  refetchOnWindowFocus: false,
});
const allClients = computed(() => allClientsData.value?.items || []);

// Client laden (wenn clientId vorhanden)
const { data: client } = useQuery({
  queryKey: ['client', clientId],
  queryFn: () => clientsApi.getClient(clientId.value!),
  enabled: computed(() => !!clientId.value),
});

// DB-Felder laden
const { data: dbFields = [] as DbField[] } = useQuery({
  queryKey: ['db-fields'],
  queryFn: () => documentEditorApi.getDbFields(),
});

// Editor-Logik
const editor = useTemplateEditor();

// Funktion zum Mappen von Mandantendaten zu Platzhaltern
function mapClientDataToPlaceholders(client: any, placeholders: any[]): Record<string, any> {
  const fillValues: Record<string, any> = {};
  
  if (!client || !placeholders) return fillValues;
  
  console.log('[mapClientDataToPlaceholders] Starting mapping for client:', client?.id, 'type:', client?.type, 'salutation:', client?.salutation);
  console.log('[mapClientDataToPlaceholders] Placeholders to map:', placeholders.map(p => ({ key: p.key, mappedDbField: p.mappedDbField, mappedFieldId: p.mappedFieldId })));
  
  placeholders.forEach((placeholder) => {
    const key = placeholder.key || placeholder.name;
    if (!key) return;
    
    console.log(`[mapClientDataToPlaceholders] Processing placeholder key: "${key}"`);
    
    // Mapping basierend auf DB-Feld-Mapping
    // Unterstütze sowohl mappedDbField (String) als auch mappedFieldId (ID)
    let dbFieldKey: string | undefined = undefined;
    if (placeholder.mappedDbField) {
      dbFieldKey = placeholder.mappedDbField;
      console.log(`[mapClientDataToPlaceholders] Found mappedDbField for "${key}": ${dbFieldKey}`);
    } else if (placeholder.mappedFieldId) {
      // Wenn mappedFieldId gesetzt ist, finde das entsprechende DB-Feld
      // WICHTIG: ID-Vergleich muss String-Vergleich sein, da DB-Feld-IDs als Strings kommen
      const dbField = dbFields.value.find(f => String(f.id) === String(placeholder.mappedFieldId));
      console.log(`[mapClientDataToPlaceholders] Looking for dbField with id: ${placeholder.mappedFieldId} (type: ${typeof placeholder.mappedFieldId}), available dbFields:`, dbFields.value.map(f => ({ id: f.id, key: f.key, type: typeof f.id })));
      if (dbField) {
        dbFieldKey = dbField.key;
        console.log(`[mapClientDataToPlaceholders] ✓ Found mappedFieldId for "${key}": dbFieldKey = ${dbFieldKey} (from dbField.id: ${dbField.id}, placeholder.mappedFieldId: ${placeholder.mappedFieldId})`);
      } else {
        console.log(`[mapClientDataToPlaceholders] ✗ No dbField found for mappedFieldId: ${placeholder.mappedFieldId} (type: ${typeof placeholder.mappedFieldId})`);
        console.log(`[mapClientDataToPlaceholders] Available dbField IDs:`, dbFields.value.map(f => ({ id: f.id, type: typeof f.id })));
      }
    }
    
    // Fallback: Wenn kein Mapping vorhanden ist, versuche direkten Match basierend auf Platzhalter-Key
    if (!dbFieldKey) {
      console.log(`[mapClientDataToPlaceholders] No mapping for placeholder key: ${key}, trying direct match`);
      const keyLower = key.toLowerCase();
      
      // Direkte Zuordnung für häufige Platzhalter-Namen
      if (keyLower === 'plz' || keyLower === 'postleitzahl') {
        if (client.zip) {
          fillValues[key] = client.zip;
          console.log(`[mapClientDataToPlaceholders] Direct match: ${key} -> ${client.zip}`);
        } else {
          console.log(`[mapClientDataToPlaceholders] Direct match attempted for ${key}, but client.zip is empty/null:`, client.zip);
        }
      } else if (keyLower === 'ort' || keyLower === 'stadt') {
        if (client.city) {
          fillValues[key] = client.city;
          console.log(`[mapClientDataToPlaceholders] Direct match: ${key} -> ${client.city}`);
        }
      } else if (keyLower === 'strasse' || keyLower === 'straße') {
        if (client.street) {
          fillValues[key] = client.street;
          console.log(`[mapClientDataToPlaceholders] Direct match: ${key} -> ${client.street}`);
        }
      } else if (keyLower === 'hausnummer' || keyLower === 'nummer') {
        if (client.number) {
          fillValues[key] = client.number;
          console.log(`[mapClientDataToPlaceholders] Direct match: ${key} -> ${client.number}`);
        }
      } else if (keyLower === 'anrede' || keyLower === 'salutation') {
        // Anrede nur für natürliche Personen
        if (client.type === 'Natürliche Person') {
          if (client.salutation && String(client.salutation).trim() !== '') {
            fillValues[key] = client.salutation;
            console.log(`[mapClientDataToPlaceholders] Direct match: ${key} -> ${client.salutation}`);
          } else {
            console.log(`[mapClientDataToPlaceholders] Direct match attempted for ${key}, but client.salutation is empty/null. client.type: ${client.type}, client.salutation: ${client.salutation}, type: ${typeof client.salutation}`);
          }
        } else {
          console.log(`[mapClientDataToPlaceholders] Direct match attempted for ${key}, but client is not a natural person. client.type: ${client.type}`);
        }
      }
    }
    
    if (dbFieldKey) {
      console.log(`[mapClientDataToPlaceholders] Processing placeholder key: ${key}, dbFieldKey: ${dbFieldKey}`);
      
      // Mandant-Felder
      if (dbFieldKey.startsWith('mandant.')) {
        const fieldName = dbFieldKey.replace('mandant.', '');
        let value: any = null;
        
        if (client.type === 'Natürliche Person') {
          switch (fieldName) {
            case 'name':
              value = `${client.firstName || ''} ${client.lastName || ''}`.trim();
              break;
            case 'vorname':
              value = client.firstName;
              break;
            case 'nachname':
              value = client.lastName;
              break;
            case 'anrede':
            case 'salutation':
              value = client.salutation;
              console.log(`[mapClientDataToPlaceholders] ✓ Mapped anrede from mandant.${fieldName}: client.salutation = ${client.salutation}, value = ${value}, type: ${typeof value}`);
              // Ensure value is set even if it's an empty string (but not null/undefined)
              if (value === null || value === undefined) {
                value = null;
              }
              break;
            case 'titel':
              value = client.title;
              break;
            case 'steuernummer':
              value = client.taxNumber;
              break;
            case 'steuerId':
              value = client.taxId;
              break;
            case 'email':
              value = client.email;
              break;
            case 'geburtstag':
            case 'geburtsdatum':
              value = client.birthDate;
              break;
            case 'geburtsort':
              value = client.birthPlace;
              break;
            case 'staatsangehörigkeit':
            case 'nationality':
              value = client.nationality;
              break;
          }
        } else {
          switch (fieldName) {
            case 'name':
            case 'firmenname':
              value = client.companyName;
              break;
            case 'rechtsform':
              value = client.legalForm;
              break;
            case 'umsatzsteuerId':
              value = client.vatId;
              break;
            case 'steuernummer':
              value = client.taxNumber;
              break;
            case 'email':
              value = client.email;
              break;
            case 'ansprechpartner':
              value = `${client.contactSalutation || ''} ${client.contactLastName || ''}`.trim();
              break;
          }
        }
        
        if (value !== null && value !== undefined) {
          fillValues[key] = value;
          console.log(`[mapClientDataToPlaceholders] ✓ Set fillValues["${key}"] = "${value}" (type: ${typeof value})`);
        } else {
          console.log(`[mapClientDataToPlaceholders] ✗ Skipping fillValues["${key}"] because value is null/undefined`);
        }
      }
      
      // Adresse-Felder
      if (dbFieldKey.startsWith('adresse.')) {
        const fieldName = dbFieldKey.replace('adresse.', '').toLowerCase();
        let value: any = null;
        
        console.log(`[mapClientDataToPlaceholders] Processing adresse field: ${fieldName}, client data:`, {
          street: client.street,
          number: client.number,
          zip: client.zip,
          city: client.city
        });
        
        switch (fieldName) {
          case 'strasse':
            value = client.street;
            break;
          case 'nummer':
            value = client.number;
            break;
          case 'plz':
          case 'postleitzahl':
            value = client.zip;
            break;
          case 'ort':
          case 'stadt':
            value = client.city;
            break;
        }
        
        console.log(`[mapClientDataToPlaceholders] Adresse field ${fieldName} -> value: ${value}`);
        
        if (value !== null && value !== undefined) {
          fillValues[key] = value;
          console.log(`[mapClientDataToPlaceholders] Set fillValues[${key}] = ${value}`);
        } else {
          console.log(`[mapClientDataToPlaceholders] Skipping fillValues[${key}] because value is null/undefined`);
        }
      }
      
      // Finanzamt-Felder
      if (dbFieldKey.startsWith('finanzamt.')) {
        const fieldName = dbFieldKey.replace('finanzamt.', '');
        let value: any = null;
        
        switch (fieldName) {
          case 'name':
            value = client.taxOffice;
            break;
          case 'strasse':
            value = client.taxOfficeStreet;
            break;
          case 'nummer':
            value = client.taxOfficeNumber;
            break;
          case 'plz':
            value = client.taxOfficeZip;
            break;
          case 'ort':
            value = client.taxOfficeCity;
            break;
          case 'email':
            value = client.taxOfficeEmail;
            break;
        }
        
        if (value !== null && value !== undefined) {
          fillValues[key] = value;
        }
      }
    }
  });
  
  return fillValues;
}

// Track if we've already loaded content to prevent multiple loads
const hasLoadedContent = ref(false);
const hasAppliedLinkedClients = ref(false);

watch(
  [template, documentData, client, routeIdDocument, templateByFilePath, loadingTemplateByFilePath, linkedClients, allClients, isLoading],
  async ([newTemplate, newDocument, newClient, routeIdDoc, templateFromFile, isLoadingTemplate, newLinkedClients, newAllClients, templateIsLoading]) => {
    // Skip if we've already loaded content (prevent multiple loads)
    if (hasLoadedContent.value) {
      return;
    }
    
    // Determine if routeId is a document
    // Check if document ID matches routeId, or if routeIdDocument says it's a document
    const isRouteIdDocument = routeIdDoc?.isDocument || (newDocument && Number(newDocument.id) === Number(routeId));
    console.log('[DocumentEditor] isRouteIdDocument:', isRouteIdDocument, 'routeIdDoc:', routeIdDoc, 'newDocument.id:', newDocument?.id, 'routeId:', routeId);
    
    // Determine source: If routeId is a document, use document; otherwise use template
    // CRITICAL: In document mode, we need to use the document's placeholders (which should have mappings from template)
    // But we might also need the template's placeholders if the document doesn't have them
    let actualTemplate = templateFromFile;
    
    // CRITICAL: If templateIdFromQuery is present, ALWAYS use newTemplate (loaded via template query with correct ID)
    // This ensures we use the correct template that was selected, not a fallback from templateByFilePath
    if (templateIdFromQuery && newTemplate) {
      // Verify that newTemplate.id matches templateIdFromQuery
      const templateIdMatches = String(newTemplate.id) === String(templateIdFromQuery);
      console.log('[DocumentEditor] templateIdFromQuery present:', templateIdFromQuery, 'newTemplate.id:', newTemplate.id, 'matches:', templateIdMatches);
      if (templateIdMatches) {
        actualTemplate = newTemplate;
        console.log('[DocumentEditor] Using newTemplate (correct template from query):', actualTemplate?.id);
      } else {
        console.warn('[DocumentEditor] WARNING: newTemplate.id does not match templateIdFromQuery! newTemplate.id:', newTemplate.id, 'templateIdFromQuery:', templateIdFromQuery);
        // Still use newTemplate, but log the mismatch
        actualTemplate = newTemplate;
      }
    } else if (newTemplate && isRouteIdDocument && templateFromFile) {
      // newTemplate is actually a document, so use templateFromFile (the correct template)
      actualTemplate = templateFromFile;
      console.log('[DocumentEditor] routeId is document, but using templateFromFile (correct template):', actualTemplate?.id);
    } else if (isDocumentMode && newTemplate) {
      // In document mode, prioritize newTemplate (the template loaded via template query)
      actualTemplate = newTemplate;
      console.log('[DocumentEditor] Document mode: Using newTemplate as actualTemplate:', actualTemplate?.id);
    } else if (newTemplate && (!isRouteIdDocument || Number(newTemplate.id) !== Number(routeId))) {
      // If newTemplate is not a document, use it
      actualTemplate = newTemplate;
    }
    console.log('[DocumentEditor] actualTemplate:', actualTemplate?.id, 'templateFromFile:', templateFromFile?.id, 'newTemplate:', newTemplate?.id, 'isRouteIdDocument:', isRouteIdDocument, 'isDocumentMode:', isDocumentMode, 'templateIdFromQuery:', templateIdFromQuery);
    
    // In document mode, ALWAYS prefer template over document to get the latest edited version
    // This ensures we use the edited template, not the original uploaded file
    // CRITICAL: In document mode, prioritize document's contentHtml if it exists
    // Only use template if document doesn't have contentHtml (e.g., when creating new document from template)
    let source: any = null;
    if (isDocumentMode && newDocument && newDocument.contentHtml && newDocument.contentHtml.trim() !== '') {
      // CRITICAL: If document has contentHtml, use it (this is the saved content)
      source = newDocument;
      console.log('[DocumentEditor] Document mode: Using document as source (has contentHtml):', source?.id, 'contentHtml length:', source?.contentHtml?.length || 0);
    } else if (isDocumentMode && actualTemplate) {
      // In document mode, if document has no contentHtml, use template (for new documents from template)
      source = actualTemplate;
      console.log('[DocumentEditor] Document mode: Using template as source (document has no contentHtml):', source?.id, 'contentHtml length:', source?.contentHtml?.length || 0);
    } else if (isDocumentMode && newTemplate) {
      // Fallback: If actualTemplate is not available, use newTemplate directly
      source = newTemplate;
      console.log('[DocumentEditor] Document mode: Using newTemplate as source (fallback):', source?.id, 'contentHtml length:', source?.contentHtml?.length || 0);
    } else if (isRouteIdDocument && newDocument && newDocument.contentHtml && newDocument.contentHtml.trim() !== '') {
      // If routeId is a document ID and document has contentHtml, use the document
      source = newDocument;
      console.log('[DocumentEditor] Using document as source (has contentHtml):', source?.id, 'contentHtml length:', source?.contentHtml?.length || 0);
    } else if (isRouteIdDocument && templateFromFile && templateFromFile.contentHtml && templateFromFile.contentHtml.trim() !== '') {
      // If routeId is a document ID but document has no contentHtml, use template (for new documents from template)
      source = templateFromFile;
      console.log('[DocumentEditor] routeId is document, but using templateFromFile (document has no contentHtml):', source?.id, 'contentHtml length:', source?.contentHtml?.length || 0);
    } else if (isRouteIdDocument && newDocument && !isDocumentMode) {
      // If routeId is a document ID and we're NOT in document mode, use the document
      source = newDocument;
      console.log('[DocumentEditor] Using document as source (not document mode):', source?.id);
    } else {
      // Otherwise use the template
      source = actualTemplate;
      console.log('[DocumentEditor] Using template as source:', source?.id);
    }
    
    console.log('[DocumentEditor] source:', source?.id, 'isRouteIdDocument:', isRouteIdDocument, 'hasContentHtml:', !!source?.contentHtml);
    console.log('[DocumentEditor] source.contentHtml length:', source?.contentHtml?.length || 0);
    console.log('[DocumentEditor] source.contentHtml preview:', source?.contentHtml?.substring(0, 100) || 'empty');
    console.log('[DocumentEditor] newTemplate?.contentHtml length:', newTemplate?.contentHtml?.length || 0);
    console.log('[DocumentEditor] actualTemplate?.contentHtml length:', actualTemplate?.contentHtml?.length || 0);
    
    // Skip if no source available
    if (!source) {
      console.warn('[DocumentEditor] No source available, waiting...');
      return;
    }
    
    // CRITICAL: If templateIdFromQuery is present, wait for template to load
    // This ensures we use the correct template that was selected
    if (templateIdFromQuery && !newTemplate && templateIsLoading) {
      console.log('[DocumentEditor] templateIdFromQuery present, waiting for template to load...', 'templateIdFromQuery:', templateIdFromQuery, 'templateIsLoading:', templateIsLoading);
      return;
    }
    
    // In document mode, wait for template to load if it's still loading
    if (isDocumentMode && !newTemplate && templateIsLoading) {
      console.log('[DocumentEditor] Document mode: Waiting for template to load...', 'templateIsLoading:', templateIsLoading);
      return;
    }
    
    // If routeId is a document and we're still loading the template, wait
    if (isRouteIdDocument && !templateFromFile && isLoadingTemplate) {
      console.log('[DocumentEditor] Waiting for templateByFilePath to load...', 'isLoadingTemplate:', isLoadingTemplate);
      return;
    }
    
            // If we have contentHtml, use it immediately (don't try to load file)
            if (source.contentHtml && source.contentHtml.trim() !== '') {
              console.log('[DocumentEditor] Using existing contentHtml from source');
              console.log('[DocumentEditor] Source object:', source);
              console.log('[DocumentEditor] Source placeholders:', source.placeholders);
              editor.contentHtml.value = source.contentHtml;
              // Nur Template-Name setzen, wenn wir nicht im Dokument-Modus sind oder wenn documentData noch nicht geladen wurde
              if (!isDocumentMode || !documentData.value) {
                editor.templateName.value = source.name;
              }
              
              // WICHTIG: Erst die Platzhalter aus dem Backend setzen, DANN scannen
              // So bleiben die mappedFieldId erhalten
              if (source.placeholders && Array.isArray(source.placeholders) && source.placeholders.length > 0) {
                console.log('[DocumentEditor] Setting placeholders from source:', source.placeholders.length);
                console.log('[DocumentEditor] Placeholders with mappedFieldId:', source.placeholders.map((p: any) => ({ key: p.key, mappedFieldId: p.mappedFieldId, mappedDbField: p.mappedDbField })));
                // Setze die Platzhalter direkt - KEIN Scannen nötig, da sie bereits aus dem Backend kommen
                editor.placeholders.value = source.placeholders;
                console.log('[DocumentEditor] Placeholders set, NOT scanning (already have placeholders from backend)');
              } else if (isDocumentMode && actualTemplate && actualTemplate.placeholders && Array.isArray(actualTemplate.placeholders) && actualTemplate.placeholders.length > 0) {
                // In document mode: If document has no placeholders, use template's placeholders (with mappings)
                console.log('[DocumentEditor] Document has no placeholders, using template placeholders with mappings:', actualTemplate.placeholders.length);
                console.log('[DocumentEditor] Template placeholders with mappedFieldId:', actualTemplate.placeholders.map((p: any) => ({ key: p.key, mappedFieldId: p.mappedFieldId, mappedDbField: p.mappedDbField })));
                editor.placeholders.value = actualTemplate.placeholders;
                console.log('[DocumentEditor] Placeholders set from template, NOT scanning');
              } else {
                // Nur scannen, wenn keine Platzhalter vorhanden sind
                console.log('[DocumentEditor] No placeholders from source or template, scanning...', 'source.placeholders:', source.placeholders);
                const scanned = editor.scanPlaceholders();
                console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length);
              }

              editor.markSaved();
              hasLoadedContent.value = true;
              return;
            }
    
    // If contentHtml is empty or missing, try to load the file
    // CRITICAL: In document mode, if the template has contentHtml, we should NOT load the file
    // Only load the file if contentHtml is truly missing (not just empty string from backend)
    const hasContentHtml = source.contentHtml && source.contentHtml.trim() !== '';
    const needsFileLoad = !hasContentHtml;
    
    console.log('[DocumentEditor] needsFileLoad:', needsFileLoad, 'hasContentHtml:', hasContentHtml, 'contentHtml length:', source.contentHtml?.length || 0);
    console.log('[DocumentEditor] source type:', source === newTemplate ? 'newTemplate' : source === newDocument ? 'newDocument' : source === actualTemplate ? 'actualTemplate' : 'unknown');
    
    // CRITICAL: Only use template with contentHtml if we're in document mode (creating new document from template)
    // When editing an existing document, use the document's content, not the template's
    if (isDocumentMode && needsFileLoad) {
      // In document mode, if source doesn't have contentHtml, check if template has it
      // This ensures we use the edited template content when creating a new document
      const templateWithContent = newTemplate?.contentHtml && newTemplate.contentHtml.trim() !== '' 
        ? newTemplate 
        : (actualTemplate?.contentHtml && actualTemplate.contentHtml.trim() !== '' 
            ? actualTemplate 
            : null);
      
      if (templateWithContent) {
        console.log('[DocumentEditor] Document mode: Template has contentHtml, using it instead of loading file. Template ID:', templateWithContent.id, 'contentHtml length:', templateWithContent.contentHtml.length);
        editor.contentHtml.value = templateWithContent.contentHtml;
        // Nur Template-Name setzen, wenn wir nicht im Dokument-Modus sind oder wenn documentData noch nicht geladen wurde
        if (!isDocumentMode || !documentData.value) {
          editor.templateName.value = templateWithContent.name;
        }
        linkedClientGroups.value = templateWithContent.linkedClientGroupIds || [];
        
        if (templateWithContent.placeholders && Array.isArray(templateWithContent.placeholders) && templateWithContent.placeholders.length > 0) {
          console.log('[DocumentEditor] Setting placeholders from template:', templateWithContent.placeholders.length);
          editor.placeholders.value = templateWithContent.placeholders;
        } else {
          const scanned = editor.scanPlaceholders();
          console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length);
        }
        
        editor.markSaved();
        hasLoadedContent.value = true;
        return;
      }
    }
    
    if (needsFileLoad) {
      
      // We need a template to load the file
      // CRITICAL: In document mode, use newTemplate (the template loaded via template query)
      // This ensures we use the correct template that was selected, not one found by file_path
      let templateToUse: any = null;
      
      if (isDocumentMode) {
        // In document mode, use newTemplate (the template loaded via template query)
        // This is the template that was selected, with the latest edits
        templateToUse = newTemplate;
        console.log('[DocumentEditor] Document mode: Using newTemplate (selected template):', templateToUse?.id);
      } else if (isRouteIdDocument) {
        // If routeId is a document (not document mode), we can ONLY use templateFromFile
        templateToUse = templateFromFile;
        console.log('[DocumentEditor] Document route (not document mode): Using templateFromFile:', templateToUse?.id);
      } else {
        // If routeId is a template, we can use newTemplate
        templateToUse = newTemplate;
        console.log('[DocumentEditor] Template mode: Using newTemplate:', templateToUse?.id);
      }
      
      console.log('[DocumentEditor] templateToUse for file loading:', templateToUse?.id, 'templateFromFile:', templateFromFile?.id, 'newTemplate:', newTemplate?.id);
      
      if (!templateToUse || !templateToUse.id) {
        // If routeId is a document and we don't have a template, we can't load the file
        if (isRouteIdDocument) {
          console.warn('[DocumentEditor] Route ID is a document ID. Cannot load file without template ID (templateByFilePath not found). Using empty content.');
        } else {
          console.warn('[DocumentEditor] No template available for file loading. Using empty content.');
        }
        editor.contentHtml.value = '<p></p>';
        // Nur Template-Name setzen, wenn wir nicht im Dokument-Modus sind oder wenn documentData noch nicht geladen wurde
        if (!isDocumentMode || !documentData.value) {
          editor.templateName.value = source.name;
        }
        linkedClientGroups.value = source.linkedClientGroupIds || [];
        
        // WICHTIG: Erst die Platzhalter aus dem Backend setzen, DANN scannen
        // So bleiben die mappedFieldId erhalten
        if (source.placeholders && source.placeholders.length > 0) {
          console.log('[DocumentEditor] Setting placeholders from source before scan:', source.placeholders.length);
          editor.placeholders.value = source.placeholders;
        }

        // Automatically scan for placeholders when content is loaded
        // scanPlaceholders() behält jetzt die mappedFieldId bei
        const scanned = editor.scanPlaceholders();
        console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length, 'with preserved mappings');
        
        editor.markSaved();
        hasLoadedContent.value = true;
        return;
      }
      
      try {
        // Use template ID for file loading
        const fileIdNum = Number(templateToUse.id);
        
        // Double-check: Make sure we're not using document ID
        if (currentDocumentId.value && fileIdNum === Number(currentDocumentId.value)) {
          console.error(`ERROR: Template ID (${fileIdNum}) matches document ID! This should not happen.`);
        editor.contentHtml.value = '<p></p>';
        // Nur Template-Name setzen, wenn wir nicht im Dokument-Modus sind oder wenn documentData noch nicht geladen wurde
        if (!isDocumentMode || !documentData.value) {
          editor.templateName.value = source.name;
        }
        linkedClientGroups.value = source.linkedClientGroupIds || [];
        
        // WICHTIG: Erst die Platzhalter aus dem Backend setzen, DANN scannen
        // So bleiben die mappedFieldId erhalten
        if (source.placeholders && source.placeholders.length > 0) {
          console.log('[DocumentEditor] Setting placeholders from source before scan:', source.placeholders.length);
          editor.placeholders.value = source.placeholders;
        }

        // Automatically scan for placeholders when content is loaded
        // scanPlaceholders() behält jetzt die mappedFieldId bei
        const scanned = editor.scanPlaceholders();
        console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length, 'with preserved mappings');
          
          editor.markSaved();
          hasLoadedContent.value = true;
          return;
        }
        
        console.log(`Loading file for template ID: ${fileIdNum} (NOT document ID ${currentDocumentId.value || 'N/A'})`);
        const fileResponse = await DocumentAPI.getDocumentFile(fileIdNum);
        const blob = fileResponse.data;
        
        // Check if it's a DOCX file
        if (blob.type.includes('word') || blob.type.includes('docx') || routeId) {
          // Convert blob to File
          const file = new File([blob], `${source.name}.docx`, { 
            type: blob.type || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
          });
          
          // Convert DOCX to HTML using mammoth
          const htmlContent = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
              try {
                const arrayBuffer = e.target?.result as ArrayBuffer;
                const result = await mammoth.convertToHtml({ arrayBuffer });
                resolve(result.value);
              } catch (error) {
                reject(error);
              }
            };
            reader.onerror = () => reject(new Error('Fehler beim Lesen der Datei'));
            reader.readAsArrayBuffer(file);
          });
          
          // Update editor content
          editor.contentHtml.value = htmlContent.trim() || '<p></p>';
          
          // WICHTIG: Wenn Platzhalter aus dem Backend vorhanden sind, KEIN Scannen!
          // So bleiben die mappedFieldId erhalten
          if (source.placeholders && source.placeholders.length > 0) {
            console.log('[DocumentEditor] Setting placeholders from source (NO scan):', source.placeholders.length);
            console.log('[DocumentEditor] Placeholders with mappedFieldId:', source.placeholders.map((p: any) => ({ key: p.key, mappedFieldId: p.mappedFieldId })));
            editor.placeholders.value = source.placeholders;
            console.log('[DocumentEditor] Placeholders set from backend, NOT scanning to preserve mappings');
          } else {
            // Nur scannen, wenn keine Platzhalter vorhanden sind
            console.log('[DocumentEditor] No placeholders from source, scanning...');
            const scanned = editor.scanPlaceholders();
            console.log('[DocumentEditor] Auto-scanned placeholders from file:', scanned.length);
          }
          
          // Update template/document in backend with HTML content (nur wenn Template-Modus)
          if (!isDocumentMode && !isRouteIdDocument && templateId.value) {
            await documentEditorApi.updateTemplate(templateId.value, {
              contentHtml: htmlContent.trim(),
              placeholders: editor.placeholders.value,
            });
          }
          
          nMessage.success('Dokument geladen und zu HTML konvertiert');
          hasLoadedContent.value = true;
        } else {
          // For other file types, use existing content or show error
          editor.contentHtml.value = source.contentHtml || '<p>Datei konnte nicht geladen werden</p>';
          
          // WICHTIG: Erst die Platzhalter aus dem Backend setzen, DANN scannen
          // So bleiben die mappedFieldId erhalten
          if (source.placeholders && source.placeholders.length > 0) {
            console.log('[DocumentEditor] Setting placeholders from source before scan:', source.placeholders.length);
            editor.placeholders.value = source.placeholders;
          }
          
          // Automatically scan for placeholders when content is loaded
          // scanPlaceholders() behält jetzt die mappedFieldId bei
          const scanned = editor.scanPlaceholders();
          console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length, 'with preserved mappings');
          
          hasLoadedContent.value = true;
        }
      } catch (error: any) {
        console.error('Error loading document file:', error);
        // Reset hasLoadedContent on error so we can retry if needed
        hasLoadedContent.value = false;
        
        // Check if error is because we tried to load document file instead of template file
        if (error?.response?.data?.error?.includes('Use template file instead')) {
          console.warn('Attempted to load document file, but should use template file. This should not happen.');
        }
        
                nMessage.warning('Datei konnte nicht geladen werden. Verwenden Sie vorhandenen Inhalt.');
                editor.contentHtml.value = source.contentHtml || '<p></p>';

                // WICHTIG: Erst die Platzhalter aus dem Backend setzen, DANN scannen
                // So bleiben die mappedFieldId erhalten
                if (source.placeholders && source.placeholders.length > 0) {
                  console.log('[DocumentEditor] Setting placeholders from source before scan:', source.placeholders.length);
                  editor.placeholders.value = source.placeholders;
                }

                // Automatically scan for placeholders when content is loaded
                // scanPlaceholders() behält jetzt die mappedFieldId bei
                const scanned = editor.scanPlaceholders();
                console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length, 'with preserved mappings');
        
        hasLoadedContent.value = true; // Mark as loaded even on error to prevent infinite retries
      }
            } else {
              // Use existing HTML content
              editor.contentHtml.value = source.contentHtml;
              
              // WICHTIG: Wenn Platzhalter bereits vom Backend kommen (mit Mappings), verwende diese direkt
              // Nur scannen, wenn keine Platzhalter vorhanden sind
              if (source.placeholders && Array.isArray(source.placeholders) && source.placeholders.length > 0) {
                console.log('[DocumentEditor] Setting placeholders from source (document mode):', source.placeholders.length);
                console.log('[DocumentEditor] Placeholders with mappedFieldId:', source.placeholders.map((p: any) => ({ key: p.key, mappedFieldId: p.mappedFieldId, mappedDbField: p.mappedDbField })));
                // Setze die Platzhalter direkt - KEIN Scannen nötig, da sie bereits aus dem Backend kommen
                editor.placeholders.value = source.placeholders;
                console.log('[DocumentEditor] Placeholders set from document, NOT scanning (already have placeholders with mappings from backend)');
              } else {
                // Nur scannen, wenn keine Platzhalter vorhanden sind
                console.log('[DocumentEditor] No placeholders from source, scanning...', 'source.placeholders:', source.placeholders);
                const scanned = editor.scanPlaceholders();
                console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length);
              }

              hasLoadedContent.value = true;
            }
    
    // Nur Template-Name setzen, wenn wir nicht im Dokument-Modus sind oder wenn documentData noch nicht geladen wurde
    if (!isDocumentMode || !documentData.value) {
      editor.templateName.value = source.name;
    }
    linkedClientGroups.value = source.linkedClientGroupIds || [];
    
    // Wenn Mandant vorhanden und im Dokument-Modus: Platzhalter automatisch füllen
    // WICHTIG: Nur füllen, wenn noch keine Werte gesetzt sind (um bereits ausgefüllte Werte nicht zu überschreiben)
    if (isDocumentMode && newClient && editor.placeholders.value.length > 0) {
      const fillValues = mapClientDataToPlaceholders(newClient, editor.placeholders.value);
      let filledCount = 0;
      Object.keys(fillValues).forEach((key) => {
        // Nur füllen, wenn noch kein Wert gesetzt ist
        if (!editor.fillValues.value[key] && fillValues[key] !== null && fillValues[key] !== undefined && fillValues[key] !== '') {
          // Format date values to yyyy-MM-dd format
          let valueToSet = fillValues[key];
          const placeholder = editor.placeholders.value.find((p: any) => (p.key || p.name) === key);
          if (placeholder && placeholder.type === 'date' && valueToSet) {
            // Format date value to yyyy-MM-dd
            if (typeof valueToSet === 'number') {
              // Timestamp - convert to yyyy-MM-dd
              const date = new Date(valueToSet);
              valueToSet = date.toISOString().split('T')[0];
              console.log('[DocumentEditor] Converted timestamp to date string for key:', key, 'from:', fillValues[key], 'to:', valueToSet);
            } else if (valueToSet instanceof Date) {
              // Date object - convert to yyyy-MM-dd
              valueToSet = valueToSet.toISOString().split('T')[0];
              console.log('[DocumentEditor] Converted Date object to date string for key:', key, 'to:', valueToSet);
            } else if (typeof valueToSet === 'string' && !/^\d{4}-\d{2}-\d{2}$/.test(valueToSet)) {
              // String that's not in yyyy-MM-dd format - try to parse and format
              const date = new Date(valueToSet);
              if (!isNaN(date.getTime())) {
                valueToSet = date.toISOString().split('T')[0];
                console.log('[DocumentEditor] Converted date string to yyyy-MM-dd for key:', key, 'from:', fillValues[key], 'to:', valueToSet);
              }
            }
          }
          console.log('[DocumentEditor] Auto-filling placeholder:', key, 'with value:', valueToSet);
          editor.updateFillValue(key, valueToSet);
          filledCount++;
        } else {
          console.log('[DocumentEditor] Skipping auto-fill for placeholder:', key, 'current value:', editor.fillValues.value[key], 'new value:', fillValues[key]);
        }
      });
      if (filledCount > 0) {
        nMessage.success(`${filledCount} Felder automatisch ausgefüllt`);
        
        // Automatisch Platzhalter scannen, wenn Daten eingefügt wurden
        // Warte kurz, damit der Editor-Content aktualisiert werden kann
        setTimeout(() => {
          console.log('[DocumentEditor] Automatically scanning placeholders after auto-fill');
          const scanned = editor.scanPlaceholders();
          console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length);
          if (scanned.length > 0 && editor.placeholders.value.length === 0) {
            // Nur Nachricht anzeigen, wenn vorher keine Platzhalter vorhanden waren
            nMessage.success(`${scanned.length} Platzhalter automatisch erkannt`);
          }
        }, 500);
      }
    }
    
    // Wenn verknüpfte Mandanten vorhanden sind: Platzhalter automatisch füllen
    if (newLinkedClients && newLinkedClients.length > 0 && newAllClients && newAllClients.length > 0 && editor.placeholders.value.length > 0) {
      // Verwende den ersten verknüpften Mandanten für die Datenübernahme
      const linkedClient = newAllClients.find((c: any) => c.id === newLinkedClients[0]);
      if (linkedClient) {
        const fillValues = mapClientDataToPlaceholders(linkedClient, editor.placeholders.value);
        let filledCount = 0;
        Object.keys(fillValues).forEach((key) => {
          // Nur füllen, wenn noch kein Wert gesetzt ist
          if (!editor.fillValues.value[key] && fillValues[key] !== null && fillValues[key] !== undefined) {
            editor.updateFillValue(key, fillValues[key]);
            filledCount++;
          }
        });
        if (filledCount > 0 && !hasAppliedLinkedClients.value) {
          const clientName = linkedClient.type === 'Natürliche Person' 
            ? `${linkedClient.firstName || ''} ${linkedClient.lastName || ''}`.trim()
            : linkedClient.companyName || 'Unbekannt';
          nMessage.success(`Daten von ${clientName} übernommen`);
          hasAppliedLinkedClients.value = true;
        }
      }
    }
    
    editor.markSaved();
  },
  { immediate: true }
);

// Speichern
const saveMutation = useMutation({
  mutationFn: async () => {
    // WICHTIG: Prüfe die placeholders VOR getTemplateData()
    console.log('[DocumentEditor] Placeholders BEFORE getTemplateData:', editor.placeholders.value);
    editor.placeholders.value.forEach((p: any) => {
      console.log(`[DocumentEditor] Placeholder ${p.key} BEFORE: mappedFieldId=${p.mappedFieldId}, mappedDbField=${p.mappedDbField}`);
    });
    
    const data = editor.getTemplateData();
    
    // Log placeholders to verify mappedFieldId is included
    console.log('[DocumentEditor] Saving placeholders:', data.placeholders);
    data.placeholders.forEach((p: any) => {
      console.log(`[DocumentEditor] Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}, mappedDbField=${p.mappedDbField}`);
    });
    
    // Determine if we're editing a document (not a template)
    // Check if routeId is a document ID or if we have a currentDocumentId
    const hadDocumentIdBefore = !!currentDocumentId.value;
    const isEditingDocument = currentDocumentId.value || (documentData.value && Number(documentData.value.id) === Number(routeId)) || routeIdDocument.value?.isDocument;
    
    // Prüfen, ob es ein Dokument ist (nicht Template)
    const isDocument = documentData.value && !(documentData.value as any).is_template && !(documentData.value as any).isTemplate;
    
    console.log('[DocumentEditor] Save mutation - isEditingDocument:', isEditingDocument, 'currentDocumentId:', currentDocumentId.value, 'document.id:', documentData.value?.id, 'routeId:', routeId, 'isDocumentMode:', isDocumentMode, 'isDocument:', isDocument);
    
    if (isDocumentMode || isEditingDocument || isDocument) {
      // Im Dokument-Modus: Dokument speichern oder erstellen
      if (currentDocumentId.value || (documentData.value && Number(documentData.value.id) === Number(routeId))) {
        // Dokument aktualisieren
        const docId = currentDocumentId.value || (documentData.value?.id || routeId);
        console.log('[DocumentEditor] Updating document with ID:', docId);
        // Include clientId if available (from query or document)
        const clientIdToSave = clientId.value || documentData.value?.clientId || (documentData.value as any)?.client_id;
        console.log('[DocumentEditor] Saving with clientId:', clientIdToSave, 'from clientId computed:', clientId.value, 'from documentData:', documentData.value?.clientId || (documentData.value as any)?.client_id);
        return documentEditorApi.updateDocument(String(docId), {
          contentHtml: data.contentHtml,
          placeholders: data.placeholders,
          clientId: clientIdToSave,
        });
      } else {
        // Neues Dokument aus Vorlage erstellen
        if (!clientId.value) {
          throw new Error('Client-ID fehlt für Dokument-Erstellung');
        }
        const actualTemplateId = templateId.value || routeId;
        if (!actualTemplateId) {
          throw new Error('Template-ID fehlt für Dokument-Erstellung');
        }
        const result = await documentEditorApi.createDocumentFromTemplate(actualTemplateId, clientId.value, {
          contentHtml: data.contentHtml,
          placeholders: data.placeholders,
          fillValues: editor.fillValues.value,
        });
        // Mark that a new document was created by storing it in the result
        (result as any).__wasNewDocument = true;
        currentDocumentId.value = result.id;
        
        // Automatisch den ausgewählten Mandanten als verknüpften Mandanten hinzufügen
        const clientIdStr = String(clientId.value);
        if (clientId.value && !linkedClients.value.includes(clientIdStr)) {
          console.log('[DocumentEditor] Automatically adding clientId to linkedClients after document creation:', clientIdStr);
          // Verwende handleLinkedClientsUpdate, damit die UI korrekt aktualisiert wird
          handleLinkedClientsUpdate([...linkedClients.value, clientIdStr]);
        }
        
        // URL aktualisieren mit Dokument-ID
        // CRITICAL: Keep templateId and clientId in query so we can always find the correct template and client
        router.replace({
          path: `/editor/${actualTemplateId}`,
          query: {
            ...route.query,
            documentId: result.id,
            templateId: actualTemplateId, // CRITICAL: Save templateId in query
            clientId: clientId.value, // CRITICAL: Save clientId in query
            mode: 'document', // CRITICAL: Keep mode in query
          },
        });
        return result;
      }
    } else {
      // Im Template-Modus: Vorlage aktualisieren
      const actualTemplateId = templateId.value || routeId;
      if (!actualTemplateId) {
        throw new Error('Template-ID fehlt');
      }
      console.log('[DocumentEditor] Updating template with ID:', actualTemplateId);
      return documentEditorApi.updateTemplate(actualTemplateId, {
        contentHtml: data.contentHtml,
        placeholders: data.placeholders,
        linkedClientGroupIds: [],
      });
    }
  },
  onSuccess: (result, variables) => {
    editor.markSaved();
    // Nur Erfolgsmeldung anzeigen, wenn es kein Auto-Save war
    if (!isAutoSaving.value) {
      // Determine if we saved a document or template
      const isEditingDocument = currentDocumentId.value || (documentData.value && Number(documentData.value.id) === Number(routeId)) || routeIdDocument.value?.isDocument;
      // Check if a new document was created (marked in mutationFn)
      const wasCreatingNewDocument = (result as any)?.__wasNewDocument === true;
      
      // If a new document was created, invalidate the documents list query
      if (wasCreatingNewDocument) {
        console.log('[DocumentEditor] New document created, invalidating documents list');
        queryClient.invalidateQueries({ queryKey: ['documents'] });
      }
      
      const message = (isDocumentMode || isEditingDocument) ? 'Dokument gespeichert' : 'Template gespeichert';
      nMessage.success(message);
    }
    saving.value = false;
  },
  onError: (error: any) => {
    nMessage.error(error.message || 'Fehler beim Speichern');
    saving.value = false;
  },
});

function handleSave() {
  saving.value = true;
  saveMutation.mutate();
}

function handleSavePlaceholders() {
  handleSave();
}

function handleRescan() {
  console.log('[DocumentEditor] handleRescan - placeholders before scan:', editor.placeholders.value);
  const extracted = editor.scanPlaceholders();
  console.log('[DocumentEditor] handleRescan - placeholders after scan:', extracted);
  nMessage.success(`${extracted.length} Platzhalter gefunden`);
}

function handleLinkedClientsUpdate(clientIds: string[]) {
  console.log('[DocumentEditor] handleLinkedClientsUpdate called with:', clientIds, 'current linkedClients:', linkedClients.value);
  linkedClients.value = clientIds;
  
  // Wenn ein Mandant hinzugefügt wurde, Daten sofort übernehmen
  if (clientIds.length > 0 && editor.placeholders.value.length > 0) {
    // Prüfe, ob allClients geladen sind, sonst warte kurz
    if (allClients.value.length > 0) {
      const linkedClient = allClients.value.find((c: any) => String(c.id) === String(clientIds[0]));
      if (linkedClient) {
        console.log('[DocumentEditor] Found linked client, filling placeholders:', linkedClient);
        console.log('[DocumentEditor] Client data - zip:', linkedClient.zip, 'city:', linkedClient.city, 'street:', linkedClient.street, 'number:', linkedClient.number, 'salutation:', linkedClient.salutation, 'type:', linkedClient.type, 'salutation type:', typeof linkedClient.salutation);
        console.log('[DocumentEditor] Full linkedClient object:', JSON.stringify(linkedClient, null, 2));
        const fillValues = mapClientDataToPlaceholders(linkedClient, editor.placeholders.value);
        console.log('[DocumentEditor] Mapped fillValues:', fillValues);
        console.log('[DocumentEditor] Anrede in fillValues:', fillValues['Anrede'] || fillValues['anrede'], 'all fillValues keys:', Object.keys(fillValues));
        console.log('[DocumentEditor] Client salutation details - value:', linkedClient.salutation, 'type:', typeof linkedClient.salutation, 'is empty:', !linkedClient.salutation || linkedClient.salutation === '');
        console.log('[DocumentEditor] Current fillValues before update:', editor.fillValues.value);
        let filledCount = 0;
        Object.keys(fillValues).forEach((key) => {
          // Nur füllen, wenn noch kein Wert gesetzt ist ODER wenn der neue Wert nicht leer ist
          const currentValue = editor.fillValues.value[key];
          const newValue = fillValues[key];
          // Prüfe, ob newValue ein gültiger Wert ist (nicht null, undefined oder leerer String)
          const isValidValue = newValue !== null && newValue !== undefined && String(newValue).trim() !== '';
          // Prüfe, ob currentValue leer ist (null, undefined oder leerer String)
          const isCurrentValueEmpty = !currentValue || currentValue === '' || currentValue === null || String(currentValue).trim() === '';
          const shouldUpdate = isCurrentValueEmpty && isValidValue;
          
          // Special handling for Anrede: always update if we have a valid value, even if currentValue exists
          const isAnredeKey = key.toLowerCase() === 'anrede' || key.toLowerCase() === 'salutation';
          const shouldUpdateAnrede = isAnredeKey && isValidValue;
          
          if (shouldUpdate || shouldUpdateAnrede) {
            // Format date values to yyyy-MM-dd format
            let formattedValue = newValue;
            const placeholder = editor.placeholders.value.find((p: any) => (p.key || p.name) === key);
            if (placeholder && placeholder.type === 'date' && newValue) {
              // Format date value to yyyy-MM-dd
              if (typeof newValue === 'number') {
                // Timestamp - convert to yyyy-MM-dd
                const date = new Date(newValue);
                formattedValue = date.toISOString().split('T')[0];
                console.log('[DocumentEditor] Converted timestamp to date string for key:', key, 'from:', newValue, 'to:', formattedValue);
              } else if (newValue instanceof Date) {
                // Date object - convert to yyyy-MM-dd
                formattedValue = newValue.toISOString().split('T')[0];
                console.log('[DocumentEditor] Converted Date object to date string for key:', key, 'to:', formattedValue);
              } else if (typeof newValue === 'string' && !/^\d{4}-\d{2}-\d{2}$/.test(newValue)) {
                // String that's not in yyyy-MM-dd format - try to parse and format
                const date = new Date(newValue);
                if (!isNaN(date.getTime())) {
                  formattedValue = date.toISOString().split('T')[0];
                  console.log('[DocumentEditor] Converted date string to yyyy-MM-dd for key:', key, 'from:', newValue, 'to:', formattedValue);
                }
              }
            }
            console.log('[DocumentEditor] Setting fillValue for key:', key, 'value:', formattedValue, '(was:', currentValue, ')', 'isAnredeKey:', isAnredeKey);
            editor.updateFillValue(key, formattedValue);
            filledCount++;
          } else {
            console.log('[DocumentEditor] Skipping fillValue for key:', key, 'reason: already set or invalid value', 'current value:', currentValue, 'new value:', newValue, 'isValidValue:', isValidValue, 'isCurrentValueEmpty:', isCurrentValueEmpty, 'isAnredeKey:', isAnredeKey);
          }
        });
        console.log('[DocumentEditor] Final fillValues after update:', editor.fillValues.value);
        console.log('[DocumentEditor] Filled count:', filledCount);
        if (filledCount > 0) {
          const clientName = linkedClient.type === 'Natürliche Person' 
            ? `${linkedClient.firstName || ''} ${linkedClient.lastName || ''}`.trim()
            : linkedClient.companyName || 'Unbekannt';
          nMessage.success(`Daten von ${clientName} übernommen`);
          
          // Automatisch Platzhalter scannen, wenn Daten eingefügt wurden
          // Warte kurz, damit der Editor-Content aktualisiert werden kann
          setTimeout(() => {
            console.log('[DocumentEditor] Automatically scanning placeholders after data insertion');
            const scanned = editor.scanPlaceholders();
            console.log('[DocumentEditor] Auto-scanned placeholders:', scanned.length);
            if (scanned.length > 0 && editor.placeholders.value.length === 0) {
              // Nur Nachricht anzeigen, wenn vorher keine Platzhalter vorhanden waren
              nMessage.success(`${scanned.length} Platzhalter automatisch erkannt`);
            }
          }, 500);
        }
      } else {
        console.log('[DocumentEditor] Linked client not found in allClients, waiting...');
        // Warte kurz und versuche es erneut
        setTimeout(() => {
          if (allClients.value.length > 0) {
            const linkedClient = allClients.value.find((c: any) => String(c.id) === String(clientIds[0]));
            if (linkedClient) {
              console.log('[DocumentEditor] Found linked client after delay, filling placeholders');
              const fillValues = mapClientDataToPlaceholders(linkedClient, editor.placeholders.value);
              Object.keys(fillValues).forEach((key) => {
                if (!editor.fillValues.value[key] && fillValues[key] !== null && fillValues[key] !== undefined) {
                  editor.updateFillValue(key, fillValues[key]);
                }
              });
            }
          }
        }, 500);
      }
    } else {
      console.log('[DocumentEditor] allClients not loaded yet, waiting...');
      // Warte, bis allClients geladen sind
      setTimeout(() => {
        if (allClients.value.length > 0 && clientIds.length > 0) {
          const linkedClient = allClients.value.find((c: any) => String(c.id) === String(clientIds[0]));
          if (linkedClient) {
            console.log('[DocumentEditor] Found linked client after allClients loaded, filling placeholders');
            const fillValues = mapClientDataToPlaceholders(linkedClient, editor.placeholders.value);
            Object.keys(fillValues).forEach((key) => {
              if (!editor.fillValues.value[key] && fillValues[key] !== null && fillValues[key] !== undefined) {
                editor.updateFillValue(key, fillValues[key]);
              }
            });
          }
        }
      }, 500);
    }
  }
}

function handlePlaceholderClick(key: string) {
  activeTab.value = 'form';
  // ggf. Event an FormPanel, um Feld zu fokussieren
}

function handleUpdateFillValues(values: Record<string, any>) {
  Object.keys(values).forEach((key) => {
    editor.updateFillValue(key, values[key]);
  });
}

async function handleExport(format: 'pdf' | 'docx') {
  try {
    // Check if all placeholders are filled
    const fillValues = editor.fillValues.value || {};
    const placeholders = editor.placeholders.value || [];
    
    // Find unfilled placeholders (excluding those with default values or empty strings that are allowed)
    const unfilledPlaceholders = placeholders.filter((p: any) => {
      const key = p.key || p.name;
      if (!key) return false;
      
      const value = fillValues[key];
      // Consider placeholder unfilled if:
      // - value is undefined, null, or empty string
      // - AND it's not explicitly marked as optional
      return (value === undefined || value === null || value === '') && !p.optional;
    });
    
    // If there are unfilled placeholders, show warning
    if (unfilledPlaceholders.length > 0) {
      const unfilledNames = unfilledPlaceholders.map((p: any) => p.label || p.key || p.name).join(', ');
      const unfilledCount = unfilledPlaceholders.length;
      
      return new Promise<void>((resolve) => {
        nDialog.warning({
          title: 'Nicht alle Platzhalter ausgefüllt',
          content: `${unfilledCount} Platzhalter ${unfilledCount === 1 ? 'ist' : 'sind'} noch nicht ausgefüllt: ${unfilledNames}. Möchten Sie trotzdem exportieren?`,
          positiveText: 'Trotzdem exportieren',
          negativeText: 'Abbrechen',
          onPositiveClick: async () => {
            await performExport(format);
            resolve();
          },
          onNegativeClick: () => {
            resolve();
          }
        });
      });
    }
    
    // All placeholders are filled, proceed with export
    await performExport(format);
  } catch (error: any) {
    console.error('[DocumentEditor] Export error:', error);
    nMessage.error(error.message || 'Fehler beim Export');
  }
}

async function performExport(format: 'pdf' | 'docx') {
  try {
    // Determine which ID to use for export
    // In document mode, use document ID if it exists (to use saved content)
    // Otherwise, use template ID
    let idToUse: string | undefined;
    let useDocumentContent = false;
    
    if (isDocumentMode && currentDocumentId.value) {
      // In document mode, if we have a document ID, use it to export the saved content
      idToUse = currentDocumentId.value;
      useDocumentContent = true;
      console.log('[DocumentEditor] Document mode: Using document ID for export:', idToUse);
    } else if (isDocumentMode) {
      // In document mode, but no document ID yet, use template ID
      idToUse = templateIdFromQuery || templateId.value || routeId;
      console.log('[DocumentEditor] Document mode: Using template ID for export (no document yet):', idToUse);
    } else {
      // In template mode, use the template ID
      idToUse = templateId.value || routeId;
      console.log('[DocumentEditor] Template mode: Using template ID for export:', idToUse);
    }
    
    if (!idToUse) {
      nMessage.error('Keine ID für Export gefunden');
      console.error('[DocumentEditor] No ID found for export. templateIdFromQuery:', templateIdFromQuery, 'templateId.value:', templateId.value, 'routeId:', routeId);
      return;
    }
    
    console.log('[DocumentEditor] Exporting with ID:', idToUse, 'format:', format, 'isDocumentMode:', isDocumentMode, 'useDocumentContent:', useDocumentContent);
    console.log('[DocumentEditor] Fill values:', editor.fillValues.value);
    console.log('[DocumentEditor] Current contentHtml length:', editor.contentHtml.value?.length || 0);
    
    // Ensure fillValues is an object (not undefined or null)
    const fillValues = editor.fillValues.value || {};
    
    // Always include current contentHtml if available (for live preview with edited content)
    // This ensures the export uses the latest edited content, not just the saved version
    const exportPayload: any = { ...fillValues };
    
    // CRITICAL: Set exportFormat explicitly (don't rely on it being in fillValues)
    exportPayload.exportFormat = format;
    console.log('[DocumentEditor] Setting exportFormat in payload:', format, 'type:', typeof format);
    
    // Include contentHtml if available (either from document or current editor state)
    if (editor.contentHtml.value && editor.contentHtml.value.trim() !== '') {
      exportPayload.contentHtml = editor.contentHtml.value;
      console.log('[DocumentEditor] Including contentHtml in export (length:', editor.contentHtml.value.length, ')');
    } else {
      console.log('[DocumentEditor] No contentHtml available, using file from backend');
    }
    
    console.log('[DocumentEditor] Export payload keys:', Object.keys(exportPayload));
    console.log('[DocumentEditor] Export payload exportFormat:', exportPayload.exportFormat);
    console.log('[DocumentEditor] Export payload fillValues (excluding exportFormat/contentHtml):', 
      Object.keys(exportPayload).filter(k => k !== 'exportFormat' && k !== 'contentHtml').map(k => `${k}=${exportPayload[k]}`));
    
    // Fetch the file as blob
    const blob = await documentEditorApi.exportTemplate(
      String(idToUse),
      exportPayload,
      format
    );
    
    // Create a blob URL and trigger download
    // Use document name if in document mode, otherwise use template name
    let filename: string;
    if (isDocumentMode && documentData.value) {
      const docName = (documentData.value as any).title || (documentData.value as any).name || editor.templateName.value;
      filename = `${docName}.${format}`;
      console.log('[DocumentEditor] Using document name for export:', docName);
    } else {
      filename = `${editor.templateName.value}.${format}`;
      console.log('[DocumentEditor] Using template name for export:', editor.templateName.value);
    }
    
    // Determine correct MIME type based on format
    const mimeType = format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    
    // Create blob with correct MIME type
    const typedBlob = new Blob([blob], { type: mimeType });
    const blobUrl = window.URL.createObjectURL(typedBlob);
    
    // Use window.document to ensure we're using the global document object
    const doc = window.document;
    const link = doc.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.style.display = 'none';
    
    // Explicitly set download attribute to force download
    link.setAttribute('download', filename);
    link.setAttribute('type', mimeType);
    
    // Add to DOM
    doc.body.appendChild(link);
    
    // Trigger download with a small delay to ensure everything is ready
    setTimeout(() => {
      link.click();
      
      // Clean up after download starts
      setTimeout(() => {
        if (link.parentNode) {
          doc.body.removeChild(link);
        }
        window.URL.revokeObjectURL(blobUrl);
      }, 100);
    }, 10);
    
    nMessage.success('Export erfolgreich - Datei wird heruntergeladen');
  } catch (error: any) {
    console.error('[DocumentEditor] Export error:', error);
    nMessage.error(error.message || 'Fehler beim Export');
    throw error; // Re-throw to be caught by handleExport
  }
}

// Auto-Save: Automatisches Speichern nach Änderungen
const autoSaveEnabled = ref(true);
const isAutoSaving = ref(false);
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

// Debounced auto-save function
const debouncedAutoSave = useDebounceFn(async () => {
  if (!autoSaveEnabled.value || isAutoSaving.value || saving.value) {
    return;
  }
  
  // Nur speichern, wenn es Änderungen gibt
  if (!editor.isDirty.value) {
    return;
  }
  
  // Prüfen, ob wir überhaupt etwas zu speichern haben
  const hasContent = editor.contentHtml.value && editor.contentHtml.value.trim() !== '';
  if (!hasContent) {
    return;
  }
  
  // Für neue Dokumente: Prüfen, ob clientId vorhanden ist
  const isEditingDocument = currentDocumentId.value || (documentData.value && Number(documentData.value.id) === Number(routeId)) || routeIdDocument.value?.isDocument;
  if ((isDocumentMode || isEditingDocument) && !currentDocumentId.value && !documentData.value) {
    // Neues Dokument: Braucht clientId
    if (!clientId.value) {
      console.log('[DocumentEditor] Auto-save skipped: No clientId for new document');
      return;
    }
  }
  
  console.log('[DocumentEditor] Auto-saving...', {
    isDocumentMode,
    isEditingDocument,
    currentDocumentId: currentDocumentId.value,
    documentId: documentData.value?.id,
    routeId,
  });
  isAutoSaving.value = true;
  
  try {
    await saveMutation.mutateAsync();
    console.log('[DocumentEditor] Auto-save successful');
  } catch (error: any) {
    console.error('[DocumentEditor] Auto-save failed:', error);
    // Keine Fehlermeldung bei Auto-Save, um den Benutzer nicht zu stören
    // Aber logge es für Debugging
    if (error.message) {
      console.error('[DocumentEditor] Auto-save error message:', error.message);
    }
  } finally {
    isAutoSaving.value = false;
  }
}, 2000); // 2 Sekunden Verzögerung

// Watch für Auto-Save
watch(
  [
    () => editor.contentHtml.value, 
    () => editor.placeholders.value, 
    () => editor.templateName.value, 
    () => linkedClients.value,
    () => editor.fillValues.value, // Auch fillValues für Dokumente überwachen
    () => currentDocumentId.value, // Auch bei Änderung der Dokument-ID
    () => documentData.value?.id, // Auch bei Änderung des Dokuments
  ],
  () => {
    if (autoSaveEnabled.value && hasLoadedContent.value) {
      // Nur auto-save, wenn Content bereits geladen wurde
      debouncedAutoSave();
    }
  },
  { deep: true }
);

// Watch für clientId: Automatisch als verknüpften Mandanten hinzufügen
watch(
  [() => clientId.value, () => isDocumentMode, () => hasLoadedContent.value, () => allClients.value.length],
  ([newClientId, newIsDocumentMode, newHasLoadedContent, allClientsLength]) => {
    // Nur in Dokument-Modus und wenn Content geladen wurde und allClients verfügbar sind
    if (newIsDocumentMode && newHasLoadedContent && newClientId && allClientsLength > 0) {
      // Prüfen, ob der Mandant bereits in linkedClients ist
      const clientIdStr = String(newClientId);
      if (!linkedClients.value.includes(clientIdStr)) {
        console.log('[DocumentEditor] Watch: Automatically adding clientId to linkedClients:', clientIdStr);
        // Verwende handleLinkedClientsUpdate, damit die UI korrekt aktualisiert wird
        handleLinkedClientsUpdate([...linkedClients.value, clientIdStr]);
      }
    }
  },
  { immediate: true }
);

onMounted(() => {
  if (!templateId) {
    router.push('/templates');
  }
  // Reset hasLoadedContent when component is mounted
  hasLoadedContent.value = false;
});

onBeforeUnmount(() => {
  // Cleanup: Finales Speichern beim Verlassen
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
  if (editor.isDirty.value && autoSaveEnabled.value) {
    // Final save before unmount
    debouncedAutoSave();
  }
});
</script>

<style>
/* Vollbild-Layout auch gegen äußere Layouts durchsetzen */
html,
body,
#app {
  height: 100%;
  background-color: #ffffff;
}

/* Editor-Root */
.document-editor {
  max-height: 100vh;
}

/* Graue Hintergründe global entfernen (Naive UI / Tailwind) */
.n-layout,
.n-layout-sider,
.n-layout-content,
.bg-slate-50,
.bg-gray-50,
.bg-gray-100 {
  background-color: #ffffff !important;
}

/* ProseMirror / TipTap-Feld auf vollflächig & weiß setzen */
.ProseMirror {
  min-height: auto !important;
  height: auto !important;
  outline: none;
  background-color: #ffffff;
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}

/* Optional: Abstände zwischen Absätzen kleiner machen */
.ProseMirror p {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

/* Letzter Absatz soll keinen Margin haben */
.ProseMirror p:last-child {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}
</style>
