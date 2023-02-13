# importing the matplotlib library
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from AgentClass import AgentClass

def visualize_agent_paths_python(agents:list[AgentClass], id:int):
	# values on x-axis
	x = []
	# values on y-axis
	y = []

	mapSizeX = 30
	mapSizeY = 30
	figTrajectories = make_subplots(rows=1, cols=1)
	figTrajectories.update_layout(title = f"Agent Path Planning Python - Sim {id})")
	figTrajectories.update_xaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')
	figTrajectories.update_yaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')

	#open file to read
	for agent in agents:
		coord = []
		coord.append([agent.position.x, agent.position.y])
		for cell in agent.path:
			coord.append([cell.position.x, cell.position.y])
		#coord.append(coord[0]) #repeat the first point to create a 'closed loop'
		xs, ys = zip(*coord) #create lists of x and y values
		# plt.plot(xs,ys)
		figTrajectories.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False))
	
		
	#x = [3, 1, 2, 5]
	#y = [5, 2, 4, 7]

	figTrajectories.show()
	# plt.axis([0, mapSizeX, 0, mapSizeY])

	# #for i, j in zip(x, y):
	# #   plt.text(i, j+0.5, '({}, {})'.format(i, j))

	# plt.show()

def visualize_agent_paths_unity(agents, id:int):	
	# values on x-axis
	x = []
	# values on y-axis
	y = []

	mapSizeX = 30
	mapSizeY = 30
	figTrajectories = make_subplots(rows=1, cols=1)
	figTrajectories.update_layout(title = f"Agent Path Planning Unity - Sim {id})")
	figTrajectories.update_xaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')
	figTrajectories.update_yaxes(range = [0, 30], showgrid=True, gridwidth=1, gridcolor='Gray')

	#open file to read
	for agent in agents:
		coord = []
		coord.append([agent["position"][0], agent["position"][2]])
		for point in agent["path_planning_goals"]:
			coord.append([point[0], point[2]])
		#coord.append(coord[0]) #repeat the first point to create a 'closed loop'
		xs, ys = zip(*coord) #create lists of x and y values
		# plt.plot(xs,ys)
		figTrajectories.add_trace(go.Scatter(x = xs, y = ys, mode="lines", showlegend=False))
	
		
	#x = [3, 1, 2, 5]
	#y = [5, 2, 4, 7]

	figTrajectories.show()
	# plt.axis([0, mapSizeX, 0, mapSizeY])

	# #for i, j in zip(x, y):
	# #   plt.text(i, j+0.5, '({}, {})'.format(i, j))

	# plt.show()

if __name__ == "__main__":
	pass
   #visualize_agent_paths("24131 PM586")