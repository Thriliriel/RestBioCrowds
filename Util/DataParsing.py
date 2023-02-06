import os
from typing import TYPE_CHECKING
from CellClass import CellClass
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

def parse_reference_simulation_data(reference_data)->dict:
    print("Parsing Reference Agent")
    ref_agent = {
        "response": reference_data,
        "total_simulation_time": reference_data["2"],
        "agents_distance_walked": list(reference_data["3"].values()),
        "total_average_distance_walked": reference_data["4"],
        "agents_speed": list(reference_data["5"].values()),
        "total_average_speed": reference_data["6"],
        "total_average_density": reference_data["7"],
        "agents_average_simulation_time": reference_data["8"],
        "new_metric": reference_data["9"],
        "cassol_metric": reference_data["10"]
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

def parse_agent_position_per_frame(output_dir:str, ip:str):
    #dictionary to calculate speeds, distances and densities later
    agent_positions_per_frame:dict[int,list[Vector3]] = {}
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
        if agentId not in agent_positions_per_frame:
            agent_positions_per_frame[agentId] = []
        agent_positions_per_frame[agentId].append(Vector3(agentX, agentY, agentZ))
    return agent_positions_per_frame, x_data, y_data

def remove_result_files(output_dir:str, ip:str):
    csv_str = ip.replace(":", "_") + ".csv"
    png_str = ip.replace(":", "_") + ".png"
    txt_str = ip.replace(":", "_") + ".txt"

    if os.path.isfile(output_dir + "/resultFile_" + csv_str):
        os.remove(output_dir + "/resultFile_" + csv_str)

    # heatmap.png
    if os.path.isfile(output_dir + "/heatmap_" + png_str):
        os.remove(output_dir + "/heatmap_" + png_str)

    # markers.csv
    if os.path.isfile(output_dir + "/markers_" + csv_str):
        os.remove(output_dir + "/markers_" + csv_str)

    # resultCellFile.txt
    if os.path.isfile(output_dir + "/resultCellFile_" + txt_str):
        os.remove(output_dir + "/resultCellFile_" + txt_str)

    # trajectories.png
    if os.path.isfile(output_dir + "/trajectories_" + png_str):
        os.remove(output_dir + "/trajectories_" + png_str)