export default function StatCard({ icon: Icon, label, value, detail, tone = 'blue' }) {
  const toneClasses = {
    blue: 'border-sky-500/20 bg-sky-500/5 text-sky-200',
    emerald: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-200',
    amber: 'border-amber-500/20 bg-amber-500/5 text-amber-200',
    rose: 'border-rose-500/20 bg-rose-500/5 text-rose-200',
    slate: 'border-slate-500/20 bg-slate-500/5 text-slate-200',
  };

  const toneClass = toneClasses[tone] ?? toneClasses.blue;

  return (
    <div className="ops-panel rounded-2xl p-5 transition duration-300 hover:-translate-y-0.5 hover:border-sky-400/40">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-50">{value}</p>
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-xl border ${toneClass}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
        <span>{detail}</span>
        <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-400">LIVE</span>
      </div>
    </div>
  );
}
