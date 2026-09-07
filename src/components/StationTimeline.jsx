export default function StationTimeline({ stations }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Route Timeline</h3>
      <div className="mt-5 space-y-4">
        {stations.map((station, index) => (
          <div key={`${station.name}-${index}`} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`h-4 w-4 rounded-full border-2 ${
                  station.status === 'completed'
                    ? 'border-emerald-500 bg-emerald-500'
                    : station.status === 'current'
                      ? 'border-sky-500 bg-sky-500'
                      : 'border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900'
                }`}
              />
              {index < stations.length - 1 && <div className="mt-1 h-12 w-px bg-slate-200 dark:bg-slate-700" />}
            </div>

            <div className="flex-1 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">{station.name}</p>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                    {station.status === 'completed' ? 'Completed' : station.status === 'current' ? 'Current' : 'Upcoming'}
                  </p>
                </div>
                <div className="text-right text-sm text-slate-600 dark:text-slate-300">
                  <p>Scheduled: {station.scheduled}</p>
                  <p>Predicted: {station.predicted}</p>
                  <p className="font-medium text-slate-900 dark:text-slate-100">{station.delay}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
