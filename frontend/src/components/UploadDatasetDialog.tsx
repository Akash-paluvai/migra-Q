import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, FileText, Upload, X } from 'lucide-react';
import { uploadDataset } from '../api/datasets';
import { DatasetDetail } from '../types/dataset';
import { LoadingState } from './LoadingState';

interface UploadDatasetDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (dataset: DatasetDetail) => void;
}

export const UploadDatasetDialog: React.FC<UploadDatasetDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [displayName, setDisplayName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setError(null);
      if (!displayName) {
        setDisplayName(selected.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV, Parquet, or ZIP file to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadDataset(file, displayName, description);
      setUploading(false);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      setUploading(false);
      const msg = err.response?.data?.detail || err.message || 'Failed to upload dataset.';
      setError(msg);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="icon-box">
              <Upload size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>Upload New Dataset</h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>Supports .csv, .parquet, or .zip containing data files</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-icon-only">
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="modal-body">
          {error && (
            <div style={{ padding: '16px', borderRadius: '8px', backgroundColor: 'var(--status-fail-bg)', border: '1px solid var(--status-fail-border)', display: 'flex', gap: '8px', alignItems: 'flex-start', color: 'var(--status-fail-text)', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
              <AlertTriangle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {/* File Select */}
          <div className="form-group">
            <label className="form-label">Dataset File (.csv, .parquet, .zip)</label>
            <div className="file-drop-area">
              <input
                type="file"
                accept=".csv,.parquet,.zip"
                onChange={handleFileSelect}
                className="file-drop-input"
              />
              <FileText size={32} style={{ color: 'var(--text-muted)', margin: '0 auto 8px auto', display: 'block' }} />
              {file ? (
                <div style={{ color: 'var(--accent-primary)', fontWeight: 500, fontSize: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  <CheckCircle size={16} />
                  <span>{file.name}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                    ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Click to upload</span> or drag and drop
                  <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>Maximum file size: 50MB</p>
                </div>
              )}
            </div>
          </div>

          {/* Display Name */}
          <div className="form-group">
            <label className="form-label">Display Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Q3 Customer Transactions"
              className="form-input"
            />
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label">Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Optional summary of dataset contents..."
              className="form-input"
              style={{ resize: 'vertical' }}
            />
          </div>

          {/* Actions */}
          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="btn-primary"
              style={{ opacity: (uploading || !file) ? 0.5 : 1, cursor: (uploading || !file) ? 'not-allowed' : 'pointer' }}
            >
              {uploading ? (
                <span>Uploading...</span>
              ) : (
                <>
                  <Upload size={16} />
                  <span>Upload & Register</span>
                </>
              )}
            </button>
          </div>
        </form>

        {uploading && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-tertiary)' }}>
            <LoadingState message="Inspecting schemas and computing dataset hash..." />
          </div>
        )}
      </div>
    </div>
  );
};
