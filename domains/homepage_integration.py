class HomepageIntegration:
    def __init__(self):
        self.data = {}

    def update_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data.get(key)

    def clear_data(self):
        self.data.clear()

    def has_data(self, key):
        return key in self.data

    def __str__(self):
        return str(self.data)
