import { ClientAPI } from '@/services/api';

interface Client {
    id?: number;
    client_type: string;
    mandate_manager?: string;
    mandate_responsible?: string;
    email?: string;
    // General fields
    tax_number?: string;
    tax_office?: string;
    tax_court?: string;
    address_zip?: string;
    address_city?: string;
    address_street?: string;
    address_number?: string;
    // For physical persons
    salutation?: string;
    title?: string;
    first_name?: string;
    last_name?: string;
    birth_date?: string;
    tax_id?: string;
    // For companies
    company_name?: string;
    legal_form?: string;
    vat_id?: string;
    // Contact person
    contact_salutation?: string;
    contact_last_name?: string;
    contact_phone?: string;
    contact_email?: string;
    contact_fax?: string;
    // Tax data
    tax_office_zip?: string;
    tax_office_city?: string;
    tax_office_street?: string;
    tax_office_number?: string;
    tax_office_email?: string;
    tax_office_fax?: string;
}

interface ClientState {
    clients: Client[];
    currentClient: Client | null;
    loading: boolean;
    error: string | null;
}

const client = {
    namespaced: true,
    state: (): ClientState => ({
        clients: [],
        currentClient: null,
        loading: false,
        error: null
    }),
    mutations: {
        SET_CLIENTS(state: ClientState, clients: Client[]) {
            state.clients = clients;
        },
        SET_CURRENT_CLIENT(state: ClientState, client: Client) {
            state.currentClient = client;
        },
        SET_LOADING(state: ClientState, loading: boolean) {
            state.loading = loading;
        },
        SET_ERROR(state: ClientState, error: string | null) {
            state.error = error;
        },
        ADD_CLIENT(state: ClientState, client: Client) {
            state.clients.push(client);
        },
        UPDATE_CLIENT(state: ClientState, updatedClient: Client) {
            const index = state.clients.findIndex(c => c.id === updatedClient.id);
            if (index !== -1) {
                state.clients.splice(index, 1, updatedClient);
            }
        },
        REMOVE_CLIENT(state: ClientState, clientId: number) {
            state.clients = state.clients.filter(client => client.id !== clientId);
        }
    },
    actions: {
        async fetchClients({ commit }: any) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                const response = await ClientAPI.getClients();
                commit('SET_CLIENTS', response.data);
            } catch (error) {
                commit('SET_ERROR', 'Fehler beim Laden der Mandanten');
                console.error('Error fetching clients:', error);
            } finally {
                commit('SET_LOADING', false);
            }
        },
        async fetchClient({ commit }: any, clientId: number) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                const response = await ClientAPI.getClient(clientId);
                commit('SET_CURRENT_CLIENT', response.data);
            } catch (error) {
                commit('SET_ERROR', 'Fehler beim Laden des Mandanten');
                console.error('Error fetching client:', error);
            } finally {
                commit('SET_LOADING', false);
            }
        },
        async createClient({ commit }: any, clientData: Client) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                const response = await ClientAPI.createClient(clientData);
                commit('ADD_CLIENT', response.data);
                return response.data;
            } catch (error) {
                commit('SET_ERROR', 'Fehler beim Erstellen des Mandanten');
                console.error('Error creating client:', error);
                throw error;
            } finally {
                commit('SET_LOADING', false);
            }
        },
        async updateClient({ commit }: any, { clientId, clientData }: { clientId: number, clientData: Client }) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                const response = await ClientAPI.updateClient(clientId, clientData);
                commit('UPDATE_CLIENT', response.data);
                return response.data;
            } catch (error) {
                commit('SET_ERROR', 'Fehler beim Aktualisieren des Mandanten');
                console.error('Error updating client:', error);
                throw error;
            } finally {
                commit('SET_LOADING', false);
            }
        },
        async deleteClient({ commit }: any, clientId: number) {
            commit('SET_LOADING', true);
            commit('SET_ERROR', null);
            try {
                await ClientAPI.deleteClient(clientId);
                commit('REMOVE_CLIENT', clientId);
                return true;
            } catch (error) {
                commit('SET_ERROR', 'Fehler beim Löschen des Mandanten');
                console.error('Error deleting client:', error);
                throw error;
            } finally {
                commit('SET_LOADING', false);
            }
        }
    },
    getters: {
        getClients: (state: ClientState) => state.clients,
        getCurrentClient: (state: ClientState) => state.currentClient,
        isLoading: (state: ClientState) => state.loading,
        getError: (state: ClientState) => state.error
    }
}

export default client;
