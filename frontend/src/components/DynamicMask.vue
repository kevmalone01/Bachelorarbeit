<template>
    <v-form ref="form" v-model="isFormValid" @submit.prevent class="dynamic-mask">
        <v-container>
            <!-- Regular form fields -->
            <v-card>
                <v-card-text>
                    <v-row>
                        <v-col v-for="(placeholder, index) in placeholders" :key="index" cols="12" sm="6">
                            <!-- Client field (read-only display) -->
                            <div v-if="placeholder.isClientField" class="client-field-container">
                                <v-text-field
                                    v-model="formValues[placeholder.name]"
                                    color="brown"
                                    :label="formatLabel(placeholder.name)"
                                    variant="outlined"
                                    readonly
                                    :prepend-inner-icon="'mdi-account-outline'"
                                >
                                    <template v-slot:append-inner>
                                        <v-tooltip text="Wird automatisch gefüllt">
                                            <template v-slot:activator="{ props }">
                                                <v-icon v-bind="props" size="small" color="info">mdi-information-outline</v-icon>
                                            </template>
                                        </v-tooltip>
                                    </template>
                                </v-text-field>
                            </div>

                            <!-- Regular form fields -->
                            <div v-else>
                                <!-- Text field -->
                                <v-text-field v-if="placeholder.type === 'text'" v-model="formValues[placeholder.name]"
                                    color="brown"
                                    :label="formatLabel(placeholder.name)" :placeholder="String(placeholder.defaultValue || '')"
                                    :rules="getRules(placeholder)" :required="placeholder.required" variant="outlined"
                                    @update:model-value="updateValue(placeholder.name)"></v-text-field>

                                <!-- Number field -->
                                <v-text-field v-else-if="placeholder.type === 'number'"
                                    color="brown"
                                    v-model="formValues[placeholder.name]" type="number"
                                    :label="formatLabel(placeholder.name)" :placeholder="String(placeholder.defaultValue || '')"
                                    :rules="getRules(placeholder)" :required="placeholder.required" variant="outlined"
                                    @update:model-value="updateValue(placeholder.name)"></v-text-field>

                                <!-- Date field -->
                                <v-text-field v-else-if="placeholder.type === 'date'"
                                    color="brown"
                                    v-model="formValues[placeholder.name]" type="date" :label="formatLabel(placeholder.name)"
                                    :rules="getRules(placeholder)" :required="placeholder.required" variant="outlined"  
                                    @update:model-value="updateValue(placeholder.name)"></v-text-field>

                                <!-- Select field -->
                                <v-select v-else-if="placeholder.type === 'select'" v-model="formValues[placeholder.name]"
                                    color="brown"
                                    :label="formatLabel(placeholder.name)" :items="placeholder.options || []"
                                    :rules="getRules(placeholder)" :required="placeholder.required" variant="outlined"
                                    @update:model-value="updateValue(placeholder.name)"></v-select>

                                <!-- Checkbox -->
                                <v-checkbox v-else-if="placeholder.type === 'checkbox'"
                                    color="brown"
                                    v-model="formValues[placeholder.name]" :label="formatLabel(placeholder.name)"
                                    :required="placeholder.required"
                                    @update:model-value="updateValue(placeholder.name)"></v-checkbox>

                                <!-- Textarea -->
                                <v-textarea v-else-if="placeholder.type === 'textarea'"
                                    color="brown"
                                    v-model="formValues[placeholder.name]" :label="formatLabel(placeholder.name)"
                                    :placeholder="String(placeholder.defaultValue || '')" :rules="getRules(placeholder)"
                                    :required="placeholder.required" variant="outlined"
                                    @update:model-value="updateValue(placeholder.name)"></v-textarea>

                                <!-- Default to text field if type is unknown -->
                                <v-text-field v-else v-model="formValues[placeholder.name]"
                                    color="brown"
                                    :label="formatLabel(placeholder.name)" :placeholder="String(placeholder.defaultValue || '')"
                                    :rules="getRules(placeholder)" :required="placeholder.required" variant="outlined"
                                    @update:model-value="updateValue(placeholder.name)"></v-text-field>
                            </div>
                        </v-col>
                    </v-row>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                        <!-- <v-btn color="brown" @click="validate">
                            Validieren
                        </v-btn> -->
                    <v-btn color="success" @click="submit" :disabled="!isFormValid">
                        Bestätigen
                    </v-btn>
                </v-card-actions>
            </v-card>

            <!-- Client field groups section -->
            <div v-if="clientFieldGroups && clientFieldGroups.length > 0" class="client-selection mb-8">
                
                <div v-for="(group, index) in clientFieldGroups" :key="group.groupName" class="client-group" color="brown">
                    <div class="text-subtitle-2 mb-3" color="brown">
                        {{ formatGroupName(group.groupName) }}
                    </div>
                    
                    <v-autocomplete
                        v-model="selectedClients[group.groupName]"
                        :items="clients || []"
                        item-title="clientDisplayName"
                        item-value="id"
                        label="Mandant auswählen"
                        placeholder="Tippen Sie um zu suchen..."
                        variant="outlined"
                        density="comfortable"
                        clearable
                        hide-details
                        class="mb-3 client-selector"
                        color="brown"
                        no-data-text="Keine Mandanten gefunden"
                        @update:model-value="(clientId) => onClientSelected(group.groupName, clientId)"
                    >
                        <template v-slot:selection="{ item }">
                            <div class="d-flex align-center">
                                <v-avatar size="32" class="me-3" color="brown" variant="outlined">
                                    <v-icon color="brown" size="18">
                                        {{ item.raw.client_type === 'natural' ? 'mdi-account' : 'mdi-domain' }}
                                    </v-icon>
                                </v-avatar>
                                <div>
                                    <div class="text-body-1">{{ item.raw.client_type === 'natural' ? (item.raw.first_name && item.raw.last_name ? item.raw.first_name + ' ' + item.raw.last_name : item.raw.clientDisplayName) : item.raw.clientDisplayName }}</div>
                                </div>
                            </div>
                        </template>
                        <template v-slot:item="{ props, item }">
                            <v-list-item 
                                v-bind="props" 
                                class="client-list-item"
                                color="brown"
                            >
                                <template v-slot:prepend>
                                    <v-avatar size="40" class="me-3" color="brown" variant="outlined">
                                        <v-icon color="brown" size="20">
                                            {{ item.raw.client_type === 'natural' ? 'mdi-account' : 'mdi-domain' }}
                                        </v-icon>
                                    </v-avatar>
                                </template>
                                <v-list-item-subtitle class="text-caption" color="brown">
                                    {{ item.raw.client_type === 'natural' ? 'Natürliche Person' : 'Unternehmen' }}
                                </v-list-item-subtitle>
                                <template v-slot:append>
                                    <v-chip 
                                        size="small" 
                                        color="brown" 
                                        variant="tonal"
                                        class="text-caption"
                                    >
                                        {{ item.raw.client_type === 'natural' ? 'Person' : 'Firma' }}
                                    </v-chip>
                                </template>
                            </v-list-item>
                        </template>
                    </v-autocomplete>
                    
                    <!-- Colored field preview -->
                    <div v-if="group.fields && group.fields.length > 0" class="field-preview" color="brown">
                        Platzhalter: {{ group.fields.map(f => formatLabel(f.name)).join(', ') }}
                    </div>
                </div>
            </div>
        </v-container>
    </v-form>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, watch, onMounted } from 'vue';
