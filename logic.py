#Object Oriented Project

class Logic:
    def __init__(self):
        self.result = None

class Workout:
    def __init__(self, name, duration, intensity):
        self.name = name
        self.duration = duration  # in minutes
        self.intensity = intensity  # e.g., 'low', 'medium', 'high'

    def calculate_calories_burned(self):
        intensity_factor = {
            'low': 4,
            'medium': 8,
            'high': 12
        }
        return self.duration * intensity_factor.get(self.intensity, 0)

a = Workout("Running", 30, "high")
print(a.calculate_calories_burned())