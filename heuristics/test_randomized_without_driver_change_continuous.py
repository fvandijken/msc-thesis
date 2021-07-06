from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearchAndFix import RandomizedSearchAndFix
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.RandomizedSearchAndFixContinuous import RandomizedSearchAndFixContinuous
from heuristics.MDVSPTWILP import MDVSPTWILP
from heuristics.RandomizedSearchbeforeafter import RandomizedSearchbeforeafter
from heuristics.RandomizedtiesCS import RandomizedtiesCS
import constants as c
from heuristics.Schedule import Schedule
from heuristics.Schedule import merge_schedules
from check import shipments_occurance
import util
import time

config = Config(
    shipments_file_time_windows='/test_data/Data 22_01 - Shipments.csv',
    gap_percentage=2.5,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedSearchAndFixContinuous(input=input, config=config)
trucks = cs.get_solution(max_number_of_iterations=300)
heur_solution = Schedule(config=config, trucks=trucks)
toc = time.time()
print('\n')
print('INITIAL SOLUTION:')
print(heur_solution)
print(heur_solution.metrics())
running_time = toc - tic
print('Running time: ', running_time)
heur_solution.visualize(with_truck_costs=True, save=True)

def exclude_truck_shipments_from_list(trucks, shipments):
    return list(filter(
        lambda shipment_tw: shipment_tw.id not in util.flatten(list(
            map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)),
                trucks))),
        shipments))

shipments_tbd = exclude_truck_shipments_from_list(trucks, input.shipments_tw)

add_greedily = RandomizedSearchbeforeafter(input=input, config=config, input_trucks=trucks,
                                sorted_shipments_tw=shipments_tbd)
final_solution = add_greedily.get_solution(number_iterations=100)[0]
tac = time.time()
print(final_solution)
print(final_solution.metrics())
running_time = tac - tic
print('Total running time: ', running_time)
total = 0
for truck in final_solution.trucks:
    for shipment in truck.shipments:
        total += 1
print('total number of shipments in solution: ', total)
#shipments_occurance(heur_solution, input)
final_solution.visualize(with_truck_costs=True, save=True)






