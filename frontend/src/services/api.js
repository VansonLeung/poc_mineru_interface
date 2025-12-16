const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function parseFiles(files, options = {}) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  if (options.lang) formData.append('lang', options.lang);
  if (options.parseMethod) formData.append('parse_method', options.parseMethod);
  if (options.backend) formData.append('backend', options.backend);
  if (typeof options.startPage === 'number') formData.append('start_page', String(options.startPage));
  if (typeof options.endPage === 'number') formData.append('end_page', String(options.endPage));
  if (typeof options.formulaEnable === 'boolean') formData.append('formula_enable', String(options.formulaEnable));
  if (typeof options.tableEnable === 'boolean') formData.append('table_enable', String(options.tableEnable));

  const response = await fetch(`${API_BASE_URL}/api/v1/parse`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Upload failed');
  }

  return response.json();
}
