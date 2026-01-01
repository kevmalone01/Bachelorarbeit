/**
 * Custom tiptap Mark Extension for highlighting placeholders {{ key }}
 */
import { Mark, mergeAttributes, type RawCommands } from '@tiptap/core';
import { Plugin } from 'prosemirror-state';
import { Decoration, DecorationSet } from 'prosemirror-view';

export interface PlaceholderMarkOptions {
  HTMLAttributes: Record<string, any>;
  fillValues: Record<string, any>;
  onPlaceholderClick?: (key: string) => void;
}

export const PlaceholderMark = Mark.create<PlaceholderMarkOptions>({
  name: 'placeholder',
  
  addOptions() {
    return {
      HTMLAttributes: {},
      fillValues: {},
      onPlaceholderClick: undefined,
    };
  },
  
  addProseMirrorPlugins() {
    const extension = this;
    const options = this.options as PlaceholderMarkOptions;
    
    function createDecorations(doc: any, opts: PlaceholderMarkOptions) {
      const decorations: Decoration[] = [];
      const { fillValues, onPlaceholderClick } = opts;
      
      doc.descendants((node: any, pos: number) => {
        if (node.isText && node.text) {
          // Pattern matches everything between {{ and }} except the braces themselves
          // Supports Unicode letters, numbers, spaces, and special characters
          const regex = /\{\{\s*([^{}]+?)\s*\}\}/g;
          let match;
          
          while ((match = regex.exec(node.text)) !== null) {
            const key = match[1].trim();
            const from = pos + match.index;
            const to = from + match[0].length;
            const filled = fillValues[key] !== null && fillValues[key] !== undefined && fillValues[key] !== '';
            const value = filled ? String(fillValues[key]) : null;
            
            decorations.push(
              Decoration.inline(from, to, {
                class: `ph ${filled ? 'ph--filled' : ''}`,
                'data-placeholder-key': key,
                'data-filled': filled ? 'true' : undefined,
                'data-placeholder-value': value || undefined,
                'data-original-placeholder': match[0], // Store original placeholder text
                title: filled && value ? `{{${key}}} → ${value}` : `{{${key}}}`,
                style: 'cursor: pointer;',
              })
            );
          }
        }
      });
      
      return DecorationSet.create(doc, decorations);
    }
    
    return [
      new Plugin({
        state: {
          init(_, { doc }) {
            return createDecorations(doc, options);
          },
          apply(tr, oldState) {
            // Get current options from extension
            const currentOptions = (extension as any).options as PlaceholderMarkOptions;
            if (tr.docChanged || tr.getMeta('updatePlaceholders')) {
              return createDecorations(tr.doc, currentOptions);
            }
            return oldState;
          },
        },
        props: {
          decorations(state) {
            const currentOptions = (extension as any).options as PlaceholderMarkOptions;
            return createDecorations(state.doc, currentOptions);
          },
          handleClick(view, pos, event) {
            const { fillValues, onPlaceholderClick } = (extension as any).options as PlaceholderMarkOptions;
            const $pos = view.state.doc.resolve(pos);
            const node = $pos.node();
            
            if (node && node.isText && node.text) {
              const text = node.text;
              const regex = /\{\{\s*([^{}]+?)\s*\}\}/g;
              let match: RegExpExecArray | null;
              let offset = 0;
              
              // Calculate the actual position in the node
              let nodeStart = pos - $pos.textOffset;
              
              while ((match = regex.exec(text)) !== null) {
                if (!match[1]) continue;
                const key = match[1].trim();
                if (!key) continue;
                
                const matchStart = nodeStart + match.index;
                const matchEnd = matchStart + match[0].length;
                
                if (pos >= matchStart && pos <= matchEnd) {
                  event.stopPropagation();
                  if (onPlaceholderClick) {
                    onPlaceholderClick(key);
                  }
                  return true;
                }
              }
            }
            
            return false;
          },
        },
      }),
      // Plugin to replace placeholder text with values in the DOM for live preview
      // Keeps the visual marking (CSS classes) while replacing the text
      // This allows editing while showing the preview
      new Plugin({
        state: {
          init() {
            // Store last known fillValues to detect changes
            return { lastFillValues: JSON.stringify((extension as any).options.fillValues || {}) };
          },
          apply(tr, value) {
            // Check if fillValues changed by comparing with stored values
            const currentFillValues = JSON.stringify((extension as any).options.fillValues || {});
            if (currentFillValues !== value.lastFillValues) {
              // FillValues changed, trigger update
              return { lastFillValues: currentFillValues };
            }
            return value;
          },
        },
        view(editorView) {
          let isUpdating = false;
          let updateInterval: ReturnType<typeof setInterval> | null = null;
          let lastFillValuesStr = JSON.stringify((extension as any).options.fillValues || {});
          let observer: MutationObserver | null = null;
          
          const updatePlaceholderText = () => {
            if (isUpdating) return;
            isUpdating = true;
            
            try {
              const { fillValues } = (extension as any).options as PlaceholderMarkOptions;
              const currentFillValuesStr = JSON.stringify(fillValues || {});
              
              // Check if fillValues actually changed
              if (currentFillValuesStr === lastFillValuesStr && updateInterval) {
                // No change, skip update
                return;
              }
              
              lastFillValuesStr = currentFillValuesStr;
              const dom = editorView.dom;
              
              // Find all text nodes that contain placeholders
              const walker = document.createTreeWalker(dom, NodeFilter.SHOW_TEXT, null);
              const textNodes: Text[] = [];
              let node: Node | null;
              while ((node = walker.nextNode())) {
                if (node.nodeType === Node.TEXT_NODE && node.textContent && node.textContent.includes('{{')) {
                  textNodes.push(node as Text);
                }
              }
              
              // Also find placeholder decorations
              const placeholderSpans = dom.querySelectorAll('span[data-placeholder-key]');
              
              // Update placeholder spans
              placeholderSpans.forEach((span: Element) => {
                const htmlSpan = span as HTMLElement;
                const key = htmlSpan.getAttribute('data-placeholder-key');
                if (!key) return;
                
                const originalPlaceholder = htmlSpan.getAttribute('data-original-placeholder') || `{{${key}}}`;
                const isFilled = fillValues[key] !== null && fillValues[key] !== undefined && fillValues[key] !== '';
                
                // Ensure the marking classes are always present
                if (!htmlSpan.classList.contains('ph')) {
                  htmlSpan.classList.add('ph');
                }
                if (isFilled && !htmlSpan.classList.contains('ph--filled')) {
                  htmlSpan.classList.add('ph--filled');
                } else if (!isFilled && htmlSpan.classList.contains('ph--filled')) {
                  htmlSpan.classList.remove('ph--filled');
                }
                
                if (isFilled) {
                  const value = String(fillValues[key]);
                  const currentValue = htmlSpan.getAttribute('data-placeholder-value');
                  
                  // Always update if value changed or if showing placeholder
                  const currentText = htmlSpan.textContent || '';
                  if (currentValue !== value || currentText.includes('{{') || currentText.trim() === originalPlaceholder.trim()) {
                    // Store the original text in a data attribute
                    htmlSpan.setAttribute('data-original-text', originalPlaceholder);
                    // Replace with value (marking classes are preserved)
                    htmlSpan.textContent = value;
                    htmlSpan.setAttribute('data-placeholder-value', value);
                    htmlSpan.setAttribute('data-filled', 'true');
                    // Ensure cursor pointer style is maintained
                    htmlSpan.style.cursor = 'pointer';
                  }
                } else {
                  // Restore original placeholder if value is removed
                  const originalText = htmlSpan.getAttribute('data-original-text') || originalPlaceholder;
                  const currentText = htmlSpan.textContent || '';
                  if (currentText !== originalText && !currentText.includes('{{')) {
                    htmlSpan.textContent = originalText;
                    htmlSpan.removeAttribute('data-placeholder-value');
                    htmlSpan.removeAttribute('data-original-text');
                    htmlSpan.removeAttribute('data-filled');
                  }
                }
              });
              
              // Also update text nodes directly (for placeholders not yet decorated)
              textNodes.forEach((textNode) => {
                const text = textNode.textContent || '';
                const regex = /\{\{\s*([^{}]+?)\s*\}\}/g;
                let match;
                while ((match = regex.exec(text)) !== null) {
                  const key = match[1].trim();
                  if (fillValues[key] !== null && fillValues[key] !== undefined && fillValues[key] !== '') {
                    const value = String(fillValues[key]);
                    // Replace in text node
                    textNode.textContent = text.replace(match[0], value);
                    break; // Only replace first match per node
                  }
                }
              });
            } finally {
              isUpdating = false;
            }
          };
          
          // Initial update
          setTimeout(updatePlaceholderText, 100);
          
          // Set up MutationObserver to watch for DOM changes
          observer = new MutationObserver(() => {
            if (!isUpdating) {
              setTimeout(updatePlaceholderText, 50);
            }
          });
          
          observer.observe(editorView.dom, {
            childList: true,
            subtree: true,
            characterData: true,
          });
          
          // Set up interval to check for fillValues changes
          updateInterval = setInterval(() => {
            const currentFillValuesStr = JSON.stringify((extension as any).options.fillValues || {});
            if (currentFillValuesStr !== lastFillValuesStr) {
              updatePlaceholderText();
            }
          }, 100); // Check every 100ms for faster updates
          
          return {
            update: (view, prevState) => {
              // Update DOM after each transaction
              setTimeout(() => {
                updatePlaceholderText();
              }, 0);
            },
            destroy: () => {
              if (updateInterval) {
                clearInterval(updateInterval);
              }
              if (observer) {
                observer.disconnect();
              }
            },
          };
        },
      }),
    ];
  },
  
  addAttributes() {
    return {
      key: {
        default: null,
        parseHTML: element => element.getAttribute('data-placeholder-key'),
        renderHTML: attributes => {
          if (!attributes.key) {
            return {};
          }
          return {
            'data-placeholder-key': attributes.key,
          };
        },
      },
      filled: {
        default: false,
        parseHTML: element => element.hasAttribute('data-filled'),
        renderHTML: attributes => {
          if (!attributes.filled) {
            return {};
          }
          return {
            'data-filled': 'true',
          };
        },
      },
      value: {
        default: null,
        parseHTML: element => element.getAttribute('data-placeholder-value'),
        renderHTML: attributes => {
          if (!attributes.value) {
            return {};
          }
          return {
            'data-placeholder-value': attributes.value,
          };
        },
      },
    };
  },
  
  parseHTML() {
    return [
      {
        tag: 'span[data-placeholder-key]',
        getAttrs: (node) => {
          if (typeof node === 'string') return false;
          const element = node as HTMLElement;
          return {
            key: element.getAttribute('data-placeholder-key'),
            filled: element.hasAttribute('data-filled'),
            value: element.getAttribute('data-placeholder-value'),
          };
        },
      },
    ];
  },
  
  renderHTML({ HTMLAttributes, mark }) {
    const key = mark.attrs.key;
    const filled = mark.attrs.filled;
    const value = mark.attrs.value;
    
    const classes = ['ph'];
    if (filled) {
      classes.push('ph--filled');
    }
    
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: classes.join(' '),
        'data-placeholder-key': key,
        'data-filled': filled ? 'true' : undefined,
        'data-placeholder-value': value || undefined,
        title: filled && value ? `{{${key}}} → ${value}` : `{{${key}}}`,
        style: 'cursor: pointer;',
        onclick: () => {
          if (this.options.onPlaceholderClick && key) {
            this.options.onPlaceholderClick(key);
          }
        },
      }),
      0,
    ];
  },
  
  addCommands() {
    return {
      setPlaceholder: (attributes: Record<string, any>) => ({ commands }: { commands: any }) => {
        return commands.setMark(this.name, attributes);
      },
      togglePlaceholder: (attributes: Record<string, any>) => ({ commands }: { commands: any }) => {
        return commands.toggleMark(this.name, attributes);
      },
      unsetPlaceholder: () => ({ commands }: { commands: any }) => {
        return commands.unsetMark(this.name);
      },
    } as Partial<RawCommands>;
  },
});


