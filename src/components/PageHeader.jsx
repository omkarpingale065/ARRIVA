export default function PageHeader({ title, subtitle, statusText, statusTone = 'LOW' }) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900 md:text-4xl dark:text-slate-50">
          {title}
        </h1>
        {subtitle && <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>}
      </div>

      {statusText && (
        <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-200">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" aria-hidden="true" />
          {statusText}
        </div>
      )}
    </div>
  );
}
