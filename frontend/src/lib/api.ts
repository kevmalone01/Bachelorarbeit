import { ref } from 'vue';
import type { DocumentsQueryParams, DocumentItem, PagedResult, Paginated, ClientItem, Advisor, LegalForm, ParticipantRole, TemplateItem, TemplatesQueryParams, TemplateType } from './types';

export async function fetchJson<T>(url: string, opts?: RequestInit & { signal?: AbortSignal }): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const resp = await fetch(url, {
      ...opts,
      signal: opts?.signal ?? controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(opts?.headers || {}),
      },
    });
    if (!resp.ok) {
      let detail: any = undefined;
      try { detail = await resp.json(); } catch {}
      const err = new Error(`HTTP ${resp.status}`);
      (err as any).status = resp.status;
      (err as any).detail = detail;
      throw err;
    }
    return await resp.json() as T;
  } finally {
    clearTimeout(timeout);
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
  },
  async createDocument(payload: Partial<DocumentItem>) {
    return fetchJson<DocumentItem>('/api/documents', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async getUsers() {
    return fetchJson<Array<{ id: string; name: string }>>('/api/users');
  },
  async getTemplates() {
    return fetchJson<Array<{ id: string; name: string }>>('/api/templates');
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

function generateDummyClients(): ClientItem[] {
  const advisors: Advisor[] = [
    { id: '1', name: 'Max Mustermann' },
    { id: '2', name: 'Lisa Beispiel' },
    { id: '3', name: 'Paul Berger' }
  ];
  const items: ClientItem[] = [];
  
  // Beispiel natürliche Personen
  for (let i = 1; i <= 7; i++) {
    const adv = advisors[i % advisors.length];
    items.push({
      id: String(i),
      type: 'Natürliche Person',
      mandateManager: 'Max Mustermann',
      mandateResponsible: 'Lisa Beispiel',
      salutation: i % 2 === 0 ? 'Herr' : 'Frau',
      title: i % 3 === 0 ? 'Dr.' : '',
      firstName: i % 2 === 0 ? 'Hans' : 'Anna',
      lastName: `Müller ${i}`,
      birthDate: new Date(1980 + (i % 20), i % 12, i % 28 + 1).toISOString().split('T')[0],
      street: `Hauptstraße ${i * 10}`,
      number: `${i}a`,
      zip: `80${100 + i}`,
      city: 'München',
      email: `person${i}@example.com`,
      taxNumber: `123/456/${78900 + i}`,
      taxId: `1234567890${i}`,
      taxOffice: {
        zip: '80331',
        city: 'München',
        street: 'Finanzamtstraße',
        number: '5',
        email: 'kontakt@finanzamt-muenchen.de',
        fax: '+49 89 1234567',
        contactSalutation: 'Herr',
        contactLastName: 'Beispiel',
        contactPhone: '+49 89 1234568',
        taxCourt: 'Finanzgericht München'
      },
      taxCourt: 'Finanzgericht München',
      advisorId: adv.id,
      advisorName: adv.name,
      createdAt: new Date(Date.now() - i * 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
  
  // Beispiel Unternehmen
  const companyLegalForms: LegalForm[] = [
    'Gesellschaft mit beschränkter Haftung (GmbH)',
    'Unternehmergesellschaft (UG)',
    'Aktiengesellschaft (AG)',
    'GmbH & Co. KG',
    'Kommanditgesellschaft (KG)'
  ];
  const companyRoles: ParticipantRole[] = ['Geschäftsführer', 'Gesellschafter', 'Komplementär', 'Kommanditist'];
  
  for (let i = 8; i <= 15; i++) {
    const adv = advisors[i % advisors.length];
    const legalForm = companyLegalForms[(i - 8) % companyLegalForms.length];
    items.push({
      id: String(i),
      type: 'Gewerbe',
      mandateManager: 'Max Mustermann',
      mandateResponsible: 'Lisa Beispiel',
      companyName: `Firma ${i} ${legalForm}`,
      legalForm: legalForm,
      street: `Industriestraße ${i * 5}`,
      number: `${i}`,
      zip: `80${200 + i}`,
      city: 'Augsburg',
      email: `firma${i}@example.com`,
      taxNumber: `987/654/${32100 + i}`,
      vatId: `DE${123456789 + i}`,
      taxOffice: {
        zip: '86150',
        city: 'Augsburg',
        street: 'Finanzamtstraße',
        number: '10',
        email: 'kontakt@finanzamt-augsburg.de',
        fax: '+49 821 7654321',
        contactSalutation: 'Frau',
        contactLastName: 'Meier',
        contactPhone: '+49 821 7654322',
        taxCourt: 'Finanzgericht München'
      },
      taxCourt: 'Finanzgericht München',
      participants: [
        {
          id: `${i}-1`,
          personId: `${i * 100}`,
          firstName: 'Max',
          lastName: 'Mustermann',
          role: companyRoles[(i - 8) % companyRoles.length]
        },
        ...(i % 2 === 0 ? [{
          id: `${i}-2`,
          personId: `${i * 100 + 1}`,
          firstName: 'Lisa',
          lastName: 'Beispiel',
          role: 'Gesellschafter' as ParticipantRole
        }] : [])
      ],
      advisorId: adv.id,
      advisorName: adv.name,
      createdAt: new Date(Date.now() - i * 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
  
  return items;
}

export const clientsApi = {
  async getClients(params: { query?: string; type?: string[]; advisorId?: string[]; legalForm?: string[]; page?: number; pageSize?: number; }) {
    // Placeholder: use dummy dataset; later replace with /api/clients
    let items = generateDummyClients();
    if (params.query) {
      const q = params.query.toLowerCase();
      items = items.filter(c =>
        (c.firstName || '').toLowerCase().includes(q) ||
        (c.lastName || '').toLowerCase().includes(q) ||
        (c.companyName || '').toLowerCase().includes(q) ||
        (c.city || '').toLowerCase().includes(q));
    }
    if (params.type?.length) {
      const set = new Set(params.type);
      items = items.filter(c => set.has(c.type));
    }
    if (params.advisorId?.length) {
      const set = new Set(params.advisorId);
      items = items.filter(c => c.advisorId && set.has(c.advisorId));
    }
    if (params.legalForm?.length) {
      const set = new Set(params.legalForm);
      // Rechtsform-Filterung: Nur für Unternehmen anwenden, natürliche Personen immer durchlassen
      items = items.filter(c => {
        if (c.type === 'Natürliche Person') {
          return true; // Natürliche Personen haben keine Rechtsform, immer durchlassen
        }
        return c.legalForm && set.has(c.legalForm);
      });
    }
    const page = Math.max(1, params.page || 1);
    const pageSize = Math.max(1, params.pageSize || 12);
    const start = (page - 1) * pageSize;
    const paged = items.slice(start, start + pageSize);
    const result: Paginated<ClientItem> = { items: paged, total: items.length, page, pageSize };
    return result;
  },
  async getClient(id: string): Promise<ClientItem> {
    // Placeholder: später ans Backend anpassen
    const all = await this.getClients({ page: 1, pageSize: 1000 });
    const found = all.items.find(c => c.id === id);
    if (!found) throw new Error('Client not found');
    return found;
  },
  async createClient(payload: Partial<ClientItem>) {
    // Placeholder success
    return { ok: true, id: String(Math.floor(Math.random() * 100000)) };
  },
  async deleteClient(id: string) {
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

function generateDummyTemplates(): TemplateItem[] {
  const creators = ['Max Mustermann', 'Lisa Beispiel', 'Paul Berger', 'Anna Schmidt'];
  const types: TemplateType[] = ['Dokumente', 'Textbausteine', 'Layoutvorlagen'];
  const items: TemplateItem[] = [];

  for (let i = 1; i <= 20; i++) {
    const creator = creators[i % creators.length];
    const type = types[i % types.length];
    const createdAt = new Date(Date.now() - i * 86400000 * 2).toISOString();
    
    items.push({
      id: String(i),
      createdAt,
      creator,
      title: `Vorlage ${i} - ${type}`,
      note: i % 3 === 0 ? `Notiz für Vorlage ${i}` : undefined,
      type,
      history: [
        {
          id: `${i}-1`,
          date: createdAt,
          user: creator,
          change: 'Vorlage erstellt'
        },
        ...(i % 3 === 0 ? [{
          id: `${i}-2`,
          date: new Date(Date.now() - i * 86400000).toISOString(),
          user: creators[(i + 1) % creators.length],
          change: 'Vorlage aktualisiert'
        }] : [])
      ]
    });
  }

  return items;
}

export const templatesApi = {
  async getTemplates(params: TemplatesQueryParams = {}): Promise<Paginated<TemplateItem>> {
    let items = generateDummyTemplates();
    
    // Filter: Suche
    if (params.query) {
      const q = params.query.toLowerCase();
      items = items.filter(t =>
        t.title.toLowerCase().includes(q) ||
        (t.note && t.note.toLowerCase().includes(q)) ||
        t.creator.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q)
      );
    }
    
    // Filter: Ersteller
    if (params.creator?.length) {
      const set = new Set(params.creator);
      items = items.filter(t => set.has(t.creator));
    }
    
    // Filter: Vorlagenart
    if (params.type?.length) {
      const set = new Set(params.type);
      items = items.filter(t => set.has(t.type));
    }
    
    // Filter: Erstellungsdatum
    if (params.createdAtFrom) {
      items = items.filter(t => t.createdAt >= params.createdAtFrom!);
    }
    if (params.createdAtTo) {
      items = items.filter(t => t.createdAt <= params.createdAtTo!);
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
    
    return { items: paged, total: items.length, page, pageSize };
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
    // Placeholder: später ans Backend anpassen
    // Wenn eine Datei vorhanden ist, sollte sie hochgeladen werden
    if (payload.file) {
      // TODO: File-Upload zum Backend
      // const formData = new FormData();
      // formData.append('file', payload.file);
      // await fetchJson('/api/templates/upload', { method: 'POST', body: formData });
    }
    return { ok: true, id: String(Math.floor(Math.random() * 100000)) };
  },
  
  async deleteTemplate(id: string): Promise<{ ok: boolean }> {
    // Placeholder: später ans Backend anpassen
    // await fetchJson(`/api/templates/${id}`, { method: 'DELETE' });
    return { ok: true };
  }
};


