from CellClass import CellClass
from Vector3Class import Vector3

class GoalClass:
	def __init__(self, id, position:Vector3):
		self.position:Vector3 = position
		self.id = id
		self.cell:CellClass = None # type: ignore