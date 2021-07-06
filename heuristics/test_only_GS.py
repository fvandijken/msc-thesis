from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.RandomizedtiesCSnomaxduration import RandomizedtiesCSnomaxduration
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
import constants as c
from heuristics.Schedule import Schedule
from heuristics.RandomizedtiesCS import RandomizedtiesCS
import check
import time
import matplotlib.pyplot as plt

config = Config(
    shipments_file_time_windows='/test_data/Data 17_04 - Shipments.csv',
    #shipments_file_time_windows='/test_data/old_data/Test Data TW 30.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# latest_start_times = set()
# for shipment_1, shipment_2 in zip(input.shipments_tw, input.shipments_tw[1:]):
#     if shipment_1.latest_start_time == shipment_2.latest_start_time and ((shipment_1.latest_start_time - shipment_1.earliest_start_time) ==  (shipment_2.latest_start_time - shipment_2.earliest_start_time)):
#         print(shipment_1.id, shipment_2.id)
# for shipment in input.shipments_tw:
#     latest_start_times.add(shipment.latest_start_time)
# for time in latest_start_times:
#     print(time, len(list(filter(lambda shipment: shipment.latest_start_time == time, input.shipments_tw))))
# print(len(set(latest_start_times)))

# Generate and analyse initial solution
tic = time.time()
cs = RandomizedtiesCS(input=input, config=config)
solution, equal_cost, equal_cost_dist = cs.get_solution()
toc = time.time()
solution.post_improve_depots()
check.shipments_occurance(solution, input)
check.time_windows(solution, input)

solution.visualize(show=False)

plt.figure()
plt.hist(equal_cost, alpha=0.5, label='cost tie')
plt.hist(equal_cost_dist, alpha=0.5, label='cost and dist tie')
plt.legend()
plt.show()

tie_count = 0
for n in equal_cost:
    if n > 1:
        tie_count += 1
print(tie_count, tie_count/len(equal_cost))

tie_count_dist = 0
for n in equal_cost_dist:
    if n > 1:
        tie_count_dist += 1
print(tie_count_dist, tie_count_dist/len(equal_cost_dist))







