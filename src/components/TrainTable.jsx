import { ArrowRight, Clock3, Gauge } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function TrainTable({ trains, onView }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-950/70">
            <tr>
              {['Train', 'Route', 'Current Location', 'Speed', 'Delay', 'Predicted ETA', 'Risk', 'Action'].map((heading) => (
                <th key={heading} className="px-4 py-3 font-medium text-slate-600 dark:text-slate-300">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {trains.map((train) => (
              <tr key={train.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/70">
                <td className="px-4 py-4">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{train.number}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{train.name}</div>
                  </div>
                </td>
                <td className="px-4 py-4 text-slate-700 dark:text-slate-300">{train.origin} → {train.destination}</td>
                <td className="px-4 py-4 text-slate-700 dark:text-slate-300">{train.currentStation}</td>
                <td className="px-4 py-4">
                  <div className="inline-flex items-center gap-2 text-slate-700 dark:text-slate-300">
                    <Gauge className="h-3.5 w-3.5 text-sky-500" />
                    {train.currentSpeed ?? '--'} km/h
                  </div>
                </td>
                <td className="px-4 py-4">
                  <div className="inline-flex items-center gap-2 text-slate-700 dark:text-slate-300">
                    <Clock3 className="h-3.5 w-3.5 text-amber-500" />
                    {train.currentDelay === null || train.currentDelay === undefined ? '--' : `${train.currentDelay > 0 ? '+' : ''}${train.currentDelay} min`}
                  </div>
                </td>
                <td className="px-4 py-4 text-slate-700 dark:text-slate-300">{train.predictedETA ?? '--'}</td>
                <td className="px-4 py-4"><StatusBadge status={train.delayRisk} /></td>
                <td className="px-4 py-4">
                  <button
                    type="button"
                    onClick={() => onView(train.id)}
                    className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    View <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
