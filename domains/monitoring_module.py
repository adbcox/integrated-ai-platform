class MonitoringModule:
    def __init__(self):
        self.metrics = {}

    def record_metric(self, name: str, value: float):
        self.metrics[name] = value

    def get_metrics(self) -> dict:
        return self.metrics

    def reset_metrics(self):
        self.metrics.clear()

    def log_metrics(self):
        for name, value in self.metrics.items():
            print(f"{name}: {value}")
