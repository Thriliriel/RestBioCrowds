
#f = g + h. The node with the lowest f is used as the next node to look at in the open list
#g = movement cost. For horizontal/vertical movement, value = 10. For diagonal movement, value = 14.
#h = estimated cost to reach the destination. Manhattan method can be used, where you calculate the total 
#number of squares moved horizontally and vertically to reach the target square from the current square, ignoring diagonal 
#movement, and ignoring any obstacles that may be in the way. OFC, multiply it for 10 (g cost)
#cell = position
#parent = parent node
#changePath = should agent change path when enter in sight?
class NodeClass:
	def __init__(self):
		self.f = self.g = self.h = 0
		self.changePath = False
		self.cell = None
		self.parent = None