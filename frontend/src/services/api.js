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

/**
 * Submit files for async processing
 * @param {File[]} files - Files to parse
 * @param {Object} options - Parse options
 * @returns {Promise<{job_id: string, status: string, status_url: string, created_at: string}>}
 */
export async function submitAsyncJob(files, options = {}) {
  const {
    lang,
    parseMethod,
    backend,
    serverUrl,
    startPage,
    endPage,
    formulaEnable,
    tableEnable,
    callbackUrl,
  } = options;

  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  formData.append('async_mode', 'true');

  if (lang) formData.append('lang', lang);
  if (parseMethod) formData.append('parse_method', parseMethod);
  if (backend) formData.append('backend', backend);
  if (serverUrl) formData.append('server_url', serverUrl);
  if (typeof startPage === 'number') formData.append('start_page', String(startPage));
  if (typeof endPage === 'number') formData.append('end_page', String(endPage));
  if (typeof formulaEnable === 'boolean') formData.append('formula_enable', String(formulaEnable));
  if (typeof tableEnable === 'boolean') formData.append('table_enable', String(tableEnable));
  if (callbackUrl) formData.append('callback_url', callbackUrl);

  const response = await fetch(`${API_BASE_URL}/api/v1/parse`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Job submission failed');
  }

  return await response.json();
}

/**
 * Get job status
 * @param {string} jobId - Job ID to query
 * @returns {Promise<{job_id: string, status: string, created_at: string, completed_at?: string, error?: string, outputs?: Array}>}
 */
export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to get job status');
  }

  return await response.json();
}

/**
 * Poll job status until completion
 * @param {string} jobId - Job ID to poll
 * @param {Object} options - Polling options
 * @param {number} options.intervalMs - Polling interval in milliseconds (default: 5000)
 * @param {number} options.maxAttempts - Maximum polling attempts (default: 120, = 10 minutes with 5s interval)
 * @param {Function} options.onStatusChange - Callback for status updates
 * @returns {Promise<Object>} Final job result
 */
export async function pollJobStatus(jobId, options = {}) {
  const {
    intervalMs = 5000,
    maxAttempts = 120,
    onStatusChange = () => {},
  } = options;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const job = await getJobStatus(jobId);
    onStatusChange(job);

    if (job.status === 'SUCCESS') {
      return job;
    }

    if (job.status === 'FAILED') {
      throw new Error(job.error || 'Job failed');
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error(`Job polling timed out after ${maxAttempts} attempts`);
}
