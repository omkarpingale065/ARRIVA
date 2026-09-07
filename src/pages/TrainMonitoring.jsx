import { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import PageHeader from '../components/PageHeader';
import TrainTable from '../components/TrainTable';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { getTrains, mergeLiveUpdate } from '../services/api';
import { createTrainSocket } from '../services/websocket';

const filters = [
  { value: 'ALL', label: 'All' },
  { value: 'ON_TIME', label: 'On Time' },
  { value: 'DELAYED', label: 'Delayed' },
  { value: 'HIGH_RISK', label: 'High Risk' },
];

export default function TrainMonitoring() {
  const navigate = useNavigate();
  const [trains, setTrains] = useState([]);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('ALL');
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
        setError('Unable to load train monitoring data.');
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

  const visibleTrains = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return trains.filter((train) => {
      const riskMatch =
        filter === 'ALL' ||
        (filter === 'ON_TIME' && train.delayRisk === 'LOW') ||
        (filter === 'DELAYED' && (train.delayRisk === 'MEDIUM' || train.delayRisk === 'HIGH')) ||
        (filter === 'HIGH_RISK' && train.delayRisk === 'HIGH');

      const queryMatch =
        normalizedQuery.length === 0 ||
        train.number.toLowerCase().includes(normalizedQuery) ||
        train.origin.toLowerCase().includes(normalizedQuery) ||
        train.destination.toLowerCase().includes(normalizedQuery) ||
        train.currentStation.toLowerCase().includes(normalizedQuery);

      return riskMatch && queryMatch;
    });
  }, [filter, query, trains]);

  if (loading) return <div className="px-4 py-8 md:px-8"><LoadingState /></div>;
  if (error) return <div className="px-4 py-8 md:px-8"><ErrorState message={error} /></div>;

  return (
    <div className="ops-shell">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <PageHeader
          title="Train Monitoring"
          subtitle="Fleet overview · live simulator telemetry · AI arrival predictions"
        />

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <label className="relative block w-full lg:max-w-md">
              <span className="sr-only">Search by train number or station</span>
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by train number or station"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-800 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              />
            </label>

            <div className="flex flex-wrap gap-2">
              {filters.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setFilter(item.value)}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                    filter === item.value
                      ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        {visibleTrains.length > 0 ? (
          <TrainTable trains={visibleTrains} onView={(trainId) => navigate(`/trains/${trainId}`)} />
        ) : (
          <EmptyState title="No trains found" message="Try a different station, train number, or filter selection." />
        )}
      </main>
    </div>
  );
}
