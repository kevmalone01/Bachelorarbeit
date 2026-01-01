<template>
  <div class="flex-1 flex flex-col bg-white">
    <!-- Formatting Toolbar -->
    <div class="border-b border-slate-200 bg-white p-2 flex items-center gap-1 flex-wrap">
      <n-button-group size="small">
        <n-button quaternary @click="editor?.chain().focus().undo().run()" :disabled="!editor?.can().undo()">
          <template #icon>
            <Undo class="w-4 h-4" />
          </template>
        </n-button>
        <n-button quaternary @click="editor?.chain().focus().redo().run()" :disabled="!editor?.can().redo()">
          <template #icon>
            <Redo class="w-4 h-4" />
          </template>
        </n-button>
      </n-button-group>
      
      <div class="w-px h-6 bg-slate-200 mx-1" />
      
      <n-button-group size="small">
        <n-button
          quaternary
          :type="editor?.isActive('bold') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleBold().run()"
        >
          <strong>B</strong>
        </n-button>
        <n-button
          quaternary
          :type="editor?.isActive('italic') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleItalic().run()"
        >
          <em>I</em>
        </n-button>
        <n-button
          quaternary
          :type="editor?.isActive('underline') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleUnderline().run()"
        >
          <u>U</u>
        </n-button>
      </n-button-group>
      
      <div class="w-px h-6 bg-slate-200 mx-1" />
      
      <n-button-group size="small">
        <n-button
          quaternary
          :type="editor?.isActive('bulletList') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleBulletList().run()"
        >
          <List class="w-4 h-4" />
        </n-button>
        <n-button
          quaternary
          :type="editor?.isActive('orderedList') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleOrderedList().run()"
        >
          <ListOrdered class="w-4 h-4" />
        </n-button>
      </n-button-group>
      
      <div class="w-px h-6 bg-slate-200 mx-1" />
      
      <n-button
        quaternary
        size="small"
        :type="showRaw ? 'primary' : 'default'"
        @click="showRaw = !showRaw"
      >
        <template #icon>
          <Code class="w-4 h-4" />
        </template>
        {}
      </n-button>
      
      <div class="w-px h-6 bg-slate-200 mx-1" />
      
      <n-button
        quaternary
        size="small"
        :type="livePreview ? 'primary' : 'default'"
        @click="livePreview = !livePreview"
        title="Live-Vorschau: Platzhalter durch Werte ersetzen"
      >
        <template #icon>
          <Eye class="w-4 h-4" />
        </template>
        Vorschau
      </n-button>
      
      <n-button quaternary size="small" @click="editor?.chain().focus().clearNodes().unsetAllMarks().run()">
        Löschen
      </n-button>
    </div>
    
    <!-- Editor Content: Full width and height, white background -->
    <div class="flex-1 w-full overflow-y-auto bg-white px-6 pt-4 pb-0">
      <div v-if="showRaw" class="font-mono text-sm whitespace-pre-wrap text-gray-900">
        {{ rawContent }}
      </div>
      <div v-else-if="livePreview" class="w-full prose max-w-none text-gray-900" v-html="mergedContent" />
      <EditorContent v-else :editor="editor" class="w-full prose max-w-none text-gray-900" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import BulletList from '@tiptap/extension-bullet-list';
import OrderedList from '@tiptap/extension-ordered-list';
import CodeBlock from '@tiptap/extension-code-block';
import Link from '@tiptap/extension-link';
import { NButton, NButtonGroup } from 'naive-ui';
import { Undo, Redo, List, ListOrdered, Code, Eye } from 'lucide-vue-next';
import { PlaceholderMark } from './PlaceholderMark';
import { mergeContentWithMarking } from '@/composables/useDocumentPlaceholders';
import type { FillValues, Placeholder } from '@/lib/types';

const props = defineProps<{
  contentHtml: string;
  placeholders: Placeholder[];
  fillValues: FillValues;
}>();

const emit = defineEmits<{
  (e: 'update:contentHtml', v: string): void;
  (e: 'placeholderClick', key: string): void;
}>();

const showRaw = ref(false);
const livePreview = ref(false); // Live-Vorschau Button (separate Ansicht) - die echte Live-Vorschau läuft immer im Editor

const rawContent = computed(() => props.contentHtml);

// Computed property for merged content (live preview) with marking
const mergedContent = computed(() => {
  return mergeContentWithMarking(props.contentHtml, props.fillValues);
});

const editor = useEditor({
  content: props.contentHtml || '<p></p>',
  extensions: [
    StarterKit,
    Underline,
    BulletList,
    OrderedList,
    CodeBlock,
    Link.configure({
      openOnClick: false,
    }),
    PlaceholderMark.configure({
      fillValues: props.fillValues,
      onPlaceholderClick: (key: string) => {
        emit('placeholderClick', key);
      },
    }),
  ],
  onUpdate: ({ editor }) => {
    // When user edits, restore placeholders from merged content
    // The merged content has spans with data-placeholder-key, we need to extract the original placeholder
    let html = editor.getHTML();
    
    // Create a temporary DOM element to parse and modify HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Find all spans with placeholder keys and restore original placeholders
    const placeholderSpans = tempDiv.querySelectorAll('span[data-placeholder-key]');
    placeholderSpans.forEach((span: Element) => {
      const htmlSpan = span as HTMLElement;
      const key = htmlSpan.getAttribute('data-placeholder-key');
      if (!key) return;
      
      // Get original placeholder from data attribute or reconstruct it
      let originalPlaceholder = htmlSpan.getAttribute('data-original-placeholder');
      if (!originalPlaceholder) {
        // Try to get from title attribute or reconstruct
        const title = htmlSpan.getAttribute('title');
        if (title && title.includes('{{')) {
          const match = title.match(/\{\{([^}]+)\}\}/);
          if (match) {
            originalPlaceholder = match[0];
          }
        }
        if (!originalPlaceholder) {
          originalPlaceholder = `{{${key}}}`;
        }
      }
      
      // Replace span with original placeholder text
      const textNode = document.createTextNode(originalPlaceholder);
      htmlSpan.parentNode?.replaceChild(textNode, htmlSpan);
    });
    
    // Get the cleaned HTML
    html = tempDiv.innerHTML;
    
    emit('update:contentHtml', html);
  },
  editorProps: {
    attributes: {
      class: 'w-full prose max-w-none focus:outline-none text-gray-900',
    },
  },
});

