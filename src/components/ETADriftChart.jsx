import { Area, AreaChart, CartesianGrid, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const timestamp = (value) => {
  if (!value) return null;
  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? null : parsed;
};

export default function ETADriftChart({ train }) {
  const data = train?.predictionHistory?.length
    ? train.predictionHistory.slice(-8).map((item) => {
      const eventTime = timestamp(item.timestamp);
      const predicted = timestamp(item.predicted_arrival);
      const scheduled = timestamp(item.scheduled_destination_arrival);
      return {
        stop: eventTime === null ? '--' : new Date(eventTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        predicted,
        scheduled,
        lower: timestamp(item.eta_lower_bound),
        upper: timestamp(item.eta_upper_bound),
      };
    })
    : (train?.stations ?? []).slice(0, 6).map((station, index) => ({
      stop: station.name ?? `Stop ${index + 1}`,
      predicted: timestamp(station.predictedAt),
      scheduled: null,
      lower: null,
      upper: null,
    }));
  const safeData = data.length ? data : [{ stop: 'No stops', predicted: null, scheduled: null, lower: null, upper: null }];
  return (
    <section className="rounded-xl border border-slate-700/70 bg-[#101b2d]">
      <div className="border-b border-slate-700/70 px-5 py-4"><h2 className="font-semibold text-slate-100">Predicted ETA Drift</h2><p className="mt-1 text-xs text-slate-500">{train ? `Selected train ${train.number}` : 'Waiting for train data'}</p></div>
      <div className="h-[310px] p-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={safeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#1c2e47" strokeDasharray="3 3" />
            <XAxis dataKey="stop" tick={{ fill: '#8c9bb5', fontSize: 10 }} />
            <YAxis tick={{ fill: '#8c9bb5', fontSize: 10 }} tickFormatter={(value) => new Date(value).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })} />
            <Tooltip contentStyle={{ background: '#0d1727', border: '1px solid #1c2e47', color: '#e8ecf1' }} />
            <Legend wrapperStyle={{ color: '#8c9bb5', fontSize: 11 }} />
            <Area type="monotone" dataKey="upper" stackId="band" stroke="none" fill="#f0a93b" fillOpacity={0.12} name="Confidence band" />
            <Area type="monotone" dataKey="lower" stackId="band" stroke="none" fill="#101b2d" fillOpacity={1} name="" />
            <Line type="monotone" dataKey="scheduled" stroke="#57667f" strokeDasharray="5 5" dot={false} name="Scheduled" />
            <Line type="monotone" dataKey="predicted" stroke="#f0a93b" strokeWidth={2} dot={{ r: 3 }} name="Predicted" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
