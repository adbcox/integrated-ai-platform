class NiimbotPrinter:
    def __init__(self, name: str):
        self.name = name

    def print_greeting(self):
        print(f"Hello from {self.name}!")

    def print_message(self, message: str):
        print(f"{self.name} says: {message}")

    def print_error(self, error: str):
        print(f"Error from {self.name}: {error}")
