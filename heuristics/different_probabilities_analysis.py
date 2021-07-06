from heuristics.Config import Config
from heuristics.InputTW import InputTW
import constants as c
from heuristics.Schedule import Schedule
from heuristics.RandomizedSearch import RandomizedSearch
from check import shipments_occurance

config = Config(
    shipments_file_time_windows='/test_data/DataTW - shipments 237.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)


input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

# Generate and analyse initial solution
best_score = float('inf')
best_prob_second = 0.0
best_prob_third = 0.0
best_solution = None
for i in range(20):
    c.prob_second_choice = 0.05 + 0.01 * (i + 1)
    print('Running iteration with second probability ' + str(c.prob_second_choice))
    for j in range(10):
        c.prob_third_choice = 0.01 * (j + 1)
        rs = RandomizedSearch(input=input, config=config)
        solution: Schedule = rs.get_solution(number_iterations=10)
        new_score = solution.get_total_costs()
        if new_score < best_score:
            print('NEW Score (' + str(c.prob_second_choice) + ', ' + str(c.prob_third_choice) + '): ' + str(new_score))
            best_score = new_score
            best_solution = solution
            best_prob_second = c.prob_second_choice
            best_prob_third = c.prob_third_choice

print('\n')
print('FINAL SOLUTION:')
print('Probability second:' + str(best_prob_second))
print('Probability third:' + str(best_prob_third))
print(best_solution)
print(best_solution.metrics())
shipments_occurance(best_solution, input)
best_solution.visualize()


