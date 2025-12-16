import React, { useCallback, useMemo, useRef, useState } from 'react';
import { marked } from 'marked';
import { parseFiles } from '../services/api.js';

export default function UploadForm() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [backend, setBackend] = useState('pipeline');
  const [serverUrl, setServerUrl] = useState('');
  const [parseMethod, setParseMethod] = useState('auto');
  const [activeTabs, setActiveTabs] = useState({});
  const inputRef = useRef(null);

  const handleFiles = useCallback((fileList) => {
    const fileArray = Array.from(fileList || []);
    setSelectedFiles(fileArray);
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      event.stopPropagation();
      handleFiles(event.dataTransfer.files);
    },
    [handleFiles],
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  const onSelectClick = () => {
    inputRef.current?.click();
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFiles.length) return;
    setIsUploading(true);
    setError(null);
    setResults([]);
    try {
      const response = await parseFiles(selectedFiles, {
        parseMethod,
        backend,
        serverUrl: backend === 'vlm-http-client' ? serverUrl : undefined,
      });
      setResults(response.outputs || []);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const downloads = useMemo(() => {
    return results.map((result) => {
      const markdownUrl = result.markdown
        ? URL.createObjectURL(new Blob([result.markdown], { type: 'text/markdown' }))
        : null;
      const jsonPayload = result.content_list_json || result.middle_json || {};
      const jsonUrl = URL.createObjectURL(new Blob([JSON.stringify(jsonPayload, null, 2)], { type: 'application/json' }));
      return { filename: result.filename, markdownUrl, jsonUrl };
    });
  }, [results]);

  const renderTabContent = (result, tab) => {
    const markdown = result.markdown || '';
    const jsonPayload = result.content_list_json || result.middle_json || result.model_output_json || {};

    if (tab === 'render') {
      const html = marked.parse(markdown || '');
      return <div className="preview" dangerouslySetInnerHTML={{ __html: html }} />;
    }
    if (tab === 'markdown') {
      return <pre className="preview preview--text">{markdown || 'No markdown available.'}</pre>;
    }
    return <pre className="preview preview--json">{JSON.stringify(jsonPayload, null, 2)}</pre>;
  };

  return (
    <div className="workspace">
      <form className="sidebar" onSubmit={onSubmit}>
        <div
          className="dropzone"
          data-testid="upload-dropzone"
          onDrop={onDrop}
          onDragOver={onDragOver}
          onClick={onSelectClick}
          role="button"
          tabIndex={0}
        >
          <p className="dropzone__title">Drag & drop files here, or click to browse</p>
          <p className="dropzone__hint">PDF, images, DOC/DOCX up to 50MB, up to 5 files.</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.jp2,.webp,.gif,.bmp,.doc,.docx"
            multiple
            className="hidden-input"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        <div className="field">
          <label htmlFor="backend">Backend</label>
          <select
            id="backend"
            value={backend}
            onChange={(e) => {
              setBackend(e.target.value);
              if (e.target.value !== 'vlm-http-client') {
                setServerUrl('');
              }
            }}
          >
            <option value="pipeline">pipeline</option>
            <option value="vlm-transformers">vlm-transformers</option>
            <option value="vlm-mlx-engine">vlm-mlx-engine</option>
            <option value="vlm-vllm-engine">vlm-vllm-engine</option>
            <option value="vlm-lmdeploy-engine">vlm-lmdeploy-engine</option>
            <option value="vlm-http-client">vlm-http-client</option>
          </select>
        </div>

        {backend === 'vlm-http-client' && (
          <div className="field">
            <label htmlFor="server_url">Server URL</label>
            <input
              id="server_url"
              type="url"
              placeholder="http://127.0.0.1:1234/v1"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
            />
          </div>
        )}

        <div className="field">
          <label htmlFor="parse_method">Parse Method</label>
          <select id="parse_method" value={parseMethod} onChange={(e) => setParseMethod(e.target.value)}>
            <option value="auto">auto</option>
            <option value="txt">txt</option>
            <option value="ocr">ocr</option>
          </select>
        </div>

        {selectedFiles.length > 0 && (
          <ul className="file-list">
            {selectedFiles.map((file) => (
              <li key={file.name}>{file.name}</li>
            ))}
          </ul>
        )}

        <div className="actions">
          <button type="submit" className="btn" disabled={isUploading || !selectedFiles.length}>
            {isUploading ? 'Uploading…' : 'Upload and Parse'}
          </button>
        </div>

        {isUploading && selectedFiles.length > 0 && (
          <div className="status">
            {selectedFiles.map((file) => (
              <p key={file.name}>Uploading {file.name}…</p>
            ))}
          </div>
        )}

        {error && <p className="error">{error}</p>}
      </form>

      <section className="panel">
        <div className="panel__body">
          {results.length === 0 && <p className="muted">No results yet. Upload files to see outputs.</p>}
          {results.map((result, index) => {
            const tab = activeTabs[result.filename] || 'render';
            return (
              <div key={result.filename} className="result-card">
                <div className="result-card__header">
                  <div>
                    <strong>{result.filename}</strong>
                    <span className="muted">Expires: {result.storage_expiry}</span>
                  </div>
                  <div className="result-card__actions">
                    {downloads[index]?.markdownUrl && (
                      <a className="btn secondary" href={downloads[index].markdownUrl} download={`${result.filename}.md`}>
                        Download Markdown
                      </a>
                    )}
                    {downloads[index]?.jsonUrl && (
                      <a className="btn secondary" href={downloads[index].jsonUrl} download={`${result.filename}.json`}>
                        Download JSON
                      </a>
                    )}
                  </div>
                </div>
                <div className="tabs">
                  {['render', 'markdown', 'json'].map((key) => (
                    <button
                      type="button"
                      key={key}
                      className={`tab ${tab === key ? 'tab--active' : ''}`}
                      onClick={() => setActiveTabs((prev) => ({ ...prev, [result.filename]: key }))}
                    >
                      {key === 'render' ? 'Markdown (rendered)' : key === 'markdown' ? 'Markdown (text)' : 'JSON'}
                    </button>
                  ))}
                </div>
                {renderTabContent(result, tab)}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
