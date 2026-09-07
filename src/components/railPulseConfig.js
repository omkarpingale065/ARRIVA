import { Activity, BarChart3, Clock3, Database, FileClock, Gauge, Map } from 'lucide-react';

export const railPulseGroups = [
  { label: 'MONITOR', items: [['Control Dashboard', '/dashboard', Gauge], ['Live Train Map', '/live-train-map', Map], ['Route Sections', '/route-sections', Activity]] },
  { label: 'FORECAST', items: [['ETA Predictions', '/eta-predictions', Clock3], ['Delay Attribution', '/delay-attribution', BarChart3], ['Model Accuracy', '/model-accuracy', Gauge]] },
  { label: 'DATA', items: [['Ingestion Feeds', '/ingestion-feeds', Database], ['Historical Logs', '/historical-logs', FileClock]] },
];
