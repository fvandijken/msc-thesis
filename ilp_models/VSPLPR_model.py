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
import operator

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
# Max and min duration
max_duration = constants.max_duration
min_duration = constants.min_duration
# depot
name_depot = constants.name_depot

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
    shipments_data = {row['Shipment_ID']: {'start_time': float(row['Starting_Time']),
                                           'end_time': float(row['Ending_Time']),
                                           'start_location': row['Starting_Location'],
                                           'end_location': row['Ending_Location']}
                      for row in reader}

N = len(shipments_data)
print(N)
# print('SHIPMENTS AS DICTIONARY: ')
# pretty(shipments_data)

# Import time difference matrix from csv to dataframe.
# The time difference matrix gives the driving time between all different locations.
time_diff_matrix = pd.read_csv(time_diff_matrix_file)
time_diff_matrix.set_index('Location', drop=True, inplace=True)

print(time_diff_matrix)

# -------------------------------------Translate data to the Network Flow Graph--------------------------------------

# Construct nodes of the Network Flow Graph
nodes = [ship_id for (ship_id, ship_data) in shipments_data.items()]

# Construct compatibility arcs with flow upper bound and cost

# The compatibility arcs are the arcs that connect shipment 1 to shipment 2 iff it is feasible to execute shipment 1,
# drive to the start location of shipment 2, and start shipment 2.
# Initiate the arcs and give them flow upper bound 1
compatibility_arcs = {}
for (first_ship_id, first_ship_data) in shipments_data.items():
    for (second_ship_id, second_ship_data) in shipments_data.items():
        waiting_time = second_ship_data['start_time'] - first_ship_data['end_time'] - \
                time_diff_matrix.at[first_ship_data['end_location'], second_ship_data['start_location']]
        if 0 <= waiting_time <= max_waiting_time:
            compatibility_arc = (first_ship_id, second_ship_id)
            compatibility_arcs[compatibility_arc] = 1
print('Number of compatibility arcs: ', len(compatibility_arcs.keys()))


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
cost = {arc: cost(arc[0], arc[1]) for (arc, _) in compatibility_arcs.items()}

# Create graph consisting of all shipments as nodes and all compatibility arcs as edges
plt.figure()
h = nx.DiGraph(compatibility_arcs.keys())
pos = nx.shell_layout(h)
nx.draw(h, pos, with_labels=True)
plt.savefig('Compatibility Graph.png')

# The backwards arcs are the arcs that connect shipment 2 to shipment 1 iff starting the trip with shipment 1 and
# ending it with shipment 2 does not exceed the maximal duration of a working day
# Note that it is only necessary to construct a backward arc (j, i) if there is a path in the compatibility graph from
# i to j. Otherwise you will never define a working day starting with i and finishing with j anyway.

# Initiate the arcs and give them flow upper bound 1
backward_arcs = {}
for (first_ship_id, first_ship_data) in shipments_data.items():
    for (second_ship_id, second_ship_data) in shipments_data.items():
        if second_ship_id != first_ship_id:
            if nx.has_path(h, first_ship_id, second_ship_id):
                if min_duration < time_diff_matrix.at[name_depot, first_ship_data['start_location']] + \
                        (second_ship_data['end_time'] - first_ship_data['start_time']) + \
                        time_diff_matrix.at[second_ship_data['end_location'], name_depot] <= \
                        max_duration:
                    backward_arc = (second_ship_id, first_ship_id)
                    backward_arcs[backward_arc] = 1
                    cost[backward_arc] = fixed_cost_new_truck + \
                                         time_diff_matrix.at[name_depot, first_ship_data['start_location']] + \
                                         time_diff_matrix.at[second_ship_data['end_location'], name_depot]
print('Number of backwards arcs: ', len(backward_arcs.keys()))


# In order for it to be possible to have a truck executing only 1 trip during a working day, it is necessary to add
# self-loops on every node
for ship_id, ship_data in shipments_data.items():
    self_loop_arc = (ship_id, ship_id)
    backward_arcs[self_loop_arc] = 1
    cost[self_loop_arc] = fixed_cost_new_truck + \
                          time_diff_matrix.at[name_depot, ship_data['start_location']] + \
                          time_diff_matrix.at[ship_data['end_location'], name_depot]

