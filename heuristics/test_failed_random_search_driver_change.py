from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearchnomaxduration import RandomizedSearchnomaxduration
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.RandomizedSearchAndFix import RandomizedSearchAndFix
import constants as c
from heuristics.Schedule import Schedule
from check import shipments_occurance
import time

config = Config(
    shipments_file_time_windows='/test_data/Data 22_01 - Shipments.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
tic = time.time()
rs = RandomizedSearchnomaxduration(input=input, config=config)
rs_solution: Schedule = rs.get_solution(number_iterations=200)
toc = time.time()
print('\n')
print('FINAL SOLUTION:')
print(rs_solution)
print(rs_solution.metrics())
shipments_occurance(rs_solution, input)
running_time = toc - tic
print('Total running time: ', running_time)
rs_solution.visualize()
# solution.create_sheet()

infeasible_trucks = rs_solution.get_too_long_trucks_without_split()
shipments_to_be_placed = []
number_infeasible_trucks = 0
for truck in infeasible_trucks:
    number_infeasible_trucks += 1
    for shipment in truck.shipments:
        # shipment.input_shipment.type += 'S'
        shipments_to_be_placed.append(shipment.input_shipment)

print('Number of infeasible trucks destroyed: ', number_infeasible_trucks)
print('Number of shipments to be replaced: ', len(shipments_to_be_placed))

feasible_part_ilp_solution = Schedule(config=config, trucks=[truck for truck in rs_solution.trucks if truck not in rs_solution.get_too_long_trucks_without_split()])
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







