from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.RandomizedSearchAndFix import RandomizedSearchAndFix
import constants as c
from heuristics.RandomizedSearchbeforeafter import RandomizedSearchbeforeafter
from heuristics.Schedule import Schedule
from check import shipments_occurance
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

number_of_iterations = 250

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
#input.print()

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedSearchbeforeafter(input=input, config=config)
solution_1, solution_2, solution_3 = cs.get_solution(number_iterations=number_of_iterations)
toc = time.time()
time = toc - tic
# print('\n')
# print('FINAL SOLUTION:')
# print(solution_1)
# print(solution_1.metrics())
# print(solution_2.metrics())
shipments_occurance(solution_1, input)
# print('Score second solution: ', solution_2.get_total_costs())
# print('Score third solution: ', solution_3.get_total_costs())
# print('TIME RANDOM SEARCH: ', time)
solution_1.visualize(save=True, with_truck_costs=False, with_shipment_ids=False)
solution_1.get_depot_distribution()
solution_2.visualize(save=False)

# print('\n')
# print('FINAL SOLUTION:')
# print(solution_2)
# print(solution_2.metrics())
# shipments_occurance(solution_2, input)
# running_time = toc - tic
# print('Total running time: ', running_time)
# solution_2.visualize(save=True)
#
# print('\n')
# print('FINAL SOLUTION:')
# print(solution_3)
# print(solution_3.metrics())
# shipments_occurance(solution_3, input)
# running_time = toc - tic
# print('Total running time: ', running_time)
# solution_3.visualize(save=True)

print('SETTINGS & SOLUTION 1: \n')
print(config.gap_percentage)
print(config.time_window_interval_in_minutes)
print(config.max_number_shipment_multiplication)
print(number_of_iterations)
print('')
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