import type { PropType } from 'vue';

interface Placeholder {
    name: string;
    type: 'text' | 'date' | 'select' | 'number' | 'checkbox' | 'textarea' | string;
    defaultValue?: string | number | boolean;
    required?: boolean;
    options?: string[];
    validation?: {
        pattern?: string;
        min?: number;
        max?: number;
        minLength?: number;
        maxLength?: number;
        errorMessage?: string;
    };
    isClientField?: boolean;
}

export default defineComponent({
    name: 'DynamicMask',

    props: {
        placeholders: {
            type: Array as PropType<Placeholder[]>,
            required: true
        },
        title: {
            type: String,
            default: 'Dokumenten-Maske',
        },
        initialValues: {
            type: Object,
            default: () => ({})
        },
        clientFieldGroups: {
            type: Array as PropType<{ groupName: string; fields: Placeholder[] }[]>,
            default: () => []
        },
        clients: {
            type: Array as PropType<{ id: string; clientDisplayName: string; client_type: string; first_name?: string; last_name?: string }[]>,
            default: () => []
        }
    },

    emits: ['update:values', 'submit', 'validation', 'client-selected'],

    setup(props, { emit }) {
        const form = ref(null);
        const isFormValid = ref(true);
        const formValues = reactive<Record<string, any>>({});
        const selectedClients = reactive<Record<string, string>>({});

        // Initialize form values from props and placeholders
        const initializeFormValues = () => {
            // Add safety check for placeholders
            if (!props.placeholders || !Array.isArray(props.placeholders)) {
                return;
            }
            
            props.placeholders.forEach((placeholder) => {
                // Add safety check for placeholder object
                if (!placeholder || typeof placeholder !== 'object' || !placeholder.name) {
                    return;
                }
                
                // Check if there's an initial value provided
                if (props.initialValues && Object.prototype.hasOwnProperty.call(props.initialValues, placeholder.name)) {
                    formValues[placeholder.name] = props.initialValues[placeholder.name];
                } else if (placeholder.defaultValue !== undefined) {
                    // Set defaultValue according to field type
                    switch (placeholder.type) {
                        case 'date':
                            // Convert string date to proper date format if needed
                            if (typeof placeholder.defaultValue === 'string') {
                                formValues[placeholder.name] = placeholder.defaultValue;
                            } else {
                                formValues[placeholder.name] = '';
                            }
                            break;
                        case 'number':
                            // Ensure number type for number fields
                            formValues[placeholder.name] = Number(placeholder.defaultValue);
                            break;
                        case 'checkbox':
                            // Convert to boolean for checkboxes
                            formValues[placeholder.name] = Boolean(placeholder.defaultValue);
                            break;
                        case 'select':
                            // Verify that the default value is in the options
                            if (placeholder.options && placeholder.options.includes(String(placeholder.defaultValue))) {
                                formValues[placeholder.name] = placeholder.defaultValue;
                            } else if (placeholder.options && placeholder.options.length > 0) {
                                formValues[placeholder.name] = placeholder.options[0];
                            } else {
                                formValues[placeholder.name] = '';
                            }
                            break;
                        default:
                            formValues[placeholder.name] = placeholder.defaultValue;
                    }
                } else {
                    // Initialize with appropriate empty value based on type
                    switch (placeholder.type) {
                        case 'checkbox':
                            formValues[placeholder.name] = false;
                            break;
                        case 'number':
                            formValues[placeholder.name] = null;
                            break;
                        case 'date':
                            formValues[placeholder.name] = '';
                            break;
                        case 'select':
                            formValues[placeholder.name] = placeholder.options && placeholder.options.length > 0
                                ? placeholder.options[0]
                                : '';
                            break;
                        default:
                            formValues[placeholder.name] = '';
                    }
                }
            });
        };

        // Format field labels to capitalize and replace underscores with spaces
        const formatLabel = (name: string): string => {
            return name
                .replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        };

        // Generate validation rules based on placeholder properties
        const getRules = (placeholder: Placeholder) => {
            const rules: Array<(v: any) => boolean | string> = [];

            // Required field validation
            if (placeholder.required) {
                rules.push((v) => !!v || `${formatLabel(placeholder.name)} ist erforderlich`);
            }

            // Validation based on type and validation options
            if (placeholder.validation) {
                const validation = placeholder.validation;

                // Pattern validation (regex)
                if (validation.pattern) {
                    const pattern = new RegExp(validation.pattern);
                    rules.push((v) => !v || pattern.test(v) ||
                        validation.errorMessage || `Ungültiges Format für ${formatLabel(placeholder.name)}`);
                }

                // Min/max for number type
                if (placeholder.type === 'number') {
                    if (validation.min !== undefined) {
                        rules.push((v) => !v || Number(v) >= validation.min! ||
                            `Minimum Wert ist ${validation.min}`);
                    }
                    if (validation.max !== undefined) {
                        rules.push((v) => !v || Number(v) <= validation.max! ||
                            `Maximum Wert ist ${validation.max}`);
                    }
                }

                // Min/max length for string types
                if (['text', 'textarea'].includes(placeholder.type)) {
                    if (validation.minLength !== undefined) {
                        rules.push((v) => !v || v.length >= validation.minLength! ||
                            `Mindestlänge ist ${validation.minLength} Zeichen`);
                    }
                    if (validation.maxLength !== undefined) {
                        rules.push((v) => !v || v.length <= validation.maxLength! ||
                            `Maximallänge ist ${validation.maxLength} Zeichen`);
                    }
                }
            }

            return rules;
        };

        // Update parent component with changed values
        const updateValue = (name: string) => {
            // Add safety check
            if (!name || typeof formValues !== 'object') {
                return;
            }
            
            try {
                emit('update:values', { ...formValues });
            } catch (error) {
                console.warn('Error updating values:', error);
            }
        };

        // Validate all fields
        const validate = async () => {
            if (!form.value) return false;

            try {
                const { valid } = await (form.value as any).validate();
                emit('validation', valid);
                return valid;
            } catch (error) {
                console.warn('Error validating form:', error);
                return false;
            }
        };

        // Submit the form
        const submit = async () => {
            try {
                const isValid = await validate();
                if (isValid) {
                    emit('submit', { ...formValues });
                }
            } catch (error) {
                console.warn('Error submitting form:', error);
            }
        };

        // Watch for changes in placeholders or initialValues
        watch(() => props.placeholders, () => {
            try {
                initializeFormValues();
            } catch (error) {
                console.warn('Error initializing form values from placeholders:', error);
            }
        }, { deep: true });
        
        watch(() => props.initialValues, () => {
            try {
                initializeFormValues();
                // Only emit if we actually changed something
                emit('update:values', { ...formValues });
            } catch (error) {
                console.warn('Error initializing form values from initial values:', error);
            }
        }, { deep: true });

        // Remove the automatic watcher on formValues to prevent circular updates
        // The updateValue function will handle emitting when users actually change values

        // Initialize form values on component mount (without auto-emit)
        onMounted(() => {
            try {
                initializeFormValues();
            } catch (error) {
                console.warn('Error initializing form values on mount:', error);
            }
        });

        const formatGroupName = (groupName: string): string => {
            return groupName
                .replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        };

        const onClientSelected = (groupName: string, clientId: string) => {
            // Emit the client-selected event to parent component
            emit('client-selected', groupName, clientId ? parseInt(clientId) : null);
        };

        const getClientItemClass = (clientType: string): string => {
            return clientType === 'natural' 
                ? 'client-item-natural' 
                : 'client-item-company';
        };

        const getClientIndicatorClass = (clientType: string): string => {
            return clientType === 'natural' 
                ? 'client-indicator-natural' 
                : 'client-indicator-company';
        };

        const getFieldPreviewClass = (index: number): string => {
            const colors = ['field-preview-blue', 'field-preview-green', 'field-preview-purple', 'field-preview-orange', 'field-preview-teal'];
            return colors[index % colors.length];
        };

        return {
            form,
            isFormValid,
            formValues,
            formatLabel,
            getRules,
            updateValue,
            validate,
            submit,
            formatGroupName,
            onClientSelected,
            selectedClients,
            getClientItemClass,
            getClientIndicatorClass,
            getFieldPreviewClass
        };
    }
});
</script>

