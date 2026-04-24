class FailurePatterns:
    """Tracks failure patterns in task executions."""

    def __init__(self):
        self.patterns = {}

    def add_failure(self, task_type: str, error_message: str) -> None:
        if task_type not in self.patterns:
            self.patterns[task_type] = []
        self.patterns[task_type].append(error_message)

    def get_patterns(self, task_type: str) -> list[str]:
        return self.patterns.get(task_type, [])

    def get_all_patterns(self) -> dict[str, list[str]]:
        return self.patterns
