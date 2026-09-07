import { useEffect, useMemo, useState } from 'react';
import RailPulseShell from '../components/RailPulseShell';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrains } from '../services/api';
export default function RouteSections() {
  const [trains, setTrains] = useState([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  useEffect(() => { getTrains().then(setTrains).catch(() => setError('Unable to load route section data.')).finally(() => setLoading(false)); }, []);
  const sections = useMemo(() => Object.values(trains.reduce((all, train) => { const key = train.routeSection || '--'; const item = all[key] ?? { key, trains: [], delay: 0 }; item.trains.push(train); item.delay += Number.isFinite(train.predictedDelay) ? train.predictedDelay : 0; all[key] = item; return all; }, {})), [trains]);
  return <RailPulseShell title="Route Sections" subtitle="Live section occupancy and delay summary">{loading ? <LoadingState /> : error ? <ErrorState message={error} /> : <div className="grid gap-4 md:grid-cols-2">{sections.map((section) => <section key={section.key} className="rounded-xl border border-[#1c2e47] bg-[#101b2d] p-5"><h2 className="font-mono text-lg text-slate-100">{section.key}</h2><p className="mt-2 text-sm text-slate-500">{section.trains.length} train{section.trains.length === 1 ? '' : 's'} in section</p><p className="mt-5 font-mono text-2xl text-amber-300">{section.trains.length ? (section.delay / section.trains.length).toFixed(1) : '--'} min</p><p className="mt-1 text-xs text-slate-500">average predicted delay</p></section>)}</div>}</RailPulseShell>;
}
