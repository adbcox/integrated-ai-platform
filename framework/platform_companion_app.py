class PlatformCompanionApp:
    def __init__(self, name: str):
        self.name = name

    def start(self):
        print(f"Starting {self.name}...")

    def stop(self):
        print(f"Stopping {self.name}...")

    def restart(self):
        self.stop()
        self.start()

    def status(self):
        print(f"{self.name} is running.")

    def update(self):
        print(f"Updating {self.name}...")
