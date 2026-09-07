from backend.ingestion import SimulatedTrainDataSource, WeatherDataSource
from simulator import TrainSimulator


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class HttpClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.response


def test_simulated_adapter_preserves_simulator_states():
    simulator = TrainSimulator(seed=1)
    simulator.add_train("T1", "1", "Test")
    source = SimulatedTrainDataSource(simulator)
    assert source.get_train_state("T1") == simulator.get_train_state("T1")


def test_weather_source_normalizes_open_meteo_response():
    client = HttpClient(
        Response(
            {
                "current": {
                    "weather_code": 63,
                    "temperature_2m": 25,
                    "precipitation": 1.2,
                    "wind_speed_10m": 14,
                }
            }
        )
    )
    weather = WeatherDataSource(http_client=client, timeout_seconds=1).get_weather(
        18.5, 73.8
    )
    assert weather.condition == "rain"
    assert not weather.is_fallback
    assert client.calls[0][1]["timeout"] == 1


def test_weather_source_falls_back_on_network_failure():
    weather = WeatherDataSource(http_client=HttpClient(error=TimeoutError())).get_weather(
        18.5, 73.8
    )
    assert weather.condition == "clear"
    assert weather.is_fallback
