from heuristics.Config import Config
from heuristics.InputTW import InputTW
import constants as c
from heuristics.MDVSPTWILP import MDVSPTWILP
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.DeterministicCS import DeterministicCS
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.Schedule import Schedule
from check import shipments_occurance

config = Config(
    shipments_file='\\test_data\Data - shipments 30.csv',
    shipments_file_time_windows='\\test_data\DataTW - shipments 237.csv',
    gap_percentage=1.42,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()


cs = DeterministicCSnomaxduration(input=input, config=config)
cs_solution: Schedule = cs.get_solution()
print('\n')
print(cs_solution)
print(cs_solution.metrics())
cs_solution.visualize()

infeasible_trucks = cs_solution.get_too_long_trucks_without_split()
shipments_to_be_placed = []
number_infeasible_trucks = 0
for truck in infeasible_trucks:
    number_infeasible_trucks += 1
    for shipment in truck.shipments:
        # shipment.input_shipment.type += 'S'
        shipments_to_be_placed.append(shipment.input_shipment)

print('Number of infeasible trucks destroyed: ', number_infeasible_trucks)
print('Number of shipments to be replaced: ', len(shipments_to_be_placed))

feasible_part_ilp_solution = Schedule(config=config, trucks=[truck for truck in cs_solution.trucks if truck not in cs_solution.get_too_long_trucks_without_split()])
print(feasible_part_ilp_solution.metrics())
feasible_part_ilp_solution.visualize()

input_greedy = InputTW(shipments_tw=shipments_to_be_placed)

concurrent_scheduler = DeterministicCS(input=input_greedy, config=config, input_trucks=[truck for truck in feasible_part_ilp_solution.trucks])
greedy_solution: Schedule = concurrent_scheduler.get_solution()
print('\n')
print(greedy_solution)
print(greedy_solution.metrics())
shipments_occurance(greedy_solution, input)
greedy_solution.visualize()