// Update editor content when prop changes (but avoid infinite loops)
watch(() => props.contentHtml, (newContent) => {
  if (editor.value) {
    const currentContent = editor.value.getHTML();
    if (currentContent !== newContent && newContent) {
      console.log('Updating editor content:', { currentContent, newContent });
      // Use emitUpdate: false to prevent triggering onUpdate
      editor.value.commands.setContent(newContent, { emitUpdate: false });
    }
  }
}, { immediate: true });

// Store original content with placeholders
const originalContent = ref<string>(props.contentHtml);

// Update original content when contentHtml changes (but not when we update it ourselves)
watch(() => props.contentHtml, (newContent) => {
  if (editor.value && newContent) {
    const currentContent = editor.value.getHTML();
    // Only update original if it's a real change from outside (not our own update)
    // Check if the new content is the original (with placeholders) or merged (with values)
    const hasPlaceholderKeys = newContent.includes('data-placeholder-key');
    const hasPlaceholders = /\{\{\s*[^{}]+\s*\}\}/.test(newContent);
    
    // Update originalContent if:
    // 1. Content changed from outside AND
    // 2. It contains placeholders (not merged content) OR
    // 3. It doesn't have placeholder-key attributes (which means it's original, not merged)
    if (newContent !== currentContent && (hasPlaceholders || !hasPlaceholderKeys)) {
      // Extract original content by removing placeholder-key attributes and restoring {{ }} placeholders
      let cleanContent = newContent;
      if (hasPlaceholderKeys) {
        // If content has placeholder-key attributes, extract the original placeholders
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newContent;
        const placeholderSpans = tempDiv.querySelectorAll('[data-placeholder-key]');
        placeholderSpans.forEach((span) => {
          const key = span.getAttribute('data-placeholder-key');
          if (key) {
            const placeholder = document.createTextNode(`{{${key}}}`);
            span.parentNode?.replaceChild(placeholder, span);
          }
        });
        cleanContent = tempDiv.innerHTML;
      }
      originalContent.value = cleanContent;
      console.log('[EditorCanvas] Updated originalContent:', cleanContent.substring(0, 100));
    }
  } else if (!editor.value && newContent) {
    // If editor is not yet initialized, just store the content
    originalContent.value = newContent;
  }
}, { immediate: true });

// Update PlaceholderMark options when fillValues or placeholders change
watch([() => props.fillValues, () => props.placeholders], () => {
  if (editor.value) {
    const placeholderExtension = editor.value.extensionManager.extensions.find(
      ext => ext.name === 'placeholder'
    );
    if (placeholderExtension) {
      console.log('[EditorCanvas] Updating fillValues:', props.fillValues);
      placeholderExtension.options.fillValues = { ...props.fillValues };
      placeholderExtension.options.onPlaceholderClick = (key: string) => {
        emit('placeholderClick', key);
      };
      
      // Update editor content with merged values for live preview
      const merged = mergeContentWithMarking(originalContent.value || props.contentHtml, props.fillValues);
      const currentContent = editor.value.getHTML();
      
      // Always update content when fillValues change to show live preview
      // Use nextTick to ensure the update happens after the current render cycle
      nextTick(() => {
        if (editor.value) {
          // Only update if content actually changed (to avoid infinite loops)
          if (merged !== currentContent) {
            console.log('[EditorCanvas] Updating editor content with merged values for live preview');
            editor.value.commands.setContent(merged, { emitUpdate: false });
          }
          
          // Always force update to re-render decorations by dispatching a transaction
          // This ensures placeholders are updated even if content didn't change
          const tr = editor.value.state.tr.setMeta('updatePlaceholders', true);
          editor.value.view.dispatch(tr);
        }
      });
    }
  }
}, { deep: true, immediate: true });

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<style scoped>
:deep(.ProseMirror) {
  outline: none;
  min-height: auto !important;
  height: auto !important;
  width: 100%;
  background: white;
  color: #111827;
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}

:deep(.ph) {
  background-color: rgb(254 249 195);
  color: rgb(113 63 18);
  text-decoration: underline;
  text-decoration-style: dotted;
  cursor: pointer;
  padding-left: 0.25rem;
  padding-right: 0.25rem;
  border-radius: 0.25rem;
}

:deep(.ph--filled) {
  background-color: rgb(220 252 231);
  color: rgb(20 83 45);
  box-shadow: 0 0 0 1px rgb(134 239 172);
}

:deep(.ph:hover) {
  box-shadow: 0 0 0 2px rgb(96 165 250);
}

/* Remove any max-width constraints from prose */
:deep(.prose) {
  max-width: 100% !important;
  min-height: auto !important;
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}
</style>

