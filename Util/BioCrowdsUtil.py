from typing import TYPE_CHECKING
from AgentClass import AgentClass
from CellClass import CellClass
from GoalClass import GoalClass
from Vector3Class import Vector3


if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass

def parse_config_file(bio_crowds:'BioCrowdsClass', file_path:str):
    print("Parsing Config File")
    _lineCount = 1
    for line in open(file_path, "r"):
        if '#' in line:
            continue
        if _lineCount == 1:
            #markers density
            bio_crowds.PORC_QTD_Marcacoes = float(line)
        elif _lineCount == 2:
            #FPS
            bio_crowds.time_step = float(line)
        elif _lineCount == 3:
            #size of each square cell
            bio_crowds.cell_size = int(line)
        elif _lineCount == 4:
            #size of the scenario (comes from json, so no needed)
            sp = line.split(',')
            bio_crowds.map_size = Vector3(int(sp[0]), int(sp[1]), int(sp[2]))
        elif _lineCount == 5:
            #using path planning?
            if line.lower() == 'false':
                bio_crowds.path_planning = False
            else:
                bio_crowds.path_planning = True

        _lineCount += 1

def parse_reference_simulation(reference_data)->dict:
    print("Parsing Reference Agent")
    ref_agent = {
        "response": reference_data,
        "total_simulation_time": reference_data["2"],
        "agents_distance_walked": list(reference_data["3"].values()),
        "total_average_distance_walked": reference_data["4"],
        "agents_speed": list(reference_data["5"].values()),
        "total_average_speed": reference_data["6"],
        "agents_average_density": list(reference_data["7"].values()),
        "total_average_density": reference_data["8"],
        "agents_average_simulation_time": reference_data["9"],
        "metric": reference_data["10"]
    }
    return ref_agent

def open_result_file(output_dir:str, ip:str, terrains_data):
    cSVPath = output_dir + "/resultFile_" + (ip.replace(":", "_")) + ".csv"
    if terrains_data == 'db':
        return open(cSVPath, "a")
    return open(cSVPath, "w")

def save_cells_file(output_dir:str, ip:str, cells_data:list[CellClass]):
    resultCellsFile = open(output_dir + "/resultCellFile_" + ip.replace(":", "_") + ".txt", "w")
    thisX = 0
    firstColumn = True
    for _cell in cells_data:
        if thisX != _cell.position.x:
            thisX = _cell.position.x
            resultCellsFile.write("\n")
            firstColumn = True

        if firstColumn:
            resultCellsFile.write(str(len(_cell.passedAgents)))
            firstColumn = False
        else:
            resultCellsFile.write("," + str(len(_cell.passedAgents)))


    resultCellsFile.close()



def find_reference_agent(agents:list[AgentClass], goals:list[GoalClass])->AgentClass:
    ref_agent:AgentClass = agents[0]   
    maxDist = 0
    for ag in agents:
        for gl in goals:
            dst = Vector3.Distance(ag.position, gl.position)
            if dst > maxDist:
                maxDist = dst
                ref_agent = ag
    return ref_agent

def parse_agent_position_by_frame(output_dir:str, ip:str):
    #dictionary to calculate speeds, distances and densities later
    agentPositionsByFrame:dict[int,list[Vector3]] = {}
    x_data:list[float] = []
    y_data:list[float] = []
    #open file to read
    #id, x, y, z
    #for line in open("resultFile.csv"):
    for line in open(output_dir + "/resultFile_" + ip.replace(":", "_") + ".csv"):
        csv_row = line.split(';')

        #parse
        agentId = int(csv_row[0])
        agentX = float(csv_row[1])
        agentY = float(csv_row[2])
        agentZ = float(csv_row[3])

        #points for the trajectories
        x_data.append(agentX)
        y_data.append(agentY)

        #agents positions by frame, for density, distance and velocities
        #if not exists yet, create the list
        if agentId not in agentPositionsByFrame:
            agentPositionsByFrame[agentId] = []

        agentPositionsByFrame[agentId].append(Vector3(agentX, agentY, agentZ))
    return agentPositionsByFrame, x_data, y_data