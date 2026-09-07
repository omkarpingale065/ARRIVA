const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

const request = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Preserve the HTTP status when the server does not return JSON.
    }
    throw new Error(detail);
  }

  return response.json();
};

const isFiniteNumber = (value) => Number.isFinite(Number(value));

export const formatETA = (value) => {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '--';
  return new Intl.DateTimeFormat('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
};

const formatMinutes = (value, { signed = false } = {}) => {
  if (!isFiniteNumber(value)) return '--';
  const minutes = Number(value);
  return `${signed && minutes >= 0 ? '+' : ''}${minutes} min`;
};

const formatStationTimeline = (state, eta) => {
  const upcoming = eta?.upcoming_station_etas ?? [];
  return [
    {
      name: state.current_station ?? '--',
      scheduled: 'Current',
      predicted: formatETA(state.simulated_at),
      predictedAt: state.simulated_at ?? null,
      delay: formatMinutes(state.current_delay_minutes, { signed: true }),
      status: state.status === 'dwelling' ? 'current' : 'completed',
    },
    ...upcoming.map((station) => ({
      name: station.station,
      scheduled: '--',
      predicted: formatETA(station.predicted_arrival),
      predictedAt: station.predicted_arrival ?? null,
      delay: 'Live prediction',
      status: 'upcoming',
    })),
  ];
};

export const normalizeTrain = (state, eta = null, history = []) => ({
  id: state.train_id ?? '',
  number: state.train_number ?? '--',
  name: state.train_name ?? '--',
  origin: state.origin ?? '--',
  destination: state.destination ?? '--',
  originCode: state.origin_code ?? state.origin ?? '--',
  destinationCode: state.destination_code ?? state.destination ?? '--',
  currentStation: state.current_station ?? '--',
  nextStation: state.next_station ?? '--',
  currentSpeed: isFiniteNumber(state.current_speed_kmh) ? Number(state.current_speed_kmh) : null,
  currentDelay: isFiniteNumber(state.current_delay_minutes) ? Number(state.current_delay_minutes) : null,
  distanceRemaining: isFiniteNumber(state.distance_remaining_km) ? Number(state.distance_remaining_km) : null,
  predictedETA: formatETA(eta?.predicted_arrival ?? state.scheduled_destination_arrival),
  predictedArrival: eta?.predicted_arrival ?? state.scheduled_destination_arrival,
  etaLowerBound: eta?.eta_lower_bound ?? null,
  etaUpperBound: eta?.eta_upper_bound ?? null,
  predictedDelay: isFiniteNumber(eta?.predicted_delay_minutes)
    ? Number(eta.predicted_delay_minutes)
    : (isFiniteNumber(state.current_delay_minutes) ? Number(state.current_delay_minutes) : null),
  scheduledDestinationArrival: state.scheduled_destination_arrival,
  confidencePercent: isFiniteNumber(eta?.confidence_percent) ? Number(eta.confidence_percent) : null,
  progressPercent: isFiniteNumber(state.progress_ratio) ? Math.round(Number(state.progress_ratio) * 100) : null,
  delayRisk: eta?.risk_level ?? 'LOW',
  statusLabel: (state.status ?? '--').replaceAll('_', ' '),
  latitude: isFiniteNumber(state.latitude) ? Number(state.latitude) : null,
  longitude: isFiniteNumber(state.longitude) ? Number(state.longitude) : null,
  routeSection: state.route_section ?? '--',
  weatherCondition: state.weather_condition ?? '--',
  trackCondition: state.track_condition ?? '--',
  stations: formatStationTimeline(state, eta),
  factors: (eta?.delay_factors ?? []).map((factor) => ({
    name: (factor.factor ?? 'unknown factor').replaceAll('_', ' '),
    detail: factor.detail ?? '--',
    impact: isFiniteNumber(factor.contribution_minutes) ? Number(factor.contribution_minutes) : null,
  })),
  predictionHistory: history,
  etaHistory: history.map((item) => ({
    time: formatETA(item.predicted_arrival),
    eta: isFiniteNumber(item.predicted_delay_minutes) ? Number(item.predicted_delay_minutes) : null,
  })),
  speedHistory: history.map((item) => ({
    time: formatETA(item.timestamp),
    speed: isFiniteNumber(item.current_speed) ? Number(item.current_speed) : null,
  })),
});

export const mergeLiveUpdate = (train, update) => {
  if (!train || train.id !== update.train_id) return train;
  return {
    ...train,
    latitude: update.latitude,
    longitude: update.longitude,
    currentSpeed: isFiniteNumber(update.current_speed) ? Number(update.current_speed) : train.currentSpeed,
    currentDelay: isFiniteNumber(update.current_delay) ? Number(update.current_delay) : train.currentDelay,
    distanceRemaining: isFiniteNumber(update.distance_remaining) ? Number(update.distance_remaining) : train.distanceRemaining,
    predictedDelay: isFiniteNumber(update.predicted_delay) ? Number(update.predicted_delay) : train.predictedDelay,
    predictedETA: formatETA(update.predicted_arrival),
    predictedArrival: update.predicted_arrival ?? train.predictedArrival,
    delayRisk: update.delay_risk ?? train.delayRisk,
    nextStation: update.next_station ?? train.nextStation,
    confidencePercent: isFiniteNumber(update.confidence_percent) ? Number(update.confidence_percent) : train.confidencePercent,
    progressPercent: isFiniteNumber(update.progress_percent) ? Number(update.progress_percent) : train.progressPercent,
  };
};

export const getTrains = async () => {
  const states = await request('/api/trains');
  return Promise.all(states.map(async (state) => {
    const [eta, historyResponse] = await Promise.all([
      request(`/api/trains/${state.train_id}/eta`),
      request(`/api/trains/${state.train_id}/history`),
    ]);
    return normalizeTrain(state, eta, historyResponse.predictions ?? []);
  }));
};

export const getTrainById = async (trainId) => {
  const [state, eta, historyResponse] = await Promise.all([
    request(`/api/trains/${trainId}`),
    request(`/api/trains/${trainId}/eta`),
    request(`/api/trains/${trainId}/history`),
  ]);
  return normalizeTrain(state, eta, historyResponse.predictions);
};

export const getTrainETA = async (trainId) => request(`/api/trains/${trainId}/eta`);

export const getDelayRisk = async (trainId) => request(`/api/trains/${trainId}/delay-risk`);

export const getTrainHistory = async (trainId) => {
  const response = await request(`/api/trains/${trainId}/history`);
  return response.predictions;
};

export const getModelComparison = async () => request('/api/model/comparison');

export const runSimulation = async ({ trainId, additionalDelay }) => {
  const result = await request('/api/simulation/advance', {
    method: 'POST',
    body: JSON.stringify({ train_id: trainId, minutes: Math.max(1, Number(additionalDelay) || 1) }),
  });
  const train = normalizeTrain(result.train, result.eta);
  return {
    currentETA: formatETA(result.eta.scheduled_destination_arrival),
    simulatedETA: formatETA(result.eta.predicted_arrival),
    additionalDelay: result.eta.predicted_delay_minutes,
    affectedStations: train.stations.slice(1).map((station) => ({
      station: station.name,
      impact: station.delay,
    })),
    simulatedDelay: result.eta.predicted_delay_minutes,
    train,
  };
};

export { API_BASE_URL };
