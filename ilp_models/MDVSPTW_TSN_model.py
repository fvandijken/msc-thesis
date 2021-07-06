import csv
import time
import gurobipy as gp
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
from gurobipy import GRB
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import constants
from itertools import chain


# -------------------------------------------- Give input to the model ----------------------------------------------

# Files
shipment_file = constants.shipment_file_time_windows
time_diff_matrix_file = constants.time_diff_matrix_file
depots_file = constants.depots_file

# Parameters

# The maximum waiting time in between shipments
max_waiting_time = constants.max_waiting_time

# Max and min duration
max_duration = constants.max_duration
min_duration = constants.min_duration
max_driving_time = constants.max_driving_time

# The weights in the cost function that determines the operational cost for executing one shipment after another
weight_waiting_time = constants.weight_waiting_time
weight_empty_driving_time = constants.weight_empty_driving_time

# The fixed cost for adding a new truck to the planning
fixed_cost_new_truck = constants.fixed_cost_new_truck

# The amount of time spend on not driving within one shipment block
loading_time = constants.loading_time

# Length of time discretizaiton interval
time_window_interval_in_minutes = constants.time_window_interval_in_minutes
max_number_shipment_multiplication = constants.max_number_shipment_multiplication

gap_percentage = constants.gap_percentage


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
pd.set_option("display.max_rows", 30, "display.max_columns", 7)
shipments_data_df = pd.read_csv(shipment_file)
print('OVERVIEW SHIPMENTS: ')
print(shipments_data_df)

