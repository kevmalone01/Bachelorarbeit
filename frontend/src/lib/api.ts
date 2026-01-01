import { ref } from 'vue';
import type { DocumentsQueryParams, DocumentItem, PagedResult, Paginated, ClientItem, Advisor, LegalForm, ParticipantRole, TemplateItem, TemplatesQueryParams, TemplateType } from './types';

export async function fetchJson<T>(url: string, opts?: RequestInit & { signal?: AbortSignal }): Promise<T> {
  // Ensure URL is relative (starts with /) to use Vite proxy
  const normalizedUrl = url.startsWith('http') ? url : (url.startsWith('/') ? url : `/${url}`);
  
  // Only create a controller if no signal is provided
  let controller: AbortController | null = null;
  let timeout: NodeJS.Timeout | null = null;
  
  if (!opts?.signal) {
    controller = new AbortController();
    timeout = setTimeout(() => controller!.abort(), 30000); // Increased timeout to 30s
  }
  
  try {
    const resp = await fetch(normalizedUrl, {
      ...opts,
      signal: opts?.signal ?? controller?.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(opts?.headers || {}),
      },
    });
    
    if (timeout) clearTimeout(timeout);
    
    if (!resp.ok) {
      let detail: any = undefined;
      try { detail = await resp.json(); } catch {}
      const err = new Error(`HTTP ${resp.status}: ${detail?.error || resp.statusText}`);
      (err as any).status = resp.status;
      (err as any).detail = detail;
      console.error(`API Error [${resp.status}]:`, url, detail);
      throw err;
    }
    const data = await resp.json() as T;
    return data;
  } catch (error: any) {
    if (timeout) clearTimeout(timeout);
    
    if (error.name === 'AbortError') {
      console.error('Request timeout:', url);
      throw new Error('Request timeout');
    }
    
    // Better error handling for network errors
    if (error.message?.includes('Load failed') || error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError') || error.message?.includes('TypeError')) {
      console.error('Network error fetching:', url, error);
      throw new Error(`Network error: Could not reach server. Please check if the backend is running on http://localhost:5001`);
    }
    
    throw error;
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

function toQuery(params: Record<string, any>): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === '') return;
    if (Array.isArray(v)) {
      v.forEach((item) => q.append(k, String(item)));
    } else {
      q.set(k, String(v));
    }
  });
  const s = q.toString();
  return s ? `?${s}` : '';
}

