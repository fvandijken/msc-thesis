from heuristics.Config import Config
from heuristics.InputTW import InputTW
import constants as c
from heuristics.MDVSPTWILP import MDVSPTWILP
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.DeterministicCS import DeterministicCS
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.RandomizedSearchbeforeafter import RandomizedSearchbeforeafter
from heuristics.Schedule import Schedule
from check import shipments_occurance
import check
import util
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

number_of_iterations = 300

input_ilp = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
#input_ilp.print()

tic = time.time()
ilp = MDVSPTWILP(input=input_ilp, config=config)
ilp_solution: Schedule = ilp.get_solution()
ilp_solution.post_improve_depots()
# print('\n')
# ilp_solution.post_shift_shipments()
# print(ilp_solution)
# print(ilp_solution.metrics())
ilp_solution.visualize(save=False, with_shipment_ids=True)

infeasible_trucks = ilp_solution.get_too_long_trucks_without_split()

shipments_to_be_placed = []
number_infeasible_trucks = 0
for truck in infeasible_trucks:
    number_infeasible_trucks += 1
    for shipment in truck.shipments:
        # shipment.input_shipment.type += 'S'
        shipments_to_be_placed.append(shipment.input_shipment)

# print('Number of infeasible trucks destroyed: ', number_infeasible_trucks)
# print('Number of shipments to be replaced: ', len(shipments_to_be_placed))

feasible_part_ilp_solution = Schedule(config=config, trucks=[truck for truck in ilp_solution.trucks if truck not in ilp_solution.get_too_long_trucks_without_split()])
# print(feasible_part_ilp_solution.metrics())
feasible_part_ilp_solution.visualize(save=False, with_shipment_ids=True)

input_greedy = InputTW(shipments_tw=shipments_to_be_placed)

concurrent_scheduler = RandomizedSearchbeforeafter(input=input_greedy, config=config, input_trucks=feasible_part_ilp_solution.trucks)
solution_1, solution_2, solution_3 = concurrent_scheduler.get_solution(number_iterations=number_of_iterations)
toc = time.time()
time = toc - tic
# print('\n')
# print(solution_1)
# print(solution_1.metrics())
check.shipments_occurance(solution_1, input_ilp)
solution_1.visualize(save=True, with_shipment_ids=False)
solution_1.get_depot_distribution()
# print('\n')
# print(solution_2)
# print(solution_2.metrics())
check.shipments_occurance(solution_2, input_ilp)
solution_2.visualize(save=False)
# print('\n')
# print(greedy_solution_3)
# print(greedy_solution_3.metrics())
# check.shipments_occurance(greedy_solution_3, input_ilp)
# greedy_solution_3.visualize()

print('SETTINGS & SOLUTION 1: \n')
print(config.gap_percentage)
print(config.time_window_interval_in_minutes)
print(config.max_number_shipment_multiplication)
print(number_of_iterations)
print("")
print(c.start_time_last_shipment)
print(c.day_duration_last_shipment)
print('\n')
print(solution_1.get_total_costs())
print(solution_1.get_total_number_of_trucks())
print(solution_1.get_number_of_drivers())
print(solution_1.get_waiting_pc())
print(solution_1.get_empty_driving_pc())
print(solution_1.get_inefficiency_pc())
print(solution_1.get_total_time())
print(solution_1.get_number_of_short_truck_days())
print(solution_1.get_average_driver_day_length())
print('\n')
# print('SOLUTION 2 & TIME: \n')
# print(solution_2.get_total_costs())
# print(solution_2.get_total_number_of_trucks())
# print(solution_2.get_number_of_drivers())
# print(solution_2.get_waiting_pc())
# print(solution_2.get_empty_driving_pc())
# print(solution_2.get_inefficiency_pc())
# print(solution_2.get_total_time())
# print(solution_2.get_number_of_short_truck_days())
# print(solution_2.get_average_driver_day_length())
# print('\n')
print(time)



