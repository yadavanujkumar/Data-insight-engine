'use client';
import { useEffect, useState } from 'react';
import { alertsApi, type Alert } from '@/lib/api';
import clsx from 'clsx';
import { BellIcon, CheckIcon } from '@heroicons/react/24/outline';

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
};

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'active' | 'all'>('active');

  const loadAlerts = () => {
    setLoading(true);
    alertsApi
      .list(filter === 'active' ? 'active' : undefined)
      .then((r) => setAlerts(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadAlerts();
  }, [filter]);

  const resolve = async (id: number) => {
    await alertsApi.resolve(id);
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'resolved' } : a)));
  };

  const activeCount = alerts.filter((a) => a.status === 'active').length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BellIcon className="h-5 w-5 text-orange-500" />
          <h3 className="font-semibold text-slate-800">Alerts</h3>
          {activeCount > 0 && (
            <span className="badge bg-red-100 text-red-700">{activeCount} active</span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('active')}
            className={clsx('text-xs px-3 py-1 rounded-lg', filter === 'active' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600')}
          >
            Active
          </button>
          <button
            onClick={() => setFilter('all')}
            className={clsx('text-xs px-3 py-1 rounded-lg', filter === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600')}
          >
            All
          </button>
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-slate-100 rounded-lg" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center text-slate-400 text-sm py-8">
          {filter === 'active' ? 'No active alerts' : 'No alerts found'}
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={clsx('border rounded-lg p-3 flex items-start justify-between gap-2', severityColors[alert.severity] || 'bg-slate-50 text-slate-700 border-slate-200')}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{alert.name}</span>
                  <span className={clsx('badge text-xs', alert.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-white/70 text-current')}>
                    {alert.status}
                  </span>
                </div>
                <p className="text-xs opacity-75 mt-0.5">
                  {alert.metric_name} | threshold: {alert.threshold_value}
                  {alert.current_value != null && ` | current: ${alert.current_value}`}
                </p>
              </div>
              {alert.status === 'active' && (
                <button
                  onClick={() => resolve(alert.id)}
                  className="shrink-0 text-green-600 hover:text-green-800"
                  title="Resolve"
                >
                  <CheckIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
