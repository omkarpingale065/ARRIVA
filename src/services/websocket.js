const configuredSocketUrl = import.meta.env.VITE_WS_URL?.trim();
const defaultSocketUrl = `${(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000')
  .replace(/^http/, 'ws')}/ws/trains?interval_seconds=2&advance_minutes=5`;

export const websocketConfig = {
  enabled: true,
  url: configuredSocketUrl || defaultSocketUrl,
};

export const createTrainSocket = ({
  onMessage,
  onError,
  onStatus,
  reconnectDelay = 2000,
} = {}) => {
  let socket;
  let reconnectTimer;
  let stopped = false;

  const connect = () => {
    if (stopped) return;
    onStatus?.('connecting');
    socket = new WebSocket(websocketConfig.url);

    socket.onopen = () => {
      window.dispatchEvent(new CustomEvent('arriva:connection', { detail: 'connected' }));
      onStatus?.('connected');
    };
    socket.onmessage = (event) => {
      try {
        onMessage?.(JSON.parse(event.data));
      } catch (error) {
        onError?.(error);
      }
    };
    socket.onerror = (event) => onError?.(event);
    socket.onclose = () => {
      window.dispatchEvent(new CustomEvent('arriva:connection', { detail: 'disconnected' }));
      onStatus?.('disconnected');
      if (!stopped) reconnectTimer = window.setTimeout(connect, reconnectDelay);
    };
  };

  connect();

  return {
    disconnect: () => {
      stopped = true;
      window.clearTimeout(reconnectTimer);
      if (!socket) return;
      if (socket.readyState === WebSocket.CONNECTING) {
        socket.onopen = () => socket.close();
      } else {
        socket.close();
      }
    },
  };
};
