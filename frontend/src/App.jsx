import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ValidationPage from './pages/ValidationPage';
import BenchmarkPage from './pages/BenchmarkPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentMigrationId, setCurrentMigrationId] = useState('');

  const handleRunValidation = (id) => {
    setCurrentMigrationId(id);
    setActiveTab('validation');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f19' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main>
        {activeTab === 'dashboard' && <Dashboard onRunValidation={handleRunValidation} />}
        {activeTab === 'validation' && <ValidationPage migrationId={currentMigrationId} />}
        {activeTab === 'benchmark' && <BenchmarkPage />}
      </main>
    </div>
  );
}
