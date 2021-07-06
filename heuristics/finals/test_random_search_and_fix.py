from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearchAndFix import RandomizedSearchAndFix
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.RandomizedSearchbeforeafter import RandomizedSearchbeforeafter
from heuristics.MDVSPTWILP import MDVSPTWILP
from heuristics.RandomizedtiesCS import RandomizedtiesCS
import constants as c
from heuristics.Schedule import Schedule
from heuristics.Schedule import merge_schedules
from check import shipments_occurance
import util
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

number_of_iterations_1 = 200
number_of_iterations_2 = 700

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
#input.print()

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedSearchAndFix(input=input, config=config)
efficient_trucks = cs.get_many_efficient_trucks(number_of_iterations=number_of_iterations_1)
partial_heur_solution = Schedule(config=config, trucks=efficient_trucks)
# toc = time.time()
# print('\n')
# print('INITIAL SOLUTION:')
# print(partial_heur_solution)
# print(partial_heur_solution.metrics())
# running_time = toc - tic
# print('Total running time: ', running_time)
# partial_heur_solution.visualize(save=True)
#
#
# print('Number of efficient fixed trucks: ', len(efficient_trucks))


def exclude_truck_shipments_from_list(trucks, shipments):
    return list(filter(
        lambda shipment_tw: shipment_tw.id not in util.flatten(list(
            map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)),
                trucks))),
        shipments))

shipments_to_be_placed = exclude_truck_shipments_from_list(efficient_trucks, input.shipments_tw)

input_greedy = InputTW(shipments_tw=shipments_to_be_placed)

random_cs = RandomizedSearchbeforeafter(input=input_greedy, config=config, input_trucks=efficient_trucks)
solution_1, solution_2, solution_3 = random_cs.get_solution(number_iterations=number_of_iterations_2)
toc = time.time()
time = toc - tic
# print('\n')
# print(solution_1)
# solution_1.metrics()
# total = 0
# for truck in solution_1.trucks:
#     for shipment in truck.shipments:
#         total += 1
# print('total number of shipments in solution: ', total)
shipments_occurance(solution_1, input)
solution_1.visualize(save=True)
solution_1.get_depot_distribution()

# print('\n')
# print(solution_2)
# solution_2.metrics()
# total = 0
# for truck in solution_2.trucks:
#     for shipment in truck.shipments:
#         total += 1
# print('total number of shipments in solution: ', total)
# shipments_occurance(solution_2, input)
# solution_2.visualize(save=False)
# print('\n')
# print(greedy_solution_3)
# greedy_solution_3.metrics()
# total = 0
# for truck in greedy_solution_3.trucks:
#     for shipment in truck.shipments:
#         total += 1
# print('total number of shipments in solution: ', total)
# shipments_occurance(greedy_solution_3, input)
# greedy_solution_3.visualize()

print('SETTINGS & SOLUTION 1: \n')
print(config.gap_percentage)
print(config.time_window_interval_in_minutes)
print(config.max_number_shipment_multiplication)
print(number_of_iterations_1)
print(number_of_iterations_2)
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





