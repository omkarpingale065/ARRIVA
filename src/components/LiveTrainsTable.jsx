import { useEffect, useState } from 'react';
import { formatETA } from '../services/api';

const numberOrDash = (value, suffix = '') => Number.isFinite(value) ? `${value}${suffix}` : '--';

export default function LiveTrainsTable({ trains, selectedTrainId, onSelect, lastUpdatedAt }) {
  const [now, setNow] = useState(null);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const refreshedSeconds = lastUpdatedAt
    ? Math.max(0, Math.floor(((now ?? lastUpdatedAt) - lastUpdatedAt) / 1000))
    : null;
  return (
    <section className="rounded-xl border border-slate-700/70 bg-[#101b2d]">
      <div className="flex items-center justify-between border-b border-slate-700/70 px-5 py-4">
        <div>
          <h2 className="font-semibold text-slate-100">Live Trains — Predicted vs Scheduled ETA</h2>
          <p className="mt-1 text-xs text-slate-500">Real-time simulator telemetry</p>
        </div>
        <span className="text-right font-mono text-[10px] uppercase tracking-widest text-emerald-400">
          <span className="block">● LIVE</span>
          <span className="mt-1 block normal-case tracking-normal text-slate-500">
            {refreshedSeconds === null ? 'waiting for feed' : `refreshed ${refreshedSeconds}s ago`}
          </span>
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs">
          <thead className="bg-[#0d1727] font-mono uppercase tracking-wider text-slate-500">
            <tr>{['Train', 'Route', 'Sched. ETA', 'Predicted ETA', 'Delta', 'Progress / confidence'].map((heading) => <th key={heading} className="px-5 py-3 font-medium">{heading}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {trains.map((train) => {
              const delta = train.predictedDelay;
              const confidence = train.confidencePercent;
              const progress = train.progressPercent;
              const deltaTone = !Number.isFinite(delta) || delta === 0
                ? 'text-slate-300'
                : delta > 0 ? 'text-rose-300' : 'text-emerald-300';
              return (
                <tr key={train.id} onClick={() => onSelect(train.id)} className={`cursor-pointer transition hover:bg-[#14243a] ${selectedTrainId === train.id ? 'bg-[#14243a]' : ''}`}>
                  <td className="px-5 py-4"><p className="font-mono font-semibold text-slate-100">{train.number}</p><p className="mt-1 text-slate-500">{train.name}</p></td>
                  <td className="px-5 py-4 text-slate-300">
                    <p>{train.originCode} → {train.destinationCode}</p>
                    <p className="mt-1 text-[10px] text-slate-500">Next: {train.nextStation ?? '--'}</p>
                  </td>
                  <td className="px-5 py-4 font-mono text-slate-300">{formatETA(train.scheduledDestinationArrival)}</td>
                  <td className="px-5 py-4 font-mono font-semibold text-amber-300">{formatETA(train.predictedArrival)}</td>
                  <td className={`px-5 py-4 font-mono ${deltaTone}`}>{numberOrDash(delta, ' min')}</td>
                  <td className="min-w-[170px] px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-1.5 flex-1 rounded-full bg-slate-700">
                        <div className="h-full rounded-full bg-amber-400" style={{ width: Number.isFinite(progress) ? `${progress}%` : '0%' }} />
                      </div>
                      <span className="font-mono text-slate-400">{numberOrDash(progress, '%')}</span>
                    </div>
                    <p className="mt-1 text-right font-mono text-[10px] text-slate-500">
                      confidence {numberOrDash(confidence, '%')}
                    </p>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
