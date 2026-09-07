const toneClasses = {
  LOW: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
  MEDIUM: 'border-amber-400/30 bg-amber-500/10 text-amber-100',
  HIGH: 'border-rose-400/30 bg-rose-500/10 text-rose-100',
  ON_TIME: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
  DELAYED: 'border-amber-400/30 bg-amber-500/10 text-amber-100',
  HIGH_RISK: 'border-rose-400/30 bg-rose-500/10 text-rose-100',
};

export default function StatusBadge({ status, className = '' }) {
  const normalized = String(status || '').toUpperCase();
  const tone = toneClasses[normalized] ?? 'border-slate-500/30 bg-slate-500/10 text-slate-200';

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${tone} ${className}`}
    >
      {normalized}
    </span>
  );
}
