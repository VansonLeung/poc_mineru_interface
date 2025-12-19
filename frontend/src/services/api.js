const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:19833';

export async function parseFiles(files, options = {}) {
  const {
    lang,
    parseMethod,
    backend,
    serverUrl,
    startPage,
    endPage,
    formulaEnable,
    tableEnable,
    timeoutMs = 180_000, // allow up to 180s for multi-file parses
  } = options;

  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  if (lang) formData.append('lang', lang);
  if (parseMethod) formData.append('parse_method', parseMethod);
  if (backend) formData.append('backend', backend);
  if (serverUrl) formData.append('server_url', serverUrl);
  if (typeof startPage === 'number') formData.append('start_page', String(startPage));
  if (typeof endPage === 'number') formData.append('end_page', String(endPage));
  if (typeof formulaEnable === 'boolean') formData.append('formula_enable', String(formulaEnable));
  if (typeof tableEnable === 'boolean') formData.append('table_enable', String(tableEnable));

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/parse`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Upload failed');
    }

    return await response.json();
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}
