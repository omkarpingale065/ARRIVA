import { useEffect, useState } from 'react';
import RailPulseShell from '../components/RailPulseShell';
import TrainMap from '../components/TrainMap';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrains, mergeLiveUpdate } from '../services/api';
import { createTrainSocket } from '../services/websocket';
export default function LiveTrainMap() {
  const [trains, setTrains] = useState([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [selected, setSelected] = useState('');
  useEffect(() => { let active = true; getTrains().then((data) => { if (active) { setTrains(data); setSelected(data[0]?.id ?? ''); } }).catch(() => active && setError('Unable to load live train positions.')).finally(() => active && setLoading(false)); const stream = createTrainSocket({ onMessage: (update) => setTrains((current) => current.map((train) => mergeLiveUpdate(train, update))) }); return () => { active = false; stream.disconnect(); }; }, []);
  return <RailPulseShell title="Live Train Map" subtitle="Current positions from the simulator and live WebSocket stream">{loading ? <LoadingState /> : error ? <ErrorState message={error} /> : <TrainMap trains={trains} selectedTrainId={selected} onSelectTrain={setSelected} />}</RailPulseShell>;
}
