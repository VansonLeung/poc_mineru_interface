import React from 'react';
import { createRoot } from 'react-dom/client';
import IndexPage from './pages/index.jsx';
import './styles.css';

const root = document.getElementById('root');

createRoot(root).render(<IndexPage />);
