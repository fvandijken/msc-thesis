import os
import pandas as pd

# -------------------------------------------- Parameters ----------------------------------------------

test_date = '31_03'

ilp_time_limit = 600
max_unfixed_shipments = 30
# Day durations
max_duration = 13.5  # Used in the algorithms
max_duration_early_start = 11 # Early start means a maximum duration of 11 hours, used in algorithms
#max_duration_visualization = 13.5  # Used in the visualization of the solution
min_duration_split = 7  # Used in determining whether to split a truckday into two driver days
max_driving_time = 9  # Could be used if we want to bound the driving day in greedy algorithm

# Other time estimates
max_waiting_time = 1.5  # Used to decrease the amount of compatibility arcs
loading_time = 1.0  # Used in determining the total driving time per truck day

# Cost function
weight_waiting_time = 30
weight_empty_driving_time = 60
fixed_cost_new_truck = 100000
weight_length = 150

# Last and first shipment indicators, used in greedy alg
day_duration_last_shipment = 11
start_time_last_shipment = 6  # In am pm hours
start_time_first_shipment = 11  # In am pm hours

# Probabilities for randomized search heuristic, used in randomized search alg
prob_second_choice = 0.2
prob_third_choice = 0.02

# ------------------------------------------------ Files ------------------------------------------------------

root = os.path.dirname(os.path.abspath(__file__))
depots_file = root + '/test_data/Data - depots.csv'
#depots_file = root + '/test_data/Data - depots real.csv'

time_diff_matrix_file = root + '/test_data/Data - distance matrix.csv'
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)

# ------------------------------------------- Old parameters --------------------------------------------------

#min_duration = 2  # This parameter is used in the algorithms
#
# # Files
# shipments_file = root + '/test_data/Data - shipments 30.csv'
# shipments_file_time_windows = root + '/test_data/DataTW - shipments 30.csv'
#
# name_depot = 'Ermelo'
# gap_percentage = 0.5
# time_window_interval_in_minutes = 20
# max_number_shipment_multiplication = 5
