import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";

export class IntelligentSearchService {
  /**
   * Analiza un issue y encuentra archivos relevantes en el proyecto
   * @param issue GitHub issue object
   * @returns Promise<string[]> Array of file paths
   */
  public async findRelevantFiles(issue: any): Promise<string[]> {
    try {
      // Obtener carpeta de trabajo
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        throw new Error("No hay carpeta de trabajo abierta");
      }
      const rootPath = workspaceFolders[0].uri.fsPath;

      // Preparar el texto del issue para análisis
      const issueText = `${issue.title} ${issue.body || ""}`;

      // Extraer palabras clave del issue
      const keywords = this.extractKeywords(issueText);

      // Buscar archivos relevantes basados en las palabras clave
      const relevantFiles = await this.searchFilesWithKeywords(
        rootPath,
        keywords
      );

      return relevantFiles;
    } catch (error) {
      vscode.window.showErrorMessage(
        `Error buscando archivos relevantes: ${(error as Error).message}`
      );
      return [];
    }
  }

  /**
   * Extrae palabras clave relevantes del texto del issue
   * @param issueText Texto completo del issue
   * @returns string[] Array de palabras clave
   */
  private extractKeywords(issueText: string): string[] {
    // Eliminar signos de puntuación y convertir a minúsculas
    const cleanText = issueText.toLowerCase().replace(/[^\w\s]/g, " ");

    // Dividir en palabras
    const words = cleanText.split(/\s+/).filter((word) => word.length > 2);

    // Eliminar palabras comunes (stopwords)
    const stopwords = [
      "the",
      "and",
      "or",
      "in",
      "on",
      "at",
      "to",
      "a",
      "an",
      "for",
      "with",
      "by",
      "about",
      "like",
      "through",
      "over",
      "before",
      "between",
      "after",
      "since",
      "without",
      "under",
      "within",
      "along",
      "following",
      "across",
      "behind",
      "beyond",
      "plus",
      "except",
      "but",
      "up",
      "out",
      "around",
      "down",
      "off",
      "above",
      "near",
    ];
    const filteredWords = words.filter((word) => !stopwords.includes(word));

    // Contar frecuencia de palabras y obtener las más relevantes
    const wordCount: Record<string, number> = {};
    filteredWords.forEach((word) => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });

    // Ordenar por frecuencia y obtener las 10 más comunes
    const sortedWords = Object.entries(wordCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map((entry) => entry[0]);

    return sortedWords;
  }

  /**
   * Busca archivos que contengan las palabras clave
   * @param rootPath Ruta base del proyecto
   * @param keywords Array de palabras clave
   * @returns Promise<string[]> Rutas de archivos relevantes
   */
  private async searchFilesWithKeywords(
    rootPath: string,
    keywords: string[]
  ): Promise<string[]> {
    // Usar VS Code search API para encontrar archivos con las palabras clave
    const results: Set<string> = new Set();

    for (const keyword of keywords) {
      // Omitir palabras clave muy cortas
      if (keyword.length < 3) continue;

      const searchResults = await vscode.workspace.findFiles(
        "**/*.{js,ts,jsx,tsx,java,py,c,cpp,h,hpp,cs,go,rb,php,html,css,scss,md,json}",
        "**/node_modules/**"
      );

      for (const file of searchResults) {
        const relativePath = vscode.workspace.asRelativePath(file);

        // Comprobar si el nombre del archivo contiene la palabra clave
        if (path.basename(relativePath).toLowerCase().includes(keyword)) {
          results.add(relativePath);
          continue;
        }

        // Leer contenido del archivo para buscar
        try {
          const content = fs.readFileSync(file.fsPath, "utf8");
          if (content.toLowerCase().includes(keyword)) {
            results.add(relativePath);
          }
        } catch (error) {
          // Ignorar errores de lectura
        }
      }
    }

    // Convertir Set a Array
    return Array.from(results).slice(0, 15); // Limitar a 15 archivos más relevantes
  }
}
