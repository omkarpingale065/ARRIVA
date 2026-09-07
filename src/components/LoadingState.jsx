export default function LoadingState({ message = 'Loading train data...' }) {
  return (
    <div className="flex min-h-[220px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-12 text-center text-slate-600 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300">
      <div>
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-slate-300 border-t-sky-500" aria-label="Loading" />
        <p className="mt-4 text-sm font-medium">{message}</p>
      </div>
    </div>
  );
}
