class ObstacleClass:
    def __init__(self, id):
        self.id = id
        self.points = []

    def AddPoint(self, point):
        self.points.append(point)