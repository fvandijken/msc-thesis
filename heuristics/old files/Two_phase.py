import csv
import itertools
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import constants

# -------------------------------------------- Give input to the model ----------------------------------------------

# Files
shipment_file = constants.shipment_file
time_diff_matrix_file = constants.time_diff_matrix_file
depots_file = constants.depots_file

# Parameters
# The maximum waiting time in between shipments
max_waiting_time = constants.max_waiting_time
# The weights in the cost function that determines the operational cost for executing one shipment after another
weight_waiting_time = constants.weight_waiting_time
weight_empty_driving_time = constants.weight_empty_driving_time

# The fixed cost for adding a new truck to the planning
fixed_cost_new_truck = constants.fixed_cost_new_truck


# ------------------------------------------------ Import Input Data -----------------------------------------------

# Format function for dictionary
def format_dict(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            format_dict(value, indent + 1)
        else:
            print('\t' * (indent + 1) + str(value))


# Import Shipments from csv to dataframe
# Shipments is a list of all shipments that have to be executed, with their Shipment ID, start time, end time,
# start location and end location
shipments_data_df = pd.read_csv(shipment_file)
print('OVERVIEW SHIPMENTS: ')
print(shipments_data_df.head())

# Import Shipments from csv to dictionary
with open(shipment_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    shipments_data = {row['Shipment_ID']: {'start_time': float(row['Starting_Time']),
                                           'end_time': float(row['Ending_Time']),
                                           'start_location': row['Starting_Location'],
                                           'end_location': row['Ending_Location']}
                      for row in reader}

N = len(shipments_data)
print(N)
# print('SHIPMENTS AS DICTIONARY: ')
# pretty(shipments_data)

# Import Depots from csv to dictionary
with open(depots_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    depots_data = {row['Depot']: int(row['Trucks']) for row in reader}

print(format_dict(depots_data))
M = len(depots_data)

# Import time difference matrix from csv to dataframe.
# The time difference matrix gives the driving time between all different locations.
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)

print(time_diff_matrix)

# -------------------------------------Translate data to the Network Flow Graph--------------------------------------

depot_list = list(depots_data.keys())

def SDVSP(shipments_data, depot):
    # Construct nodes of the Network Flow Graph
    nodes = [ship_id for (ship_id, ship_data) in shipments_data.items()] + ['s', 't']

    # Construct compatibility arcs with flow upper bound and cost

    # The compatibility arcs are the arcs that connect shipment 1 to shipment 2 iff it is feasible to execute shipment 1,
    # drive to the start location of shipment 2, and start shipment 2.
    # Initiate the arcs and give them flow upper bound 1
    arcs_dict = {}
    for (first_ship_id, first_ship_data) in shipments_data.items():
        for (second_ship_id, second_ship_data) in shipments_data.items():
            waiting_time = second_ship_data['start_time'] - first_ship_data['end_time'] - \
                           time_diff_matrix.at[first_ship_data['end_location'], second_ship_data['start_location']]
            if 0 <= waiting_time <= max_waiting_time:
                arcs_dict[(first_ship_id, second_ship_id)] = 1


    # print("COMPATIBILITY ARCS: ")
    # format_dict(arcs_dict)


    # Determine the cost for the compatibility arcs
    # Determine the empty driving time between the execution of shipment 1 and shipment 2
    def empty_driving_time(ship_1, ship_2):
        return time_diff_matrix.at[ship_1['end_location'], ship_2['start_location']]


    # Determine the waiting time between the execution of shipment 1 and shipment 2
    def waiting_time(ship_1, ship_2):
        return ship_2['start_time'] - ship_1['end_time'] - empty_driving_time(ship_1, ship_2)


    # The cost of compatibility arc (ship 1, ship 2) is the operational cost of executing shipment 2 after shipment 1
    # The operational cost is weighted sum of the empty driving time and the waiting time

    def cost(ship_id_1, ship_id_2):
        ship_1 = shipments_data[ship_id_1]
        ship_2 = shipments_data[ship_id_2]
        operational_cost = weight_waiting_time * waiting_time(ship_1, ship_2) + \
                           weight_empty_driving_time * empty_driving_time(ship_1, ship_2)
        return operational_cost


    # Assign the costs to the compatibility arcs
    cost = {
        arc: cost(arc[0], arc[1]) for (arc, _) in arcs_dict.items()
    }

    # Construct pull out / pull in arcs with flow upper bound and cost
    # The cost of the pull out arcs is a fixed cost for adding a new truck to the planning plus the operational costs

    for (ship_id, ship_data) in shipments_data.items():
        time_diff_from_depot = time_diff_matrix.at[depot, ship_data['start_location']]
        pull_out_arc = ('s', ship_id)
        arcs_dict[pull_out_arc] = 1
        cost[pull_out_arc] = fixed_cost_new_truck + time_diff_from_depot

        # The cost of the pull in arcs is the operational costs
        time_diff_to_depot = time_diff_matrix.at[ship_data['end_location'], depot]
        pull_in_arc = (ship_id, 't')
        arcs_dict[pull_in_arc] = 1
        cost[pull_in_arc] = time_diff_to_depot

    # Construct circulation arc with flow upper bound and cost
    arcs_dict[('t', 's')] = N
    cost[('t', 's')] = 0

    # print("COSTS: ")
    # format_dict(cost)

    arcs, flow_upper = gp.multidict(arcs_dict)

    # -------------------------------------- Optimization model -----------------------------------------------------------


    model = gp.Model('min-cost-flow')

    # Decision variables
    flow = model.addVars(arcs, obj=cost, name="flow")

    # Constraints
    # Flow upper bound for every arc: For every arc the flow is bounded by an upperbound.
    model.addConstrs(
        (flow[i, j] <= flow_upper[i, j] for i, j in arcs), "upper")

    # Flow conservation for every node: For every node the incoming flow is exactly the same as the outgoing flow.
    model.addConstrs(
        (flow.sum(node, '*') == flow.sum('*', node)
         for node in nodes), "conservation")

    # Flow requirement for shipment nodes: For every shipment node the incoming and outgoing flow is exactly 1.
    for node in nodes:
        if node != 's' and node != 't':
            model.addConstr(flow.sum('*', node) == 1,
                            "cap incoming node %s" % node)
            # model.addConstr(flow.sum(node, '*') == 1,
            #                 "cap outgoing node %s" % node)

    # Optimize the model
    model.optimize()

    # ---------------------------------------- Print the solution -----------------------------------------------------

    solution_arcs = []
    if model.status == GRB.OPTIMAL:
        solution = model.getAttr('x', flow)
        for i, j in arcs:
            if solution[i, j] > 0:
                #print('%s -> %s: %g' % (i, j, solution[i, j]))
                solution_arcs += [(i, j)]
        print('The total number of trucks needed is: ' + str(int(solution['t', 's'])))

    return solution_arcs

depot_to_shipments_dict = {}
for depot in depot_list:
    depot_to_shipments_dict[depot] = {}
for ship_id, ship_data in shipments_data.items():
    start_location = shipments_data[ship_id]['start_location']
    nearest_depot = min(depot_list, key=lambda depot: time_diff_matrix.at[depot, start_location])
    depot_to_shipments_dict[nearest_depot][ship_id] = ship_data

Total_number_of_trucks = 0
depot_solution_dict = {}
for depot in depot_list:
    depot_solution_arcs = SDVSP(depot_to_shipments_dict[depot], depot)

    # Graph Flow Model
    plt.figure(figsize=(20, 10))
    k = nx.Graph(depot_solution_arcs)
    fixed_positions = {'s': (0.4, 0), 't': (1, 0)}
    fixed_nodes = fixed_positions.keys()
    pos = nx.spring_layout(k, pos=fixed_positions, fixed=fixed_nodes)
    nx.draw(k, pos, with_labels=True, font_size=20)
    name_fig = 'Network Flow Solution Graph ' + depot + '.png'
    plt.savefig(name_fig)



# # ---------------------------------------- Visualize solution as graph ------------------------------------------------
#
# # Graph Flow Model
# plt.figure(figsize=(20, 10))
# h = nx.Graph(arcs)
# fixed_positions = {'s': (0.4, 0), 't': (1, 0)}
# fixed_nodes = fixed_positions.keys()
# pos = nx.spring_layout(h, pos=fixed_positions, fixed=fixed_nodes)
# nx.draw(h, pos, with_labels=True, font_size=20)
# plt.savefig('Network Flow Model Graph.png')
#
# # Graph Flow Model
# plt.figure(figsize=(20, 10))
# k = nx.Graph(solution_arcs)
# fixed_positions = {'s': (0.4, 0), 't': (1, 0)}
# fixed_nodes = fixed_positions.keys()
# pos = nx.spring_layout(h, pos=fixed_positions, fixed=fixed_nodes)
# nx.draw(k, pos, with_labels=True, font_size=20)
# plt.savefig('Network Flow Solution Graph.png')
#
# # Graph showing different cycles
# plt.figure(figsize=(20, 10))
# f = nx.Graph(solution_arcs)
# fixed_positions = {'s': (0, 0), 't': (0, 0)}
# fixed_nodes = fixed_positions.keys()
# pos = nx.spring_layout(f, pos=fixed_positions, fixed=fixed_nodes)
# nx.draw(f, pos, with_labels=True, font_size=16)
# plt.savefig('Depot Solution Graph.png')
#
# # Directed graph generating different truck trips from cycles in the graph
# g = nx.DiGraph(solution_arcs)
#
# # Making sure that every cycle goes from 's', to the shipments, to 't'
# cycles = []
# for cycle in nx.simple_cycles(g):
#     number = 1
#     cycle_s_to_t = []
#     for node in cycle:
#         if node == 's':
#             for i in range(len(cycle)):
#                 cycle_s_to_t.append(cycle[(cycle.index(node) + i) % len(cycle)])
#     cycles.append(cycle_s_to_t)
#
# # Print the different truck trips
# number = 1
# for cycle in cycles:
#     print('truck trip ' + str(number) + ': ' + str(cycle))
#     number += 1
#
# number_of_vehicles = len(cycles)
# print('cycles: ', cycles)
#
# # ----------------------------------------- Evaluate Solution ---------------------------------------------------------
#
# # Analyze input data
#
# # Sum over the duration of the shipments to generate the total number of hours that have to be planned
# total_hours_input = 0
# for ship_id, ship_data in shipments_data.items():
#     ship_duration = shipments_data[ship_id]['end_time'] - shipments_data[ship_id]['start_time']
#     total_hours_input += ship_duration
#
# # Analyze the solution
#
# # Determine different variables of the solution that could be insightful
# total_waiting_time = 0
# total_empty_driving_time = 0
# total_pull_out_time = 0
# total_pull_in_time = 0
# total_shipment_time_check = 0
# total_hours_planned = 0
# truck_trip_durations = []
#
#
# # Define functions to make the code better readable
# def start_loc_ith_trip_in_cycle(j):
#     return shipments_data[cycle[j]]['start_location']
#
#
# def end_loc_ith_trip_in_cycle(j):
#     return shipments_data[cycle[j]]['end_location']
#
#
# def driving_time_from_ith_trip_to_next_trip(j):
#     return time_diff_matrix.at[end_loc_ith_trip_in_cycle(j), start_loc_ith_trip_in_cycle(j + 1)]
#
#
# def start_time_ith_trip_in_cycle(j):
#     return shipments_data[cycle[j]]['start_time']
#
#
# def end_time_ith_trip_in_cycle(j):
#     return shipments_data[cycle[j]]['end_time']
#
#
# def duration_ith_trip_in_cycle(j):
#     return end_time_ith_trip_in_cycle(j) - start_time_ith_trip_in_cycle(j)
#
#
# for cycle in cycles:
#     # Pull out trips
#     total_pull_out_time += time_diff_matrix.at[config.name_depot, start_loc_ith_trip_in_cycle(1)]
#     # Shipment trips
#     for i in range(len(cycle) - 2):
#         total_shipment_time_check += end_time_ith_trip_in_cycle(i + 1) - start_time_ith_trip_in_cycle(i + 1)
#     # Driving empty in between shipments
#     for i in range(len(cycle) - 3):
#         total_empty_driving_time += time_diff_matrix.at[
#             end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
#     # Waiting time in between shipments
#     for i in range(len(cycle) - 3):
#         total_waiting_time += start_time_ith_trip_in_cycle(i + 2) - end_time_ith_trip_in_cycle(i + 1) - \
#                               time_diff_matrix.at[end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
#     # Pull in trips
#     total_pull_in_time += time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), config.name_depot]
#     # Durations
#     truck_trip_durations.append(round(end_time_ith_trip_in_cycle(len(cycle) - 2) + \
#                                       time_diff_matrix.at[
#                                           end_loc_ith_trip_in_cycle(len(cycle) - 2), config.name_depot] -
#                                       (start_time_ith_trip_in_cycle(1) -
#                                        time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), config.name_depot]), 2))
#
# for h in truck_trip_durations:
#     total_hours_planned += h
#
# inefficiency_percentage = (total_hours_planned - total_hours_input) / total_hours_planned
# inefficiency_percentage_no_pull_arcs = (total_hours_planned - total_hours_input - total_pull_out_time -
#                                         total_pull_in_time) / total_hours_planned
#
# # Print the different variables
# print('The total waiting time is: ', str(round(total_waiting_time, 2)), ' hours')
# print('The total empty driving time is: ', str(total_empty_driving_time), ' hours')
# print('The total pull out time is: ', str(total_pull_out_time), ' hours')
# print('The total pull in time is: ', str(total_pull_in_time), ' hours')
# print('The durations of the truck trips are: ', str(truck_trip_durations))
# print('The total hours of input is: ', str(total_hours_input), ' hours')
# print('The total hours planned is: ', str(round(total_hours_planned, 2)), ' hours')
# print('The inefficiency percentage (i.e. percentage of hours in planning that is devoted to something else than '
#       'executing shipments) is: ', str(round(100 * inefficiency_percentage, 2)), '%')
# print('The inefficiency percentage without pull out/in is: ', str(round(100 * inefficiency_percentage_no_pull_arcs, 2)),
#       '%')
#
# # ------------------------------------- Visualize solution as Gantt Chart -------------------------------------------
#
# # figure parameters
# bar_height = 2
# space_between_bars = 2
# space_below_lowest_bar = 2
# space_above_highest_bar = 2
#
# # Constructing the figure
# fig, gnt = plt.subplots(figsize=(10, 5))
# fig = plt.subplots_adjust(right=0.58)
#
# plt.title('Visualization of optimal solution of SDVSP for N=75')
# gnt.grid(False)
#
# # Constructing the axes
# # x axis
# gnt.set_xlim(-1, 21)
# gnt.set_xlabel('Time')
# gnt.set_xticks([i for i in range(21)])
# gnt.set_xticklabels(['04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
#                      '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '00:00'],
#                     fontsize=6, rotation=30)
#
# # y axis
# gnt.set_ylabel('Truck Trips')
# gnt.set_ylim(0, number_of_vehicles * (bar_height + space_between_bars) + space_above_highest_bar)
# gnt.set_yticks([space_below_lowest_bar + 0.5 * bar_height + (bar_height + space_between_bars) * i for i in
#                 range(number_of_vehicles)])
# gnt.set_yticklabels((i + 1 for i in range(number_of_vehicles)), fontsize=8)
#
# # Constructing bars for different type of activities in a truck trip
# y = space_below_lowest_bar
#
# for cycle in cycles:
#     # Pull out trips
#     gnt.broken_barh(
#         [(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[config.name_depot, start_loc_ith_trip_in_cycle(1)],
#           time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), config.name_depot])],
#         (y, bar_height), facecolors='tab:green', edgecolor='black')
#     # Shipment trips
#     for i in range(len(cycle) - 2):
#         gnt.broken_barh([(start_time_ith_trip_in_cycle(i + 1),
#                           duration_ith_trip_in_cycle(i + 1))],
#                         (y, bar_height), facecolors='tab:orange', edgecolor='black')
#     # Driving empty in between shipments
#     for i in range(len(cycle) - 3):
#         gnt.broken_barh([(end_time_ith_trip_in_cycle(i + 1),
#                           driving_time_from_ith_trip_to_next_trip(i + 1))],
#                         (y, bar_height), facecolors='tab:blue', edgecolor='black')
#     # Waiting time in between shipments
#     for i in range(len(cycle) - 3):
#         gnt.broken_barh([(end_time_ith_trip_in_cycle(i + 1) + driving_time_from_ith_trip_to_next_trip(i + 1),
#                           start_time_ith_trip_in_cycle(i + 2) - end_time_ith_trip_in_cycle(i + 1) -
#                           driving_time_from_ith_trip_to_next_trip(i + 1))],
#                         (y, bar_height), facecolors='tab:grey', edgecolor='black')
#     # Pull in trips
#     gnt.broken_barh([(end_time_ith_trip_in_cycle(len(cycle) - 2),
#                       time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), config.name_depot])],
#                     (y, bar_height),
#                     facecolors='tab:green', edgecolor='black', label=str(cycle[len(cycle) - 2]))
#     y += bar_height + space_between_bars
#
# # Constructing the legend
# legend_elements = [Line2D([0], [0], color='tab:orange', lw=6, label='Shipment'),
#                    Line2D([0], [0], color='tab:green', lw=6, label='Stem trips'),
#                    Line2D([0], [0], color='tab:blue', lw=6, label='Empty Driving'),
#                    Line2D([0], [0], color='tab:grey', lw=6, label='Waiting')]
# gnt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
#
# # Printing analytics in the gantt chart
# txt = \
#     'Total waiting time is: ' + str(round(total_waiting_time, 2)) + ' hours \n' + 'Total empty driving time ' \
#     'and stem time is: ' + str(total_empty_driving_time + total_pull_in_time + total_pull_out_time) + ' hours \n' + \
#     'Total number of hours planned is: ' + str(round(total_hours_planned, 2)) + ' hours \n' + \
#     'Total hours of input was: ' + str(total_hours_input) + ' hours \n' + 'The inefficiency is: {0}%'.format(
#         str(round(100 * inefficiency_percentage, 2))) + '\n' + \
#     'The inefficiency without pull arcs is: ' + str(round(100 * inefficiency_percentage_no_pull_arcs, 2)) + '%'
#
# plt.text(1.05, 0.3, txt, horizontalalignment='left', verticalalignment='center', transform=gnt.transAxes)
#
# # Save the figure
# plt.savefig("gantt chart Two Phase.png")
