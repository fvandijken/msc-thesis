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
from operator import itemgetter
import sys

# -------------------------------------------- Give input to the model ----------------------------------------------

# Files
shipment_file = constants.shipment_file
time_diff_matrix_file = constants.time_diff_matrix_file

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
print(shipments_data_df)

# Import Shipments from csv to dictionary
with open(shipment_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    shipments_data_s = {row['Shipment_ID'] + '.s': {'start_time': float(row['Starting_Time']),
                                                    'end_time': float(row['Ending_Time']),
                                                    'start_location': row['Starting_Location'],
                                                    'end_location': row['Ending_Location']}
                        for row in reader}
with open(shipment_file, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    shipments_data_e = {row['Shipment_ID'] + '.e': {'start_time': float(row['Starting_Time']),
                                                    'end_time': float(row['Ending_Time']),
                                                    'start_location': row['Starting_Location'],
                                                    'end_location': row['Ending_Location']}
                        for row in reader}

shipments_data = {**shipments_data_s, **shipments_data_e}

N = len(shipments_data_s)
print(N)
# print('SHIPMENTS AS DICTIONARY: ')
# pretty(shipments_data)

# Import time difference matrix from csv to dataframe.
# The time difference matrix gives the driving time between all different locations.
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)

print(time_diff_matrix.head())

# -------------------------------------Translate data to the Network Flow Graph--------------------------------------


# Construct nodes of the Network Flow Graph
start_nodes = [ship_id for (ship_id, ship_data) in shipments_data_s.items()]
end_nodes = [ship_id for (ship_id, ship_data) in shipments_data_e.items()]
nodes = start_nodes + end_nodes + ['s', 't']
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

# Construct first matches
arcs_dict = {}
print('number of locations: ' + str(len(locations)))
print('number of connection based arcs: ' + str(len(comp_arcs)))
first_matches = []
for location in locations:
    for end_ship_id, end_ship_data in filter(lambda item: item[1]['end_location'] == location,
                                             shipments_data_e.items()):
        for next_location in locations - set(location):
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
            arcs_dict[latest_first_match] = N

print('number of latest first matches: ', len(latest_first_matches))


# Determine the cost for the compatibility arcs
# Determine the empty driving time between the execution of shipment 1 and shipment 2
def empty_driving_time(ship_1, ship_2):
    return time_diff_matrix.at[ship_1['end_location'], ship_2['start_location']]


# Determine the waiting time between the execution of shipment 1 and shipment 2
def waiting_time(ship_1, ship_2):
    return ship_2['start_time'] - ship_1['end_time'] - empty_driving_time(ship_1, ship_2)


# The cost of compatibility arc (ship 1, ship 2) is the operational cost of executing shipment 2 after shipment 1
# The operational cost is weighted sum of the empty driving time and the waiting time

def cost(end_ship_id, start_ship_id):
    end_ship_data = shipments_data_e[end_ship_id]
    start_ship_data = shipments_data_s[start_ship_id]
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
        arcs_dict[waiting_arc] = len(starting_shipments)
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
        arcs_dict[waiting_arc] = len(ending_shipments)
        cost[waiting_arc] = weight_waiting_time * (next_end_time - this_end_time)
        count_waiting_arcs += 1

print('number of waiting arcs: ', count_waiting_arcs)
print('number of time space based arcs: ', len(arcs_dict))

# Construct shipment arcs
for (start_ship_id, start_ship_data) in shipments_data_s.items():
    for (end_ship_id, end_ship_data) in shipments_data_e.items():
        if start_ship_id != end_ship_id and start_ship_data == end_ship_data:
            shipment_arc = (start_ship_id, end_ship_id)
            arcs_dict[shipment_arc] = 1
            cost[shipment_arc] = 0

print('number of time space based arcs with shipments arcs: ', len(arcs_dict))

# Construct pull out / pull in arcs with flow upper bound and cost
# The cost of the pull out arcs is a fixed cost for adding a new truck to the planning plus the operational costs

for (start_ship_id, start_ship_data) in shipments_data_s.items():
    time_diff_from_depot = weight_empty_driving_time * time_diff_matrix.at[constants.name_depot, start_ship_data['start_location']]
    pull_out_arc = ('s', start_ship_id)
    arcs_dict[pull_out_arc] = 1
    cost[pull_out_arc] = fixed_cost_new_truck + time_diff_from_depot

# The cost of the pull in arcs is the operational costs
for (end_ship_id, end_ship_data) in shipments_data_e.items():
    time_diff_to_depot = weight_empty_driving_time * time_diff_matrix.at[end_ship_data['end_location'], constants.name_depot]
    pull_in_arc = (end_ship_id, 't')
    arcs_dict[pull_in_arc] = 1
    cost[pull_in_arc] = time_diff_to_depot

# Construct circulation arc with flow upper bound and cost
arcs_dict[('t', 's')] = N
cost[('t', 's')] = 0

# Define the variables
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
for start_node, end_node in list(zip(start_nodes, end_nodes)):
    model.addConstr(flow[start_node, end_node] == 1)
    # model.addConstr(flow.sum('*', node) == 1, "cap incoming node %s" % node)
    # model.addConstr(flow.sum(node, '*') == 1,
    #                "cap outgoing node %s" % node)

# Optimize the model
model.optimize()

# ---------------------------------------- Print the solution ----------------------------------------------------------

solution_arcs = []
if model.status == GRB.OPTIMAL:
    solution = model.getAttr('x', flow)
    for i, j in arcs:
        if solution[i, j] > 0:
            print('%s -> %s: %g' % (i, j, solution[i, j]))
            solution_arcs += [(i, j)]
    print('The total number of trucks needed is: ' + str(int(solution['t', 's'])))

# ---------------------------------------- Visualize solution as graph ------------------------------------------------

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
# pos = nx.spring_layout(k, pos=fixed_positions, fixed=fixed_nodes)
# nx.draw(k, pos, with_labels=True, font_size=20)
# plt.savefig('Network Flow Solution Graph.png')

# Graph showing different cycles
plt.figure(figsize=(20, 10))
f = nx.Graph(solution_arcs)
fixed_positions = {'s': (0, 0), 't': (0, 0)}
fixed_nodes = fixed_positions.keys()
pos = nx.spring_layout(f, pos=fixed_positions, fixed=fixed_nodes)
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
        if node == 's':
            for i in range(len(cycle)):
                cycle_s_to_t.append(cycle[(cycle.index(node) + i) % len(cycle)])
    #print('cycle s to t: ', cycle_s_to_t)
    cycles_s_to_t.append(cycle_s_to_t)
    real_cycle = ['s']
    for i in range(len(cycle_s_to_t)-1):
        if cycle_s_to_t[i][:-2] == cycle_s_to_t[i+1][:-2]:
            real_cycle.append(cycle_s_to_t[i])
    real_cycle += ['t']
    real_cycles.append(real_cycle)
    #print('real: ', real_cycle)

cycles = []
visited = set()
for cycle in real_cycles:
    should_continue = False
    for ship in cycle:
        if ship != 's' and ship != 't' and ship in visited:
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
#print('cycles: ', cycles)

# ----------------------------------------- Evaluate Solution ---------------------------------------------------------

# Analyze input data

# Sum over the duration of the shipments to generate the total number of hours that have to be planned
total_hours_input = 0
for ship_id, ship_data in shipments_data_s.items():
    ship_duration = shipments_data[ship_id]['end_time'] - shipments_data[ship_id]['start_time']
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


# Define functions to make the code better readable
def start_loc_ith_trip_in_cycle(j):
    return shipments_data[cycle[j]]['start_location']


def end_loc_ith_trip_in_cycle(j):
    return shipments_data[cycle[j]]['end_location']


def driving_time_from_ith_trip_to_next_trip(j):
    return time_diff_matrix.at[end_loc_ith_trip_in_cycle(j), start_loc_ith_trip_in_cycle(j + 1)]


def start_time_ith_trip_in_cycle(j):
    return shipments_data[cycle[j]]['start_time']


def end_time_ith_trip_in_cycle(j):
    return shipments_data[cycle[j]]['end_time']


def duration_ith_trip_in_cycle(j):
    return end_time_ith_trip_in_cycle(j) - start_time_ith_trip_in_cycle(j)


for cycle in cycles:
    # Pull out trips
    total_pull_out_time += time_diff_matrix.at[constants.name_depot, start_loc_ith_trip_in_cycle(1)]
    # Shipment trips
    for i in range(len(cycle) - 2):
        total_shipment_time_check += end_time_ith_trip_in_cycle(i + 1) - start_time_ith_trip_in_cycle(i + 1)
    # Driving empty in between shipments
    for i in range(len(cycle) - 3):
        total_empty_driving_time += time_diff_matrix.at[
            end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
    # Waiting time in between shipments
    for i in range(len(cycle) - 3):
        total_waiting_time += start_time_ith_trip_in_cycle(i + 2) - end_time_ith_trip_in_cycle(i + 1) - \
                              time_diff_matrix.at[end_loc_ith_trip_in_cycle(i + 1), start_loc_ith_trip_in_cycle(i + 2)]
    # Pull in trips
    total_pull_in_time += time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), constants.name_depot]
    # Durations
    truck_trip_durations.append(round(end_time_ith_trip_in_cycle(len(cycle) - 2) + \
                                      time_diff_matrix.at[
                                          end_loc_ith_trip_in_cycle(len(cycle) - 2), constants.name_depot] -
                                      (start_time_ith_trip_in_cycle(1) -
                                       time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), constants.name_depot]), 2))

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
print('The total hours of input is: ', str(round(total_hours_input, 2)), ' hours')
print('The total hours planned is: ', str(round(total_hours_planned, 2)), ' hours')
print('The inefficiency percentage (i.e. percentage of hours in planning that is devoted to something else than '
      'executing shipments) is: ', str(round(100 * inefficiency_percentage, 2)), '%')
