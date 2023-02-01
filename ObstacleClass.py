from Vector3Class import Vector3

class ObstacleClass:
    def __init__(self, id):
        self.id = id
        self.points:list[Vector3] = []

    def AddPoint(self, point:Vector3):
        self.points.append(point)