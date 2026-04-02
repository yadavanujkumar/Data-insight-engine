'use client';
import { useEffect, useState } from 'react';
import { qualityApi, type QualityScore } from '@/lib/api';
import clsx from 'clsx';

interface Props {
  datasetId: number;
}

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const color = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600';
  const bg = score >= 80 ? 'bg-green-100' : score >= 60 ? 'bg-yellow-100' : 'bg-red-100';
  return (
    <div className={clsx('rounded-lg p-3 text-center', bg)}>
      <div className={clsx('text-2xl font-bold', color)}>{score.toFixed(0)}</div>
      <div className="text-xs text-slate-600 mt-1">{label}</div>
    </div>
  );
}

export default function DataQualityCard({ datasetId }: Props) {
  const [quality, setQuality] = useState<QualityScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    qualityApi
      .getScore(datasetId)
      .then((r) => setQuality(r.data))
      .catch(() => setError('Failed to load quality score'))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) return <div className="card animate-pulse h-48 bg-slate-100" />;
  if (error) return <div className="card text-red-500">{error}</div>;
  if (!quality) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-800">Data Quality</h3>
        <div className="flex items-center gap-2">
          <div
            className="text-3xl font-bold"
            style={{
              color:
                quality.overall_score >= 80
                  ? '#16a34a'
                  : quality.overall_score >= 60
                  ? '#ca8a04'
                  : '#dc2626',
            }}
          >
            {quality.overall_score.toFixed(1)}
          </div>
          <div className="text-slate-500 text-sm">/100</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <ScoreGauge score={quality.completeness} label="Completeness" />
        <ScoreGauge score={quality.consistency} label="Consistency" />
        <ScoreGauge score={quality.validity} label="Validity" />
        <ScoreGauge score={quality.uniqueness} label="Uniqueness" />
      </div>

      {quality.issues.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-600 mb-2">Issues ({quality.issues.length})</h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {quality.issues.slice(0, 5).map((issue, i) => (
              <div
                key={i}
                className={clsx(
                  'text-xs px-2 py-1 rounded flex items-center gap-2',
                  issue.severity === 'critical' ? 'bg-red-50 text-red-700' : 'bg-yellow-50 text-yellow-700'
                )}
              >
                <span className="font-medium">{issue.column}:</span>
                <span>{issue.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
