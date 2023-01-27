from typing import TYPE_CHECKING
from Vector3Class import Vector3


if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass

def ParseConfigFile(bio_crowds:'BioCrowdsClass', file_path:str):
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
            bio_crowds.timeStep = float(line)
        elif _lineCount == 3:
            #size of each square cell
            bio_crowds.cellSize = int(line)
        elif _lineCount == 4:
            #size of the scenario (comes from json, so no needed)
            sp = line.split(',')
            bio_crowds.mapSize = Vector3(int(sp[0]), int(sp[1]), int(sp[2]))
        elif _lineCount == 5:
            #using path planning?
            if line.lower() == 'false':
                bio_crowds.pathPlanning = False
            else:
                bio_crowds.pathPlanning = True

        _lineCount += 1

def ParseReferenceSimulation(reference_data)->dict:
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

    