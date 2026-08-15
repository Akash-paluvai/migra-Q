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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Upload New Dataset</h2>
              <p className="text-xs text-slate-400">Supports .csv, .parquet, or .zip containing data files</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-3 text-red-400 text-xs font-mono">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* File Select */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
              Dataset File (.csv, .parquet, .zip)
            </label>
            <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-950/40 relative">
              <input
                type="file"
                accept=".csv,.parquet,.zip"
                onChange={handleFileSelect}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <FileText className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              {file ? (
                <div className="text-emerald-400 font-medium text-sm flex items-center justify-center space-x-2">
                  <CheckCircle className="w-4 h-4" />
                  <span>{file.name}</span>
                  <span className="text-slate-500 text-xs font-mono">
                    ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
              ) : (
                <div className="text-slate-400 text-xs">
                  <span className="font-semibold text-slate-200">Click to upload</span> or drag and drop
                  <p className="text-slate-500 mt-1">Maximum file size: 50MB</p>
                </div>
              )}
            </div>
          </div>

          {/* Display Name */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1">
              Display Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Q3 Customer Transactions"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-1">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Optional summary of dataset contents..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Actions */}
          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center space-x-2 shadow-lg shadow-emerald-950/50"
            >
              {uploading ? (
                <span>Uploading...</span>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Register</span>
                </>
              )}
            </button>
          </div>
        </form>

        {uploading && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/80">
            <LoadingState message="Inspecting schemas and computing dataset hash..." />
          </div>
        )}
      </div>
    </div>
  );
};
