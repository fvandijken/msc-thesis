from heuristics.Config import Config
from heuristics.InputTW import InputTW
import constants as c
from heuristics.Schedule import Schedule
from heuristics.ListSearch import ListSearch
import check
import time

config = Config(
    shipments_file_time_windows='\\test_data\Data '+ c.test_date + ' - Shipments.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)


input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
#input.print()


# Generate and analyse initial solution
tic = time.time()
ls = ListSearch(input=input, config=config)
solution_1: Schedule = ls.get_solution()
toc = time.time()
# print('\n')
# print('FINAL SOLUTION:')
# print(solution)
# print(solution.metrics())
running_time = toc - tic
#print('Total running time: ', running_time)
check.shipments_occurance(solution_1, input)
check.time_windows(solution_1, input)
solution_1.visualize(show=False, save=True, with_shipment_ids=True)
solution_1.get_depot_distribution()
# solution.create_sheet()

print('SETTINGS & SOLUTION 1: \n')
print(config.gap_percentage)
print(config.time_window_interval_in_minutes)
print(config.max_number_shipment_multiplication)
print(500)
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
print(running_time)

