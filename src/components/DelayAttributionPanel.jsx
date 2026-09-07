import { Activity, Gauge, Radio, TrainFront } from 'lucide-react';

const icons = [Activity, Gauge, Radio, TrainFront];

export default function DelayAttributionPanel({ trains }) {
  const grouped = trains.flatMap((train) => train.factors.map((factor) => ({ ...factor, trainId: train.id }))).reduce((result, factor) => {
    const key = factor.name || 'unknown factor';
    const current = result[key] ?? { ...factor, count: 0, total: 0 };
    current.count += 1;
    current.total += Number.isFinite(factor.impact) ? factor.impact : 0;
    result[key] = current;
    return result;
  }, {});
  const factors = Object.values(grouped);
  return (
    <section className="rounded-xl border border-slate-700/70 bg-[#101b2d]">
      <div className="border-b border-slate-700/70 px-5 py-4"><h2 className="font-semibold text-slate-100">Delay Attribution — Section Wide</h2><p className="mt-1 text-xs text-slate-500">Aggregated from current live train factors</p></div>
      <div className="divide-y divide-slate-800">
        {factors.length ? factors.map((factor, index) => {
          const Icon = icons[index % icons.length];
          return <div key={factor.name} className="flex items-center gap-4 px-5 py-4"><div className="grid h-9 w-9 place-items-center rounded-full bg-amber-400/10 text-amber-300"><Icon size={16} /></div><div className="min-w-0 flex-1"><p className="capitalize text-sm font-medium text-slate-200">{factor.name}</p><p className="mt-1 truncate text-xs text-slate-500">{factor.detail}</p></div><div className="text-right"><p className="font-mono text-xs text-slate-400">{factor.count} train{factor.count === 1 ? '' : 's'}</p><p className="mt-1 font-mono text-sm text-amber-300">{factor.total ? `${(factor.total / factor.count).toFixed(1)} min avg` : '--'}</p></div></div>;
        }) : <p className="px-5 py-8 text-sm text-slate-500">No delay factors available.</p>}
      </div>
    </section>
  );
}
