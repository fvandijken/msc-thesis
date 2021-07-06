from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearchAndFix import RandomizedSearchAndFix
import constants as c
from heuristics.Schedule import Schedule
from check import shipments_occurance
import time

config = Config(
    shipments_file_time_windows='/test_data/Data 15_04 - Shipments.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedSearchAndFix(input=input, config=config)
trucks = cs.get_many_efficient_trucks(number_of_iterations=100)
solution = Schedule(config=config, trucks=trucks)
toc = time.time()
print('\n')
print('FINAL SOLUTION:')
print(solution)
print(solution.metrics())
#shipments_occurance(solution, input)
running_time = toc - tic
print('Total running time: ', running_time)
solution.visualize(save=True)