comp_arcs, flow_upper_c = gp.multidict(compatibility_arcs)
backw_arcs, flow_upper_b = gp.multidict(backward_arcs)


# Now we only need to do one thing before we can start defining the LP: creating a set of all cycles in the graph that
# contain two or more backward arcs. In order to do this, we create the graph.

# all arcs in a list
arcs = comp_arcs + backw_arcs

# create graph
Graph = nx.MultiDiGraph(arcs)
plt.figure(figsize=(12, 10))
pos = nx.shell_layout(Graph)
nx.draw(Graph, pos=pos, edge_color='red')
plt.savefig('Graph with compatibility arcs.png')

# construct list of all cycles
cycles = []
for cycle in nx.simple_cycles(Graph):
    cycles.append(cycle)

# we only need to consider the cycles that consist of 3 or more arcs, otherwise they cannot contain 2 or more backw arcs
long_enough_cycles_nodes = []
for cycle in cycles:
    if len(cycle) > 2:
        long_enough_cycles_nodes.append(cycle)

# express the found cycles in edges instead of nodes
long_enough_cycles_arcs = []
for cycle in long_enough_cycles_nodes:
    edge_cycle = []
    for i in range(len(cycle) - 1):
        edge_cycle.append((cycle[i], cycle[i + 1]))
    edge_cycle.append((cycle[len(cycle) - 1], cycle[0]))
    long_enough_cycles_arcs.append(edge_cycle)

print('Number of cycles of length > 2 in graph: ', len(long_enough_cycles_nodes))

# Select all cycles in the set that have two or more backwards arcs and put them in a new set
multiple_backward_edge_cycles = []
for cycle in long_enough_cycles_arcs:
    count = 0
    for edge in cycle:
        if edge in list(backward_arcs.keys()):
            count += 1
    if count >= 2:
        multiple_backward_edge_cycles.append(cycle)

print('Number of cycles with > 1 backw arc: ', len(multiple_backward_edge_cycles))

# -------------------------------------- Optimization model -----------------------------------------------------------


model = gp.Model('min-cost-flow')

# Decision variables
comp_flow = model.addVars(comp_arcs, obj=cost, vtype=GRB.INTEGER, name="compatibilityflow")
backw_flow = model.addVars(backw_arcs, obj=cost, vtype=GRB.INTEGER, name="backwardsflow")

# model.setObjective(cost[comp_flow], GRB.MINIMIZE)

# Constraints
# Flow upper bound for every arc: For every arc the flow is bounded by an upperbound.
model.addConstrs(
    (comp_flow[i, j] <= 1 for i, j in comp_arcs), "uppercomp")

model.addConstrs(
    (backw_flow[i, j] <= 1 for i, j in backw_arcs), "upperbackw")

# Flow conservation for every node: For every node the incoming flow is exactly the same as the outgoing flow.
model.addConstrs(
    (comp_flow.sum(node, '*') + backw_flow.sum(node, '*') == comp_flow.sum('*', node) + backw_flow.sum('*', node)
     for node in nodes), "conservation")

# Flow requirement for shipment nodes: For every shipment node the incoming and outgoing flow is exactly 1.
for node in nodes:
    model.addConstr(comp_flow.sum('*', node) + backw_flow.sum('*', node) == 1,
                    "requiredflow%s" % node)
    # model.addConstr(flow.sum(node, '*') == 1,
    #                 "cap outgoing node %s" % node)

# Er mogen geen twee backwards arcs in een cycle zitten.
for cycle in multiple_backward_edge_cycles:
    acc = 0
    for edge in cycle:
        acc += comp_flow.get(edge, 0)
        acc += backw_flow.get(edge, 0)
    model.addConstr(acc <= len(cycle) - 1,
                    "multibackwarcs")

# Optimize the model
model.optimize()
model.write("mymodel.mps")

# ---------------------------------------- Print the solution ----------------------------------------------------------

