/**
 * Composable for template editor state management.
 * Handles content, placeholders, fill values, and dirty tracking.
 */
import { ref, computed, watch } from 'vue';
import type { Placeholder, FillValues, DocumentTemplate } from '@/lib/types';
import { extractPlaceholders, mergeContent } from './useDocumentPlaceholders';

export function useTemplateEditor(initialTemplate?: DocumentTemplate) {
  // Editor state
  const contentHtml = ref(initialTemplate?.contentHtml || '');
  const placeholders = ref<Placeholder[]>(initialTemplate?.placeholders || []);
  const fillValues = ref<FillValues>({});
  const isDirty = ref(false);
  const templateName = ref(initialTemplate?.name || '');
  
  // Initialize fill values from placeholders with default values
  watch(placeholders, (newPlaceholders) => {
    newPlaceholders.forEach(placeholder => {
      if (placeholder.defaultValue !== undefined && !(placeholder.key in fillValues.value)) {
        fillValues.value[placeholder.key] = placeholder.defaultValue as string | number;
      }
    });
  }, { immediate: true });
  
  // Track changes
  watch([contentHtml, placeholders, templateName], () => {
    isDirty.value = true;
  }, { deep: true });
  
  // Merged content preview
  const mergedContent = computed(() => {
    return mergeContent(contentHtml.value, fillValues.value);
  });
  
  // Extract placeholders from current content
  // Preserves existing placeholder mappings (mappedFieldId, label, etc.)
  function scanPlaceholders() {
    const extracted = extractPlaceholders(contentHtml.value);
    
    console.log('[useTemplateEditor] scanPlaceholders - extracted:', extracted);
    console.log('[useTemplateEditor] scanPlaceholders - existing placeholders:', placeholders.value);
    
    // Preserve existing placeholder data (mappedFieldId, label, etc.) when keys match
    const existingPlaceholdersMap = new Map(
      placeholders.value.map(p => [p.key, p])
    );
    
    // Merge extracted placeholders with existing data
    const merged = extracted.map(newPlaceholder => {
      const existing = existingPlaceholdersMap.get(newPlaceholder.key);
      if (existing) {
        // Preserve existing mappings and metadata, but update type if changed
        const mergedPlaceholder = {
          ...newPlaceholder,
          // WICHTIG: mappedFieldId und mappedDbField müssen erhalten bleiben
          mappedFieldId: existing.mappedFieldId,
          mappedDbField: existing.mappedDbField,
          label: existing.label || newPlaceholder.label,
          defaultValue: existing.defaultValue,
          required: existing.required,
          description: existing.description,
        };
        console.log('[useTemplateEditor] Merged placeholder:', mergedPlaceholder.key, 'mappedFieldId:', mergedPlaceholder.mappedFieldId);
        return mergedPlaceholder;
      }
      console.log('[useTemplateEditor] New placeholder (no existing):', newPlaceholder.key);
      return newPlaceholder;
    });
    
    // Auch Platzhalter behalten, die nicht mehr im Content sind (falls gewünscht)
    // Für jetzt: Nur die gemergten Platzhalter verwenden
    
    console.log('[useTemplateEditor] Final merged placeholders:', merged);
    placeholders.value = merged;
    isDirty.value = true;
    return merged;
  }
  
  // Update placeholder
  function updatePlaceholder(key: string, updates: Partial<Placeholder>) {
    const index = placeholders.value.findIndex(p => p.key === key);
    if (index !== -1) {
      placeholders.value[index] = { ...placeholders.value[index], ...updates };
      isDirty.value = true;
    }
  }
  
  // Remove placeholder
  function removePlaceholder(key: string) {
    placeholders.value = placeholders.value.filter(p => p.key !== key);
    delete fillValues.value[key];
    isDirty.value = true;
  }
  
  // Update fill value
  function updateFillValue(key: string, value: string | number | null) {
    fillValues.value[key] = value;
  }
  
  // Reset all fill values
  function resetFillValues() {
    fillValues.value = {};
    placeholders.value.forEach(placeholder => {
      if (placeholder.defaultValue !== undefined) {
        fillValues.value[placeholder.key] = placeholder.defaultValue as string | number;
      }
    });
  }
  
  // Mark as saved
  function markSaved() {
    isDirty.value = false;
  }
  
  // Get template data for saving
  function getTemplateData(): Omit<DocumentTemplate, 'id'> {
    console.log('[useTemplateEditor] getTemplateData - placeholders:', placeholders.value);
    placeholders.value.forEach((p: any) => {
      console.log(`[useTemplateEditor] Placeholder ${p.key}: mappedFieldId=${p.mappedFieldId}, mappedDbField=${p.mappedDbField}`);
    });
    return {
      name: templateName.value,
      contentHtml: contentHtml.value,
      placeholders: placeholders.value,
    };
  }
  
  return {
    // State
    contentHtml,
    placeholders,
    fillValues,
    isDirty,
    templateName,
    
    // Computed
    mergedContent,
    
    // Methods
    scanPlaceholders,
    updatePlaceholder,
    removePlaceholder,
    updateFillValue,
    resetFillValues,
    markSaved,
    getTemplateData,
  };
}

