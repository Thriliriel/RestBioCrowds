from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from AgentClass import AgentClass
from Vector3Class import Vector3


class MarkerClass:
    def __init__(self, position):
        self.position:Vector3 = position
        self.minDistance = 5.0
        self.taken = False
        self.owner:'AgentClass' = None # type: ignore

    def ResetMarker(self):
        self.minDistance = 5.0
        self.taken = False
        self.owner = None # type: ignore