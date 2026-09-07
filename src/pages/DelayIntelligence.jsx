import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowUpRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import PageHeader from '../components/PageHeader';
import DelayRiskCard from '../components/DelayRiskCard';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrains, mergeLiveUpdate } from '../services/api';
import { createTrainSocket } from '../services/websocket';

export default function DelayIntelligence() {
  const [trains, setTrains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getTrains()
      .then((data) => {
        if (!active) return;
        setTrains(data);
      })
      .catch(() => {
        if (!active) return;
        setError('Unable to load delay intelligence insights.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    const stream = createTrainSocket({
      onMessage: (update) => setTrains((current) => current.map((train) => mergeLiveUpdate(train, update))),
    });

    return () => {
      active = false;
      stream.disconnect();
    };
  }, []);

  const train = useMemo(() => trains.find((item) => item.id === '12123') ?? trains[0], [trains]);

  if (loading) return <div className="px-4 py-8 md:px-8"><LoadingState /></div>;
  if (error) return <div className="px-4 py-8 md:px-8"><ErrorState message={error} /></div>;
  if (!train) return null;

  return (
    <div className="ops-shell">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <PageHeader
          title="Delay Intelligence"
          subtitle="Understand current delay risk and factors affecting train arrival."
        />

        <section className="mb-8">
          <DelayRiskCard train={train} />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-50">Why is the train delayed?</h3>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {train.factors.map((factor) => (
              <div key={factor.name} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/70">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{factor.name}</p>
                  <ArrowUpRight className="h-4 w-4 text-sky-500" />
                </div>
                <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{factor.detail}</p>
                <p className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-50">Impact: {factor.impact}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
