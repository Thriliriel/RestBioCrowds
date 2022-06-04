import json
from AgentClass import AgentClass
from Vector3Class import Vector3
from CellClass import CellClass
from MarkerClass import MarkerClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass

class ParserJSON:
	#def ParseJsonContent(str_content:str):
	def ParseJsonContent(content):
		goals:list[GoalClass] = []
		agents:list[AgentClass] = []
		obstacles:list[ObstacleClass] = []

		#content = json.loads(str_content)

		#terrain size
		_terrain_size = content['terrains'][0]['terrain_size']
		mapSize = Vector3(int(_terrain_size[0]),
			int(_terrain_size[2]), 0)

		#goals
		for _goal in content['goals']:
			_pos = _goal['position']
			goals.append(GoalClass(len(goals), Vector3(_pos[0], _pos[2], 0.0)))

		#agents
		for _agent in content['agents']:
			_pos = _agent['position']
			_goalID = _agent['goal_list'][0]

			agents.append(AgentClass(id=len(agents), 
				goal=goals[_goalID], 
				radius=1.0, 
				maxSpeed=1.2, 
				usePathPlanning=True, 
				position=Vector3(_pos[0],_pos[2],0.0)))

		#obstacles
		for _obstacles in content['obstacles']:
			obstacles.append(ObstacleClass(len(obstacles)))
			for _point in _obstacles['point_list']:
				obstacles[len(obstacles)-1].AddPoint(Vector3(float(_point[0]), float(_point[1]), float(_point[2])))
        
		return (mapSize, goals, agents, obstacles)

	def ParseFile(file_path:str):
		print("use a file: " + file_path)
		file = open(file_path,'r', encoding='utf8')
		return ParserJSON.ParseJsonContent(file.read())