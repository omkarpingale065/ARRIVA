import { useEffect, useState } from 'react';
import RailPulseShell from '../components/RailPulseShell';
import LiveTrainsTable from '../components/LiveTrainsTable';
import ETADriftChart from '../components/ETADriftChart';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getTrains } from '../services/api';
export default function ETAPredictions() { const [trains, setTrains] = useState([]); const [selected, setSelected] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); useEffect(() => { getTrains().then((data) => { setTrains(data); setSelected(data[0]?.id ?? ''); }).catch(() => setError('Unable to load ETA predictions.')).finally(() => setLoading(false)); }, []); const train = trains.find((item) => item.id === selected) ?? trains[0]; return <RailPulseShell title="ETA Predictions" subtitle="Predicted and scheduled arrivals with prediction history">{loading ? <LoadingState /> : error ? <ErrorState message={error} /> : <div className="space-y-4"><LiveTrainsTable trains={trains} selectedTrainId={train?.id} onSelect={setSelected} /><ETADriftChart train={train} /></div>}</RailPulseShell>; }