<style scoped>
.v-card {
    margin-bottom: 20px;
}

.dynamic-mask {
    overflow-y: auto;
    max-height: 60vh;
}

.client-selection {
    /* border-bottom: 1px solid #e0e0e0; */
    /* padding-bottom: 2rem; */
    /* margin-bottom: 2rem; */
}

.client-group {
    margin-bottom: 1.5rem;
    padding: 1.5rem;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: 1px solid #f0f0f0;
}

.client-group:not(:last-child) {
    border-bottom: 1px solid #f5f5f5;
}

.client-group:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Group color classes */
.bg-blue-50 {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-color: #bae6fd;
}

.bg-green-50 {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border-color: #bbf7d0;
}

.bg-purple-50 {
    background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
    border-color: #d8b4fe;
}

.bg-orange-50 {
    background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
    border-color: #fdba74;
}

.bg-teal-50 {
    background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
    border-color: #99f6e4;
}

/* Text colors */
.text-blue-700 {
    color: #1d4ed8;
    font-weight: 600;
}

.text-green-700 {
    color: #15803d;
    font-weight: 600;
}

.text-purple-700 {
    color: #7c3aed;
    font-weight: 600;
}

.text-orange-700 {
    color: #c2410c;
    font-weight: 600;
}

.text-teal-700 {
    color: #0f766e;
    font-weight: 600;
}

