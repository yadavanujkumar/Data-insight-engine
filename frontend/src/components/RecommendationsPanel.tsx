'use client';
import { useEffect, useState } from 'react';
import { recommendationsApi, type Recommendation } from '@/lib/api';
import clsx from 'clsx';
import { LightBulbIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
};

interface Props {
  datasetId?: number;
}

export default function RecommendationsPanel({ datasetId }: Props) {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    recommendationsApi
      .list()
      .then((r) => setRecs(r.data))
      .finally(() => setLoading(false));
  }, []);

  const generate = async () => {
    if (!datasetId) return;
    setGenerating(true);
    try {
      const res = await recommendationsApi.generate(datasetId);
      setRecs((prev) => [...res.data, ...prev]);
    } finally {
      setGenerating(false);
    }
  };

  const updateStatus = async (id: number, status: string) => {
    await recommendationsApi.update(id, status);
    setRecs((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));
  };

  if (loading) return <div className="card animate-pulse h-48 bg-slate-100" />;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <LightBulbIcon className="h-5 w-5 text-yellow-500" />
          <h3 className="font-semibold text-slate-800">Recommendations</h3>
        </div>
        {datasetId && (
          <button onClick={generate} disabled={generating} className="btn-secondary text-sm">
            {generating ? 'Generating...' : 'Generate'}
          </button>
        )}
      </div>

      {recs.length === 0 ? (
        <div className="text-center text-slate-400 text-sm py-8">
          No recommendations yet. Upload a dataset and click Generate.
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {recs.map((rec) => (
            <div
              key={rec.id}
              className={clsx(
                'border rounded-lg p-3 transition-opacity',
                rec.status === 'completed' || rec.status === 'dismissed' ? 'opacity-50' : ''
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={clsx('badge', priorityColors[rec.priority] || 'bg-slate-100 text-slate-600')}>
                      {rec.priority}
                    </span>
                    {rec.category && (
                      <span className="badge bg-blue-50 text-blue-600">{rec.category}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-800">{rec.title}</p>
                  {rec.description && (
                    <p className="text-xs text-slate-500 mt-1">{rec.description}</p>
                  )}
                  <p className="text-xs text-slate-400 mt-1">
                    Impact: {(rec.expected_impact * 100).toFixed(0)}%
                  </p>
                </div>
                {rec.status === 'pending' && (
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => updateStatus(rec.id, 'completed')}
                      title="Mark complete"
                      className="text-green-500 hover:text-green-700"
                    >
                      <CheckCircleIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => updateStatus(rec.id, 'dismissed')}
                      title="Dismiss"
                      className="text-slate-400 hover:text-slate-600"
                    >
                      <XCircleIcon className="h-5 w-5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
