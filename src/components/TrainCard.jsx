import { ArrowRight, Gauge, Clock3 } from 'lucide-react';

export default function TrainCard({ train, onView }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Train {train.number}</p>
          <h3 className="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-50">{train.origin} → {train.destination}</h3>
        </div>
        <button
          type="button"
          onClick={onView}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          View <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <Gauge className="h-4 w-4 text-sky-500" />
          <span>{train.currentSpeed ?? '--'} km/h</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <Clock3 className="h-4 w-4 text-amber-500" />
          <span>{train.currentDelay === null || train.currentDelay === undefined ? '--' : `${train.currentDelay > 0 ? '+' : ''}${train.currentDelay} min`}</span>
        </div>
      </div>
    </div>
  );
}
