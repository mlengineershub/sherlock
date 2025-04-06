import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import InvestigationPage from './pages/InvestigationPage/InvestigationPage';
import RemediationPage from './pages/RemediationPage/RemediationPage';

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<InvestigationPage />} />
          <Route path="/investigation" element={<InvestigationPage />} />
          <Route path="/remediation" element={<RemediationPage />} />
          <Route path="/remediation/:investigationId" element={<RemediationPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;