export const api = {
  async getDocuments(params: DocumentsQueryParams) {
    // Backend returns an array of documents; we adapt it to our PagedResult<DocumentItem>
    type BackendDoc = {
      id: number;
      title: string;
      content?: string;
      document_type?: string;
      status?: string;
      created_at?: string;
      updated_at?: string;
      client_id?: number | null;
    };
    try {
      const raw = await fetchJson<BackendDoc[]>(`/api/documents`);
    // Map to DocumentItem
    let items: DocumentItem[] = raw.map((d) => ({
      id: String(d.id),
      modified: d.updated_at || d.created_at || new Date().toISOString(),
      name: d.title,
      status: (d.status && d.status.toLowerCase() === 'draft') ? 'Draft'
        : (d.status && d.status.toLowerCase() === 'finished') ? 'Finished'
        : (d.status && d.status.toLowerCase() === 'in_progress') ? 'In Progress'
        : (d.status && d.status.toLowerCase() === 'to_be_reviewed') ? 'To Be Reviewed'
        : 'Not Started',
      owner: '',      // not provided by backend – can be filled later
      mandant: d.client_id ? String(d.client_id) : undefined,
      deadline: undefined,
      template: d.document_type,
    }));
    // Client-side filtering (basic)
    if (params.query) {
      const q = params.query.toLowerCase();
      items = items.filter(i =>
        i.name.toLowerCase().includes(q) ||
        (i.template || '').toLowerCase().includes(q) ||
        (i.mandant || '').toLowerCase().includes(q)
      );
    }
    if (params.status && params.status.length) {
      const set = new Set(params.status);
      items = items.filter(i => set.has(i.status));
    }
    if (params.owner && params.owner.length) {
      const set = new Set(params.owner);
      items = items.filter(i => i.owner && set.has(i.owner));
    }
    if (params.template && params.template.length) {
      const set = new Set(params.template);
      items = items.filter(i => i.template && set.has(i.template));
    }
    // Deadline: mangels eigenem Feld nutzen wir 'modified' als Referenz
    if (params.deadlineFrom || params.deadlineTo) {
      const fromTs = params.deadlineFrom ? Date.parse(params.deadlineFrom) : -Infinity;
      const toTs = params.deadlineTo ? Date.parse(params.deadlineTo) : Infinity;
      items = items.filter(i => {
        const ts = i.deadline ? Date.parse(i.deadline) : Date.parse(i.modified);
        return ts >= fromTs && ts <= toTs;
      });
    }
    // Sorting
    if (params.sortBy) {
      const dir = params.sortDir === 'desc' ? -1 : 1;
      const key = params.sortBy as keyof DocumentItem;
      items = items.slice().sort((a,b) => {
        const va = (a[key] || '') as any;
        const vb = (b[key] || '') as any;
        return va > vb ? dir : va < vb ? -dir : 0;
      });
    }
    // Pagination
    const page = Math.max(1, params.page || 1);
    const pageSize = Math.max(1, params.pageSize || 20);
    const start = (page - 1) * pageSize;
    const paged = items.slice(start, start + pageSize);
    return {
      items: paged,
      page,
      pageSize,
      total: items.length,
    } satisfies PagedResult<DocumentItem>;
    } catch (error: any) {
      console.error('Error fetching documents:', error);
      // Return empty result instead of throwing
      return {
        items: [],
        page: params.page || 1,
        pageSize: params.pageSize || 20,
        total: 0,
      } satisfies PagedResult<DocumentItem>;
    }
  },
  async createDocument(payload: Partial<DocumentItem>) {
    return fetchJson<DocumentItem>('/api/documents', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async deleteDocument(id: string) {
    await fetchJson(`/api/documents/${id}`, {
      method: 'DELETE',
    });
    return { ok: true };
  },
  async getUsers() {
    return fetchJson<Array<{ id: string; name: string }>>('/api/users');
  },
  async getTemplates() {
    // Get templates from document templates endpoint
    const templates = await fetchJson<Array<{ id: string; name: string }>>('/api/documents/templates');
    return templates.map(t => ({ id: t.id, name: t.name }));
  },
};

// ---- Clients API (placeholder implementations) ----
const legalForms: LegalForm[] = [
  'Einzelunternehmen',
  'Aktiengesellschaft (AG)',
  'Gesellschaft bürgerlichen Rechts (GbR)',
  'Gesellschaft mit beschränkter Haftung (GmbH)',
  'GmbH & Co. KG',
  'Kommanditgesellschaft (KG)',
  'Offene Handelsgesellschaft (OHG)',
  'Partnerschaftsgesellschaft (PartG)',
  'Unternehmergesellschaft (UG)',
  'Stiftung'
];

// Dummy function removed - now using real API

export const clientsApi = {
  async getClients(params: { query?: string; type?: string[]; advisorId?: string[]; legalForm?: string[]; page?: number; pageSize?: number; }) {
    // Get real clients from API
    const rawClients = await fetchJson<Array<any>>('/api/clients');
    let items: ClientItem[] = rawClients.map((c: any) => {
      // Map backend client data to ClientItem format
      const client: ClientItem = {
        id: String(c.id),
        type: c.client_type === 'natural' ? 'Natürliche Person' : 'Gewerbe',
        mandateManager: c.mandate_manager || '',
        mandateResponsible: c.mandate_responsible || '',
        email: c.email || '',
        taxNumber: c.tax_number || '',
        taxId: c.tax_id || '',
        vatId: c.vat_id || '',
        street: c.address_street || '',
        number: c.address_number || '',
        zip: c.address_zip || '',
        city: c.address_city || '',
        createdAt: c.created_at || new Date().toISOString(),
        updatedAt: c.updated_at || new Date().toISOString(),
      };
      
      if (c.client_type === 'natural') {
        // Handle salutation - it could be a string ('Herr'/'Frau') or an object with .value
        let salutationValue = '';
        if (c.salutation) {
          if (typeof c.salutation === 'string') {
            salutationValue = c.salutation;
          } else if (c.salutation.value) {
            salutationValue = c.salutation.value;
          } else {
            salutationValue = String(c.salutation);
          }
        }
        client.salutation = salutationValue;
        console.log('[getClients] Mapped salutation for client', c.id, ':', c.salutation, '->', salutationValue, '(type:', typeof c.salutation, ')');
        client.title = c.title || '';
        client.firstName = c.first_name || '';
        client.lastName = c.last_name || '';
        client.birthDate = c.birth_date || '';
        client.birthPlace = c.birth_place || '';
        client.nationality = c.nationality || '';
      } else {
        client.companyName = c.company_name || '';
        client.legalForm = c.legal_form?.value || '';
        client.contactSalutation = c.contact_salutation?.value || '';
        client.contactLastName = c.contact_last_name || '';
        client.contactPhone = c.contact_phone || '';
        client.contactEmail = c.contact_email || '';
        client.contactFax = c.contact_fax || '';
      }
      
      return client;
    });
    // Filter: Suche - nur anwenden wenn nicht leer
    if (params.query && params.query.trim() !== '') {
      const q = params.query.toLowerCase();
      items = items.filter(c =>
        (c.firstName || '').toLowerCase().includes(q) ||
        (c.lastName || '').toLowerCase().includes(q) ||
        (c.companyName || '').toLowerCase().includes(q) ||
        (c.city || '').toLowerCase().includes(q));
    }
    
    // Filter: Typ - nur anwenden wenn Werte vorhanden sind
    if (params.type && Array.isArray(params.type) && params.type.length > 0) {
      const validTypes = params.type.filter(t => t && t.trim() !== '');
      if (validTypes.length > 0) {
        const set = new Set(validTypes);
        items = items.filter(c => set.has(c.type));
      }
    }
    
    // Filter: Berater - nur anwenden wenn Werte vorhanden sind
    if (params.advisorId && Array.isArray(params.advisorId) && params.advisorId.length > 0) {
      const validAdvisorIds = params.advisorId.filter(id => id && id.trim() !== '');
      if (validAdvisorIds.length > 0) {
        const set = new Set(validAdvisorIds);
        items = items.filter(c => c.advisorId && set.has(c.advisorId));
      }
    }
    
    // Filter: Rechtsform - nur anwenden wenn Werte vorhanden sind
    if (params.legalForm && Array.isArray(params.legalForm) && params.legalForm.length > 0) {
      const validLegalForms = params.legalForm.filter(lf => lf && lf.trim() !== '');
      if (validLegalForms.length > 0) {
        const set = new Set(validLegalForms);
        // Rechtsform-Filterung: Nur für Unternehmen anwenden, natürliche Personen immer durchlassen
        items = items.filter(c => {
          if (c.type === 'Natürliche Person') {
            return true; // Natürliche Personen haben keine Rechtsform, immer durchlassen
          }
          return c.legalForm && set.has(c.legalForm);
        });
      }
    }
    const page = Math.max(1, params.page || 1);
    const pageSize = Math.max(1, params.pageSize || 12);
    const start = (page - 1) * pageSize;
    const paged = items.slice(start, start + pageSize);
    const result: Paginated<ClientItem> = { items: paged, total: items.length, page, pageSize };
    return result;
  },
  async getClient(id: string): Promise<ClientItem> {
    const client = await fetchJson<any>(`/api/clients/${id}`);
    // Map to ClientItem format (same mapping as in getClients)
    const clientItem: ClientItem = {
      id: String(client.id),
      type: client.client_type === 'natural' ? 'Natürliche Person' : 'Gewerbe',
      mandateManager: client.mandate_manager || '',
      mandateResponsible: client.mandate_responsible || '',
      email: client.email || '',
      taxNumber: client.tax_number || '',
      taxId: client.tax_id || '',
      vatId: client.vat_id || '',
      street: client.address_street || '',
      number: client.address_number || '',
      zip: client.address_zip || '',
      city: client.address_city || '',
      createdAt: client.created_at || new Date().toISOString(),
      updatedAt: client.updated_at || new Date().toISOString(),
    };
    
    if (client.client_type === 'natural') {
      // Handle salutation - it could be a string ('Herr'/'Frau') or an object with .value
      let salutationValue = '';
      if (client.salutation) {
        if (typeof client.salutation === 'string') {
          salutationValue = client.salutation;
        } else if (client.salutation.value) {
          salutationValue = client.salutation.value;
        } else {
          salutationValue = String(client.salutation);
        }
      }
      clientItem.salutation = salutationValue;
      console.log('[getClient] Mapped salutation:', client.salutation, '->', clientItem.salutation);
      clientItem.title = client.title || '';
      clientItem.firstName = client.first_name || '';
      clientItem.lastName = client.last_name || '';
      clientItem.birthDate = client.birth_date || '';
      clientItem.birthPlace = client.birth_place || '';
      clientItem.nationality = client.nationality || '';
    } else {
      clientItem.companyName = client.company_name || '';
      clientItem.legalForm = client.legal_form?.value || '';
      clientItem.contactSalutation = client.contact_salutation?.value || '';
      clientItem.contactLastName = client.contact_last_name || '';
      clientItem.contactPhone = client.contact_phone || '';
      clientItem.contactEmail = client.contact_email || '';
      clientItem.contactFax = client.contact_fax || '';
    }
    
    return clientItem;
  },
  async createClient(payload: Partial<ClientItem>) {
    // Map ClientItem to backend format
    const backendPayload: any = {
      client_type: payload.type === 'Natürliche Person' ? 'natural' : 'company',
      mandate_manager: payload.mandateManager || '',
      mandate_responsible: payload.mandateResponsible || '',
      email: payload.email || '',
      tax_number: payload.taxNumber || '',
      address_street: payload.street || '',
      address_number: payload.number || '',
      address_zip: payload.zip || '',
      address_city: payload.city || '',
      tax_court: payload.taxCourt || '',
    };
    
    if (payload.type === 'Natürliche Person') {
      // Map Salutation - always include it, even if empty
      const salutationMap: Record<string, string> = {
        'Herr': 'HERR',
        'Frau': 'FRAU',
        'Divers': 'HERR', // Default to HERR if Divers
      };
      // Always include salutation in the payload if it exists in the payload
      // Check if salutation key exists (even if value is empty/null)
      if ('salutation' in payload) {
        const salutationValue = payload.salutation;
        if (salutationValue && String(salutationValue).trim()) {
          const mappedValue = salutationMap[String(salutationValue)] || String(salutationValue);
          backendPayload.salutation = mappedValue;
          console.log('[createClient] Mapped salutation:', salutationValue, '->', backendPayload.salutation);
        } else {
          // Empty or null value - send null explicitly
          backendPayload.salutation = null;
          console.log('[createClient] Salutation is empty/null, sending null');
        }
      } else {
        // If salutation key doesn't exist in payload, don't include it
        console.log('[createClient] Salutation not in payload, not sending');
      }
      backendPayload.title = payload.title || '';
      backendPayload.first_name = payload.firstName || '';
      backendPayload.last_name = payload.lastName || '';
      // Always include birth_place and nationality, even if empty
      if ('birthPlace' in payload) {
        backendPayload.birth_place = payload.birthPlace || '';
        console.log('[createClient] Including birth_place:', backendPayload.birth_place);
      }
      if ('nationality' in payload) {
        backendPayload.nationality = payload.nationality || '';
        console.log('[createClient] Including nationality:', backendPayload.nationality);
      }
      // Ensure birthDate is a string in YYYY-MM-DD format
      if (payload.birthDate) {
        let birthDateStr: string;
        if (typeof payload.birthDate === 'number') {
          // If it's a timestamp, convert to date string
          const date = new Date(payload.birthDate);
          birthDateStr = date.toISOString().split('T')[0];
        } else if (typeof payload.birthDate === 'string') {
          // Already a string, use it directly
          birthDateStr = payload.birthDate;
        } else {
          // If it's a Date object or other format
          const date = new Date(payload.birthDate);
          birthDateStr = date.toISOString().split('T')[0];
        }
        backendPayload.birth_date = birthDateStr;
      }
      backendPayload.tax_id = payload.taxId || '';
    } else {
      backendPayload.company_name = payload.companyName || '';
      // Map LegalForm from frontend string to backend enum value
      const legalFormMap: Record<string, string> = {
        'Gesellschaft mit beschränkter Haftung (GmbH)': 'GMBH',
        'Aktiengesellschaft (AG)': 'AG',
        'Offene Handelsgesellschaft (OHG)': 'OHG',
        'Unternehmergesellschaft (UG)': 'UG',
        'Kommanditgesellschaft (KG)': 'KG',
        'Gesellschaft bürgerlichen Rechts (GbR)': 'GBR',
        'Einzelunternehmen': 'EINZELFIRMA',
      };
      backendPayload.legal_form = legalFormMap[payload.legalForm || ''] || payload.legalForm || '';
      backendPayload.vat_id = payload.vatId || '';
      // Map contact salutation
      const contactSalutationMap: Record<string, string> = {
        'Herr': 'HERR',
        'Frau': 'FRAU',
        'Divers': 'HERR',
      };
      backendPayload.contact_salutation = contactSalutationMap[payload.contactSalutation || ''] || payload.contactSalutation || '';
      backendPayload.contact_last_name = payload.contactLastName || '';
      backendPayload.contact_phone = payload.contactPhone || '';
      backendPayload.contact_email = payload.contactEmail || '';
      backendPayload.contact_fax = payload.contactFax || '';
    }
    
    // Tax office fields - map flat fields
    if (payload.taxOfficeZip || payload.taxOfficeCity || payload.taxOfficeStreet) {
      // tax_office is a string field - use city or empty string
      backendPayload.tax_office = payload.taxOffice || payload.taxOfficeCity || '';
      backendPayload.tax_office_zip = payload.taxOfficeZip || '';
      backendPayload.tax_office_city = payload.taxOfficeCity || '';
      backendPayload.tax_office_street = payload.taxOfficeStreet || '';
      backendPayload.tax_office_number = payload.taxOfficeNumber || '';
      backendPayload.tax_office_email = payload.taxOfficeEmail || '';
      backendPayload.tax_office_fax = payload.taxOfficeFax || '';
    }
    
    console.log('[createClient] Final backend payload:', JSON.stringify(backendPayload, null, 2));
    console.log('[createClient] Salutation in payload:', backendPayload.salutation, 'type:', typeof backendPayload.salutation);
    
    try {
      const response = await fetchJson<{ id: number }>('/api/clients', {
        method: 'POST',
        body: JSON.stringify(backendPayload),
      });
      console.log('[createClient] Response:', response);
      return { ok: true, id: String(response.id) };
    } catch (error: any) {
      console.error('API Error creating client:', error);
      throw error;
    }
  },
  async updateClient(id: string, payload: Partial<ClientItem>) {
    // Map ClientItem to backend format (similar to createClient)
    const backendPayload: any = {
      mandate_manager: payload.mandateManager || '',
      mandate_responsible: payload.mandateResponsible || '',
      email: payload.email || '',
      tax_number: payload.taxNumber || '',
      address_street: payload.street || '',
      address_number: payload.number || '',
      address_zip: payload.zip || '',
      address_city: payload.city || '',
      tax_court: payload.taxCourt || '',
    };
    
    if (payload.type === 'Natürliche Person') {
      // Map Salutation - always include it, even if empty
      const salutationMap: Record<string, string> = {
        'Herr': 'HERR',
        'Frau': 'FRAU',
        'Divers': 'HERR',
      };
      // Always include salutation in the payload
      // Check if salutation exists in payload (even if null/undefined/empty)
      if ('salutation' in payload) {
        const salutationValue = payload.salutation;
        if (salutationValue && String(salutationValue).trim()) {
          backendPayload.salutation = salutationMap[String(salutationValue)] || String(salutationValue);
        } else {
          // Send null to clear it (backend will handle it)
          backendPayload.salutation = null;
        }
      } else {
        // If salutation is not in payload, don't include it (keep existing value)
      }
      // Always include these fields if they exist in payload
      if ('title' in payload) backendPayload.title = payload.title || '';
      if ('firstName' in payload) backendPayload.first_name = payload.firstName || '';
      if ('lastName' in payload) backendPayload.last_name = payload.lastName || '';
      if ('birthDate' in payload) backendPayload.birth_date = payload.birthDate || '';
      if ('birthPlace' in payload) backendPayload.birth_place = payload.birthPlace || '';
      if ('nationality' in payload) backendPayload.nationality = payload.nationality || '';
      if ('taxId' in payload) backendPayload.tax_id = payload.taxId || '';
    } else {
      // Map legal form
      const legalFormMap: Record<string, string> = {
        'Gesellschaft mit beschränkter Haftung (GmbH)': 'GMBH',
        'Aktiengesellschaft (AG)': 'AG',
        'Offene Handelsgesellschaft (OHG)': 'OHG',
        'Unternehmergesellschaft (UG)': 'UG',
        'Kommanditgesellschaft (KG)': 'KG',
        'Gesellschaft bürgerlichen Rechts (GbR)': 'GBR',
        'Einzelunternehmen': 'EINZELFIRMA',
      };
      backendPayload.company_name = payload.companyName || '';
      backendPayload.legal_form = legalFormMap[payload.legalForm || ''] || payload.legalForm || '';
      backendPayload.vat_id = payload.vatId || '';
      // Map contact salutation
      const contactSalutationMap: Record<string, string> = {
        'Herr': 'HERR',
        'Frau': 'FRAU',
        'Divers': 'HERR',
      };
      backendPayload.contact_salutation = contactSalutationMap[payload.contactSalutation || ''] || payload.contactSalutation || '';
      backendPayload.contact_last_name = payload.contactLastName || '';
      backendPayload.contact_phone = payload.contactPhone || '';
      backendPayload.contact_email = payload.contactEmail || '';
      backendPayload.contact_fax = payload.contactFax || '';
    }
    
    // Tax office fields
    if (payload.taxOfficeZip || payload.taxOfficeCity || payload.taxOfficeStreet) {
      backendPayload.tax_office = payload.taxOffice || payload.taxOfficeCity || '';
      backendPayload.tax_office_zip = payload.taxOfficeZip || '';
      backendPayload.tax_office_city = payload.taxOfficeCity || '';
      backendPayload.tax_office_street = payload.taxOfficeStreet || '';
      backendPayload.tax_office_number = payload.taxOfficeNumber || '';
      backendPayload.tax_office_email = payload.taxOfficeEmail || '';
      backendPayload.tax_office_fax = payload.taxOfficeFax || '';
    }
    
    console.log('[updateClient] Final backend payload:', JSON.stringify(backendPayload, null, 2));
    console.log('[updateClient] Salutation in payload:', backendPayload.salutation, 'type:', typeof backendPayload.salutation);
    console.log('[updateClient] birth_place in payload:', backendPayload.birth_place, 'type:', typeof backendPayload.birth_place);
    console.log('[updateClient] nationality in payload:', backendPayload.nationality, 'type:', typeof backendPayload.nationality);
    
    try {
      const response = await fetchJson<any>(`/api/clients/${id}`, {
        method: 'PUT',
        body: JSON.stringify(backendPayload),
      });
      console.log('[updateClient] Response:', response);
      return response;
    } catch (error: any) {
      console.error('API Error updating client:', error);
      throw error;
    }
  },
  async deleteClient(id: string) {
    await fetchJson(`/api/clients/${id}`, { method: 'DELETE' });
    return { ok: true };
  },
  async getAdvisors(): Promise<Advisor[]> {
    return [
      { id: '1', name: 'Max Mustermann' },
      { id: '2', name: 'Lisa Beispiel' },
      { id: '3', name: 'Paul Berger' },
    ];
  },
  async getLegalForms(): Promise<LegalForm[]> {
    return legalForms;
  }
};

// ---- Templates API ----
// Lokaler State für gelöschte Vorlagen-IDs (wird beim Neuladen der Seite zurückgesetzt)
const deletedTemplateIds = new Set<string>();

// Dummy function removed - now using real API

export const templatesApi = {
  async getTemplates(params: TemplatesQueryParams = {}): Promise<Paginated<TemplateItem>> {
    try {
      // Get real templates from API
      const rawTemplates = await fetchJson<Array<any>>('/api/documents/templates');
      
      if (!rawTemplates || !Array.isArray(rawTemplates)) {
        console.warn('Templates API returned invalid data:', rawTemplates);
        return {
          items: [],
          total: 0,
          page: params.page || 1,
          pageSize: params.pageSize || 20,
        };
      }
      
      console.log('[Templates API] Successfully fetched', rawTemplates.length, 'templates');
      console.log('[Templates API] Filter params:', {
        query: params.query,
        creator: params.creator,
        type: params.type,
        createdAtFrom: params.createdAtFrom,
        createdAtTo: params.createdAtTo,
      });
      
      let items: TemplateItem[] = rawTemplates.map((t: any) => ({
        id: String(t.id || ''),
        createdAt: t.created_at || new Date().toISOString(),
        creator: 'System', // Backend doesn't provide creator yet
        title: t.name || 'Unbenannt',
        note: undefined,
        type: 'Dokumente' as TemplateType,
        history: []
      }));
      
      console.log('[Templates API] After mapping:', items.length, 'items');
    
    // Filter: Suche
    if (params.query && params.query.trim() !== '') {
      const q = params.query.toLowerCase();
      const beforeFilter = items.length;
      items = items.filter(t =>
        t.title.toLowerCase().includes(q) ||
        (t.note && t.note.toLowerCase().includes(q)) ||
        t.creator.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q)
      );
      console.log('[Templates API] After query filter:', items.length, 'items (was', beforeFilter, ')');
    }
    
    // Filter: Ersteller - nur filtern wenn wirklich Werte vorhanden sind
    if (params.creator && Array.isArray(params.creator) && params.creator.length > 0) {
      // Filter out empty strings and null values
      const validCreators = params.creator.filter(c => c && c.trim() !== '');
      if (validCreators.length > 0) {
        const set = new Set(validCreators);
        const beforeFilter = items.length;
        items = items.filter(t => set.has(t.creator));
        console.log('[Templates API] After creator filter:', items.length, 'items (was', beforeFilter, '), filter set:', Array.from(set));
      } else {
        console.log('[Templates API] Creator filter skipped - no valid creators');
      }
    } else {
      console.log('[Templates API] Creator filter skipped - params.creator:', params.creator);
    }
    
    // Filter: Vorlagenart - nur filtern wenn wirklich Werte vorhanden sind
    if (params.type && Array.isArray(params.type) && params.type.length > 0) {
      // Filter out empty strings and null values
      const validTypes = params.type.filter(t => t && t.trim() !== '');
      if (validTypes.length > 0) {
        const set = new Set(validTypes);
        const beforeFilter = items.length;
        items = items.filter(t => set.has(t.type));
        console.log('[Templates API] After type filter:', items.length, 'items (was', beforeFilter, '), filter set:', Array.from(set));
      } else {
        console.log('[Templates API] Type filter skipped - no valid types');
      }
    } else {
      console.log('[Templates API] Type filter skipped - params.type:', params.type);
    }
    
    // Filter: Erstellungsdatum
    if (params.createdAtFrom) {
      const beforeFilter = items.length;
      items = items.filter(t => t.createdAt >= params.createdAtFrom!);
      console.log('[Templates API] After createdAtFrom filter:', items.length, 'items (was', beforeFilter, ')');
    }
    if (params.createdAtTo) {
      const beforeFilter = items.length;
      items = items.filter(t => t.createdAt <= params.createdAtTo!);
      console.log('[Templates API] After createdAtTo filter:', items.length, 'items (was', beforeFilter, ')');
    }
    
    // Sortierung
    if (params.sortBy) {
      const dir = params.sortDir === 'desc' ? -1 : 1;
      items.sort((a, b) => {
        const aVal = (a as any)[params.sortBy!];
        const bVal = (b as any)[params.sortBy!];
        if (aVal < bVal) return -1 * dir;
        if (aVal > bVal) return 1 * dir;
        return 0;
      });
    }
    
    // Paginierung
    const page = Math.max(1, params.page || 1);
    const pageSize = Math.max(1, params.pageSize || 20);
    const start = (page - 1) * pageSize;
    const paged = items.slice(start, start + pageSize);
    
    console.log('[Templates API] Final result - total items:', items.length, 'paged items:', paged.length, 'page:', page, 'pageSize:', pageSize);
    
    return { items: paged, total: items.length, page, pageSize };
    } catch (error: any) {
      console.error('[Templates API] Error fetching templates:', error);
      // Re-throw the error so the query can handle it properly
      // This allows the UI to show an error state instead of silently failing
      throw error;
    }
  },
  
  async getCreators(): Promise<Array<{ id: string; name: string }>> {
    return [
      { id: '1', name: 'Max Mustermann' },
      { id: '2', name: 'Lisa Beispiel' },
      { id: '3', name: 'Paul Berger' },
      { id: '4', name: 'Anna Schmidt' },
    ];
  },
  
  async getTemplateTypes(): Promise<TemplateType[]> {
    return ['Dokumente', 'Textbausteine', 'Layoutvorlagen'];
  },
  
  async createTemplate(payload: { title: string; note?: string; type: TemplateType; creator: string; file?: File }): Promise<{ ok: boolean; id: string }> {
    // Wenn eine Datei vorhanden ist, sollte sie hochgeladen werden
    if (payload.file) {
      const formData = new FormData();
      formData.append('file', payload.file);
      formData.append('name', payload.title);
      formData.append('description', payload.note || '');
      formData.append('is_template', 'true');
      formData.append('placeholders', JSON.stringify([])); // Leere Platzhalter-Liste, wird im Editor gemappt
      formData.append('linkedClientGroupIds', JSON.stringify([]));
      
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Failed to upload template' }));
        throw new Error(error.error || 'Failed to upload template');
      }
      
      const data = await response.json();
      return { ok: true, id: String(data.id) };
    }
    throw new Error('Keine Datei zum Hochladen angegeben');
  },
  
  async deleteTemplate(id: string): Promise<{ ok: boolean }> {
    await fetchJson(`/api/documents/templates/${id}`, { method: 'DELETE' });
    return { ok: true };
  }
};