.text-blue-600 {
    color: #2563eb;
}

.text-green-600 {
    color: #16a34a;
}

/* Client selector styles */
.client-selector {
    border-radius: 8px;
}

.client-selector .v-field {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.client-selector .v-field:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.client-selector .v-field--focused {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Client list item styles */
.client-list-item {
    padding: 12px 16px;
    margin: 4px 8px;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.client-list-item:hover {
    background: #f8fafc;
    transform: translateX(4px);
}

.client-item-natural:hover {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.client-item-company:hover {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

/* Field preview styles */
.field-preview {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.875rem;
    margin-top: 8px;
    font-weight: 500;
    border: 1px solid transparent;
}

.field-preview-blue {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    color: #1e40af;
    border-color: #93c5fd;
}

.field-preview-green {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    color: #166534;
    border-color: #86efac;
}

.field-preview-purple {
    background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
    color: #6b21a8;
    border-color: #c4b5fd;
}

.field-preview-orange {
    background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
    color: #9a3412;
    border-color: #fb923c;
}

.field-preview-teal {
    background: linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%);
    color: #134e4a;
    border-color: #5eead4;
}

/* Avatar and icon enhancements */
.v-avatar {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.client-list-item:hover .v-avatar {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Chip styling */
.v-chip {
    font-weight: 500;
    letter-spacing: 0.5px;
}
</style>
