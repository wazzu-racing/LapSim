# Instances of this class are saved within users' local files to store track/lap data.
class LapData():
    def __init__(self, points):
        self.points = points
        self.car = None
        self.generated_track = None
        self.file_location = ""