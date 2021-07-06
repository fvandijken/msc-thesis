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
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

number_of_iterations_1 = 200
number_of_iterations_2 = 500

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedSearchAndFix(input=input, config=config)
splittable_trucks = cs.get_many_splittable_trucks(number_of_iterations=number_of_iterations_1)
# partial_heur_solution = Schedule(config=config, trucks=splittable_trucks)
# toc = time.time()
# print('\n')
print('INITIAL SOLUTION:')
# print(partial_heur_solution)
# print(partial_heur_solution.metrics())
# #shipments_occurance(heur_solution, input)
# running_time = toc - tic
# print('Total running time: ', running_time)
# partial_heur_solution.visualize(save=True)

#efficient_trucks = list(filter(lambda truck: truck.get_duration() < c.max_duration, trucks))
# splittable_trucks = list(filter(lambda truck: truck.is_splittable(), splittable_trucks))

# print('Number of fixed trucks: ', len(trucks))
# print('Number of efficient trucks: ', len(efficient_trucks))
# print('Number of splittable trucks: ', len(splittable_trucks))

splittable_solution = Schedule(config=config, trucks=splittable_trucks)

#infeasible_trucks = heur_solution.get_too_long_trucks_without_split()

# shipments_to_be_placed = []
# number_infeasible_trucks = 0
# for truck in infeasible_trucks:
#     number_infeasible_trucks += 1
#     for shipment in truck.shipments:
#         # shipment.input_shipment.type += 'S'
#         shipments_to_be_placed.append(shipment.input_shipment)

# splittable_trucks = heur_solution.get_splittable_trucks()
#
def flatten(list_of_lists):
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten(list_of_lists[0]) + flatten(list_of_lists[1:])
    return list_of_lists[:1] + flatten(list_of_lists[1:])
#
def exclude_truck_shipments_from_list(trucks, shipments):
    return list(filter(
        lambda shipment_tw: shipment_tw.id not in flatten(list(
            map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)),
                trucks))),
        shipments))


shipments_to_be_placed = exclude_truck_shipments_from_list(splittable_trucks, input.shipments_tw)

#print('Number of infeasible trucks destroyed: ', number_infeasible_trucks)
# print('Number of shipments to be replaced: ', len(shipments_to_be_placed))

# feasible_part_heur_solution = Schedule(config=config, trucks=[truck for truck in splittable_trucks])
# print(feasible_part_heur_solution.metrics())
# feasible_part_heur_solution.visualize()
# number_of_shipments_placed = 0
# for truck in splittable_trucks:
#     for shipment in truck.shipments:
#         number_of_shipments_placed += 1
# print('number of shipments placed: ', number_of_shipments_placed)
# print('TOTAL NUMBER OF SHIPMENTS: ', len(shipments_to_be_placed) + number_of_shipments_placed)

input_second_phase = InputTW(shipments_tw=shipments_to_be_placed)

random_cs = RandomizedSearchbeforeafter(input=input_second_phase, config=config, input_trucks=None)
solution_1, solution_2, solution_3 = random_cs.get_solution(number_iterations=number_of_iterations_2)
toc = time.time()
time = toc - tic

# print('\n')
# print(solution_1)
# solution_1.metrics()
# solution_1.visualize()
# print('\n')
# print(solution_1)
# solution_1.metrics()
# solution_1.visualize()

final_solution_1 = merge_schedules(solution_1, splittable_solution)
# print('FINAL SOLUTION:')
# print(final_solution)
# print(final_solution.metrics())
shipments_occurance(final_solution_1, input)
final_solution_1.visualize(save=True, with_shipment_ids=True)
solution_1.get_depot_distribution()

final_solution_2 = merge_schedules(solution_2, splittable_solution)
# print('FINAL SOLUTION:')
# print(final_solution)
# print(final_solution.metrics())
# shipments_occurance(final_solution_2, input)
# final_solution_2.visualize(save=False, with_shipment_ids=False)

print('SETTINGS & SOLUTION 1: \n')
print(config.gap_percentage)
print(config.time_window_interval_in_minutes)
print(config.max_number_shipment_multiplication)
print(number_of_iterations_1)
print(number_of_iterations_2)
print(c.start_time_last_shipment)
print(c.day_duration_last_shipment)
print('\n')
print(final_solution_1.get_total_costs())
print(final_solution_1.get_total_number_of_trucks())
print(final_solution_1.get_number_of_drivers())
print(final_solution_1.get_waiting_pc())
print(final_solution_1.get_empty_driving_pc())
print(final_solution_1.get_inefficiency_pc())
print(final_solution_1.get_total_time())
print(final_solution_1.get_number_of_short_truck_days())
print(final_solution_1.get_average_driver_day_length())
print('\n')
# print('SOLUTION 2 & TIME: \n')
# print(final_solution_2.get_total_costs())
# print(final_solution_2.get_total_number_of_trucks())
# print(final_solution_2.get_number_of_drivers())
# print(final_solution_2.get_waiting_pc())
# print(final_solution_2.get_empty_driving_pc())
# print(final_solution_2.get_inefficiency_pc())
# print(final_solution_2.get_total_time())
# print(final_solution_2.get_number_of_short_truck_days())
# print(final_solution_2.get_average_driver_day_length())
# print('\n')
print(time)



