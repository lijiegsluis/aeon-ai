import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import SelectTool from './SelectTool.tsx';

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <SelectTool />
    </StrictMode>,
);