# Import Shipments from csv to dictionary
with open(shipment_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    base_shipments_data = {row['shipment_id'] : {'earliest_start_time': float(row['earliest_start_time']),
                                                'latest_start_time': float(row['latest_start_time']),
                                                'earliest_end_time': float(row['earliest_end_time']),
                                                'latest_end_time': float(row['latest_end_time']),
                                                'start_location': row['start_location'],
                                                'end_location': row['end_location']}
                           for row in reader}

shipments_data_s = {}
shipments_data_e = {}
base_to_windowed_map = {}
interval = int(time_window_interval_in_minutes * 1/.6)
for ship_id, ship_data in base_shipments_data.items():
    length = int((ship_data['latest_start_time'] - ship_data['earliest_start_time']) * 100)
    i = 1
    base_to_windowed_map[ship_id] = []
    if np.ceil(length/interval) + 1 <= max_number_shipment_multiplication:
        pass
    else:
        interval = int(length / (max_number_shipment_multiplication - 2))
    #interval = max(interval, min(30, int(length / (max_number_shipment_multiplication - 2))))
    for minutes in list(range(0, length, interval)) + [length]:
        key = ship_id + '.' + str(i)
        key_s = key + '_s'
        key_e = key + '_e'
        shipments_data_s[key_s] = {
            'start_time': ship_data['earliest_start_time'] + minutes * 0.01,
            'end_time': ship_data['earliest_end_time'] + minutes * 0.01,
            'start_location': ship_data['start_location'],
            'end_location': ship_data['end_location']
        }
        shipments_data_e[key_e] = {
            'start_time': ship_data['earliest_start_time'] + minutes * 0.01,
            'end_time': ship_data['earliest_end_time'] + minutes * 0.01,
            'start_location': ship_data['start_location'],
            'end_location': ship_data['end_location']
        }
        base_to_windowed_map[ship_id].append(key)
        i += 1

shipments_data = {**shipments_data_s, **shipments_data_e}

# Import Depots from csv to dictionary
with open(depots_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    depots_data = {row['Depot']: int(row['Trucks']) for row in reader}

format_dict(depots_data)
M = len(depots_data)

# Import time difference matrix from csv to dataframe.
# The time difference matrix gives the driving time between all different locations.
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)

print(time_diff_matrix.head())

N = len(base_shipments_data)
print('number of shipments input: ', N)
print('time discretization distance: ', time_window_interval_in_minutes)
print('max number of shipment multiplications: ', max_number_shipment_multiplication)

print('number of shipments after time discretization: ', len(shipments_data_s))
for ship, lst in base_to_windowed_map.items():
    print(ship, len(lst))

for ship_id, ship_data in shipments_data.items():
    print(ship_id)
for ship_id, ship_data in shipments_data.items():
    print(ship_data['start_time'])
for ship_id, ship_data in shipments_data.items():
    print(ship_data['end_time'])



# -------------------------------------Translate data to the Network Flow Graph--------------------------------------

# Create list of depots
depot_list = list(depots_data.keys())

# Determine startup costs: take the average cost of driving from Ermelo to the start location
total_fixed_cost = 0
for depot in depot_list:
    fixed_cost = weight_empty_driving_time * 2 * time_diff_matrix.at['Ermelo', depot]
    total_fixed_cost += fixed_cost
fixed_cost_new_truck = total_fixed_cost / M
fixed_cost_new_truck = constants.fixed_cost_new_truck

print('fixed cost new truck: ', fixed_cost_new_truck)

shipment_per_depot = []
for depot in depot_list:
    nodes = [depot + "_" + ship_id for (ship_id, _) in shipments_data.items()]
    nodes_no_time_windows = list({depot + "_" + ship_id[:ship_id.rfind('.')] for (ship_id, _) in shipments_data.items()})
    shipment_per_depot.append(nodes)

depot_nodes_start = [depot + '_s' for depot in depot_list]
depot_nodes_end = [depot + '_t' for depot in depot_list]

locations = set.union({value['start_location'] for (_, value) in shipments_data_s.items()},
                      {value['end_location'] for (_, value) in shipments_data_e.items()})


# Construct compatibility arcs with flow upper bound and cost

# The compatibility arcs are the arcs that connect shipment 1 to shipment 2 iff it is feasible to execute shipment 1,
# drive to the start location of shipment 2, and start shipment 2.
# Initiate the arcs and give them flow upper bound 1

comp_arcs = {}
for (end_ship_id, end_ship_data) in shipments_data_e.items():
    for (start_ship_id, start_ship_data) in shipments_data_s.items():
        waiting_time = start_ship_data['start_time'] - end_ship_data['end_time'] - \
                       time_diff_matrix.at[end_ship_data['end_location'], start_ship_data['start_location']]
        if 0 <= waiting_time:
            comp_arcs[(end_ship_id, start_ship_id)] = 1

arcs_dict = {}
print('number of locations: ' + str(len(locations)))
print('number of connection based arcs: ' + str(len(comp_arcs)))
first_matches = []
for location in locations:
    for end_ship_id, end_ship_data in filter(lambda item: item[1]['end_location'] == location,
                                             shipments_data_e.items()):
        for next_location in locations:
            earliest_start_id = ''
            earliest_start_time = 0
            for start_ship_id, start_ship_data in filter(lambda item: item[1]['start_location'] == next_location,
                                                         shipments_data_s.items()):
                if (end_ship_id, start_ship_id) in comp_arcs and (
                        earliest_start_id == '' or start_ship_data['start_time'] < earliest_start_time):
                    earliest_start_id = start_ship_id
                    earliest_start_time = start_ship_data['start_time']
            if earliest_start_id != '':
                first_match = (end_ship_id, earliest_start_id)
                first_matches.append(first_match)

print('number of first matches arcs: ', len(first_matches))

# Construct latest first matches

latest_first_matches = []
relevant_locations = {shipments_data_s[earliest_start_id]['start_location'] for (_, earliest_start_id) in first_matches}
relevant_start_shipments = {earliest_start_id for (_, earliest_start_id) in first_matches}
for start_ship_id in relevant_start_shipments:
    for previous_location in locations:
        latest_end_shipment_id = ''
        latest_end_time = 0
        for (end_ship_id, earliest_start_id) in filter(
                lambda item: shipments_data_e[item[0]]['end_location'] == previous_location,
                first_matches):
            if (end_ship_id, start_ship_id) in first_matches and (latest_end_shipment_id == '' or shipments_data_e[end_ship_id]['end_time'] > latest_end_time):
                latest_end_shipment_id = end_ship_id
                latest_end_time = shipments_data_e[end_ship_id]['end_time']
        if latest_end_shipment_id != '':
            latest_first_match = (latest_end_shipment_id, start_ship_id)
            latest_first_matches.append(latest_first_match)
            for depot in depot_list:
                arcs_dict[(depot + "_" + latest_end_shipment_id, depot + "_" + start_ship_id)] = N

print('number of latest first matches: ', len(latest_first_matches))
print(latest_first_matches)

# Determine the cost for the compatibility arcs
# Determine the empty driving time between the execution of shipment 1 and shipment 2
def empty_driving_time(ship_1_data, ship_2_data):
    return time_diff_matrix.at[ship_1_data['end_location'], ship_2_data['start_location']]


# Determine the waiting time between the execution of shipment 1 and shipment 2
def waiting_time(ship_1_data, ship_2_data):
    return ship_2_data['start_time'] - ship_1_data['end_time'] - empty_driving_time(ship_1_data, ship_2_data)


# The cost of compatibility arc (ship 1, ship 2) is the operational cost of executing shipment 2 after shipment 1
# The operational cost is weighted sum of the empty driving time and the waiting time

def cost(end_ship_id, start_ship_id):
    end_ship_data = shipments_data_e[end_ship_id[end_ship_id.index('_') + 1:]]
    start_ship_data = shipments_data_s[start_ship_id[start_ship_id.index('_') + 1:]]
    operational_cost = weight_waiting_time * waiting_time(end_ship_data, start_ship_data) + \
                       weight_empty_driving_time * empty_driving_time(end_ship_data, start_ship_data)
    return operational_cost

# Assign the costs to the compatibility arcs
cost = {
    arc: cost(arc[0], arc[1]) for (arc, _) in arcs_dict.items()
}

# Construct waiting arcs between start shipments
count_waiting_arcs = 0
for location in locations:
    starting_shipments = []
    for start_ship_id, start_ship_data in filter(lambda item: item[1]['start_location'] == location,
                                                 shipments_data_s.items()):
        starting_shipments.append((start_ship_id, start_ship_data['start_time']))
    starting_shipments.sort(key=lambda tup: tup[1])
    for i in range(len(starting_shipments) - 1):
        this_ship_id, this_start_time = starting_shipments[i]
        next_ship_id, next_start_time = starting_shipments[i + 1]
        waiting_arc = (this_ship_id, next_ship_id)
        for depot in depot_list:
            arcs_dict[(depot + "_" + this_ship_id, depot + "_" + next_ship_id)] = len(starting_shipments)
        cost[waiting_arc] = weight_waiting_time * (next_start_time - this_start_time)
        count_waiting_arcs += 1

# Construct waiting arcs between end shipments
for location in locations:
    ending_shipments = []
    for end_ship_id, end_ship_data in filter(lambda item: item[1]['end_location'] == location,
                                             shipments_data_e.items()):
        ending_shipments.append((end_ship_id, end_ship_data['end_time']))
    ending_shipments.sort(key=lambda tup: tup[1])
    for i in range(len(ending_shipments) - 1):
        this_ship_id, this_end_time = ending_shipments[i]
        next_ship_id, next_end_time = ending_shipments[i + 1]
        waiting_arc = (this_ship_id, next_ship_id)
        for depot in depot_list:
            arcs_dict[(depot + "_" + this_ship_id, depot + "_" + next_ship_id)] = len(ending_shipments)
        cost[waiting_arc] = weight_waiting_time * (next_end_time - this_end_time)
        count_waiting_arcs += 1

print('number of waiting arcs: ', count_waiting_arcs)
print('number of time space based arcs: ', int(len(arcs_dict)/M))

# Construct shipment arcs

for (start_ship_id, start_ship_data) in shipments_data_s.items():
    for (end_ship_id, end_ship_data) in shipments_data_e.items():
        if start_ship_id != end_ship_id and start_ship_data == end_ship_data:
            shipment_arc = (start_ship_id, end_ship_id)
            for depot in depot_list:
                arcs_dict[(depot + "_" + start_ship_id, depot + "_" + end_ship_id)] = 1
            cost[shipment_arc] = 0

print('number of time space based arcs with shipments arcs: ', int(len(arcs_dict)/M))

# Construct pull out / pull in arcs with flow upper bound and cost
# The cost of the pull out arcs is a fixed cost for adding a new truck to the planning plus the operational costs

# pull out arcs
for depot in depot_list:
    for (ship_id, ship_data) in shipments_data_s.items():
        cost_from_depot = weight_empty_driving_time * time_diff_matrix.at[depot, ship_data['start_location']]
        pull_out_arc = (depot + "_s", depot + "_" + ship_id)
        arcs_dict[pull_out_arc] = 1
        cost[pull_out_arc] = fixed_cost_new_truck + cost_from_depot

# pull in arcs
for depot in depot_list:
    for (ship_id, ship_data) in shipments_data_e.items():
        cost_to_depot = weight_empty_driving_time * time_diff_matrix.at[ship_data['end_location'], depot]
        pull_in_arc = (depot + "_" + ship_id, depot + "_t")
        arcs_dict[pull_in_arc] = 1
        cost[pull_in_arc] = cost_to_depot

# Construct circulation arcs with flow upper bound and cost
for depot in depot_list:
    circulation_arc = (depot + "_t", depot + "_s")
    arcs_dict[circulation_arc] = N
    cost[circulation_arc] = 0

arcs, flow_upper = gp.multidict(arcs_dict)
format_dict(cost)
# -------------------------------------- Optimization model -----------------------------------------------------------

# Model
model = gp.Model('min-cost-flow')

# Decision variables
# flow = model.addVars(arcs, obj=cost, name="flow")
flow = model.addVars(arcs, obj=cost, vtype=GRB.INTEGER, name="flow")

# Constraints
# Flow upper bound for every arc: For every arc the flow is bounded by an upperbound.
model.addConstrs((flow[i, j] <= flow_upper[i, j] for i, j in arcs), "upper")

# Flow conservation for every node: For every node the incoming flow is exactly the same as the outgoing flow.
flat_nodes = [node for nodes in shipment_per_depot for node in nodes]
model.addConstrs(
    (flow.sum(node, '*') == flow.sum('*', node)
     for node in flat_nodes), "c")
model.addConstrs(
    (flow.sum(start_node, '*') == flow.sum('*', start_node)
     for start_node in depot_nodes_start), "conservation_s")
model.addConstrs(
    (flow.sum(end_node, '*') == flow.sum('*', end_node)
     for end_node in depot_nodes_end), "conservation_e")

# Flow requirement in every shipment node: every shipment node has an inflow of exactly one in total in all layers.
# Only visit one of the nodes for the same time window.
for i in range(len(shipment_per_depot[0])):
    acc = 0
    nodes = []
    for j in range(len(shipment_per_depot)):
        key = shipment_per_depot[j][i]
        key_core = key[(key.find('_') + 1):key.rfind('.')]
        print(key)
        print(key_core)
        time_window_nodes = base_to_windowed_map[key_core]
        for k in range(len(time_window_nodes)):
            key_depot = key[:(key.find('_') + 1)]
            nodes.append(key_depot + time_window_nodes[k])
            acc += flow[(key_depot + time_window_nodes[k] + '_s', key_depot + time_window_nodes[k] + '_e')]
    print('nodes: ', nodes)
    print(shipment_per_depot[0][i])
    model.addConstr(acc == 1, "exactly_one_" + shipment_per_depot[0][i])

# for ship_id in base_shipments_data:
#     acc = 0
#     nodes = []
#     time_window_nodes = base_to_windowed_map[ship_id]
#     for time_window_node in time_window_nodes:
#         for depot in depot_list:
#             nodes.append(depot + '_' + time_window_node)
#             acc += flow[(depot + '_' + time_window_node + '_s', depot + '_' + time_window_node + '_e')]
#     model.addConstr(acc == 1, "exactly_one_" + ship_id)

# Capacity cap depots: every layer has a maximum flow equal to the maximum depot capacity.
for i in range(len(depot_nodes_start)):
    model.addConstrs(
        (flow.sum(start_node, '*') <= depots_data[start_node[:-2]]
         for start_node in depot_nodes_start), "depot_cap"
    )

# Optimize the model
model.Params.MIPGap = gap_percentage/100
model.Params.MIPFocus = 1
tic = time.time()
model.optimize()
toc = time.time()
time = toc - tic
print('running time: ', time)

# ---------------------------------------- Print the solution ----------------------------------------------------------

solution_arcs = []
if model.status == GRB.OPTIMAL:
    solution = model.getAttr('x', flow)
    for i, j in arcs:
        if solution[i, j] > 0:
            print('%s -> %s: %g' % (i, j, solution[i, j]))
            solution_arcs += [(i, j)]
    #         total_trucks = 0
    #         for depot_t in end_depot_nodes:
    #             for i,_ in solution_arcs:
    #                 if i == depot_t:
    #                     total_trucks += solution[i, j]
    # print('The total number of trucks needed is: ' + total_trucks)

# ---------------------------------------- Visualize solution as graph ------------------------------------------------

# # Graph Flow Model
# plt.figure(figsize=(20, 10))
# h = nx.Graph(arcs)
# pos = nx.random_layout(h)
# nx.draw(h, pos, with_labels=True, font_size=20)
# plt.savefig('Network Flow Model Graph.png')
#
# # Graph Flow Model
# plt.figure(figsize=(20, 10))
# k = nx.Graph(solution_arcs)
# pos = nx.spring_layout(h)
# nx.draw(k, pos, with_labels=True, font_size=20)
# plt.savefig('Network Flow Solution Graph.png')
#
# # Graph showing different cycles
# plt.figure(figsize=(20, 10))
# f = nx.Graph(solution_arcs)
# pos = nx.spring_layout(f)
# nx.draw(f, pos, with_labels=True, font_size=16)
# plt.savefig('Network Cycle Solution Graph.png')

# Graph showing different cycles
plt.figure(figsize=(20, 10))
f = nx.Graph(solution_arcs)
#fixed_positions = {'Ermelo_s':(0,0), 'Ermelo_t': (0.0), 'FC1_s': (0,0), 'FC2_s': (0,0), 'FC1_t': (0,0), 'FC2_t': (0,0)}
#fixed_nodes = fixed_positions.keys()
pos = nx.spring_layout(f)
nx.draw(f, pos, with_labels=True, font_size=16)
plt.savefig('Depot Solution Graph.png')

# Directed graph generating different truck trips from cycles in the graph
g = nx.DiGraph(solution_arcs)

# Making sure that every cycle goes from 's', to the shipments, to 't'
cycles_s_to_t = []
real_cycles = []
for cycle in nx.simple_cycles(g):
    number = 1
    cycle_s_to_t = []
    for node in cycle:
        if node in depot_nodes_start:
            for i in range(len(cycle)):
                cycle_s_to_t.append(cycle[(cycle.index(node) + i) % len(cycle)])
    print('cycle s to t: ', cycle_s_to_t)
    cycles_s_to_t.append(cycle_s_to_t)
    real_cycle = [cycle_s_to_t[0]]
    for i in range(len(cycle_s_to_t)-1):
        if cycle_s_to_t[i][:-2] == cycle_s_to_t[i+1][:-2]:
            real_cycle.append(cycle_s_to_t[i])
    real_cycle += [cycle_s_to_t[-1]]
    real_cycles.append(real_cycle)
    #print('real: ', real_cycle)

cycles = []
visited = set()
for cycle in real_cycles:
    should_continue = False
    for ship in cycle:
        if ship not in depot_nodes_start and ship not in depot_nodes_end and ship in visited:
            should_continue = True
    if should_continue:
        continue
    cycles.append(cycle)
    for ship in cycle:
        visited.add(ship)

# Print the different truck trips
number = 1
for cycle in cycles:
    print('truck trip ' + str(number) + ': ' + str(cycle))
    number += 1

number_of_vehicles = len(cycles)
# print('cycles: ', cycles)

# ----------------------------------------- Evaluate Solution ---------------------------------------------------------

# Analyze input data

# Sum over the duration of the shipments to generate the total number of hours that have to be planned
total_hours_input = 0
for ship_id, ship_data in base_shipments_data.items():
    ship_duration = ship_data['earliest_end_time'] - ship_data['earliest_start_time']
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
def start_loc_ith_trip_in_cycle(j):
    shipment = cycle[j][cycle[j].index('_') + 1:]
    return shipments_data[shipment]['start_location']


def end_loc_ith_trip_in_cycle(j):
    shipment = cycle[j][cycle[j].index('_') + 1:]
    return shipments_data[shipment]['end_location']


def driving_time_from_ith_trip_to_next_trip(j):
    return time_diff_matrix.at[end_loc_ith_trip_in_cycle(j), start_loc_ith_trip_in_cycle(j + 1)]


def start_time_ith_trip_in_cycle(j):
    shipment = cycle[j][cycle[j].index('_') + 1:]
    return shipments_data[shipment]['start_time']


def end_time_ith_trip_in_cycle(j):
    shipment = cycle[j][cycle[j].index('_') + 1:]
    return shipments_data[shipment]['end_time']


def duration_ith_trip_in_cycle(j):
    return end_time_ith_trip_in_cycle(j) - start_time_ith_trip_in_cycle(j)


def get_depot_from_cycle(cycle):
    depot = cycle[0][:cycle[0].index('_')]
    return depot


def get_duration_from_cycle(cycle):
    first_ship_id = cycle[1][cycle[1].index('_') + 1:]
    last_ship_id = cycle[-2][cycle[-2].index('_') + 1:]
    duration = time_diff_matrix.at[get_depot_from_cycle(cycle), shipments_data[first_ship_id]['start_location']] + \
               (shipments_data[last_ship_id]['end_time'] - shipments_data[first_ship_id]['start_time']) + \
               time_diff_matrix.at[shipments_data[last_ship_id]['end_location'], get_depot_from_cycle(cycle)]
    return duration


for cycle in cycles:
    depot = get_depot_from_cycle(cycle)
    # Pull out trips
    pull_out_time = time_diff_matrix.at[depot, start_loc_ith_trip_in_cycle(1)]
    total_pull_out_time += pull_out_time
    # Shipment trips
    shipment_time = 0
    for i in range(len(cycle) - 2):
        one_shipment_time = end_time_ith_trip_in_cycle(i + 1) - start_time_ith_trip_in_cycle(i + 1)
        shipment_time += one_shipment_time
    total_shipment_time_check += shipment_time
    # Driving empty in between shipments
    empty_driving_time = 0
    for i in range(len(cycle) - 3):
        one_empty_driving_time = time_diff_matrix.at[
            end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
        empty_driving_time += one_empty_driving_time
    total_empty_driving_time += empty_driving_time
    # Waiting time in between shipments
    waiting_time = 0
    for i in range(len(cycle) - 3):
        one_waiting_time = start_time_ith_trip_in_cycle(i + 2) - end_time_ith_trip_in_cycle(i + 1) - \
                           time_diff_matrix.at[end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
        waiting_time += one_waiting_time
    total_waiting_time += waiting_time
    # Pull in trips
    pull_in_time = time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), depot]
    total_pull_in_time += pull_in_time
    # Durations
    truck_trip_durations.append(round(get_duration_from_cycle(cycle), 2))
    driving_time = round(
        pull_out_time - (len(cycle) - 2) * loading_time + shipment_time + empty_driving_time + pull_in_time, 2)
    truck_trip_driving_time.append(driving_time)

number_too_long_duration = 0
for h in truck_trip_durations:
    if h > max_duration:
        number_too_long_duration += 1

number_too_long_driving_time = 0
for h in truck_trip_durations:
    if h > max_driving_time:
        number_too_long_driving_time += 1

for h in truck_trip_durations:
    total_hours_planned += h

inefficiency_percentage = (total_hours_planned - total_hours_input) / total_hours_planned
inefficiency_percentage_no_pull_arcs = (total_hours_planned - total_hours_input - total_pull_out_time -
                                        total_pull_in_time) / total_hours_planned

# Print the different variables
print('The total waiting time is: ', str(round(total_waiting_time, 2)), ' hours')
print('The total empty driving time is: ', str(total_empty_driving_time), ' hours')
print('The total pull out time is: ', str(total_pull_out_time), ' hours')
print('The total pull in time is: ', str(total_pull_in_time), ' hours')
print('The durations of the truck trips are: ', str(truck_trip_durations))
print('Of which ', number_too_long_duration, ' are too long')
print('The total number of hours driving is: ', str(truck_trip_driving_time))
print('Of which ', number_too_long_driving_time, ' are too long')
print('The total hours of input is: ', str(round(total_hours_input, 2)), ' hours')
print('The total hours planned is: ', str(round(total_hours_planned, 2)), ' hours')
print('The inefficiency percentage (i.e. percentage of hours in planning that is devoted to something else than '
      'executing shipments) is: ', str(round(100 * inefficiency_percentage, 2)), '%')
print('The inefficiency percentage without pull out/in is: ', str(round(100 * inefficiency_percentage_no_pull_arcs, 2)),
      '%')


def get_driving_time_from_cycle(cycle):
    cycle_index = cycles.index(cycle)
    driving_time = truck_trip_driving_time[cycle_index]
    return driving_time


# Find reliefpoints
relief_dict = {}
for cycle in cycles:
    cycle_key = tuple(cycle)
    depot = get_depot_from_cycle(cycle)
    relief_dict[cycle_key] = []
    for i in range(len(cycle) - 2):
        if start_loc_ith_trip_in_cycle(i + 1) == depot:
            relief_dict[cycle_key].append(start_time_ith_trip_in_cycle(i + 1))
        if end_loc_ith_trip_in_cycle(i + 1) == depot:
            relief_dict[cycle_key].append(end_time_ith_trip_in_cycle(i + 1))

# ------------------------------------- Visualize solution as Gantt Chart -------------------------------------------

# figure parameters
bar_height = 3
space_between_bars = 3
space_below_lowest_bar = 3
space_above_highest_bar = 3

# Constructing the figure
fig, gnt = plt.subplots(figsize=(20, 10))
fig = plt.subplots_adjust(right=0.58)

plt.title('Visualization optimal solution of MDVSPTW')
gnt.grid(False)

# Constructing the axes
# x axis
gnt.set_xlim(-1, 23)
gnt.set_xlabel('Time')
gnt.set_xticks([i for i in range(23)])
gnt.set_xticklabels(['04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
                     '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '00:00', '01:00', '02:00'],
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
    depot = get_depot_from_cycle(cycle)
    # Pull out trips
    if depot == 'DC1':
        gnt.broken_barh([(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[depot, start_loc_ith_trip_in_cycle(1)],
                          time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), depot])],
                        (y, bar_height), facecolors='tab:cyan', edgecolor='black')
    elif depot == 'Ermelo':
        gnt.broken_barh([(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[depot, start_loc_ith_trip_in_cycle(1)],
                          time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), depot])],
                        (y, bar_height), facecolors='tab:green', edgecolor='black')
    else:
        gnt.broken_barh([(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[depot, start_loc_ith_trip_in_cycle(1)],
                          time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), depot])],
                        (y, bar_height), facecolors='tab:purple', edgecolor='black')
    # Shipment trips
    for i in range(len(cycle) - 2):
        gnt.broken_barh([(start_time_ith_trip_in_cycle(i + 1),
                          duration_ith_trip_in_cycle(i + 1))],
                        (y, bar_height), facecolors='tab:orange', edgecolor='black')
    # Driving empty in between shipments
    for i in range(len(cycle) - 3):
        gnt.broken_barh([(end_time_ith_trip_in_cycle(i + 1),
                          driving_time_from_ith_trip_to_next_trip(i + 1))],
                        (y, bar_height), facecolors='tab:blue', edgecolor='black')
    # Waiting time in between shipments
    for i in range(len(cycle) - 3):
        gnt.broken_barh([(end_time_ith_trip_in_cycle(i + 1) + driving_time_from_ith_trip_to_next_trip(i + 1),
                          start_time_ith_trip_in_cycle(i + 2) - end_time_ith_trip_in_cycle(i + 1) -
                          driving_time_from_ith_trip_to_next_trip(i + 1))],
                        (y, bar_height), facecolors='tab:grey', edgecolor='black')
    # Pull in trips
    if depot == 'DC1':
        gnt.broken_barh([(end_time_ith_trip_in_cycle(len(cycle) - 2),
                          time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), depot])], (y, bar_height),
                        facecolors='tab:cyan', edgecolor='black', label=str(cycle[len(cycle) - 2]))
    elif depot == 'Ermelo':
        gnt.broken_barh([(end_time_ith_trip_in_cycle(len(cycle) - 2),
                          time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), depot])], (y, bar_height),
                        facecolors='tab:green', edgecolor='black', label=str(cycle[len(cycle) - 2]))
    else:
        gnt.broken_barh([(end_time_ith_trip_in_cycle(len(cycle) - 2),
                          time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), depot])], (y, bar_height),
                        facecolors='tab:purple', edgecolor='black', label=str(cycle[len(cycle) - 2]))
    # Reliefpoints
    cycle_key = tuple(cycle)
    if get_duration_from_cycle(cycle) <= max_duration and get_driving_time_from_cycle(cycle) <= max_driving_time:
        for relief_time in relief_dict[cycle_key]:
            gnt.annotate('', (relief_time, y + bar_height),
                         xytext=(relief_time, y + bar_height + 2),
                         arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='pink', edgecolor='pink',
                                         shrink=0.05), fontsize=6, horizontalalignment='right', verticalalignment='top')
    if get_duration_from_cycle(cycle) <= max_duration and get_driving_time_from_cycle(cycle) > max_driving_time:
        for relief_time in relief_dict[cycle_key]:
            gnt.annotate('', (relief_time, y + bar_height),
                         xytext=(relief_time, y + bar_height + 2),
                         arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='maroon', edgecolor='maroon',
                                         shrink=0.05), fontsize=6, horizontalalignment='right', verticalalignment='top')
    if get_duration_from_cycle(cycle) > max_duration:
        for relief_time in relief_dict[cycle_key]:
            gnt.annotate('', (relief_time, y + bar_height),
                         xytext=(relief_time, y + bar_height + 2),
                         arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor='r', edgecolor='r',
                                         shrink=0.05), fontsize=6, horizontalalignment='right', verticalalignment='top')

    # Step up in y direction
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
    'Total hours of input was: ' + str(round(total_hours_input, 2)) + ' hours \n' + 'The inefficiency is: {0}%'.format(
        str(round(100 * inefficiency_percentage, 2))) + '\n' + \
    'The inefficiency without stem trips is: ' + str(round(100 * inefficiency_percentage_no_pull_arcs, 2)) + '%'

plt.text(1.05, 0.3, txt, horizontalalignment='left',
         verticalalignment='center', transform=gnt.transAxes)

# Save the figure
plt.savefig("figures/gantt chart MDVSPTW TSN.png")
