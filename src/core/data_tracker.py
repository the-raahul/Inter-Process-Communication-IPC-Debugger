class DataTracker:
    def __init__(self):
        self.events = []

    def track(self, source, destination, data):
        self.events.append({"source": source, "destination": destination, "data": data})

    def get_events(self):
        return self.events