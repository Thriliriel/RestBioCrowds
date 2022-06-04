import json
from AgentClass import AgentClass
from Vector3Class import Vector3
from CellClass import CellClass
from MarkerClass import MarkerClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass

class ParserTXT:

    def ParseConfigurationFile():
        marker_density = 0.65
        time_step = 0.02
        cell_size = 2
        map_size = Vector3(20, 20, 0)
        use_path_planing = True
        lineCount = 1
        for line in open("Input/config.txt", "r"):
            if '#' in line:
                continue
            if lineCount == 1:
                #markers density
                marker_density = float(line)
            elif lineCount == 2:
                #FPS
                time_step = float(line)
            elif lineCount == 3:
                #size of each square cell
                cell_size = int(line)
            elif lineCount == 4:
                #size of the scenario
                sp = line.split(',')
                map_size = Vector3(int(sp[0]), int(sp[1]), int(sp[2]))
            elif lineCount == 5:
                if line.lower() == 'false':
                    use_path_planing = False
            lineCount += 1
        return (marker_density, time_step, cell_size, map_size, use_path_planing)

    def ParseGoals():
        goals:list[GoalClass] = []

        for line in open("Input/goals.txt", "r"):
            if '#' in line:
                continue

            #create goal
            gl = line.split(',')
            goals.append(GoalClass(int(gl[0]), Vector3(float(gl[1]), float(gl[2]), float(gl[3]))))

        return goals
    
    def ParseAgents(goal_list, use_path_planning):
        
        agents:list[AgentClass] = []

        for line in open("Input/agents.txt", "r"):
            if '#' in line:
                continue

            #create agent
            ag = line.split(',')

            #find the goal with this id
            gl = None
            for i in range(0, len(goal_list)):
                if goal_list[i].id == int(ag[1]):
                    gl = goal_list[i]
                    break

            agents.append(AgentClass(int(ag[0]), gl, float(ag[2]), float(ag[3]), use_path_planning, Vector3(float(ag[4]), float(ag[5]), float(ag[6]))))
        return agents

    def ParseObstacles():
        
        obstacles:list[ObstacleClass] = []

        #read the obstacles file
        for line in open("Input/obstacles.txt", "r"):
            if '#' in line:
                continue

            #create obstacle
            ob = line.split(',')

            #if size is one, it is the id
            if len(ob) == 1:
                obstacles.append(ObstacleClass(int(ob[0])))
            #if size is three, it is one of the points
            elif len(ob) == 3:
                obstacles[len(obstacles)-1].AddPoint(Vector3(float(ob[0]), float(ob[1]), float(ob[2])))
            #else, something is wrong
            else:
                print("Error: input size is wrong!")
                exit
        return obstacles