print('The inefficiency percentage without pull out/in is: ', str(round(100 * inefficiency_percentage_no_pull_arcs, 2)),
      '%')

# ------------------------------------- Visualize solution as Gantt Chart -------------------------------------------

# figure parameters
bar_height = 2
space_between_bars = 2
space_below_lowest_bar = 2
space_above_highest_bar = 2

# Constructing the figure
fig, gnt = plt.subplots(figsize=(10, 5))
fig = plt.subplots_adjust(right=0.58)

plt.title('Visualization of optimal solution of SDVSP for N=75')
gnt.grid(False)

# Constructing the axes
# x axis
gnt.set_xlim(-1, 21)
gnt.set_xlabel('Time')
gnt.set_xticks([i for i in range(21)])
gnt.set_xticklabels(['04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
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
    gnt.broken_barh(
        [(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[constants.name_depot, start_loc_ith_trip_in_cycle(1)],
          time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), constants.name_depot])],
        (y, bar_height), facecolors='tab:green', edgecolor='black')
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
    gnt.broken_barh([(end_time_ith_trip_in_cycle(len(cycle) - 2),
                      time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), constants.name_depot])],
                    (y, bar_height),
                    facecolors='tab:green', edgecolor='black', label=str(cycle[len(cycle) - 2]))
    y += bar_height + space_between_bars