// ---- Document Editor API ----
import type { DocumentTemplate, DbField, FillValues } from './types';

export const documentEditorApi = {
  async getTemplates(): Promise<DocumentTemplate[]> {
    const data = await fetchJson<Array<DocumentTemplate & { file_path?: string }>>(`/api/documents/templates`);
    return data.map(t => ({
      ...t,
      filePath: t.file_path || (t as any).filePath || null,
    }));
  },
  
  async getTemplate(id: string): Promise<DocumentTemplate> {
    const data = await fetchJson<DocumentTemplate & { file_path?: string }>(`/api/documents/templates/${id}`);
    return {
      ...data,
      filePath: data.file_path || (data as any).filePath || null,
    };
  },
  
  async getDocument(id: string): Promise<DocumentTemplate & { clientId?: string; client_id?: number; is_template?: boolean; isTemplate?: boolean }> {
    const data = await fetchJson<DocumentTemplate & { file_path?: string; clientId?: string; client_id?: number; is_template?: boolean; isTemplate?: boolean }>(`/api/documents/${id}`);
    return {
      id: String(data.id),
      name: data.title || data.name,
      contentHtml: data.content || '',
      placeholders: data.placeholders || [],
      linkedClientGroupIds: data.linkedClientGroupIds || [],
      filePath: data.file_path || (data as any).filePath || null,
      clientId: data.clientId || (data.client_id ? String(data.client_id) : undefined),
      client_id: data.client_id,
      is_template: data.is_template,
      isTemplate: data.isTemplate || data.is_template,
    };
  },
  
  async updateTemplate(id: string, payload: { name?: string; contentHtml?: string; placeholders?: any[]; linkedClientGroupIds?: string[] }): Promise<{ ok: boolean }> {
    await fetchJson(`/api/documents/templates/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return { ok: true };
  },
  
  async updateDocument(id: string, payload: { contentHtml?: string; placeholders?: any[]; clientId?: string }): Promise<{ ok: boolean }> {
    await fetchJson(`/api/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        content: payload.contentHtml,
        placeholders: payload.placeholders,
        clientId: payload.clientId,
      }),
    });
    return { ok: true };
  },
  
  async saveTemplate(file: File, name: string, contentHtml: string, placeholders: any[], linkedClientGroupIds: string[]): Promise<{ id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('description', contentHtml);
    formData.append('is_template', 'true');
    formData.append('placeholders', JSON.stringify(placeholders));
    formData.append('linkedClientGroupIds', JSON.stringify(linkedClientGroupIds));
    
    const response = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to save template');
    }
    
    const data = await response.json();
    return { id: String(data.id) };
  },
  
  async exportTemplate(id: string, fillValues: FillValues, format: 'pdf' | 'docx'): Promise<Blob> {
    // Use existing document export endpoint
    // Include format and contentHtml in the request body
    // Note: fillValues may already contain exportFormat and contentHtml
    const payload: any = { ...fillValues };
    
    // CRITICAL: Always set exportFormat explicitly (override any existing value)
    payload.exportFormat = format;
    console.log('[api.ts] exportTemplate - format:', format, 'payload.exportFormat:', payload.exportFormat);
    console.log('[api.ts] exportTemplate - payload keys:', Object.keys(payload));
    
    // contentHtml should already be in fillValues if provided
    // No need to add it again
    
    const response = await fetch(`/api/documents/download/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = 'Failed to export template';
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.error || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    return await response.blob();
  },
  
  async getDbFields(): Promise<DbField[]> {
    const data = await fetchJson<DbField[]>('/api/db-fields');
    return data;
  },
  
  async createDocumentFromTemplate(templateId: string, clientId: string, payload: { contentHtml?: string; placeholders?: any[]; fillValues?: FillValues }): Promise<{ id: string }> {
    const response = await fetchJson<{ id: number }>(`/api/documents/create-from-template/${templateId}`, {
      method: 'POST',
      body: JSON.stringify({
        contentHtml: payload.contentHtml,
        placeholders: payload.placeholders,
        fillValues: payload.fillValues,
        client_id: clientId,
      }),
    });
    return { id: String(response.id) };
  },
};