comp_solution_arcs = []
backw_solution_arcs = []
if model.status == GRB.OPTIMAL:
    comp_solution = model.getAttr('x', comp_flow)
    backw_solution = model.getAttr('x', backw_flow)
    for i, j in comp_arcs:
        if comp_solution[i, j] > 0:
            print('%s -> %s: %g' % (i, j, comp_solution[i, j]))
            comp_solution_arcs.append((i, j))
    for i, j in backw_arcs:
        if backw_solution[i, j] > 0:
            print('%s -> %s: %g' % (i, j, backw_solution[i, j]))
            backw_solution_arcs.append((i, j))
solution_arcs = comp_solution_arcs + backw_solution_arcs
# print('BACKWARD ARCS:')
# print(backw_solution_arcs)
# print('COMPATIBILITY ARCS:')
# print(comp_solution_arcs)
# print('ALL SOLUTION ARCS:')
# print(solution_arcs)


# ---------------------------------------- Visualize solution as graph ------------------------------------------------

# Graph Flow Visualization
plt.figure(figsize=(20, 10))
G = nx.Graph(solution_arcs)
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, font_size=20)
plt.savefig('Network Flow Solution Graph.png')
print('The total number of trucks needed is: ', nx.number_connected_components(G))
list_of_components = [c for c in sorted(nx.connected_components(G), key=len, reverse=True)]

trips = []
for component in list_of_components:
    trip = []
    for ship_id in component:
        trip.append(ship_id)
    trip.sort(key=lambda ship_id: shipments_data[ship_id]['start_time'])
    trips.append(trip)

cycles = []
for trip in trips:
    cycle = ['s'] + trip + ['t']
    cycles.append(cycle)

# print('cycles: ', cycles)


# Print the different truck trips
number = 1
for cycle in cycles:
    print('truck trip ' + str(number) + ': ' + str(cycle))
    number += 1

number_of_vehicles = len(cycles)

# ----------------------------------------- Evaluate Solution ---------------------------------------------------------

# Analyze input data

# Sum over the duration of the shipments to generate the total number of hours that have to be planned
total_hours_input = 0
for ship_id, ship_data in shipments_data.items():
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
    total_pull_out_time += time_diff_matrix.at[name_depot, start_loc_ith_trip_in_cycle(1)]
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
    total_pull_in_time += time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), name_depot]
    # Durations
    truck_trip_durations.append(round(end_time_ith_trip_in_cycle(len(cycle) - 2) + \
                                      time_diff_matrix.at[
                                          end_loc_ith_trip_in_cycle(len(cycle) - 2), name_depot] -
                                      (start_time_ith_trip_in_cycle(1) -
                                       time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), name_depot]), 2))

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
print('The total hours of input is: ', str(total_hours_input), ' hours')
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

plt.title(r'Visualization optimal solution of VSPLPR for $T_{max}=13$, N=15')
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
        [(start_time_ith_trip_in_cycle(1) - time_diff_matrix.at[name_depot, start_loc_ith_trip_in_cycle(1)],
          time_diff_matrix.at[start_loc_ith_trip_in_cycle(1), name_depot])],
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
                      time_diff_matrix.at[end_loc_ith_trip_in_cycle(len(cycle) - 2), name_depot])],
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
    'and stem time is: ' + str(total_empty_driving_time + total_pull_in_time + total_pull_out_time) + ' hours \n' + \
    'Total number of hours planned is: ' + str(round(total_hours_planned, 2)) + ' hours \n' + \
    'Total hours of input was: ' + str(total_hours_input) + ' hours \n' + 'The inefficiency is: {0}%'.format(
        str(round(100 * inefficiency_percentage, 2))) + '\n' + \
    'The inefficiency without pull arcs is: ' + str(round(100 * inefficiency_percentage_no_pull_arcs, 2)) + '%'

plt.text(1.05, 0.3, txt, horizontalalignment='left',
         verticalalignment='center', transform=gnt.transAxes)

# Save the figure
plt.savefig("figures/gantt chart VSPLPR.png")