# Constructing the legend
legend_elements = [Line2D([0], [0], color='tab:orange', lw=6, label='Shipment'),
                   Line2D([0], [0], color='tab:green', lw=6, label='Stem trips'),
                   Line2D([0], [0], color='tab:blue', lw=6, label='Empty Driving'),
                   Line2D([0], [0], color='tab:grey', lw=6, label='Waiting')]
gnt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

# Printing analytics in the gantt chart
txt = \
    'Total waiting time is: ' + str(round(total_waiting_time, 2)) + ' hours \n' + 'Total empty driving time ' \
                                                                                  'and stem time is: ' + str(
        total_empty_driving_time + total_pull_in_time + total_pull_out_time) + ' hours \n' + \
    'Total number of hours planned is: ' + str(round(total_hours_planned, 2)) + ' hours \n' + \
    'Total hours of input was: ' + str(round(total_hours_input, 2)) + ' hours \n' + 'The inefficiency is: {0}%'.format(
        str(round(100 * inefficiency_percentage, 2))) + '\n' + \
    'The inefficiency without pull arcs is: ' + str(round(100 * inefficiency_percentage_no_pull_arcs, 2)) + '%'

plt.text(1.05, 0.3, txt, horizontalalignment='left', verticalalignment='center', transform=gnt.transAxes)

# Save the figure
plt.savefig("figures/gantt chart SDVSP_TSN.png")
