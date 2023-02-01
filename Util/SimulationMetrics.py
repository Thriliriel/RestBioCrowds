import math
from typing import TYPE_CHECKING
from AgentClass import AgentClass
from CellClass import CellClass
from GoalClass import GoalClass
from Vector3Class import Vector3

if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass

def walked_distances(agent_pos_per_frame:dict[int,list[Vector3]]):
    print("Calculating Walked Distances")

    agent_distance_walked:dict[int,float] = {}
    total_distance_walked:float = 0.0

    #for each agent
    for _agent, _positions in agent_pos_per_frame.items():
        agent_walked = 0 
        last_pos = -1

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
                agent_walked += abs(Vector3.Distance(_pos, last_pos))
                last_pos = _pos

        #update the dict. 
        total_distance_walked += agent_walked
        agent_distance_walked[_agent] = agent_walked
    return total_distance_walked, agent_distance_walked

def average_agent_speed(time_step:float, agent_frame_quant:dict[int, int], agent_dist_walked:dict[int,float]):
    print("Calculatin Agent average speed")
    #with the distance walked, as well as the qnt of frames of each agent (size of each), we can calculate mean speed
    agent_speed:dict[int,float] = {}
    speed_sum:float = 0.0
    for ag in agent_dist_walked:
        vel = agent_dist_walked[ag] / (agent_frame_quant[ag] * time_step)
        speed_sum += vel
        agent_speed[ag] = vel

    return speed_sum, agent_speed

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
