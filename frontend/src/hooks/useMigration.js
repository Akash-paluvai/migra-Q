import { useState } from 'react';
import { submitMigration, runValidation, triggerRepair, getScorecard } from '../api/client';

export function useMigration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [migration, setMigration] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [scorecard, setScorecard] = useState(null);

  const startMigration = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await submitMigration(payload);
      setMigration(data);
      return data;
    } catch (err) {
      setError(err.message || 'Migration submission failed');
    } finally {
      setLoading(false);
    }
  };

  const executeValidation = async (migrationId) => {
    setLoading(true);
    try {
      const res = await runValidation(migrationId);
      setValidationResult(res);
      const sc = await getScorecard(migrationId);
      setScorecard(sc);
    } catch (err) {
      setError(err.message || 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    migration,
    validationResult,
    scorecard,
    startMigration,
    executeValidation
  };
}
