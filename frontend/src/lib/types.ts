export type DocumentStatus = 'Draft' | 'To Be Reviewed' | 'In Progress' | 'Not Started' | 'Finished';

export interface DocumentItem {
  id: string;
  modified: string;    // ISO-Date
  name: string;
  status: DocumentStatus;
  owner: string;
  mandant?: string;
  deadline?: string;   // ISO-Date
  template?: string;
}

export interface PagedResult<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}

export interface DocumentsQueryParams {
  query?: string;
  status?: string[];        // multiple
  owner?: string[];         // multiple
  template?: string[];      // multiple
  deadlineFrom?: string;
  deadlineTo?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
}

// ---- Clients ---
export type ClientType = 'Natürliche Person' | 'Gewerbe';

export type LegalForm =
  | 'Einzelunternehmen' 
  | 'Aktiengesellschaft (AG)' 
  | 'Gesellschaft bürgerlichen Rechts (GbR)' 
  | 'Gesellschaft mit beschränkter Haftung (GmbH)' 
  | 'GmbH & Co. KG' 
  | 'Kommanditgesellschaft (KG)' 
  | 'Offene Handelsgesellschaft (OHG)' 
  | 'Partnerschaftsgesellschaft (PartG)' 
  | 'Unternehmergesellschaft (UG)' 
  | 'Stiftung';

export type ParticipantRole =
  | 'Einzelunternehmer'
  | 'Aktionär'
  | 'Vorstand'
  | 'Gesellschafter'
  | 'Geschäftsführender Gesellschafter'
  | 'Komplementär'
  | 'Kommanditist'
  | 'Partner'
  | 'Geschäftsführender Partner'
  | 'Geschäftsführer'
  | 'Stifter'
  | 'Destinatär';

export interface Advisor {
  id: string;
  name: string;
}

export interface TaxOffice {
  zip?: string;
  city?: string;
  street?: string;
  number?: string;
  email?: string;
  fax?: string;
  contactSalutation?: string;
  contactLastName?: string;
  contactPhone?: string;
  taxCourt?: string;
}

export interface Participant {
  id: string;
  personId: string;  // ID der natürlichen Person
  firstName: string;
  lastName: string;
  role: ParticipantRole;
}

export interface ClientItem {
  id: string;
  type: ClientType;
  
  // Gemeinsame Felder
  mandateManager?: string;
  mandateResponsible?: string;
  zip?: string;
  city?: string;
  street?: string;
  number?: string;
  email?: string;
  taxNumber?: string;
  taxOffice?: TaxOffice;
  taxCourt?: string;
  
  // Natürliche Person
  salutation?: string;
  title?: string;
  firstName?: string;
  lastName?: string;
  birthDate?: string;  // ISO
  taxId?: string;  // Steuer-ID
  
  // Unternehmen
  companyName?: string;
  legalForm?: LegalForm;
  vatId?: string;  // UST-ID
  participants?: Participant[];  // Beteiligte
  
  // Meta
  advisorId?: string;
  advisorName?: string;
  createdAt: string;   // ISO
  updatedAt: string;   // ISO
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ---- Templates ----
export type TemplateType = 'Dokumente' | 'Textbausteine' | 'Layoutvorlagen';

export interface TemplateHistoryItem {
  id: string;
  date: string;  // ISO-Date
  user: string;
  change: string;  // Beschreibung der Änderung
}

export interface TemplateItem {
  id: string;
  createdAt: string;    // ISO-Date - Erstellungsdatum
  creator: string;      // Ersteller
  title: string;        // Titel
  note?: string;        // Notiz (optional)
  history: TemplateHistoryItem[];  // Änderungshistorie
  type: TemplateType;   // Vorlagenart
  fileUrl?: string;     // URL zur hochgeladenen Word-Datei (optional)
}

export interface TemplatesQueryParams {
  query?: string;
  creator?: string[];      // multiple
  type?: string[];         // multiple
  createdAtFrom?: string;
  createdAtTo?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
}

