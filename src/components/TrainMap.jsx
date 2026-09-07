import { MapContainer, Marker, Popup, Polyline, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import { MapPinned } from 'lucide-react';

const riskColorMap = {
  LOW: '#34d399',
  MEDIUM: '#fbbf24',
  HIGH: '#f87171',
};

const createMarkerIcon = (risk) => {
  const color = riskColorMap[risk] ?? '#38bdf8';

  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:${color}; box-shadow:0 0 0 6px rgba(15, 23, 42, 0.12);" class="marker-dot"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
};

export default function TrainMap({ trains, selectedTrainId, onSelectTrain }) {
  const selectedTrain = trains.find((train) => train.id === selectedTrainId) ?? trains[0];

  const stationPath = [
    [18.5204, 73.8567],
    [18.7503, 73.4074],
    [19.0762, 73.3181],
    [19.2356, 73.1305],
    [19.076, 72.8777],
  ];

  return (
    <div className="ops-panel ops-grid rounded-2xl p-3">
      <div className="mb-3 flex items-center justify-between gap-3 px-2">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-50">Live Train Network</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">Current simulated train positions</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
          <MapPinned className="h-3.5 w-3.5 text-sky-500" />
          Maharashtra corridor
        </div>
      </div>

      <div className="h-[420px] overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
        <MapContainer center={[18.951, 73.35]} zoom={8} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Polyline positions={stationPath} pathOptions={{ color: '#3b82f6', weight: 3, opacity: 0.8 }} />

          {trains.filter((train) => train.latitude !== null && train.longitude !== null).map((train) => (
            <Marker
              key={train.id}
              position={[train.latitude, train.longitude]}
              icon={createMarkerIcon(train.delayRisk)}
              eventHandlers={{
                click: () => onSelectTrain(train.id),
              }}
            >
              <Popup>
                <div className="space-y-1 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Train {train.number}</p>
                  <p>{train.origin} → {train.destination}</p>
                  <p>Speed: {train.currentSpeed ?? '--'} km/h</p>
                  <p>Delay: {train.currentDelay === null ? '--' : `${train.currentDelay >= 0 ? '+' : ''}${train.currentDelay} min`}</p>
                  <p>ETA: {train.predictedETA ?? '--'}</p>
                  <p>Risk: {train.delayRisk ?? '--'}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {selectedTrain && (
        <div className="mt-4 rounded-xl border border-sky-500/15 bg-sky-500/5 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Selected train</p>
              <h4 className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-50">Train {selectedTrain.number}</h4>
            </div>
            <span className="rounded-full border border-sky-500/20 bg-sky-500/10 px-2.5 py-1 text-xs font-medium text-sky-700 dark:text-sky-200">
              {selectedTrain.statusLabel}
            </span>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Current Speed</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selectedTrain.currentSpeed ?? '--'} km/h</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Current Delay</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selectedTrain.currentDelay === null ? '--' : `${selectedTrain.currentDelay >= 0 ? '+' : ''}${selectedTrain.currentDelay} min`}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Predicted ETA</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selectedTrain.predictedETA ?? '--'}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Delay Risk</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selectedTrain.delayRisk}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
