import React, { useState } from 'react';
import UploadForm from '../components/UploadForm.jsx';

export default function IndexPage() {
  const [showGuide, setShowGuide] = useState(false);

  return (
    <main className="page">
      <header className="page__header">
        <div className="page__header-title">
          <h1>Octopus Document Parser</h1>
          <p>Upload PDFs, images, or DOCX and receive Markdown/JSON outputs synchronously.</p>
        </div>
        <div className="page__header-actions">
          <button type="button" className="btn secondary" onClick={() => setShowGuide(true)}>
            API Guide
          </button>
        </div>
      </header>
      <section className="page__body">
        <UploadForm />
      </section>
      {showGuide && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal__header">
              <h2>API usage for tools (e.g. Dify)</h2>
              <button type="button" className="btn secondary" onClick={() => setShowGuide(false)}>
                Close
              </button>
            </div>
            <div className="modal__body">
              <div className="guide-grid">
                <div>
                  <h3>Endpoint</h3>
                  <p>
                    <code>POST /api/v1/parse</code> (multipart/form-data)
                  </p>
                </div>
                <div>
                  <h3>Endpoint</h3>
                  <p>
                    <code>POST /api/v1/parse</code> (multipart/form-data)
                  </p>
                </div>
                <div>
                  <h3>Required</h3>
                  <p>
                    <code>files[]</code> (pdf/image/doc/docx)
                  </p>
                </div>
                <div>
                  <h3>Optional fields</h3>
                  <p>
                    <code>backend</code> (pipeline or vlm-*), <code>parse_method</code> (auto|txt|ocr), <code>lang</code>,
                    <code>server_url</code> (vlm-http-client), <code>start_page</code>, <code>end_page</code>,
                    <code>formula_enable</code>, <code>table_enable</code>
                  </p>
                </div>
              </div>
              <h3>cURL example</h3>
              <pre className="guide-card__code">curl -X POST http://localhost:19833/api/v1/parse \
  -H "X-API-Key: &lt;optional&gt;" \
  -F "files=@/path/to/doc.pdf" \
  -F "backend=pipeline" \
  -F "parse_method=auto"</pre>
              <h3>Response</h3>
              <p>
                <code>outputs[]</code> with <code>filename</code>, <code>markdown</code> (or <code>markdown_url</code>),
                <code>content_list_json</code>, <code>middle_json</code>, <code>model_output_json</code>, <code>storage_expiry</code>.
                Errors include <code>detail</code> and <code>request_id</code>.
              </p>
              <div className="guide-tip">
                <strong>Dify tip:</strong> method POST, body multipart/form-data, field name <code>files</code>; add optional fields as needed.
              </div>
            </div>
          </div>
        </div>
      )}
      <footer className="page__footer">© 2025 Octopus InfoTech Limited</footer>
    </main>
  );
}
