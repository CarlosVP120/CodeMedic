// Función: extraer el contenido más largo entre comillas simples de AIMessage(content='...') solo dentro de agent: {'messages': [...]} y omitir ToolMessage
export function extractLargestAIMessageContent(log: string): string {
  if (!log) return '';
  // Buscar la sección 'agent' y luego 'messages'
  const agentMatch = log.match(/agent\s*:\s*\{[\s\S]*?messages\s*:\s*\[([\s\S]*?)\][\s\S]*?\}/);
  if (!agentMatch) return '';
  const messagesBlock = agentMatch[1];
  // Iterar sobre cada aparición de AIMessage(content='...')
  const aiMessageRegex = /AIMessage\(content='([^']*)'/g;
  let match;
  let maxContent = '';
  while ((match = aiMessageRegex.exec(messagesBlock)) !== null) {
    const content = match[1] || '';
    if (content.length > maxContent.length) {
      maxContent = content;
    }
  }
  return maxContent;
} 