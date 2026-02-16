/**
 * Split text into parts, marking matches for bold highlighting.
 * Returns array of {text, bold} segments.
 */
export interface HighlightPart {
  text: string;
  bold: boolean;
}

export function highlightMatch(text: string, query: string): HighlightPart[] {
  if (!query) return [{ text, bold: false }];

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const parts: HighlightPart[] = [];
  let lastIndex = 0;

  let idx = lowerText.indexOf(lowerQuery, lastIndex);
  while (idx !== -1) {
    if (idx > lastIndex) {
      parts.push({ text: text.slice(lastIndex, idx), bold: false });
    }
    parts.push({ text: text.slice(idx, idx + query.length), bold: true });
    lastIndex = idx + query.length;
    idx = lowerText.indexOf(lowerQuery, lastIndex);
  }

  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), bold: false });
  }

  return parts.length > 0 ? parts : [{ text, bold: false }];
}
