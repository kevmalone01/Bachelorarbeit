import axios from 'axios';

// Create Axios instance
const api = axios.create({
    baseURL: '',  // Empty because Vite proxy handles the path rewriting
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    }
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add authentication token and other common headers
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Centralized error handling
        if (error.response) {
            // Server response received with an error (non-2xx status)
            // Check if we expected a blob but got JSON error
            if (error.config.responseType === 'blob' && error.response.data instanceof Blob) {
                try {
                    // Try to parse the blob as JSON to get the actual error message
                    const text = await error.response.data.text();
                    const errorData = JSON.parse(text);
                    console.error('API Error Response (from blob):', errorData);
                    error.response.data = errorData;
                } catch (parseError) {
                    console.error('API Error Response:', error.response.data);
                }
            } else {
                console.error('API Error Response:', error.response.data);
            }
        } else if (error.request) {
            // Request sent, but no response received
            console.error('API No Response:', error.request);
        } else {
            // Request setup error
            console.error('API Request Error:', error.message);
        }
        return Promise.reject(error);
    }
);

export default api;

// Export document API functions
export const DocumentAPI = {
    // Get all document templates
    getTemplates: async () => {
        return api.get('/api/documents/templates');
    },
    
    // Get document by ID
    getDocumentById: async (documentId: number) => {
        return api.get(`/api/documents/${documentId}`);
    },
    
    // Get original document file by ID
    getDocumentFile: async (documentId: number) => {
        return api.get(`/api/documents/${documentId}/file`, {
            responseType: 'blob'
        });
    },
    
    // Get document text content by ID
    getDocumentText: async (documentId: number) => {
        return api.get(`/api/documents/${documentId}/text`);
    },
    
    // Get temporary preview without saving
    getTemporaryPreview: async (file: File, placeholderValues: Record<string, any>) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('placeholders', JSON.stringify(placeholderValues));
        

        return api.post('/api/documents/preview-temp', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Upload document
    uploadDocument: async (file: File, name: string, description: string) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('description', description);

        return api.post('/api/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    
    // Save document template with placeholders
    saveTemplate: async (file: File, name: string, description: string, placeholders: Array<any>) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('description', description);
        formData.append('placeholders', JSON.stringify(placeholders));

        return api.post('/api/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Update existing document template with placeholders
    updateTemplate: async (documentId: number, file: File | null, name: string, description: string, placeholders: Array<any>) => {
        const formData = new FormData();
        if (file) {
            formData.append('file', file);
        }
        formData.append('name', name);
        formData.append('description', description);
        formData.append('placeholders', JSON.stringify(placeholders));

        return api.put(`/api/documents/${documentId}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Create a document from a template
    createFromTemplate: async (templateId: number, placeholderValues: Record<string, any>) => {
        return api.post(`/api/documents/create-from-template/${templateId}`, placeholderValues);
    },

    // Get document preview by ID
    getDocumentPreview: async (documentId: number, placeholderValues: Record<string, any>) => {
        return api.post(`/api/documents/preview/${documentId}`, placeholderValues);
    },

    // Download document
    downloadDocument: async (documentId: number, placeholderValues: Record<string, any>) => {
        return api.post(`/api/documents/download/${documentId}`, placeholderValues, {
            responseType: 'blob'
        });
    },
    
    // Update placeholder name
    updatePlaceholderName: async (documentId: number, oldName: string, newName: string) => {
        return api.put(`/api/documents/${documentId}/placeholders/rename`, {
            oldName,
            newName
        });
    },
    
    // Update placeholder name in temporary file
    updatePlaceholderNameInTemp: async (file: File, oldName: string, newName: string) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('oldName', oldName);
        formData.append('newName', newName);
        
        return api.post('/api/documents/placeholders/rename-temp', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    
    // Delete document template
    deleteTemplate: async (documentId: number) => {
        return api.delete(`/api/documents/${documentId}`);
    }
}; 

// Export client API functions
export const ClientAPI = {
    // Get all clients
    getClients: async () => {
        return api.get('/api/clients');
    },

    // Get client by ID
    getClient: async (clientId: number) => {
        return api.get(`/api/clients/${clientId}`);
    },

    // Create new client
    createClient: async (clientData: Record<string, any>) => {
        return api.post('/api/clients', clientData);
    },

    // Update client
    updateClient: async (clientId: number, clientData: Record<string, any>) => {
        return api.put(`/api/clients/${clientId}`, clientData);
    },

    // Delete client
    deleteClient: async (clientId: number) => {
        return api.delete(`/api/clients/${clientId}`);
    }
}; 

// Export workflow API functions
export const WorkflowAPI = {
    // Get all work orders/workflows
    getWorkOrders: async () => {
        return api.get('/api/work-orders');
    },

    // Get work order by ID
    getWorkOrder: async (workOrderId: number) => {
        return api.get(`/api/work-orders/${workOrderId}`);
    },

    // Create new work order/workflow
    createWorkOrder: async (workflowData: Record<string, any>) => {
        return api.post('/api/work-orders', workflowData);
    },

    // Create new work order/workflow with documents
    createWorkOrderWithDocuments: async (workflowData: Record<string, any>, files: File[]) => {
        const formData = new FormData();
        
        // Add workflow data
        Object.keys(workflowData).forEach(key => {
            if (workflowData[key] !== null && workflowData[key] !== undefined) {
                formData.append(key, workflowData[key]);
            }
        });
        
        // Add files
        files.forEach((file, index) => {
            formData.append(`documents`, file);
        });

        return api.post('/api/work-orders/with-documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Update work order
    updateWorkOrder: async (workOrderId: number, workflowData: Record<string, any>) => {
        return api.put(`/api/work-orders/${workOrderId}`, workflowData);
    },

    // Delete work order
    deleteWorkOrder: async (workOrderId: number) => {
        return api.delete(`/api/work-orders/${workOrderId}`);
    },

    // Get workflow documents
    getWorkflowDocuments: async (workOrderId: number) => {
        return api.get(`/api/work-orders/${workOrderId}/documents`);
    },

    // Upload additional documents to existing workflow
    uploadWorkflowDocuments: async (workOrderId: number, files: File[]) => {
        const formData = new FormData();
        
        files.forEach((file) => {
            formData.append('documents', file);
        });

        return api.post(`/api/work-orders/${workOrderId}/documents`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Get workflow document file for viewing
    getWorkflowDocumentFile: async (workOrderId: number, documentId: number) => {
        return api.get(`/api/work-orders/${workOrderId}/documents/${documentId}/file`, {
            responseType: 'blob'
        });
    },

    // Delete workflow document
    deleteWorkflowDocument: async (workOrderId: number, documentId: number) => {
        return api.delete(`/api/work-orders/${workOrderId}/documents/${documentId}`);
    },

    // Extract fields from workflow documents using AI
    extractFieldsFromDocuments: async (workOrderId: number, templateId: number, userModel?: string) => {
        return api.post(`/api/work-orders/${workOrderId}/extract-fields`, {
            template_id: templateId,
            user_model_preference: userModel
        });
    },

    // Get AI summary of workflow documents
    getWorkflowDocumentsSummary: async (workOrderId: number) => {
        return api.get(`/api/work-orders/${workOrderId}/documents-summary`);
    }
}; 

// Export user API functions
export const UserAPI = {
    // Get user settings
    getUserSettings: async (userId: number) => {
        return api.get(`/api/users/settings/${userId}`);
    },

    // Update user settings
    updateUserSettings: async (userId: number, settings: Record<string, any>) => {
        return api.put(`/api/users/settings/${userId}`, settings);
    },

    // Get available Ollama models and status
    getAvailableModels: async () => {
        return api.get('/api/users/models');
    },

    // Get Ollama installer information
    getOllamaInstallerInfo: async () => {
        return api.get('/api/users/ollama-installer');
    },

    // Create new user
    createUser: async (userData: Record<string, any>) => {
        return api.post('/api/users', userData);
    }
}; 