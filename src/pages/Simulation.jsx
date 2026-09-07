import { useEffect, useMemo, useState } from 'react';
import { Gauge, TimerReset } from 'lucide-react';
import Navbar from '../components/Navbar';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrains, runSimulation } from '../services/api';

export default function Simulation() {
  const [trains, setTrains] = useState([]);
  const [selectedTrainId, setSelectedTrainId] = useState('12123');
  const [simulationMinutes, setSimulationMinutes] = useState(5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let active = true;

    getTrains()
      .then((data) => {
        if (!active) return;
        setTrains(data);
        if (data[0]) setSelectedTrainId(data[0].id);
      })
      .catch(() => {
        if (!active) return;
        setError('Unable to load simulation options.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedTrain = useMemo(
    () => trains.find((train) => train.id === selectedTrainId) ?? trains[0],
    [selectedTrainId, trains],
  );

  const handleRunSimulation = async () => {
    if (!selectedTrain) return;
    setRunning(true);
    setError('');
    try {
      const simulation = await runSimulation({ trainId: selectedTrain.id, additionalDelay: simulationMinutes });
      setResult({ ...simulation, before: selectedTrain });
      setTrains((current) => current.map((train) => train.id === simulation.train.id ? simulation.train : train));
    } catch {
      setError('Unable to advance the selected train simulation.');
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="px-4 py-8 md:px-8"><LoadingState /></div>;
  if (error) return <div className="px-4 py-8 md:px-8"><ErrorState message={error} /></div>;

  return (
    <div className="ops-shell">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <PageHeader
          title="Train Simulation Lab"
          subtitle="Advance the simulator and watch AI ETA predictions respond to changing conditions."
        />

        <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div className="ops-panel rounded-2xl p-6">
            <div className="mb-6">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Selected train</p>
              <h3 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">Train {selectedTrain?.number ?? '--'}</h3>
            </div>

            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="train-select">
                Train
              </label>
              <select
                id="train-select"
                value={selectedTrainId}
                onChange={(event) => setSelectedTrainId(event.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                {trains.map((train) => (
                  <option key={train.id} value={train.id}>Train {train.number} — {train.origin} → {train.destination}</option>
                ))}
              </select>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="delay-slider">
                  Simulation Duration
                </label>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
                  <div className="mb-2 flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
                    <span>Simulation duration</span>
                    <span className="font-semibold text-slate-50">{simulationMinutes} min</span>
                  </div>
                  <input
                    id="delay-slider"
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={simulationMinutes}
                    onChange={(event) => setSimulationMinutes(Number(event.target.value))}
                    className="w-full accent-sky-500"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleRunSimulation}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-sky-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-300"
              >
                {running ? 'Advancing simulation...' : 'Advance Simulation'}
              </button>
            </div>
          </div>

          <div className="ops-panel rounded-2xl p-6">
            {result ? (
              <>
                <div className="mb-6 grid gap-4 md:grid-cols-2">
                  {[['BEFORE', result.before], ['AFTER', result.train]].map(([label, state]) => (
                    <div key={label} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{label} · live state</p>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                        <span className="text-slate-400">Speed <strong className="block text-slate-100">{state.currentSpeed} km/h</strong></span>
                        <span className="text-slate-400">Delay <strong className="block text-slate-100">+{state.currentDelay} min</strong></span>
                        <span className="text-slate-400">Distance <strong className="block text-slate-100">{state.distanceRemaining} km</strong></span>
                        <span className="text-slate-400">Risk <strong className="block text-sky-200">{state.delayRisk}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/70">
                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                      <Gauge className="h-4 w-4 text-sky-500" />
                      <span className="text-xs uppercase tracking-[0.18em]">Current ETA</span>
                    </div>
                    <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-50">{result.currentETA}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/70">
                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                      <TimerReset className="h-4 w-4 text-amber-500" />
                      <span className="text-xs uppercase tracking-[0.18em]">Simulated ETA</span>
                    </div>
                    <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-50">{result.simulatedETA}</p>
                  </div>
                </div>

                <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/70">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Additional Delay</p>
                  <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-50">+{result.additionalDelay} min</p>
                </div>

                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Affected Stations</h4>
                  <div className="mt-4 space-y-3">
                    {result.affectedStations.map((item) => (
                      <div key={item.station} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700">
                        <span className="font-medium text-slate-700 dark:text-slate-200">{item.station}</span>
                        <span className="text-slate-600 dark:text-slate-300">{item.impact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex h-full min-h-[320px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-center text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">
                Select a train and run a simulation to model the impact.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
