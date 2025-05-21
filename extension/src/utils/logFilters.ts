// Función: analizar todos los bloques de AIMessage y mostrar el más largo
export function extractLargestAIMessageContent(log: string): string {
  if (!log) return '';
  const lines = log.split('\n');
  const indices: number[] = [];
  for (let i = 0; i < lines.length; i++) {
    if (/AIMessage/i.test(lines[i])) {
      indices.push(i);
    }
  }
  const blocks: {text: string, size: number}[] = [];
  for (const idx of indices) {
    let blockLines = [lines[idx]];
    let j = idx + 1;
    while (j < lines.length && lines[j].trim() !== '') {
      blockLines.push(lines[j]);
      j++;
    }
    // Unir el bloque y extraer todos los content='...' o content="..."
    const blockText = blockLines.join(' ');
    const contentRegex = /content=(?:'([^']*)'|"([^"]*)")/g;
    let contentMatch;
    let contents: string[] = [];
    while ((contentMatch = contentRegex.exec(blockText)) !== null) {
      contents.push(contentMatch[1] || contentMatch[2]);
    }
    if (contents.length > 0) {
      const joined = contents.join('<br>');
      blocks.push({text: joined, size: joined.length});
    }
  }
  // Ordenar por tamaño descendente y tomar el más grande
  if (blocks.length === 0) return '';
  const sorted = blocks.sort((a, b) => b.size - a.size);
  return sorted[0].text;
}

// Función: extraer bloques de código Python delimitados por triple backtick (más flexible)
export function extractPythonCodeBlocks(log: string): string[] {
  if (!log) return [];
  // Busca cualquier bloque entre ``` y ``` (soporta en una sola línea o multilínea)
  const regex = /```[ \t]*[a-zA-Z0-9]*[ \t]*\n?([\s\S]*?)```/g;
  const results: string[] = [];
  let match;
  while ((match = regex.exec(log)) !== null) {
    results.push(match[1].trim());
  }
  return results;
} 