import csv
import itertools
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from operator import itemgetter
import constants
import os

# -------------------------------------------- Give input to the model ----------------------------------------------

# Files
# ROOT_DIR = 'config.py'
shipments_file = constants.shipments_file
time_diff_matrix_file = constants.time_diff_matrix_file
depots_file = constants.depots_file

# Parameters
# The weights in the cost function that determines the operational cost for executing one shipment after another
weight_waiting_time = constants.weight_waiting_time
weight_empty_driving_time = constants.weight_empty_driving_time

# Maximum working day duration
max_duration = constants.max_duration
max_duration_reliefpoints = constants.max_duration_reliefpoints
max_driving_time = constants.max_driving_time

# The fixed cost for adding a new truck to the planning
fixed_cost_new_truck = constants.fixed_cost_new_truck
startup_costs_Ermelo = constants.startup_costs_Ermelo
startup_costs_FCDC = constants.startup_costs_FCDC

# The amount of time spend on not driving within one shipment block
loading_time = constants.loading_time

# Import time difference matrix from csv to dataframe.
# The time difference matrix gives the driving time between all different locations.
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)


# ------------------------------------------------ General Functions -----------------------------------------------

# Format function for dictionary
def format_dict(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            format_dict(value, indent + 1)
        else:
            print('\t' * (indent + 1) + str(value))


# ------------------------------------------------ Import Input Data -----------------------------------------------
class concurrent_scheduler:

    def __init__(self, shipments_file, depots_file, parameters):
        self.shipments_file = shipments_file
        self.depots_file = depots_file
        self.parameters = parameters

    # Import Shipments from csv to dataframe
    # Shipments is a list of all shipments that have to be executed, with their Shipment ID, start time, end time,
    # start location and end location

    def algorithm(self):

        shipment_data_df = pd.read_csv(self.shipments_file)

        # Import Shipments from csv to dictionary
        with open(self.shipments_file, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            shipments_data = [{'shipment_id': row['Shipment_ID'],
                               'start_time': float(row['Starting_Time']),
                               'end_time': float(row['Ending_Time']),
                               'start_location': row['Starting_Location'],
                               'end_location': row['Ending_Location']}
                              for row in reader]

        # Import Depots from csv to dictionary
        with open(self.depots_file, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            depots_data = {row['Depot']: int(row['Trucks']) for row in reader}

        # Print input data
        N = len(shipments_data)
        M = len(depots_data)
        print('overview depots: ')
        print('total: ', M)
        print(format_dict(depots_data))
        print('overview shipments: ')
        print('total: ', N)
        print(shipment_data_df.head())
        print(N)

        # --------------------------------------------- Prepare for the algorithm --------------------------------------------

        # def execute_alg(self):

        # Determine startup costs: take the average cost of driving from Ermelo to the start location
        depot_list = list(depots_data.keys())
        total_fixed_cost = 0
        for depot in depot_list:
            fixed_cost = weight_empty_driving_time * 2 * time_diff_matrix.at['Ermelo', depot]
            total_fixed_cost += fixed_cost
        startup_costs_FCDC = total_fixed_cost / len(depot_list)
        startup_costs_Ermelo = total_fixed_cost / len(depot_list)
        print('startup costs FC and DC is: ', startup_costs_FCDC)
        print('startup costs Ermelo is: ', startup_costs_Ermelo)

        # Create a class 'Truck' that represents a truck situated at a certain depot, to which we are going to
        # assign the shipments

        class Truck:
            id_accumulator = 1

            def __init__(self, start_depot):
                self.start_depot = start_depot
                if self.start_depot == 'Ermelo':
                    self.startup_cost = startup_costs_Ermelo
                else:
                    self.startup_cost = startup_costs_FCDC
                self.active = False
                self.shipments = []
                self.id = Truck.id_accumulator
                Truck.id_accumulator += 1

            def is_active(self):
                return self.active

            def get_start_depot(self):
                return self.start_depot

            def get_last_shipment(self):
                return self.shipments[-1]

            def get_startup_cost(self):
                return self.startup_cost

            def add_shipment(self, shipment):
                self.active = True
                self.shipments.append(shipment)

            def remove_ith_shipment(self, i):
                del self.shipments[i]
                if len(self.shipments) == 0:
                    self.active = False

            def remove_shipment(self, shipment):
                if shipment not in self.shipments:
                    print('Removed shipment not in truck')
                else:
                    self.shipments.pop(shipment)
                    if len(self.shipments) == 0:
                        self.active = False

            def get_shipments(self):
                return self.shipments

            def get_id(self):
                return self.id

            def get_startup_costs(self):
                return self.startup_cost

            def get_empty_driving_costs(self):
                empty_driving_costs = 0
                if self.is_active():
                    empty_driving_costs += weight_empty_driving_time * time_diff_matrix.at[
                        self.start_depot, self.shipments[0]['start_location']]
                    for i in range(len(self.shipments) - 1):
                        empty_driving_costs += weight_empty_driving_time * time_diff_matrix.at[
                            self.shipments[i]['end_location'], self.shipments[i + 1]['start_location']]
                    empty_driving_costs += weight_empty_driving_time * time_diff_matrix.at[
                        self.shipments[-1]['end_location'], self.start_depot]
                return empty_driving_costs

            def get_waiting_costs(self):
                waiting_costs = 0
                for i in range(len(self.shipments) - 1):
                    waiting_costs += weight_waiting_time * (
                                self.shipments[i + 1]['start_time'] - self.shipments[i]['end_time'] -
                                time_diff_matrix.at[
                                    self.shipments[i]['end_location'], self.shipments[i + 1]['start_location']])
                return waiting_costs

            def get_total_costs(self):
                total_costs = 0
                if self.is_active():
                    total_costs = self.startup_cost + self.get_empty_driving_costs() + self.get_waiting_costs()
                return round(total_costs, 2)

            def __str__(self):
                return 'Truck %2d starts at depot %6s, has total cost %s and executes the shipments: %s' % (
                    self.id, self.start_depot, self.get_total_costs(),
                    [shipment['shipment_id'] for shipment in self.shipments])

            # a trip shows the truck trip: depot, shipments sequence, depot.
            def get_trip(self):
                trip = [self.start_depot] + [shipment['shipment_id'] for shipment in self.shipments] + [
                    self.start_depot]
                return trip

        # Define the functions that are needed inside the algorithm

        def driving_time_between_shipments(left_shipment, right_shipment):
            return time_diff_matrix.at[left_shipment['end_location'], right_shipment['start_location']]

        def cost_active_truck(truck: Truck, shipment):
            last_shipment = truck.get_last_shipment()
            if shipment['start_time'] - last_shipment['end_time'] - driving_time_between_shipments(last_shipment,
                                                                                                   shipment) >= 0:
                return weight_waiting_time * (
                        shipment['start_time'] - last_shipment['end_time'] - driving_time_between_shipments(
                    last_shipment,
                    shipment)) + \
                       weight_empty_driving_time * driving_time_between_shipments(last_shipment, shipment)
            else:
                return 1000000000

        def cost_inactive_truck(truck: Truck, shipment):
            return truck.startup_cost + weight_empty_driving_time * (
                time_diff_matrix.at[truck.get_start_depot(), shipment['start_location']])

        def get_active_trucks():
            return filter(lambda truck: truck.is_active(), trucks)

        def get_inactive_trucks():
            return filter(lambda truck: not truck.is_active(), trucks)

        def duration_with_potential_shipment(truck: Truck, shipment):
            duration_with_shipment = time_diff_matrix.at[
                                         truck.get_start_depot(), truck.get_shipments()[0]['start_location']] + \
                                     (shipment['end_time'] - truck.get_shipments()[0]['start_time']) + \
                                     time_diff_matrix.at[shipment['end_location'], truck.get_start_depot()]
            return duration_with_shipment

        def driving_time_with_potential_shipment(truck: Truck, shipment):
            driving_time_with_shipment = time_diff_matrix.at[
                truck.get_start_depot(), truck.get_shipments()[0]['start_location']]
            for ship in truck.get_shipments():
                ship_duration = ship['end_time'] - ship['start_time'] - loading_time
                driving_time_with_shipment += ship_duration
            driving_time_with_shipment += time_diff_matrix.at[
                truck.get_shipments()[-1]['end_location'], shipment['start_location']]
            driving_time_with_shipment += (shipment['end_time'] - shipment['start_time']) - loading_time
            driving_time_with_shipment += time_diff_matrix.at[shipment['end_location'], truck.get_start_depot()]
            return driving_time_with_shipment

        # Initiate all trucks available
        trucks = [Truck(depot) for depot, number_of_trucks in depots_data.items() for _ in range(number_of_trucks)]

        # Sort the shipments by increasing start time
        sorted_shipments = sorted(shipments_data, key=itemgetter('start_time'))

        # --------------------------------------------- Execute for the algorithm --------------------------------------------

        # Loop over all shipments in increasing start time order
        for shipment in sorted_shipments:
            # Keep up whether the shipment is placed or not
            placed = False
            # Decide for all trucks whether they are active or not and if they are active if the current shipment would fit
            # without exceeding the maximal duration
            active_trucks = list(get_active_trucks())
            inactive_trucks = list(get_inactive_trucks())
            active_trucks_with_space = []
            for truck in active_trucks:
                if duration_with_potential_shipment(truck,
                                                    shipment) < max_duration and driving_time_with_potential_shipment(
                        truck, shipment) < max_driving_time:
                    active_trucks_with_space.append(truck)
            # Pick from all active trucks with space the least costly one to assign the shipment to
            for truck in active_trucks_with_space:
                last_shipment = truck.get_last_shipment()
                if last_shipment['end_time'] + driving_time_between_shipments(last_shipment, shipment) <= shipment[
                    'start_time'] and not placed:
                    the_best_truck = min(active_trucks_with_space, key=lambda truck: cost_active_truck(truck, shipment))
                    costs = [cost_active_truck(truck, shipment) for truck in active_trucks]
                    the_best_truck.add_shipment(shipment)
                    placed = True
                    # print('just placed on active truck: ', truck.get_id(), shipment)
            # If there is no feasible active truck, pick from all non-active trucks the least costly one to add to the planning
            # and assign the shipment to this truck
            if not placed:
                the_best_truck = min(inactive_trucks, key=lambda truck: cost_inactive_truck(truck, shipment))
                the_best_truck.add_shipment(shipment)
                placed = True
                # print('just placed on new truck: ', the_best_truck.get_id(), shipment)
            # If shipment is not placed, print statement
            if not placed:
                # print("Shipment could not be placed")
                pass

        # --------------------------------------------- Print the results ---------------------------------------------------

        # Define the trips of every truck in a list. Notice these also define the trucks without shipments assigned to them.
        trips = []
        for truck in trucks:
            trip = truck.get_trip() + [truck.get_duration()]
            trips.append(trip)

        # Define the cycles_form that have the same form as the cycles from the LP models: [depot, ship_id_1, ..., depot]
        cycles_form = []
        for trip in trips:
            if len(trip) > 2:
                cycle_form = trip
                cycles_form.append(cycle_form)

        # Define the cycles we will use to analyse the solution and build the gantt chart
        cycles_to_trucks = {}
        cycles = []
        for truck in trucks:
            cycle = [truck.get_start_depot()] + truck.get_shipments() + [truck.get_start_depot()]
            if len(cycle) > 2:
                cycle_key = cycle[1]['shipment_id']
                cycles_to_trucks[cycle_key] = truck
                cycles.append(cycle)

        # Define and print total number of trucks needed
        number_of_vehicles = len(cycles)
        print('number of cycles: ', number_of_vehicles)

        # ----------------------------------------- Evaluate Solution ---------------------------------------------------------

        # Analyze input data

        # Sum over the duration of the shipments to generate the total number of hours that have to be planned
        total_hours_input = 0
        for shipment in shipments_data:
            ship_duration = shipment['end_time'] - shipment['start_time']
            total_hours_input += ship_duration

        # Analyze the solution

        # Determine different variables of the solution that could be insightful
        total_waiting_time = 0
        total_empty_driving_time = 0
        total_pull_out_time = 0
        total_pull_in_time = 0
        total_shipment_time_check = 0
        total_hours_planned = 0
        truck_trip_durations = []
        truck_trip_driving_time = []

        # Define functions to make the code better readable
        def start_loc_ith_trip_in_cycle(cycle, j):
            return cycle[j]['start_location']

        def end_loc_ith_trip_in_cycle(cycle, j):
            return cycle[j]['end_location']

        def driving_time_from_ith_trip_to_next_trip(cycle, j):
            return time_diff_matrix.at[end_loc_ith_trip_in_cycle(cycle, j), start_loc_ith_trip_in_cycle(cycle, j + 1)]

        def start_time_ith_trip_in_cycle(cycle, j):
            return cycle[j]['start_time']

        def end_time_ith_trip_in_cycle(cycle, j):
            return cycle[j]['end_time']

        def duration_ith_trip_in_cycle(cycle, j):
            return end_time_ith_trip_in_cycle(cycle, j) - start_time_ith_trip_in_cycle(cycle, j)

        def get_depot_from_cycle(cycle):
            return cycle[0]

        def get_duration_from_cycle(cycle):
            duration = time_diff_matrix.at[get_depot_from_cycle(cycle), cycle[1]['start_location']] + \
                       (cycle[-2]['end_time'] - cycle[1]['start_time']) + \
                       time_diff_matrix.at[cycle[-2]['end_location'], get_depot_from_cycle(cycle)]
            return duration

        for cycle in cycles:
            print(cycle)
            depot = get_depot_from_cycle(cycle)
            # Pull out trips
            pull_out_time = time_diff_matrix.at[depot, start_loc_ith_trip_in_cycle(cycle, 1)]
            total_pull_out_time += pull_out_time
            # Shipment trips
            shipment_time = 0
            for i in range(len(cycle) - 2):
                one_shipment_time = end_time_ith_trip_in_cycle(cycle, i + 1) - start_time_ith_trip_in_cycle(cycle,
                                                                                                            i + 1)
                shipment_time += one_shipment_time
            total_shipment_time_check += shipment_time
            # Driving empty in between shipments
            empty_driving_time = 0
            for i in range(len(cycle) - 3):
                one_empty_driving_time = time_diff_matrix.at[
                    end_loc_ith_trip_in_cycle(cycle, i + 1), start_loc_ith_trip_in_cycle(cycle, i + 2)]
                empty_driving_time += one_empty_driving_time
            total_empty_driving_time += empty_driving_time
            # Waiting time in between shipments
            waiting_time = 0
            for i in range(len(cycle) - 3):
                one_waiting_time = start_time_ith_trip_in_cycle(cycle, i + 2) - end_time_ith_trip_in_cycle(cycle,
                                                                                                           i + 1) - \
                                   time_diff_matrix.at[
                                       end_loc_ith_trip_in_cycle(cycle, i + 1), start_loc_ith_trip_in_cycle(cycle,
                                                                                                            i + 2)]
                waiting_time += one_waiting_time
            total_waiting_time += waiting_time
            # Pull in trips
            pull_in_time = time_diff_matrix.at[end_loc_ith_trip_in_cycle(cycle, len(cycle) - 2), depot]
            total_pull_in_time += pull_in_time
            # Duration and driving time
            truck_trip_durations.append(round(get_duration_from_cycle(cycle), 2))
            driving_time = round(
                pull_out_time - (len(cycle) - 2) * loading_time + shipment_time + empty_driving_time + pull_in_time, 2)
            truck_trip_driving_time.append(driving_time)

        costs_per_truck = []
        total_costs = 0
        for truck in trucks:
            total_hours_planned += truck.get_duration()
            if truck.is_active():
                costs_per_truck.append(truck.get_total_costs())
                total_costs += truck.get_total_costs()

        inefficiency_percentage = (total_hours_planned - total_hours_input) / total_hours_planned
        inefficiency_percentage_no_pull_arcs = (total_hours_planned - total_hours_input - total_pull_out_time -
                                                total_pull_in_time) / total_hours_planned

        # Print the different variables
        print('The total waiting time is: ', str(round(total_waiting_time, 2)), ' hours')
        print('The total empty driving time is: ', str(total_empty_driving_time), ' hours')
        print('The total pull out time is: ', str(total_pull_out_time), ' hours')
        print('The total pull in time is: ', str(total_pull_in_time), ' hours')
        print('The durations of the truck trips are: ', str(truck_trip_durations))
        print('The total number of hours driving is: ', str(truck_trip_driving_time))
        print('The total hours of input is: ', str(round(total_hours_input, 2)), ' hours')
        print('The total hours planned is: ', str(round(total_hours_planned, 2)), ' hours')
        print(
            'The inefficiency percentage (i.e. percentage of hours in planning that is devoted to something else than '
            'executing shipments) is: ', str(round(100 * inefficiency_percentage, 2)), '%')
        print('The inefficiency percentage without pull out/in is: ',
              str(round(100 * inefficiency_percentage_no_pull_arcs, 2)),
              '%')
        print('The costs per truck is: ', costs_per_truck)
        print('The total cost is: ', round(total_costs, 2))

        def get_driving_time_from_cycle(cycle):
            cycle_index = cycles.index(cycle)
            driving_time = truck_trip_driving_time[cycle_index]
            return driving_time

        def get_end_time_from_cycle(cycle):
            end_time_last_shipment = cycle[-2]['end_time']
            driving_back_time = time_diff_matrix.at[cycle[-2]['end_location'], get_depot_from_cycle(cycle)]
            return end_time_last_shipment + driving_back_time

        def get_costs_from_cycle(cycle):
            costs = cycles_to_trucks[cycle[1]['shipment_id']].get_total_costs()
            return costs

        # Find reliefpoints
        relief_dict = {}
        for cycle in cycles:
            cycle_key = cycle[1]['shipment_id']
            depot = get_depot_from_cycle(cycle)
            relief_dict[cycle_key] = []
            for i in range(len(cycle) - 2):
                if start_loc_ith_trip_in_cycle(cycle, i + 1) == depot:
                    relief_dict[cycle_key].append(start_time_ith_trip_in_cycle(cycle, i + 1))
                if end_loc_ith_trip_in_cycle(cycle, i + 1) == depot:
                    relief_dict[cycle_key].append(end_time_ith_trip_in_cycle(cycle, i + 1))

    # ------------------------------------- Visualize solution as Gantt Chart -------------------------------------------

    # figure parameters
    bar_height = 3
    space_between_bars = 3
    space_below_lowest_bar = 3
    space_above_highest_bar = 3

    # Constructing the figure
    fig, gnt = plt.subplots(figsize=(20, 10))
    fig = plt.subplots_adjust(right=0.58)

    plt.title('Visualization of solution of MDVSP by Concurrent Scheduler')
    gnt.grid(False)

    # Constructing the axes
    # x axis
    gnt.set_xlim(-1, 21)
    gnt.set_xlabel('Time')
    gnt.set_xticks([i for i in range(21)])
    gnt.set_xticklabels(
        ['04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
         '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '00:00'],
        fontsize=6, rotation=30)

    # y axis
    gnt.set_ylabel('Truck Trips')
    gnt.set_ylim(0, number_of_vehicles * (bar_height + space_between_bars) + space_above_highest_bar)
    gnt.set_yticks([space_below_lowest_bar + 0.5 * bar_height + (bar_height + space_between_bars) * i for i in
                    range(number_of_vehicles)])
    gnt.set_yticklabels((i + 1 for i in range(number_of_vehicles)), fontsize=8)

    # Constructing bars for different type of activities in a truck trip
    y = space_below_lowest_bar

    for cycle in cycles:
        # Pull out trips
        if get_depot_from_cycle(cycle) == 'Ermelo':
            gnt.broken_barh(
                [(start_time_ith_trip_in_cycle(cycle, 1) - time_diff_matrix.at[
                    get_depot_from_cycle(cycle), start_loc_ith_trip_in_cycle(cycle, 1)],
                  time_diff_matrix.at[start_loc_ith_trip_in_cycle(cycle, 1), get_depot_from_cycle(cycle)])],
                (y, bar_height), facecolors='tab:green', edgecolor='black')
        elif get_depot_from_cycle(cycle) == 'DC1':
            gnt.broken_barh(
                [(start_time_ith_trip_in_cycle(cycle, 1) - time_diff_matrix.at[
                    get_depot_from_cycle(cycle), start_loc_ith_trip_in_cycle(cycle, 1)],
                  time_diff_matrix.at[start_loc_ith_trip_in_cycle(cycle, 1), get_depot_from_cycle(cycle)])],
                (y, bar_height), facecolors='tab:cyan', edgecolor='black')
        else:
            gnt.broken_barh(
                [(start_time_ith_trip_in_cycle(cycle, 1) - time_diff_matrix.at[
                    get_depot_from_cycle(cycle), start_loc_ith_trip_in_cycle(cycle, 1)],
                  time_diff_matrix.at[start_loc_ith_trip_in_cycle(cycle, 1), get_depot_from_cycle(cycle)])],
                (y, bar_height), facecolors='tab:purple', edgecolor='black')
        # Shipment trips
        for i in range(len(cycle) - 2):
            gnt.broken_barh([(start_time_ith_trip_in_cycle(cycle, i + 1),
                              duration_ith_trip_in_cycle(cycle, i + 1))],
                            (y, bar_height), facecolors='tab:orange', edgecolor='black')
        # Driving empty in between shipments
        for i in range(len(cycle) - 3):
            gnt.broken_barh([(end_time_ith_trip_in_cycle(cycle, i + 1),
                              driving_time_from_ith_trip_to_next_trip(cycle, i + 1))],
                            (y, bar_height), facecolors='tab:blue', edgecolor='black')
        # Waiting time in between shipments
        for i in range(len(cycle) - 3):
            gnt.broken_barh(
                [(end_time_ith_trip_in_cycle(cycle, i + 1) + driving_time_from_ith_trip_to_next_trip(cycle, i + 1),
                  start_time_ith_trip_in_cycle(cycle, i + 2) - end_time_ith_trip_in_cycle(cycle, i + 1) -
                  driving_time_from_ith_trip_to_next_trip(cycle, i + 1))],
                (y, bar_height), facecolors='tab:grey', edgecolor='black')
        # Pull in trips
        if get_depot_from_cycle(cycle) == 'Ermelo':
            gnt.broken_barh([(end_time_ith_trip_in_cycle(cycle, len(cycle) - 2),
                              time_diff_matrix.at[
                                  end_loc_ith_trip_in_cycle(cycle, len(cycle) - 2), get_depot_from_cycle(cycle)])],
                            (y, bar_height),
                            facecolors='tab:green', edgecolor='black')
        elif get_depot_from_cycle(cycle) == 'DC1':
            gnt.broken_barh([(end_time_ith_trip_in_cycle(cycle, len(cycle) - 2),
                              time_diff_matrix.at[
                                  end_loc_ith_trip_in_cycle(cycle, len(cycle) - 2), get_depot_from_cycle(cycle)])],
                            (y, bar_height),
                            facecolors='tab:cyan', edgecolor='black')
        else:
            gnt.broken_barh([(end_time_ith_trip_in_cycle(cycle, len(cycle) - 2),
                              time_diff_matrix.at[
                                  end_loc_ith_trip_in_cycle(cycle, len(cycle) - 2), get_depot_from_cycle(cycle)])],
                            (y, bar_height),
                            facecolors='tab:purple', edgecolor='black')
        # Reliefpoints
        cycle_key = cycle[1]['shipment_id']
        if get_duration_from_cycle(cycle) <= max_duration_reliefpoints and get_driving_time_from_cycle(
                cycle) <= max_driving_time:
            for relief_time in relief_dict[cycle_key]:
                gnt.annotate('', (relief_time, y + bar_height),
                             xytext=(relief_time, y + bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='pink', edgecolor='pink',
                                             shrink=0.05), fontsize=6, horizontalalignment='right',
                             verticalalignment='top')
        if get_duration_from_cycle(cycle) <= max_duration_reliefpoints and get_driving_time_from_cycle(
                cycle) > max_driving_time:
            for relief_time in relief_dict[cycle_key]:
                gnt.annotate('', (relief_time, y + bar_height),
                             xytext=(relief_time, y + bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='maroon',
                                             edgecolor='maroon',
                                             shrink=0.05), fontsize=6, horizontalalignment='right',
                             verticalalignment='top')
        if get_duration_from_cycle(cycle) > max_duration_reliefpoints:
            for relief_time in relief_dict[cycle_key]:
                gnt.annotate('', (relief_time, y + bar_height),
                             xytext=(relief_time, y + bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='r', edgecolor='r',
                                             shrink=0.05), fontsize=6, horizontalalignment='right',
                             verticalalignment='top')
        gnt.annotate(get_costs_from_cycle(cycle), (get_end_time_from_cycle(cycle), y + bar_height),
                     xytext=(get_end_time_from_cycle(cycle), y + bar_height + 2),
                     arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='pink', edgecolor='pink',
                                     shrink=0.05), fontsize=8, horizontalalignment='right',
                     verticalalignment='top')
        y += bar_height + space_between_bars

    # Constructing the legend
    legend_elements = [Patch(edgecolor='black', facecolor='tab:orange', linewidth=0.5, label='Shipment'),
                       Patch(edgecolor='black', facecolor='tab:cyan', linewidth=0.5, label='Stem trips DC'),
                       Patch(edgecolor='black', facecolor='tab:purple', linewidth=0.5, label='Stem trips FC'),
                       Patch(edgecolor='black', facecolor='tab:green', linewidth=0.5, label='Stem trips Ermelo'),
                       Patch(edgecolor='black', facecolor='tab:blue', linewidth=0.5, label='Empty Driving'),
                       Patch(edgecolor='black', facecolor='tab:grey', linewidth=0.5, label='Waiting'),
                       Line2D([], [], color='r', marker='$\downarrow$', markersize=8,
                              label='Reliefpoint on trip with too long duration', lw=0),
                       Line2D([], [], color='maroon', marker='$\downarrow$', markersize=8,
                              label='Reliefpoint on trip with too long driving time', lw=0),
                       Line2D([], [], color='pink', marker='$\downarrow$', markersize=8,
                              label='Reliefpoint on feasible trip', lw=0)]
    gnt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

    # Printing analytics in the gantt chart
    txt = \
        'Total waiting time is: ' + str(round(total_waiting_time, 2)) + ' hours \n' + 'Total empty driving time ' \
                                                                                      'and stem time is: ' + str(
            total_empty_driving_time + total_pull_in_time + total_pull_out_time) + ' hours \n' + \
        'Total number of hours planned is: ' + str(round(total_hours_planned, 2)) + ' hours \n' + \
        'Total hours of input was: ' + str(
            round(total_hours_input, 2)) + ' hours \n' + 'The inefficiency is: {0}%'.format(
            str(round(100 * inefficiency_percentage, 2))) + '\n' + \
        'The inefficiency without pull arcs is: ' + str(
            round(100 * inefficiency_percentage_no_pull_arcs, 2)) + '% \n' + 'The total costs are: ' + str(total_costs)

    plt.text(1.05, 0.3, txt, horizontalalignment='left', verticalalignment='center', transform=gnt.transAxes)

    # Save the figure
    plt.savefig("figures/gantt chart local search heuristic.png")


# ------------------------------------------- Local Search Heuristic -------------------------------------------------

# Define the class 'Schedule' as a set of Trucks
class Schedule:

    def __init__(self):
        self.trucks = []

    def add_truck(self, truck: Truck):
        self.trucks.append(truck)

    def get_trucks(self):
        return self.trucks

    def is_feasible(self):
        is_feasible = True
        for truck in self.trucks:
            for i in range(len(truck.get_shipments()) - 1):
                if truck.get_shipments()[i]['start_time'] + time_diff_matrix.at[
                    truck.get_shipments()[i]['end_location'], truck.get_shipments()[i + 1]['start_location']] > \
                        truck.get_shipments()[i + 1]['start_time']:
                    is_feasible = False
                    infeasible_truck = str(truck)
            if truck.get_duration() > max_duration:
                is_feasible = False
        return is_feasible

    def get_waiting_costs(self):
        waiting_costs = 0
        for truck in self.trucks:
            waiting_costs += truck.get_waiting_costs()
        return waiting_costs

    def get_empty_driving_costs(self):
        empty_driving_costs = 0
        for truck in self.trucks:
            empty_driving_costs += truck.get_empty_driving_costs()
        return empty_driving_costs

    def get_total_costs(self):
        if self.is_feasible():
            total_costs = 0
            for truck in self.trucks:
                total_costs += truck.get_total_costs()
        else:
            total_costs = 10000000
        return total_costs

    def __str__(self):
        string = 'Schedule has total cost: ' + str(self.get_total_costs()) + ', \n'
        i = 1
        for truck in self.get_trucks():
            string += 'Truck ' + str(i) + ' ' + str(truck) + '\n'
            i += 1
        return string

    def swap_last_shipment(self, truck_1: Truck, truck_2: Truck):
        if truck_1 not in self.get_trucks() or truck_2 not in self.get_trucks():
            print('trucks to swap not found in schedule')
        else:
            truck_2.add_shipment(truck_1.get_shipments()[-1])
            truck_1.remove_ith_shipment(-1)
            truck_1.add_shipment(truck_2.get_shipments()[-2])
            truck_2.remove_ith_shipment(-2)


schedule = Schedule()
for truck in trucks:
    if truck.is_active():
        schedule.add_truck(truck)
initial_total_costs = schedule.get_total_costs()
print('INITIAL SCHEDULE: ', str(schedule))
best_schedule = schedule
best_costs = best_schedule.get_total_costs()
for i in range(len(schedule.get_trucks())):
    for j in [x for x in range(len(schedule.get_trucks())) if x != i]:
        # for truck_id_1 in 'set of truckids'
        #      for truck_id_2 in [x for x in 'set of truckids' if x != truck_id_1]:
        schedule.swap_last_shipment(schedule.trucks[i], schedule.trucks[j])
        new_costs = schedule.get_total_costs()
        print('after swapping truck ', i + 1, ' and ', j + 1, ' we compare ', best_costs, ' to ', new_costs)
        if new_costs < best_costs:
            best_schedule = schedule
            best_costs = best_schedule.get_total_costs()
print('BEST SCHEDULE: ', str(best_schedule))
