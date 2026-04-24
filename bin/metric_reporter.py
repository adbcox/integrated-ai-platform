class MetricReporter:
    """Class to generate reports based on metrics."""

    def __init__(self, data: dict):
        self.data = data

    def generate_report(self) -> str:
        """Generate a plain text report from the provided data."""
        report_lines = []
        for key, value in self.data.items():
            report_lines.append(f"{key}: {value}")
        return "\n".join(report_lines)

    def generate_json_report(self) -> str:
        """Generate a JSON formatted report from the provided data."""
        import json
        return json.dumps(self.data, indent=4)

    def save_report_to_file(self, file_path: str, format: str = 'txt') -> None:
        """Save the report to a file in the specified format (txt or json)."""
        if format == 'txt':
            report = self.generate_report()
        elif format == 'json':
            report = self.generate_json_report()
        else:
            raise ValueError("Unsupported format. Use 'txt' or 'json'.")
        
        with open(file_path, 'w') as file:
            file.write(report)

if __name__ == "__main__":
    sample_data = {
        "metric1": 10,
        "metric2": 20,
        "metric3": 30
    }
    reporter = MetricReporter(sample_data)
    print(reporter.generate_report())
