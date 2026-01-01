/**
 * Composable for document placeholder extraction and merging.
 * Reuses logic from DocumentCreationView.
 */
import type { Placeholder, PlaceholderType, FillValues } from '@/lib/types';

/**
 * Extract placeholders from HTML/text content using regex pattern {{ key }}
 */
export function extractPlaceholders(html: string): Placeholder[] {
  if (!html) return [];
  
  // Decode HTML entities first (e.g., &lt; becomes <, &amp; becomes &)
  // This ensures placeholders are recognized even if they're encoded
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  const decodedHtml = tempDiv.textContent || tempDiv.innerText || html;
  
  // Pattern to match {{ key }} placeholders
  // Supports Unicode letters (including German umlauts: ä, ö, ü, ß), numbers, spaces, and common special characters
  // Matches everything between {{ and }} except the braces themselves
  const pattern = /\{\{\s*([^{}]+?)\s*\}\}/g;
  const uniqueKeys = new Set<string>();
  const matches = decodedHtml.matchAll(pattern);
  
  for (const match of matches) {
    const key = match[1].trim();
    if (key && !uniqueKeys.has(key)) {
      uniqueKeys.add(key);
    }
  }
  
  // Convert to Placeholder objects with guessed types
  return Array.from(uniqueKeys).map(key => ({
    key,
    type: guessType(key),
    label: key,
  }));
}

/**
 * Merge placeholder values into HTML content.
 * Safely replaces {{ key }} with values, avoiding double replacements.
 */
export function mergeContent(html: string, values: FillValues): string {
  if (!html) return '';
  
  let result = html;
  
  // Sort placeholders by length (longest first) to avoid replacing parts of longer placeholders
  const sortedKeys = Object.keys(values).sort((a, b) => b.length - a.length);
  
  for (const key of sortedKeys) {
    const value = values[key];
    if (value !== null && value !== undefined) {
      // Escape HTML entities in the value
      const escapedValue = String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
      
      // Replace all occurrences of {{ key }} with the value
      const placeholderPattern = new RegExp(`\\{\\{\\s*${escapeRegExp(key)}\\s*\\}\\}`, 'g');
      result = result.replace(placeholderPattern, escapedValue);
    }
  }
  
  return result;
}

/**
 * Escape HTML attribute values
 */
