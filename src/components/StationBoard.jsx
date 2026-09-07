import { formatETA } from '../services/api';
import useNextArrival from '../hooks/useNextArrival';

const valueOrDash = (value) => value === null || value === undefined || value === '' ? '--' : value;
const finite = (value) => Number.isFinite(Number(value));

export default function StationBoard({ trains, clock = new Date(), compact = false }) {
  const train = useNextArrival(trains);
  if (!train) {
    return (
      <section className="rounded-3xl border border-[#1c2e47] border-l-4 border-sky-400 bg-[#101b2d] p-6 text-center text-slate-400">
        Station Control: waiting for live train data...
      </section>
    );
  }

  const delay = finite(train.predictedDelay) ? Number(train.predictedDelay) : train.currentDelay;
  const status = train.delayRisk === 'HIGH' || (finite(delay) && delay > 5) ? 'DELAYED' : 'ON TIME';
  const delayTone = !finite(delay) || delay === 0 ? 'text-slate-300' : delay > 0 ? 'text-rose-300' : 'text-emerald-300';

  return (
    <section className={`rounded-3xl border border-[#1c2e47] border-l-4 border-sky-400 bg-[#101b2d] text-center ${compact ? 'p-6' : 'p-6 sm:p-10'}`}>
      <div className="flex items-center justify-between text-left">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-sky-300">Station Control</p>
          <p className="mt-2 text-sm text-slate-400">Live synthetic operations feed</p>
        </div>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          Next Arrival · {clock.toLocaleTimeString('en-GB')}
        </p>
      </div>
      <div className="mt-8">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Train {valueOrDash(train.number)}</p>
        <h2 className="mt-3 text-3xl font-semibold text-slate-50">{valueOrDash(train.name)}</h2>
        <p className="mt-2 text-lg text-slate-300">{valueOrDash(train.origin)} → {valueOrDash(train.destination)}</p>
      </div>
      <div className="mt-8 grid gap-6 sm:grid-cols-3">
        <div><p className="text-xs uppercase tracking-widest text-slate-400">Predicted ETA</p><p className="mt-2 text-4xl font-semibold text-sky-200">{formatETA(train.predictedArrival)}</p></div>
        <div><p className="text-xs uppercase tracking-widest text-slate-400">Delay</p><p className={`mt-2 text-4xl font-semibold ${delayTone}`}>{finite(delay) ? `${delay >= 0 ? '+' : ''}${delay.toFixed(1)} min` : '--'}</p></div>
        <div><p className="text-xs uppercase tracking-widest text-slate-400">Status</p><p className={`mt-2 text-4xl font-semibold ${status === 'DELAYED' ? 'text-rose-300' : 'text-emerald-300'}`}>{status}</p></div>
      </div>
      <p className="mt-8 text-sm text-slate-400">
        Current station: {valueOrDash(train.currentStation)} · Platform: 1 · Scheduled: {formatETA(train.scheduledDestinationArrival)}
      </p>
    </section>
  );
}
