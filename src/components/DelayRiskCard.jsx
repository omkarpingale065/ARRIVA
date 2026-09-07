import StatusBadge from './StatusBadge';

export default function DelayRiskCard({ train }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Train {train.number}</p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">Delay Risk</h3>
        </div>
        <StatusBadge status={train.delayRisk} className="text-xs px-3 py-1.5" />
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-950/70">
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Risk Level</span>
          <span className="text-2xl font-semibold text-slate-900 dark:text-slate-50">{train.delayRisk}</span>
        </div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
          <div
            className={`h-full rounded-full ${
              train.delayRisk === 'LOW'
                ? 'bg-emerald-500'
                : train.delayRisk === 'MEDIUM'
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
            }`}
            style={{ width: train.delayRisk === 'LOW' ? '33%' : train.delayRisk === 'MEDIUM' ? '66%' : '100%' }}
          />
        </div>
      </div>
    </div>
  );
}
