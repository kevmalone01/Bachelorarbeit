<template>
    <v-card class="mask-card">
        <v-card-text>
            <v-row>
                <v-col v-for="(placeholder, index) in placeholders" :key="index" cols="12" sm="6">
                    <!-- Readonly mode -->
                    <template v-if="readonly">
                        <div class="mask-field">
                            <span class="mask-label">{{ formatLabel(placeholder.label || placeholder.name) }}:</span>
                            <span class="mask-value">{{ displayValue(placeholder) }}</span>
                        </div>
                    </template>
                    <!-- Editable mode -->
                    <template v-else>
                        <!-- Text field -->
                        <v-text-field v-if="placeholder.type === 'text'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :placeholder="String(placeholder.defaultValue || '')"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                        <!-- Number field -->
                        <v-text-field v-else-if="placeholder.type === 'number'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            type="number"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :placeholder="String(placeholder.defaultValue || '')"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                        <!-- Date field -->
                        <v-text-field v-else-if="placeholder.type === 'date'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            type="date"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                        <!-- Select field -->
                        <v-select v-else-if="placeholder.type === 'select'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :items="placeholder.options || []"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                        <!-- Checkbox -->
                        <v-checkbox v-else-if="placeholder.type === 'checkbox'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :required="placeholder.required"
                            @update:model-value="emitUpdate"
                        />
                        <!-- Textarea -->
                        <v-textarea v-else-if="placeholder.type === 'textarea'"
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :placeholder="String(placeholder.defaultValue || '')"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                        <!-- Default to text field if type is unknown -->
                        <v-text-field v-else
                            v-model="localValues[placeholder.name]"
                            color="brown"
                            :label="formatLabel(placeholder.label || placeholder.name)"
                            :placeholder="String(placeholder.defaultValue || '')"
                            :required="placeholder.required"
                            variant="outlined"
                            density="compact"
                            hide-details
                            @update:model-value="emitUpdate"
                        />
                    </template>
                </v-col>
            </v-row>
        </v-card-text>
    </v-card>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue';
import type { PropType } from 'vue';

interface Placeholder {
    name: string;
    type: string;
    label?: string;
    defaultValue?: string | number | boolean;
    required?: boolean;
    options?: string[];
}

export default defineComponent({
    name: 'Mask',
    props: {
        placeholders: {
            type: Array as PropType<Placeholder[]>,
            required: true
        },
        values: {
            type: Object as () => Record<string, any>,
            required: true
        },
        title: {
            type: String,
            default: 'Masken-Ansicht',
        },
        readonly: {
            type: Boolean,
            default: true
        }
    },
    emits: ['update:values'],
    setup(props, { emit }) {
        const localValues = ref({ ...props.values });

        watch(() => props.values, (newVal) => {
            localValues.value = { ...newVal };
        }, { deep: true });

        const emitUpdate = () => {
            emit('update:values', { ...localValues.value });
        };

        // Format field labels to capitalize and replace underscores with spaces
        const formatLabel = (name: string): string => {
            return name
                .replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        };

        // Display value for readonly mode
        const displayValue = (placeholder: Placeholder) => {
            const value = localValues.value[placeholder.name];
            if (placeholder.type === 'checkbox') {
                return value ? '✓' : '';
            }
            return value;
        };

        return { formatLabel, localValues, emitUpdate, displayValue };
    }
});
</script>

<style scoped>
.mask-card {
    margin-bottom: 20px;
}

.mask-field {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.mask-label {
    font-weight: bold;
    margin-right: 8px;
    min-width: 120px;
}

.mask-value {
    color: #5d4037;
}
</style>