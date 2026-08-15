import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { EnterpriseShell } from './components/EnterpriseShell';
import { LandingPage } from './pages/LandingPage';
import { MigrationsPage } from './pages/MigrationsPage';
import { NewMigrationPage } from './pages/NewMigrationPage';
import { MigrationWorkspace } from './pages/MigrationWorkspace';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <EnterpriseShell>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/migrations" element={<MigrationsPage />} />
          <Route path="/migrations/new" element={<NewMigrationPage />} />
          <Route path="/migrations/:migrationId/*" element={<MigrationWorkspace />} />
        </Routes>
      </EnterpriseShell>
    </BrowserRouter>
  );
};

export default App;
