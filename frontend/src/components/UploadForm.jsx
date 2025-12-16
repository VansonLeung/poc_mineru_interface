import React, { useCallback, useMemo, useRef, useState } from 'react';
import { parseFiles } from '../services/api.js';

export default function UploadForm() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
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
      const response = await parseFiles(selectedFiles, { parseMethod: 'auto', backend: 'pipeline' });
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

  return (
    <form className="card" onSubmit={onSubmit}>
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
        <p className="dropzone__hint">PDF and image files up to 50MB, up to 5 files.</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.jp2,.webp,.gif,.bmp"
          multiple
          className="hidden-input"
          onChange={(e) => handleFiles(e.target.files)}
        />
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

      {results.length > 0 && (
        <div className="results">
          {results.map((result, index) => (
            <div key={result.filename} className="result-card">
              <div className="result-card__header">
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
              {result.markdown && <pre className="preview">{result.markdown}</pre>}
            </div>
          ))}
        </div>
      )}
    </form>
  );
}
