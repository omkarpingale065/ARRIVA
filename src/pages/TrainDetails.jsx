import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Clock3, Gauge, Route, TimerReset } from 'lucide-react';
import Navbar from '../components/Navbar';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import StationTimeline from '../components/StationTimeline';
import ETAChart from '../components/ETAChart';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrainById, mergeLiveUpdate } from '../services/api';
import { createTrainSocket } from '../services/websocket';

export default function TrainDetails() {
  const { trainId } = useParams();
  const [train, setTrain] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getTrainById(trainId)
      .then((data) => {
        if (!active) return;
        if (!data) {
          setError('The requested train record could not be found.');
          return;
        }
        setTrain(data);
      })
      .catch(() => {
        if (!active) return;
        setError('Unable to load the train details.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    const stream = createTrainSocket({
      onMessage: (update) => setTrain((current) => mergeLiveUpdate(current, update)),
    });

    return () => {
      active = false;
      stream.disconnect();
    };
  }, [trainId]);

  const etaHistory = useMemo(
    () => (train?.etaHistory ?? []).map((entry) => ({ time: entry.time, eta: Number(entry.eta) })),
    [train],
  );

  const speedHistory = useMemo(
    () => (train?.speedHistory ?? []).map((entry) => ({ time: entry.time, speed: Number(entry.speed) })),
    [train],
  );

  if (loading) return <div className="px-4 py-8 md:px-8"><LoadingState /></div>;
  if (error) return <div className="px-4 py-8 md:px-8"><ErrorState message={error} /></div>;
  if (!train) return null;

  return (
    <div className="ops-shell">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <PageHeader
          title={`Train ${train.number}`}
          subtitle={`${train.origin} → ${train.destination}`}
          statusText={`LIVE · ${train.statusLabel}`}
        />

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div className="ops-panel rounded-3xl p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Predicted Arrival</p>
                <p className="mt-3 text-4xl font-semibold tracking-tight text-sky-200">{train.predictedETA}</p>
              </div>
              <StatusBadge status={train.delayRisk} className="text-xs px-3 py-1.5" />
            </div>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">{train.currentDelay === null ? '--' : `${train.currentDelay >= 0 ? '+' : ''}${train.currentDelay} minutes from schedule`}</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <div className="ops-panel rounded-2xl p-5">
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <Gauge className="h-4 w-4 text-sky-500" />
                <span className="text-xs uppercase tracking-[0.18em]">Current Speed</span>
              </div>
              <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-50">{train.currentSpeed ?? '--'} km/h</p>
            </div>
            <div className="ops-panel rounded-2xl p-5">
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <Clock3 className="h-4 w-4 text-amber-500" />
                <span className="text-xs uppercase tracking-[0.18em]">Current Delay</span>
              </div>
              <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-50">{train.currentDelay ?? '--'} min</p>
            </div>
            <div className="ops-panel rounded-2xl p-5">
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <Route className="h-4 w-4 text-emerald-500" />
                <span className="text-xs uppercase tracking-[0.18em]">Distance Remaining</span>
              </div>
              <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-50">{train.distanceRemaining ?? '--'} km</p>
            </div>
            <div className="ops-panel rounded-2xl p-5">
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <TimerReset className="h-4 w-4 text-rose-500" />
                <span className="text-xs uppercase tracking-[0.18em]">Delay Risk</span>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <p className="text-2xl font-semibold text-slate-900 dark:text-slate-50">{train.delayRisk}</p>
                <StatusBadge status={train.delayRisk} />
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <StationTimeline stations={train.stations} />

          <div className="space-y-6">
            <ETAChart title="ETA Prediction History" data={etaHistory} dataKey="eta" color="#38bdf8" yLabel="ETA (min)" />
            <ETAChart title="Speed History" data={speedHistory} dataKey="speed" color="#34d399" yLabel="Speed (km/h)" />
          </div>
        </section>
      </main>
    </div>
  );
}
