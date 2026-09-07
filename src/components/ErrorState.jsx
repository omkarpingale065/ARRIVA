export default function ErrorState({ title = 'Unable to load data', message = 'The service is temporarily unavailable.' }) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-10 text-center text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm">{message}</p>
    </div>
  );
}
