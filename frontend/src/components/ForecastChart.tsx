'use client';
import { useState } from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { forecastingApi, type ForecastResult } from '@/lib/api';

interface Props {
  datasetId: number;
  columns: string[];
}

export default function ForecastChart({ datasetId, columns }: Props) {
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [targetCol, setTargetCol] = useState(columns[0] || '');
  const [dateCol, setDateCol] = useState(columns[1] || '');
  const [horizon, setHorizon] = useState(30);
  const [error, setError] = useState<string | null>(null);

  const runForecast = async () => {
    if (!targetCol || !dateCol) return;
    setLoading(true);
    setError(null);
    try {
      const res = await forecastingApi.run({
        dataset_id: datasetId,
        target_column: targetCol,
        date_column: dateCol,
        horizon,
      });
      setResult(res.data);
    } catch {
      setError('Forecast failed. Ensure the date and target columns are valid.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = result?.predictions.map((p) => ({
    step: `T+${p.step}`,
    value: p.value,
    lower: p.lower,
    upper: p.upper,
  }));

  return (
    <div className="card">
      <h3 className="font-semibold text-slate-800 mb-4">Forecasting</h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Target Column</label>
          <select
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
            value={targetCol}
            onChange={(e) => setTargetCol(e.target.value)}
          >
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Date Column</label>
          <select
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
            value={dateCol}
            onChange={(e) => setDateCol(e.target.value)}
          >
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Horizon (days)</label>
          <input
            type="number"
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            min={1}
            max={365}
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={runForecast}
            disabled={loading}
            className="btn-primary w-full disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Run Forecast'}
          </button>
        </div>
      </div>

      {error && <div className="text-red-500 text-sm mb-3">{error}</div>}

      {result && chartData && (
        <div>
          <div className="flex items-center gap-4 mb-3 text-sm text-slate-600">
            <span>Model: <strong>{result.model_used}</strong></span>
            {result.metrics?.mae != null && (
              <span>MAE: <strong>{result.metrics.mae.toFixed(2)}</strong></span>
            )}
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="step" tick={{ fontSize: 11 }} interval={Math.floor(chartData.length / 6)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="upper" stroke="transparent" fill="#bfdbfe" name="Upper CI" />
              <Area type="monotone" dataKey="lower" stroke="transparent" fill="#f8fafc" name="Lower CI" />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" dot={false} strokeWidth={2} name="Forecast" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {!result && !loading && (
        <div className="h-48 flex items-center justify-center text-slate-400 text-sm border-2 border-dashed border-slate-200 rounded-lg">
          Configure and run a forecast to see predictions
        </div>
      )}
    </div>
  );
}
