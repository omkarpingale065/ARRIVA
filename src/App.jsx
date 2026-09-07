import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TrainMonitoring from './pages/TrainMonitoring';
import TrainDetails from './pages/TrainDetails';
import DelayIntelligence from './pages/DelayIntelligence';
import Simulation from './pages/Simulation';
import LiveTrainMap from './pages/LiveTrainMap';
import RouteSections from './pages/RouteSections';
import ETAPredictions from './pages/ETAPredictions';
import DelayAttribution from './pages/DelayAttribution';
import ModelAccuracy from './pages/ModelAccuracy';
import IngestionFeeds from './pages/IngestionFeeds';
import HistoricalLogs from './pages/HistoricalLogs';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/station-display" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trains" element={<TrainMonitoring />} />
        <Route path="/trains/:trainId" element={<TrainDetails />} />
        <Route path="/delay-intelligence" element={<DelayIntelligence />} />
        <Route path="/simulation" element={<Simulation />} />
        <Route path="/live-train-map" element={<LiveTrainMap />} />
        <Route path="/route-sections" element={<RouteSections />} />
        <Route path="/eta-predictions" element={<ETAPredictions />} />
        <Route path="/delay-attribution" element={<DelayAttribution />} />
        <Route path="/model-accuracy" element={<ModelAccuracy />} />
        <Route path="/ingestion-feeds" element={<IngestionFeeds />} />
        <Route path="/historical-logs" element={<HistoricalLogs />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
