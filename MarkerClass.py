
from Vector3Class import Vector3


class MarkerClass:
    def __init__(self, position):
        self.position:Vector3 = position
        self.minDistance = 5
        self.taken = False
        self.owner = None

    def ResetMarker(self):
        self.minDistance = 5
        self.taken = False
        self.owner = None