import React from 'react';
import UploadForm from '../components/UploadForm.jsx';

export default function IndexPage() {
  return (
    <main className="page">
      <header className="page__header">
        <div>
          <h1>Octopus Document Parser</h1>
          <p>Upload PDFs, images, or DOCX and receive Markdown/JSON outputs synchronously.</p>
        </div>
      </header>
      <section className="page__body">
        <UploadForm />
      </section>
      <footer className="page__footer">© 2025 Octopus InfoTech Limited</footer>
    </main>
  );
}
