class DashboardPlatform:
    def __init__(self):
        self.data = {}

    def update_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data.get(key)

    def display(self):
        for key, value in self.data.items():
            print(f"{key}: {value}")
