import math
from typing import TYPE_CHECKING
from CellClass import CellClass
from Vector3Class import Vector3
from statistics import fmean

if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass

def walked_distances(agent_pos_per_frame:dict[int,list[Vector3]]):
    print("Calculating Walked Distances")

    agent_distance_walked:dict[int,float] = {}
    total_distance_walked:float = 0.0
    agents_min_displacement:dict[int,float] = {}
    agents_max_displacement:dict[int,float] = {}
    #for each agent
    for _agent, _positions in agent_pos_per_frame.items():
        agent_walked = 0 
        last_pos = -1
        min_displacement = 1000
        max_displacement = -1000
        #for each position of this agent
        for _pos in _positions:

            #if no position yet, just continue (need two to calculate)
            if last_pos == -1:
                #update lastPos, so we can use later
                last_pos = _pos

                continue
            #else, calculate
            else:
                #distance
                displacement = abs(Vector3.Distance(_pos, last_pos))
                agent_walked += displacement
                last_pos = _pos
                min_displacement = min(min_displacement, displacement)
                max_displacement = max(max_displacement, displacement)

        #update the dict. 
        total_distance_walked += agent_walked
        agent_distance_walked[_agent] = agent_walked
        agents_min_displacement[_agent] = min_displacement
        agents_max_displacement[_agent] = max_displacement
    return total_distance_walked, agent_distance_walked, agents_min_displacement, agents_max_displacement

def average_agent_speed(time_step:float, agent_frame_quant:dict[int, int], agent_dist_walked:dict[int,float]):
    print("Calculating Agent average speed")
    #with the distance walked, as well as the qnt of frames of each agent (size of each), we can calculate mean speed
    agent_speed:dict[int,float] = {}
    speed_sum:float = 0.0
    for ag in agent_dist_walked:
        vel = agent_dist_walked[ag] / (agent_frame_quant[ag] * time_step)
        speed_sum += vel
        agent_speed[ag] = vel
    return speed_sum, agent_speed

def cell_average_local_density(cell_list:list[CellClass]):
    # remove frames with value 0 (no agents at frame)
    valid_cell_densities:dict[CellClass,list[int]] = { }
    for _cell in cell_list:
        valid_cell_densities[_cell] = [d for d in _cell.agents_in_cell if d > 0]
    # remove cells with len 0 (no agents during simulation)
    valid_cell_densities = {c: d for c, d in valid_cell_densities.items() if len(d) > 0}
    # average density for valid frames
    average_cell_density = {c: fmean(d) for c, d in valid_cell_densities.items()}
    # sum averages
    total_cell_density = sum([sum(d) for d in valid_cell_densities.values()])
    return total_cell_density, average_cell_density

def frame_average_local_density(cell_list:list[CellClass]):
    local_density_per_frame = []
    frame_quant = len(cell_list[0].agents_in_cell)
    for frame in range(frame_quant):
        frame_densities = [c.agents_in_cell[frame] for c in cell_list]
        frame_densities = [d for d in frame_densities if d > 0]
        local_density_per_frame.append(fmean(frame_densities))
    return local_density_per_frame

def cell_maximum_local_density(cell_list:list[CellClass]):
    #find max local density per cell and its index (frame)
    max_cell_density_value = [max(c.agents_in_cell) for c in cell_list]
    max_cell_density_index = [c.agents_in_cell.index(max(c.agents_in_cell)) for c in cell_list]

    #find the "max max" local density between cell and its index (cell index)
    max_density_value = max(max_cell_density_value)
    max_density_index = max_cell_density_value.index(max_density_value)
    max_density_cell = cell_list[max_density_index]

    # returns the "max max" density value, the frame it occurs, and the cell id
    return max_density_value, max_cell_density_index[max_density_index], max_density_cell.id

def agent_local_density_per_frame(agent_frame_count:dict[int, int], agent_pos_per_frame:dict[int,list[Vector3]]):
    #for densities, we calculate the local densities for each agent, each frame
    local_densities:dict[int,dict[int,int]] = {}
    #get the maximum amount of frames
    maxframes = max(agent_frame_count.values())

    #for each frame	
    #if dist is lower or equal sqrt(1/pi) (area of the circle, 1m²ish), update density
    maxDistance = math.sqrt(1 / math.pi)
    for _frame in range(maxframes):
        local_densities[_frame] = {}
        #for each agent, we check local density
        for _agent in agent_pos_per_frame:
            #maybe this agent is not present in the simulation on this frame, so check it
            if _frame >= len(agent_pos_per_frame[_agent]):
                continue

            localDensity = 1
            for ag2 in agent_pos_per_frame:
                #maybe this agent is not present in the simulation on this frame, so check it
                if _frame >= len(agent_pos_per_frame[ag2]):
                    continue

                #if ag is equal ag2, it is the same agent
                if _agent != ag2:
                    #check distance
                    distDen = Vector3.Distance(agent_pos_per_frame[_agent][_frame], agent_pos_per_frame[ag2][_frame])
                    #if dist is lower or equal 1/pi (area of the circle, 1m²ish), update density
                    if distDen <= maxDistance:
                        localDensity += 1

            #update local densities
            local_densities[_frame][_agent] = localDensity
    return local_densities

def agent_average_local_densities(local_densities:dict[int,dict[int,int]], agent_frame_count:dict[int, int]):
    agent_density_sum:dict[int,int] = {}
    for _frame in local_densities:
        for _agent in local_densities[_frame]:
            if _agent not in agent_density_sum:
                agent_density_sum[_agent] = local_densities[_frame][_agent]
            else:
                agent_density_sum[_agent] += local_densities[_frame][_agent]

    agent_average_local_density = {}
    total_density_sum = 0
    for ld in agent_density_sum:
        dnt = agent_density_sum[ld] / agent_frame_count[ld]
        total_density_sum += dnt
        agent_average_local_density[ld] = dnt

    return total_density_sum, agent_density_sum