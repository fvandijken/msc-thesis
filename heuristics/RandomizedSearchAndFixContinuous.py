from heuristics.Config import Config
from heuristics.InputTW import InputTW
from heuristics.Schedule import Schedule
import numpy as np
import random
import constants as c
import copy
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedtiesCS import RandomizedtiesCS
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.RandomizedtiesCSnomaxduration import RandomizedtiesCSnomaxduration
from heuristics.RandomizedCSnomaxduration import RandomizedCSnomaxduration


class RandomizedSearchAndFixContinuous:

    def __init__(self, input: InputTW, config: Config, input_trucks=None, sorted_shipments_tw=None):
        self.input = input
        self.config = config
        self.input_trucks = input_trucks
        self.shipments_tw = input.shipments_tw
        self.sorted_shipments_tw = sorted_shipments_tw

    def get_solution_old(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        best_solution = initial_solution
        best_score = initial_solution.get_costs_without_feasibility()
        splittable_trucks = best_solution.get_splittable_trucks()
        efficient_trucks = best_solution.get_efficient_trucks()
        fixed_trucks = splittable_trucks + efficient_trucks
        shipments_tbd = exclude_truck_shipments_from_list(fixed_trucks, self.shipments_tw)
        print(len(shipments_tbd))
        for i in range(number_of_iterations):
            number_of_fixed_trucks = len(fixed_trucks)
            new_cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_solution.post_improve_depots()
            splittable_trucks = new_solution.get_splittable_trucks()
            efficient_trucks = new_solution.get_efficient_trucks()
            if len(splittable_trucks) + len(efficient_trucks) > 0:
                print(number_of_fixed_trucks, ' fixed trucks: ')
                print([truck.id for truck in splittable_trucks])
                print([truck.id for truck in efficient_trucks])
                print('shipments to plan: ', len(shipments_tbd))
            fixed_trucks += splittable_trucks + efficient_trucks
            shipments_tbd = exclude_truck_shipments_from_list(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks(),
                                                                        shipments_tbd)
            print(new_solution.get_total_costs())
            if len(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks()) >= len(fixed_trucks):
                if len(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks()) > number_of_fixed_trucks:
                    best_solution = new_solution
                    best_score = new_solution.get_costs_without_feasibility()
                    print(best_score)
                elif new_solution.get_costs_without_feasibility() < best_score:
                    best_solution = new_solution
                    best_score = new_solution.get_costs_without_feasibility()
                    print(best_score)

        return best_solution, fixed_trucks

    def get_many_splittable_trucks(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        splittable_trucks = initial_solution.get_splittable_trucks()
        shipments_tbd = exclude_truck_shipments_from_list(splittable_trucks, self.shipments_tw)
        print(len(shipments_tbd))
        for i in range(number_of_iterations):
            new_cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_splittable_trucks = new_solution.get_splittable_trucks()
            if len(new_splittable_trucks) > 0:
                splittable_trucks += new_splittable_trucks
                number_of_splittable_trucks = len(splittable_trucks)
                print(number_of_splittable_trucks, ' fixed trucks: ')
                print([truck.id for truck in splittable_trucks])
                shipments_tbd = exclude_truck_shipments_from_list(new_splittable_trucks, shipments_tbd)
                print('shipments to plan: ', len(shipments_tbd))

        return splittable_trucks

    def get_solution(self, max_number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: (shipment_tw.latest_start_time, shipment_tw.latest_start_time - shipment_tw.earliest_start_time))
        shipments_tbd = self.shipments_tw
        print(len(shipments_tbd))
        trucks = []
        i = 0
        while len(shipments_tbd) > 0 and i < max_number_of_iterations:
            new_cs = RandomizedtiesCS(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_trucks = []
            print('\n', 'ROUND ', i+1)
            for truck in new_solution.get_trucks():
                accept_probability = accept_probability_generator(iteration=i+1, cost_truck=truck.get_total_costs())
                rand = random.random()
                if rand < accept_probability:
                    accept = True
                else:
                    accept = False
                if accept:
                    new_trucks.append(truck)
                print('for truck cost ', truck.get_total_costs(), ' we have prob: ', accept_probability, 'is accepted: ', accept)
            if len(new_trucks) > 0:
                trucks += new_trucks
                shipments_tbd = exclude_truck_shipments_from_list(new_trucks, shipments_tbd)
                print('shipments to plan: ', len(shipments_tbd))
            i += 1

        return trucks


def exclude_truck_shipments_from_list(trucks, shipments):
    return list(filter(
        lambda shipment_tw: shipment_tw.id not in flatten(list(
            map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)),
                trucks))),
        shipments))


def flatten(list_of_lists):
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten(list_of_lists[0]) + flatten(list_of_lists[1:])
    return list_of_lists[:1] + flatten(list_of_lists[1:])

def accept_probability_generator(iteration, cost_truck):
    if cost_truck == c.fixed_cost_new_truck:
        probability = 1
    else:
        probability = np.exp(-(cost_truck-c.fixed_cost_new_truck)/(0.7*iteration))
    return probability
