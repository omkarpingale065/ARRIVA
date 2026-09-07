import { useEffect, useMemo, useState } from 'react';
import { Search, TrainFront } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import LiveTrainsTable from '../components/LiveTrainsTable';
import ETADriftChart from '../components/ETADriftChart';
import DelayAttributionPanel from '../components/DelayAttributionPanel';
import StationBoard from '../components/StationBoard';
import { getModelComparison, getTrains, mergeLiveUpdate } from '../services/api';
import { createTrainSocket } from '../services/websocket';
import { railPulseGroups } from '../components/railPulseConfig';

const finite = (value) => Number.isFinite(Number(value));
const minutes = (value) => finite(value) ? `${Number(value).toFixed(1)} min` : '--';

export default function Dashboard() {
  const [trains, setTrains] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selectedTrainId, setSelectedTrainId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [clock, setClock] = useState(new Date());
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null);

  useEffect(() => {
    let active = true;
    Promise.all([getTrains(), getModelComparison()])
      .then(([data, comparison]) => {
        if (!active) return;
        setTrains(data);
        setSelectedTrainId(data[0]?.id ?? '');
        setMetrics(comparison);
        setLastUpdatedAt(Date.now());
      })
      .catch(() => active && setError('Unable to load live dashboard data.'))
      .finally(() => active && setLoading(false));
    const stream = createTrainSocket({
      onMessage: (update) => {
        setTrains((current) => current.map((train) => mergeLiveUpdate(train, update)));
        setLastUpdatedAt(Date.now());
      },
    });
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => { active = false; stream.disconnect(); window.clearInterval(timer); };
  }, []);

  const visibleTrains = useMemo(() => {
    const value = query.trim().toLowerCase();
    return trains.filter((train) => !value || [train.number, train.name, train.origin, train.destination].some((item) => String(item ?? '').toLowerCase().includes(value)));
  }, [query, trains]);
  const selectedTrain = trains.find((train) => train.id === selectedTrainId) ?? trains[0];
  const averageDelay = trains.length ? trains.reduce((sum, train) => sum + (finite(train.predictedDelay) ? Number(train.predictedDelay) : 0), 0) / trains.length : null;
  const onTime = trains.length ? (trains.filter((train) => train.delayRisk === 'LOW' || (finite(train.currentDelay) && train.currentDelay <= 0)).length / trains.length) * 100 : null;

  if (loading) return <div className="ops-shell p-6"><LoadingState message="Loading live control dashboard..." /></div>;
  if (error) return <div className="ops-shell p-6"><ErrorState message={error} /></div>;

  const stats = [
    ['Trains Tracked Live', trains.length || '--', 'vs scheduled fleet', 'border-amber-400'],
    ['Avg Predicted Delay', minutes(averageDelay), 'AI destination estimate', 'border-rose-400'],
    ['On-Time Performance', finite(onTime) ? `${onTime.toFixed(1)}%` : '--', 'LOW risk or no current delay', 'border-emerald-400'],
    ['Model MAE (ETA)', metrics && finite(metrics.model_mae) ? `${Number(metrics.model_mae).toFixed(3)} min` : '--', 'offline test-set MAE', 'border-sky-400'],
  ];

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-200">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-[#1c2e47] bg-[#0c1626] p-5 lg:block">
          <Link to="/dashboard" className="block border-b border-[#1c2e47] pb-7">
            <div className="font-mono text-xl font-semibold tracking-[0.18em] text-slate-100">RAILPULSE</div>
            <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Dynamic ETA Engine</div>
          </Link>
          <nav className="mt-7 space-y-7">
            {railPulseGroups.map((group) => <div key={group.label}><p className="mb-2 px-2 font-mono text-[10px] tracking-[0.2em] text-slate-500">{group.label}</p><div className="space-y-1">{group.items.map(([label, to, Icon]) => <NavLink key={label} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm ${isActive ? 'border-l-2 border-amber-400 bg-[#14243a] text-slate-100' : 'text-slate-500 hover:bg-[#14243a] hover:text-slate-200'}`}><Icon size={15} />{label}</NavLink>)}</div></div>)}
          </nav>
          <div className="mt-10 rounded-md border border-[#1c2e47] bg-[#0d1727] p-3 font-mono text-[10px] text-slate-500"><span className="text-emerald-400">● MODEL ONLINE</span><p className="mt-2 text-slate-300">Linear Regression</p><p>MAE {metrics && finite(metrics.model_mae) ? Number(metrics.model_mae).toFixed(3) : '--'} min</p></div>
        </aside>
        <main className="min-w-0 flex-1 p-5 md:p-8">
          <header className="flex flex-col justify-between gap-5 border-b border-[#1c2e47] pb-6 md:flex-row md:items-start">
            <div><h1 className="text-2xl font-semibold text-slate-100">Section Control — Central Division</h1><p className="mt-2 text-sm text-slate-500">Live network overview · ETA prediction · delay intelligence</p></div>
            <div className="flex items-center gap-5"><label className="flex items-center gap-2 rounded-md border border-[#1c2e47] bg-[#0d1727] px-3 py-2 text-slate-500"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search trains..." className="w-36 bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-600" /></label><div className="text-right font-mono"><div className="text-sm text-slate-200">{clock.toLocaleTimeString('en-GB')}</div><div className="mt-1 text-[10px] text-slate-500">{clock.toLocaleDateString('en-GB')}</div></div></div>
          </header>
          <section className="mb-8">
            <StationBoard trains={trains} clock={clock} />
          </section>
          <section className="my-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map(([label, value, detail, accent]) => <div key={label} className={`rounded-lg border border-[#1c2e47] border-l-4 ${accent} bg-[#101b2d] p-4`}><p className="text-xs text-slate-500">{label}</p><p className="mt-3 font-mono text-2xl font-semibold text-slate-100">{value}</p><p className="mt-2 font-mono text-[10px] text-slate-500">{detail}</p></div>)}
          </section>
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(340px,0.8fr)]">
            <LiveTrainsTable
              trains={visibleTrains}
              selectedTrainId={selectedTrain?.id}
              onSelect={setSelectedTrainId}
              lastUpdatedAt={lastUpdatedAt}
            />
            <ETADriftChart train={selectedTrain} />
          </section>
          <div className="mt-4"><DelayAttributionPanel trains={trains} /></div>
          <footer className="mt-5 flex items-center gap-2 font-mono text-[10px] text-slate-600"><TrainFront size={13} /> Synthetic simulator feed · live updates via WebSocket</footer>
        </main>
      </div>
    </div>
  );
}