function escapeHtmlAttr(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Merge placeholder values into HTML content with visual marking.
 * Replaces {{ key }} with marked spans that show the value but keep the placeholder styling.
 */
export function mergeContentWithMarking(html: string, values: FillValues): string {
  if (!html) return '';
  
  let result = html;
  
  // Sort placeholders by length (longest first) to avoid replacing parts of longer placeholders
  const sortedKeys = Object.keys(values).sort((a, b) => b.length - a.length);
  
  for (const key of sortedKeys) {
    const value = values[key];
    const filled = value !== null && value !== undefined && value !== '';
    
    // Escape HTML entities in the value
    const escapedValue = filled
      ? String(value)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;')
      : '';
    
    // Escape key for HTML attributes
    const escapedKey = escapeHtmlAttr(key);
    
    // Replace all occurrences of {{ key }} with marked span
    const placeholderPattern = new RegExp(`\\{\\{\\s*${escapeRegExp(key)}\\s*\\}\\}`, 'g');
    
    if (filled) {
      // Replace with marked span containing the value, but keep original placeholder in data attribute
      const originalPlaceholder = `{{${key}}}`;
      const escapedOriginal = escapeHtmlAttr(originalPlaceholder);
      result = result.replace(
        placeholderPattern,
        `<span class="ph ph--filled" data-placeholder-key="${escapedKey}" data-filled="true" data-placeholder-value="${escapedValue}" data-original-placeholder="${escapedOriginal}" style="cursor: pointer;" title="{{${escapedKey}}} → ${escapedValue}">${escapedValue}</span>`
      );
    } else {
      // Keep placeholder but mark it
      result = result.replace(
        placeholderPattern,
        `<span class="ph" data-placeholder-key="${escapedKey}" data-original-placeholder="{{${escapedKey}}}" style="cursor: pointer;" title="{{${escapedKey}}}">{{${key}}}</span>`
      );
    }
  }
  
  // Also mark any remaining placeholders that don't have values
  const remainingPattern = /\{\{\s*([^{}]+?)\s*\}\}/g;
  result = result.replace(remainingPattern, (match, key) => {
    const trimmedKey = key.trim();
    if (!sortedKeys.includes(trimmedKey)) {
      const escapedKeyAttr = escapeHtmlAttr(trimmedKey);
      return `<span class="ph" data-placeholder-key="${escapedKeyAttr}" style="cursor: pointer;" title="{{${escapedKeyAttr}}}">${match}</span>`;
    }
    return match;
  });
  
  return result;
}

/**
 * Guess placeholder type based on key name (heuristic).
 */
export function guessType(key: string): PlaceholderType {
  const lowerKey = key.toLowerCase();
  
  // Date fields
  if (lowerKey.includes('datum') || lowerKey.includes('date')) {
    return 'date';
  }
  
  // Text fields that should NOT be numbers (check these first)
  if (lowerKey.includes('anrede') || 
      lowerKey.includes('salutation') ||
      lowerKey.includes('titel') ||
      lowerKey.includes('name') ||
      lowerKey.includes('email') ||
      lowerKey.includes('strasse') ||
      lowerKey.includes('straße') ||
      lowerKey.includes('ort') ||
      lowerKey.includes('stadt') ||
      lowerKey.includes('rechtsform') ||
      lowerKey.includes('steuernummer') ||
      lowerKey.includes('steuerid') ||
      lowerKey.includes('umsatzsteuerid') ||
      lowerKey.includes('vatid')) {
    return 'text';
  }
  
  // Number fields (only specific numeric fields)
  if (lowerKey.includes('betrag') || 
      lowerKey.includes('summe') || 
      lowerKey.includes('preis') || 
      lowerKey.includes('kosten') ||
      lowerKey === 'plz' ||
      lowerKey === 'postleitzahl' ||
      (lowerKey.includes('hausnummer') && !lowerKey.includes('steuernummer')) ||
      (lowerKey.includes('nummer') && lowerKey.includes('haus'))) {
    return 'number';
  }
  
  // Multiline text fields
  if (lowerKey.includes('beschreibung') || 
      lowerKey.includes('text') || 
      lowerKey.includes('kommentar') || 
      lowerKey.includes('notiz') ||
      lowerKey.includes('bemerkung')) {
    return 'multiline';
  }
  
  // Dropdown/select fields
  if (lowerKey.includes('status') || 
      lowerKey.includes('typ') || 
      lowerKey.includes('art') || 
      lowerKey.includes('kategorie')) {
    return 'dropdown';
  }
  
  // Default to text
  return 'text';
}

/**
 * Escape special regex characters in a string.
 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Merge existing placeholders with newly extracted ones.
 * New keys are added, removed keys are marked (but kept in array).
 */
export function mergePlaceholders(
  existing: Placeholder[],
  extracted: Placeholder[]
): Placeholder[] {
  const existingMap = new Map<string, Placeholder>();
  existing.forEach(p => existingMap.set(p.key, p));
  
  const extractedKeys = new Set(extracted.map(p => p.key));
  const result: Placeholder[] = [];
  
  // Add all extracted placeholders
  extracted.forEach(extractedPlaceholder => {
    const existingPlaceholder = existingMap.get(extractedPlaceholder.key);
    if (existingPlaceholder) {
      // Keep existing configuration (type, mapping, etc.)
      result.push(existingPlaceholder);
    } else {
      // New placeholder
      result.push(extractedPlaceholder);
    }
  });
  
  // Keep removed placeholders but mark them (optional - you might want to remove them)
  existing.forEach(existingPlaceholder => {
    if (!extractedKeys.has(existingPlaceholder.key)) {
      // Placeholder was removed from content
      // You could add a flag like: { ...existingPlaceholder, removed: true }
      // For now, we'll keep them in the list
      result.push(existingPlaceholder);
    }
  });
  
  return result;
}

