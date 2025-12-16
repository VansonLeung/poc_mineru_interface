import React from 'react';
import UploadForm from '../components/UploadForm.jsx';

export default function IndexPage() {
  return (
    <main className="page">
      <header className="page__header">
        <h1>Miner-U Web Interface</h1>
        <p>Upload PDFs or images and receive Markdown/JSON outputs synchronously.</p>
      </header>
      <section className="page__content">
        <UploadForm />
      </section>
    </main>
  );
}
