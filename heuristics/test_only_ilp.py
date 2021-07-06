from heuristics.Config import Config
from heuristics.InputTW import InputTW
import constants as c
from heuristics.Schedule import Schedule
from heuristics.MDVSPTWILP import MDVSPTWILP
from heuristics.MDVSPTWILP_big_size import MDVSPTWILPbigsize
from check import shipments_occurance
from heuristics.RandomizedSearch import RandomizedSearch
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)


input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
tic = time.time()
ilp = MDVSPTWILP(input=input, config=config)
solution: Schedule = ilp.get_solution()
toc = time.time()
time = toc - tic
print('\n')

# print('FINAL SOLUTION:')
# print(solution)
# print(solution.metrics())
shipments_occurance(solution, input)
solution.visualize(show=False, save=True, with_shipment_ids=False)

number_home_depot = 0
number_other_depot = 0
for truck in solution.get_trucks():
    for ship in truck.shipments:
        if truck.start_depot == ship.start_location:
            number_home_depot += 1
        else:
            number_other_depot += 1
print('number of home depot: ', number_home_depot)
print('number of other depot: ', number_other_depot)


print('TIME: ', time)