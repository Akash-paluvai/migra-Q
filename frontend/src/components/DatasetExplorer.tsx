import React, { useEffect, useState } from 'react';
import { Database, FileSpreadsheet, Hash, Layers, Table, X } from 'lucide-react';
import { getDataset, getDatasetPreview } from '../api/datasets';
import { DatasetDetail, DatasetPreviewResponse } from '../types/dataset';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';

interface DatasetExplorerProps {
  datasetId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectDataset?: (datasetId: string) => void;
}

export const DatasetExplorer: React.FC<DatasetExplorerProps> = ({
  datasetId,
  isOpen,
  onClose,
  onSelectDataset,
}) => {
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !datasetId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    getDataset(datasetId)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          const defaultTable = data.table_summaries[0]?.table_name || '';
          setSelectedTable(defaultTable);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load dataset details');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [datasetId, isOpen]);

  useEffect(() => {
    if (!isOpen || !datasetId || !selectedTable) return;

    let isMounted = true;
    setPreviewLoading(true);

    getDatasetPreview(datasetId, selectedTable, 100)
      .then((data) => {
        if (isMounted) {
          setPreview(data);
          setPreviewLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setPreviewLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [datasetId, selectedTable, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/75 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-4xl bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 sticky top-0 z-10 backdrop-blur">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                {detail?.display_name || datasetId}
                {detail?.is_builtin && (
                  <span className="px-2 py-0.5 text-xs font-mono font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    BUILT-IN
                  </span>
                )}
                {detail?.is_upload && (
                  <span className="px-2 py-0.5 text-xs font-mono font-medium rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    UPLOADED
                  </span>
                )}
              </h2>
              <p className="text-sm text-slate-400 mt-0.5">{detail?.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {onSelectDataset && (
              <button
                onClick={() => {
                  onSelectDataset(datasetId);
                  onClose();
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-emerald-950/50"
              >
                Use This Dataset
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="flex-1 p-8">
            <LoadingState message="Loading dataset metadata and schema..." />
          </div>
        ) : error ? (
          <div className="flex-1 p-8">
            <ErrorState title="Error Loading Dataset" message={error} />
          </div>
        ) : detail ? (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Quick Stats Bar */}
            <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/50 border border-slate-800/80">
              <div>
                <span className="text-xs font-medium text-slate-400 block flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5" /> Total Rows
                </span>
                <span className="text-lg font-bold text-slate-100 font-mono mt-1 block">
                  {detail.row_count_total.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-xs font-medium text-slate-400 block flex items-center gap-1">
                  <Table className="w-3.5 h-3.5" /> Tables
                </span>
                <span className="text-lg font-bold text-slate-100 font-mono mt-1 block">
                  {detail.table_count}
                </span>
              </div>
              <div>
                <span className="text-xs font-medium text-slate-400 block flex items-center gap-1">
                  <Hash className="w-3.5 h-3.5" /> Content Hash
                </span>
                <span className="text-sm font-mono text-emerald-400 mt-1 block truncate">
                  {detail.dataset_hash}
                </span>
              </div>
              <div>
                <span className="text-xs font-medium text-slate-400 block flex items-center gap-1">
                  <FileSpreadsheet className="w-3.5 h-3.5" /> Profile
                </span>
                <span className="text-sm font-mono text-slate-300 mt-1 block uppercase">
                  {detail.profile}
                </span>
              </div>
            </div>

            {/* Table Selector Tabs */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Dataset Tables
              </label>
              <div className="flex flex-wrap gap-2">
                {detail.table_summaries.map((t) => {
                  const active = t.table_name === selectedTable;
                  return (
                    <button
                      key={t.table_name}
                      onClick={() => setSelectedTable(t.table_name)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 border ${
                        active
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-sm'
                          : 'bg-slate-950/40 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-800/50'
                      }`}
                    >
                      <Table className="w-4 h-4" />
                      <span>{t.table_name}</span>
                      <span className="px-2 py-0.5 text-xs font-mono rounded bg-slate-900 text-slate-400 border border-slate-800">
                        {t.row_count.toLocaleString()} rows
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Table Schema Specification */}
            {selectedTable && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    Schema Specification: <span className="text-emerald-400 font-mono lowercase">{selectedTable}</span>
                  </h3>
                </div>
                <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/40">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-4 font-semibold">#</th>
                        <th className="py-2.5 px-4 font-semibold">Column Name</th>
                        <th className="py-2.5 px-4 font-semibold">Data Type</th>
                        <th className="py-2.5 px-4 font-semibold">Nullable</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {detail.table_summaries
                        .find((t) => t.table_name === selectedTable)
                        ?.columns.map((col) => (
                          <tr key={col.name} className="hover:bg-slate-800/30 transition-colors">
                            <td className="py-2 px-4 text-slate-500">{col.ordinal_position}</td>
                            <td className="py-2 px-4 font-medium text-slate-200 flex items-center gap-2">
                              {col.name}
                              {col.primary_key && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                  PK
                                </span>
                              )}
                            </td>
                            <td className="py-2 px-4 text-emerald-400 font-semibold">{col.data_type}</td>
                            <td className="py-2 px-4 text-slate-400">{col.nullable ? 'YES' : 'NO'}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Live Sample Row Preview */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  Sample Rows Preview (Max 100)
                </h3>
                {preview && (
                  <span className="text-xs font-mono text-slate-400">
                    Showing {preview.returned_rows} of {preview.total_rows.toLocaleString()} rows
                  </span>
                )}
              </div>

              {previewLoading ? (
                <div className="py-8">
                  <LoadingState message="Fetching live sample rows..." />
                </div>
              ) : preview && preview.rows.length > 0 ? (
                <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 max-h-72 overflow-y-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 sticky top-0 z-10 backdrop-blur">
                      <tr>
                        {preview.columns.map((col) => (
                          <th key={col.name} className="py-2.5 px-4 font-semibold whitespace-nowrap">
                            {col.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40 text-slate-300">
                      {preview.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-800/20 transition-colors">
                          {preview.columns.map((col) => {
                            const val = row[col.name];
                            return (
                              <td key={col.name} className="py-2 px-4 whitespace-nowrap text-slate-300">
                                {val === null ? (
                                  <span className="text-slate-500 italic">null</span>
                                ) : typeof val === 'object' ? (
                                  JSON.stringify(val)
                                ) : (
                                  String(val)
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-950/30 text-center text-sm text-slate-400">
                  No sample rows available for this table.
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
