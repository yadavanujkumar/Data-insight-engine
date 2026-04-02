'use client';
import { useEffect, useState } from 'react';
import Navbar from './Navbar';
import DataQualityCard from './DataQualityCard';
import ForecastChart from './ForecastChart';
import RecommendationsPanel from './RecommendationsPanel';
import AlertsPanel from './AlertsPanel';
import NLQInterface from './NLQInterface';
import MetricsPanel from './MetricsPanel';
import { datasetsApi, cleaningApi, type Dataset } from '@/lib/api';
import {
  CloudArrowUpIcon,
  CircleStackIcon,
  SparklesIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

export default function Dashboard() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<Dataset | null>(null);
  const [uploading, setUploading] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [tab, setTab] = useState<'overview' | 'forecast' | 'nlq'>('overview');
  const [uploadError, setUploadError] = useState<string | null>(null);

  const loadDatasets = () => {
    datasetsApi.list().then((r) => {
      setDatasets(r.data);
      if (r.data.length > 0 && !selected) setSelected(r.data[0]);
    });
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const res = await datasetsApi.upload(file);
      setDatasets((prev) => [res.data, ...prev]);
      setSelected(res.data);
    } catch {
      setUploadError('Upload failed. Ensure the file is a valid CSV or Excel file.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleClean = async () => {
    if (!selected) return;
    setCleaning(true);
    try {
      await cleaningApi.run({
        dataset_id: selected.id,
        operations: ['missing_values', 'duplicates', 'outliers'],
      });
      loadDatasets();
    } finally {
      setCleaning(false);
    }
  };

  const handleDelete = async (id: number) => {
    await datasetsApi.delete(id);
    setDatasets((prev) => prev.filter((d) => d.id !== id));
    if (selected?.id === id) setSelected(datasets.find((d) => d.id !== id) || null);
  };

  const columns = selected?.column_info ? Object.keys(selected.column_info) : [];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 flex flex-col p-4 gap-4 overflow-y-auto">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Datasets
            </label>
            <label className={clsx('btn-primary w-full text-center cursor-pointer block text-sm', uploading && 'opacity-50 pointer-events-none')}>
              {uploading ? 'Uploading...' : (
                <span className="flex items-center justify-center gap-1">
                  <CloudArrowUpIcon className="h-4 w-4" /> Upload
                </span>
              )}
              <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleUpload} />
            </label>
            {uploadError && <p className="text-red-500 text-xs mt-1">{uploadError}</p>}
          </div>

          <div className="flex-1 space-y-1">
            {datasets.length === 0 && (
              <p className="text-slate-400 text-xs text-center py-4">No datasets yet. Upload a file.</p>
            )}
            {datasets.map((ds) => (
              <div
                key={ds.id}
                onClick={() => setSelected(ds)}
                className={clsx(
                  'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors',
                  selected?.id === ds.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-700'
                )}
              >
                <CircleStackIcon className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{ds.name}</p>
                  <p className="text-xs text-slate-400">{ds.row_count?.toLocaleString() ?? '?'} rows</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(ds.id); }}
                  className="hidden group-hover:block text-slate-400 hover:text-red-500"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <CircleStackIcon className="h-16 w-16 mb-4 opacity-30" />
              <h2 className="text-lg font-medium">No dataset selected</h2>
              <p className="text-sm">Upload a CSV or Excel file to get started</p>
            </div>
          ) : (
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">{selected.name}</h2>
                  <p className="text-sm text-slate-500">
                    {selected.row_count?.toLocaleString()} rows × {selected.column_count} columns
                    {selected.quality_score != null && (
                      <span className="ml-2">· Quality: <strong>{selected.quality_score.toFixed(1)}/100</strong></span>
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleClean}
                    disabled={cleaning}
                    className="btn-secondary flex items-center gap-1 text-sm"
                  >
                    <SparklesIcon className="h-4 w-4" />
                    {cleaning ? 'Cleaning...' : 'Auto Clean'}
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 border-b border-slate-200">
                {(['overview', 'forecast', 'nlq'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={clsx(
                      'px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors',
                      tab === t
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    )}
                  >
                    {t === 'nlq' ? 'Ask AI' : t}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {tab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <DataQualityCard datasetId={selected.id} />
                  <AlertsPanel />
                  <RecommendationsPanel datasetId={selected.id} />
                  <MetricsPanel />
                </div>
              )}

              {tab === 'forecast' && (
                <ForecastChart datasetId={selected.id} columns={columns} />
              )}

              {tab === 'nlq' && (
                <NLQInterface datasetId={selected.id} />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
