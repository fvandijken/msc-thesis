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
from operator import itemgetter
import constants
from itertools import chain
import os
from heuristics.Config import Config
import constants as c
from heuristics.InputTW import InputTW
from heuristics.Shipment import Shipment, ShipmentTW


class MDVSPTWILP_classes:

    def __init__(self, input: InputTW, config: Config):
        self.input = input
        self.shipments_tw = input.shipments_tw
        self.depots = input.depots
        self.config = config
        input.shipments_tw[0].discretize_time_windows(config)
        self.discretized_shipments = list(
            map(lambda shipment: shipment.discretize_time_windows(config), self.shipments_tw))
        self.flat_discretized_shipments = [shipment for lst in self.discretized_shipments for shipment in lst]

    def get_solution(self):
        depot_list = list(self.depots.keys())

        # Determine startup costs: take the average cost of driving from Ermelo to the start location
        total_fixed_cost = 0
        for depot in depot_list:
            fixed_cost = c.weight_empty_driving_time * 2 * c.time_diff_matrix.at['Ermelo', depot]
            total_fixed_cost += fixed_cost
        fixed_cost_new_truck = total_fixed_cost / len(depot_list)
        fixed_cost_new_truck = constants.fixed_cost_new_truck

        # Construct depot nodes
        depot_to_nodes_map = {}
        depot_to_nodes_without_depot_map = {}
        shipments_per_depot = []
        for depot in depot_list:
            nodes = []
            nodes_without_depot = []
            for shipment in self.flat_discretized_shipments:
                if 'IB' in shipment.type:
                    nodes.append(depot + '_' + shipment.id)
                    nodes_without_depot.append(shipment.id)
                elif shipment.start_location == depot:
                    nodes.append(depot + '_' + shipment.id)
                    nodes_without_depot.append(shipment.id)
            shipments_per_depot.append(nodes)
            depot_to_nodes_map[depot] = nodes
            depot_to_nodes_without_depot_map[depot] = nodes_without_depot
            # nodes_no_time_windows = list({depot + "_" + ship_id[:ship_id.rfind('.')] for ship_id in nodes})

        depot_nodes_start = [depot + '_s' for depot in depot_list]
        depot_nodes_end = [depot + '_t' for depot in depot_list]

        # Construct compatibility arcs with flow upper bound and cost

        # The compatibility arcs are the arcs that connect shipment 1 to shipment 2 iff it is feasible to execute shipment 1,
        # drive to the start location of shipment 2, and start shipment 2.
        # Initiate the arcs and give them flow upper bound 1

        arcs_dict = {}
        for depot in depot_list:
            for first_shipment in filter(lambda shipment: shipment.id in depot_to_nodes_without_depot_map[depot],
                                         self.flat_discretized_shipments):
                for second_shipment in filter(lambda shipment: shipment.id in depot_to_nodes_without_depot_map[depot],
                                              self.flat_discretized_shipments):
                    waiting_time = second_shipment.start_time - first_shipment.end_time - \
                                   c.time_diff_matrix.at[first_shipment.end_location, second_shipment.start_location]
                    if 0 <= waiting_time <= c.max_waiting_time:
                        arcs_dict[(first_shipment, second_shipment)] = 1

        # Assign the costs to the compatibility arcs
        cost = {
            arc: operational_cost(arc[0], arc[1]) for (arc, _) in arcs_dict.items()
        }

        # Construct pull out / pull in arcs with flow upper bound and cost
        # The cost of the pull out arcs is a fixed cost for adding a new truck to the planning plus the operational costs

        # pull out arcs
        for depot in depot_list:
            for shipment in filter(lambda shipment: shipment.id in depot_to_nodes_without_depot_map[depot],
                                   self.flat_discretized_shipments):
                time_diff_from_depot = c.weight_empty_driving_time * c.time_diff_matrix.at[
                    depot, shipment.start_location]
                pull_out_arc = (depot + "_s", shipment)
                arcs_dict[pull_out_arc] = 1
                cost[pull_out_arc] = fixed_cost_new_truck + time_diff_from_depot

        # pull in arcs
        for depot in depot_list:
            for shipment in filter(lambda shipment: shipment.id in depot_to_nodes_without_depot_map[depot],
                                               self.flat_discretized_shipments):
                time_diff_to_depot = c.weight_empty_driving_time * c.time_diff_matrix.at[
                    shipment.end_location, depot]
                pull_in_arc = (shipment, depot + "_t")
                arcs_dict[pull_in_arc] = 1
                cost[pull_in_arc] = time_diff_to_depot

        # Construct circulation arcs with flow upper bound and cost
        for depot in depot_list:
            circulation_arc = (depot + "_t", depot + "_s")
            arcs_dict[circulation_arc] = len(self.flat_discretized_shipments)
            cost[circulation_arc] = 0

        arcs, flow_upper = gp.multidict(arcs_dict)

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
        flat_nodes = [node for nodes in shipments_per_depot for node in nodes]
        all_nodes = flat_nodes + depot_nodes_start + depot_nodes_end
        model.addConstrs(
            (flow.sum(node, '*') == flow.sum('*', node)
             for node in all_nodes), "c")

        # Flow requirement in every shipment node: every shipment node has an inflow of exactly one in total in all layers.
        # Only visit one of the nodes for the same time window.

        # for i in range(len(shipments_per_depot[0])):
        #     acc = 0
        #     nodes = []
        #     for j in range(len(shipments_per_depot)):
        #         key = shipments_per_depot[j][i]
        #         time_window_nodes = base_to_windowed_map[key[(key.find('_') + 1):key.rfind('.')]]
        #         for k in range(len(time_window_nodes)):
        #             nodes.append(key[:(key.find('_') + 1)] + time_window_nodes[k])
        #             acc += flow.sum(key[:(key.find('_') + 1)] + time_window_nodes[k], '*')
        #     model.addConstr(acc == 1, "exactly_one_" + shipments_per_depot[0][i])
        for shipment_tw in self.shipments_tw:
            acc = 0
            nodes = []
            for potential_ship_id in flat_nodes:
                if shipment_tw.id in potential_ship_id:
                    nodes.append(potential_ship_id)
                    acc += flow.sum(potential_ship_id, '*')
            model.addConstr(acc == 1, "exactly_one_" + shipment_tw.id)

        # Capacity cap depots: every layer has a maximum flow equal to the maximum depot capacity.
        for i in range(len(depot_nodes_start)):
            model.addConstrs(
                (flow.sum(start_node, '*') <= self.depots[start_node[:-2]]
                 for start_node in depot_nodes_start), "depot_cap"
            )

        # Parameters
        # Termination Parameters
        model.Params.MIPGap = c.gap_percentage / 100
        # model.Params.timelimit = 300.0

        # Optimize the model
        model.optimize()

        # ---------------------------------------- Print the solution ----------------------------------------------------------

        solution_arcs = []
        if model.status == GRB.OPTIMAL:
            solution = model.getAttr('x', flow)
            for i, j in arcs:
                if solution[i, j] > 0:
                    # print('%s -> %s: %g' % (i, j, solution[i, j]))
                    solution_arcs += [(i, j)]
            #         total_trucks = 0
            #         for depot_t in end_depot_nodes:
            #             for i,_ in solution_arcs:
            #                 if i == depot_t:
            #                     total_trucks += solution[i, j]
            # print('The total number of trucks needed is: ' + total_trucks)

        # ---------------------------------------- Visualize solution as graph ------------------------------------------------

        # Directed graph generating different truck trips from cycles in the graph
        g = nx.DiGraph(solution_arcs)

        # Making sure that every cycle goes from 's', to the shipments, to 't'
        cycles = []
        for cycle in nx.simple_cycles(g):
            number = 1
            cycle_s_to_t = []
            for node in cycle:
                if node in depot_nodes_start:
                    for i in range(len(cycle)):
                        cycle_s_to_t.append(cycle[(cycle.index(node) + i) % len(cycle)])
            cycles.append(cycle_s_to_t)
        # cycles = sorted(cycles, key=lambda cycle: (
        #         shipments_data[cycle[1][(cycle[1].find('_') + 1):]]['start_time'] - c.time_diff_matrix.at[
        #     cycle[0][:cycle[0].find('_')], shipments_data[cycle[1][(cycle[1].find('_') + 1):]]['start_location']]))

        # Print the different truck trips
        number = 1
        for cycle in cycles:
            print('truck trip ' + str(number) + ': ' + str(cycle))
            number += 1

        # for cycle in cycles:
        #     for i in range(len(cycle)-2):
        #         print(cycle[i+1])

        number_of_vehicles = len(cycles)
        # print('cycles: ', cycles)

        for depot in depot_list:
            number_trucks_from_depot = 0
            for cycle in cycles:
                if depot in cycle[0]:
                    number_trucks_from_depot += 1
            print('number of trucks based at depot ', depot, ': ', number_trucks_from_depot)


# ---------------------------------------------- Help Functions ----------------------------------------------------

def empty_driving_time(shipment_1: Shipment, shipment_2: Shipment):
    return c.time_diff_matrix.at[shipment_1.end_location, shipment_2.start_location]


def waiting_time(shipment_1: Shipment, shipment_2: Shipment):
    return shipment_2.start_time - shipment_1.end_time - empty_driving_time(shipment_1, shipment_2)


def operational_cost(shipment_1: Shipment, shipment_2: Shipment):
    operational_cost = c.weight_waiting_time * waiting_time(shipment_1, shipment_2) + \
                       c.weight_empty_driving_time * empty_driving_time(shipment_1, shipment_2)
    return operational_cost
