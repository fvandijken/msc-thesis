from heuristics.Config import Config
from heuristics.InputTW import InputTW
from heuristics.Schedule import Schedule
import copy
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedtiesCSnomaxduration import RandomizedtiesCSnomaxduration
from heuristics.RandomizedCSnomaxduration import RandomizedCSnomaxduration
from heuristics.RandomizedtiesCS import RandomizedtiesCS
import constants as c


class RandomizedSearchAndFix:

    def __init__(self, input: InputTW, config: Config, input_trucks=None, sorted_shipments_tw=None):
        self.input = input
        self.config = config
        self.input_trucks = input_trucks
        self.shipments_tw = input.shipments_tw
        self.sorted_shipments_tw = sorted_shipments_tw

    def get_solution(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        best_solution = initial_solution
        best_score = initial_solution.get_total_costs()
        splittable_trucks = best_solution.get_splittable_trucks()
        efficient_trucks = best_solution.get_efficient_trucks()
        fixed_trucks = splittable_trucks + efficient_trucks
        shipments_tbd = exclude_truck_shipments_from_list(fixed_trucks, self.shipments_tw)
        # print(len(shipments_tbd))
        for i in range(number_of_iterations):
            number_of_fixed_trucks = len(fixed_trucks)
            new_cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_solution.post_improve_depots()
            splittable_trucks = new_solution.get_splittable_trucks()
            efficient_trucks = new_solution.get_efficient_trucks()
            # if len(splittable_trucks) + len(efficient_trucks) > 0:
                # print(number_of_fixed_trucks, ' fixed trucks: ')
                # print([truck.id for truck in splittable_trucks])
                # print([truck.id for truck in efficient_trucks])
                # print('shipments to plan: ', len(shipments_tbd))
            fixed_trucks += splittable_trucks + efficient_trucks
            shipments_tbd = exclude_truck_shipments_from_list(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks(),
                                                                        shipments_tbd)
            # print(new_solution.get_total_costs())
            if len(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks()) >= len(fixed_trucks):
                if len(new_solution.get_splittable_trucks() + new_solution.get_efficient_trucks()) > number_of_fixed_trucks:
                    best_solution = new_solution
                    best_score = new_solution.get_total_costs()
                    # print(best_score)
                elif new_solution.get_total_costs() < best_score:
                    best_solution = new_solution
                    best_score = new_solution.get_total_costs()
                    # print(best_score)
        best_solution.post_improve_depots()

        return best_solution

    def get_many_splittable_trucks(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        splittable_trucks = initial_solution.get_splittable_trucks()
        shipments_tbd = exclude_truck_shipments_from_list(splittable_trucks, self.shipments_tw)
        # print(len(shipments_tbd))
        unfixed_ratio = len(shipments_tbd)/len(self.shipments_tw)
        for i in range(number_of_iterations):
            if len(shipments_tbd) < c.max_unfixed_shipments:
                break
            new_cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_splittable_trucks = list(new_solution.get_splittable_trucks())
            if len(new_splittable_trucks) > 0:
                splittable_trucks += new_splittable_trucks
                number_of_splittable_trucks = len(splittable_trucks)
                # print(number_of_splittable_trucks, ' fixed trucks: ')
                # print([truck.id for truck in splittable_trucks])
                shipments_tbd = exclude_truck_shipments_from_list(new_splittable_trucks, shipments_tbd)
                unfixed_ratio = len(shipments_tbd) / len(self.shipments_tw)
                # print('shipments to plan: ', len(shipments_tbd))

        return splittable_trucks

    def get_many_efficient_trucks(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedtiesCS(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        efficient_trucks = initial_solution.get_efficient_trucks()
        shipments_tbd = exclude_truck_shipments_from_list(efficient_trucks, self.shipments_tw)
        # print(len(shipments_tbd))
        unfixed_ratio = len(shipments_tbd) / len(self.shipments_tw)
        for i in range(number_of_iterations):
            if len(shipments_tbd) < c.max_unfixed_shipments:
                break
            new_cs = RandomizedtiesCS(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_efficient_trucks = new_solution.get_efficient_trucks()
            if len(new_efficient_trucks) > 0:
                efficient_trucks += new_efficient_trucks
                number_of_splittable_trucks = len(efficient_trucks)
                # print(number_of_splittable_trucks, ' fixed trucks: ')
                # print([truck.id for truck in efficient_trucks])
                shipments_tbd = exclude_truck_shipments_from_list(new_efficient_trucks, shipments_tbd)
                unfixed_ratio = len(shipments_tbd) / len(self.shipments_tw)
                # print('shipments to plan: ', len(shipments_tbd))

        return efficient_trucks

    def get_many_splittable_and_efficient_trucks(self, number_of_iterations):
        self.shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks,
                                       sorted_shipments_tw=self.shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        splittable_trucks = list(initial_solution.get_splittable_trucks())
        efficient_trucks = list(initial_solution.get_efficient_trucks())
        fixed_trucks = splittable_trucks + efficient_trucks
        shipments_tbd = exclude_truck_shipments_from_list(fixed_trucks, self.shipments_tw)
        # print(len(shipments_tbd))
        unfixed_ratio = len(shipments_tbd) / len(self.shipments_tw)
        for i in range(number_of_iterations):
            if len(shipments_tbd) < c.max_unfixed_shipments:
                break
            new_cs = RandomizedtiesCSnomaxduration(input=self.input, config=self.config, input_trucks=None,
                                               sorted_shipments_tw=shipments_tbd)
            new_solution: Schedule = new_cs.get_solution()
            new_splittable_trucks = list(new_solution.get_splittable_trucks())
            new_efficient_trucks = list(new_solution.get_efficient_trucks())
            new_fixed_trucks = new_splittable_trucks + new_efficient_trucks
            if len(new_fixed_trucks) > 0:
                # if len(new_splittable_trucks) > 0:
                #     print('found new splittable truck: ', [truck.id for truck in new_splittable_trucks])
                # if len(new_efficient_trucks) > 0:
                #     print('found new efficient truck: ', [truck.id for truck in new_efficient_trucks])
                fixed_trucks += new_fixed_trucks
                number_of_fixed_trucks = len(fixed_trucks)
                # print(number_of_fixed_trucks, ' fixed trucks: ')
                shipments_tbd = exclude_truck_shipments_from_list(new_fixed_trucks, shipments_tbd)
                unfixed_ratio = len(shipments_tbd) / len(self.shipments_tw)
                # print('shipments to plan: ', len(shipments_tbd), '\n')

        return fixed_trucks


def exclude_truck_shipments_from_list(trucks, shipments):
    return copy.deepcopy(list(filter(
        lambda shipment_tw: shipment_tw.id not in flatten(list(
            map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)),
                trucks))),
        shipments)))


def flatten(list_of_lists):
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten(list_of_lists[0]) + flatten(list_of_lists[1:])
    return list_of_lists[:1] + flatten(list_of_lists[1:])

def get_shipments_from_trucks(trucks):
    return list(flatten(list(map(lambda truck: list(map(lambda shipment: shipment.id, truck.shipments)), trucks))))
