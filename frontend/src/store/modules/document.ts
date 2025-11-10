interface DocumentState {
    documents: any[]
    currentDocument: any
    templates: Template[]
    currentTemplate: Template | null
}

interface Template {
    id: string
    name: string
    description: string
    fileName: string
    fileType: string
    filePath: string
    placeholders: Placeholder[]
    createdAt: string
    updatedAt: string
    previewUrl?: string
}

interface Placeholder {
    name: string
    type: string
    required: boolean
    defaultValue?: any
    options?: string[]
    validation: {
        pattern?: string
        min?: number
        max?: number
        minLength?: number
        maxLength?: number
        errorMessage?: string
    }
}

const document = {
    state: (): DocumentState => ({
        documents: [],
        currentDocument: null,
        templates: [],
        currentTemplate: null
    }),
    
    mutations: {
        SET_TEMPLATES(state: DocumentState, templates: Template[]) {
            state.templates = templates
        },
        
        ADD_TEMPLATE(state: DocumentState, template: Template) {
            state.templates.push(template)
        },
        
        UPDATE_TEMPLATE(state: DocumentState, template: Template) {
            const index = state.templates.findIndex(t => t.id === template.id)
            if (index !== -1) {
                state.templates[index] = template
            }
        },
        
        DELETE_TEMPLATE(state: DocumentState, templateId: string) {
            state.templates = state.templates.filter(t => t.id !== templateId)
        },
        
        SET_CURRENT_TEMPLATE(state: DocumentState, template: Template | null) {
            state.currentTemplate = template
        }
    },
    
    actions: {
        async fetchTemplates({ commit }: any) {
            try {
                // For demo purposes, return mock data
                const mockTemplates: Template[] = [
                    {
                        id: '1',
                        name: 'Arbeitsvertrag',
                        description: 'Standard Arbeitsvertrag Vorlage',
                        fileName: 'arbeitsvertrag.docx',
                        fileType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        filePath: '/uploads/templates/arbeitsvertrag.docx',
                        placeholders: [
                            {
                                name: 'arbeitgeber',
                                type: 'text',
                                required: true,
                                validation: {}
                            },
                            {
                                name: 'arbeitnehmer',
                                type: 'text',
                                required: true,
                                validation: {}
                            },
                            {
                                name: 'beginn',
                                type: 'date',
                                required: true,
                                validation: {}
                            }
                        ],
                        createdAt: '2023-05-15T10:30:00Z',
                        updatedAt: '2023-05-15T10:30:00Z'
                    }
                ]
                
                commit('SET_TEMPLATES', mockTemplates)
                return mockTemplates
            } catch (error) {
                console.error('Error fetching templates:', error)
                throw error
            }
        },
        
        async saveTemplate({ commit }: any, templateData: Partial<Template>) {
            try {
                // For demo purposes, create a mock template
                const newTemplate: Template = {
                    id: Date.now().toString(),
                    name: templateData.name || 'Unbenanntes Template',
                    description: templateData.description || '',
                    fileName: templateData.fileName || '',
                    fileType: templateData.fileType || '',
                    filePath: `/uploads/templates/${templateData.fileName}`,
                    placeholders: templateData.placeholders || [],
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                    previewUrl: templateData.previewUrl
                }
                
                commit('ADD_TEMPLATE', newTemplate)
                return newTemplate
            } catch (error) {
                console.error('Error saving template:', error)
                throw error
            }
        },
        
        async updateTemplate({ commit }: any, templateData: Template) {
            try {
                // For demo purposes, update the template directly
                const updatedTemplate = {
                    ...templateData,
                    updatedAt: new Date().toISOString()
                }
                
                commit('UPDATE_TEMPLATE', updatedTemplate)
                return updatedTemplate
            } catch (error) {
                console.error('Error updating template:', error)
                throw error
            }
        },
        
        async deleteTemplate({ commit }: any, templateId: string) {
            try {
                // Remove from state
                commit('DELETE_TEMPLATE', templateId)
                return true
            } catch (error) {
                console.error('Error deleting template:', error)
                throw error
            }
        },
        
        setCurrentTemplate({ commit }: any, template: Template | null) {
            commit('SET_CURRENT_TEMPLATE', template)
        }
    },
    
    getters: {
        allTemplates: (state: DocumentState) => state.templates,
        templateById: (state: DocumentState) => (id: string) => {
            return state.templates.find(template => template.id === id) || null
        },
        currentTemplate: (state: DocumentState) => state.currentTemplate
    }
}

export default document
