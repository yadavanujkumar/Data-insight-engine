'use client';
import { useEffect, useState } from 'react';
import { metricsApi, type MetricSummary } from '@/lib/api';
import { ChartBarIcon } from '@heroicons/react/24/outline';

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState<MetricSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    metricsApi
      .list()
      .then((r) => setMetrics(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card animate-pulse h-32 bg-slate-100" />;

  if (metrics.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <ChartBarIcon className="h-5 w-5 text-indigo-500" />
          <h3 className="font-semibold text-slate-800">System Metrics</h3>
        </div>
        <p className="text-slate-400 text-sm text-center py-4">No metrics recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <ChartBarIcon className="h-5 w-5 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">System Metrics</h3>
      </div>
      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.metric_name} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
            <span className="text-sm font-medium text-slate-700">{m.metric_name}</span>
            <div className="flex gap-4 text-xs text-slate-500">
              <span>avg: <strong className="text-slate-800">{m.avg?.toFixed(2) ?? 'N/A'}</strong></span>
              <span>max: <strong className="text-slate-800">{m.max?.toFixed(2) ?? 'N/A'}</strong></span>
              <span>n: <strong className="text-slate-800">{m.count}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
