class ControlModule:
    def __init__(self):
        self.state = "idle"
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def unsubscribe(self, observer):
        self.observers.remove(observer)

    def notify_observers(self, event):
        for observer in self.observers:
            observer.update(event)

    def start_task(self, task_name):
        self.state = "running"
        self.notify_observers({"event": "task_started", "task": task_name})

    def complete_task(self, task_name, success=True):
        self.state = "idle" if success else "failed"
        self.notify_observers({"event": "task_completed", "task": task_name, "success": success})
