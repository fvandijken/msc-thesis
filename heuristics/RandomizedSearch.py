from heuristics.Config import Config
from heuristics.InputTW import InputTW
import copy
import util
import numpy as np
from heuristics.Schedule import Schedule
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedtiesCS import RandomizedtiesCS
from heuristics.RandomizedtiesCSnomaxduration import RandomizedtiesCSnomaxduration
from heuristics.RandomizedCSnomaxduration import RandomizedCSnomaxduration
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter

class RandomizedSearch:

    def __init__(self, input: InputTW, config: Config, input_trucks=None, sorted_shipments_tw=None):
        self.input = input
        self.config = config
        self.input_trucks = copy.deepcopy(input_trucks)
        self.sorted_shipments_tw = sorted_shipments_tw

    def get_solution(self, number_iterations):
        total_score = 0
        cs = RandomizedtiesCS(input=self.input, config=self.config, input_trucks=self.input_trucks, sorted_shipments_tw=self.sorted_shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        best_solution_1 = initial_solution
        best_number_of_trucks = initial_solution.get_total_number_of_trucks()
        best_solution_2 = initial_solution
        best_solution_3 = initial_solution
        best_score_1 = initial_solution.get_total_costs()
        #print('NEW best score: ', best_score_1)
        best_score_2 = best_score_1
        best_score_3 = best_score_1
        total_score += best_score_1
        for i in range(number_iterations):
            #if i % 10 == 0:
                #print(i)
            new_cs = RandomizedtiesCS(input=self.input, config=self.config, input_trucks=self.input_trucks, sorted_shipments_tw=self.sorted_shipments_tw)
            solution: Schedule = new_cs.get_solution()
            # fixed_shipments = []
            # for truck in self.input_trucks:
            #     for ship in truck.shipments:
            #         fixed_shipments.append(ship)
            # print('number of input shipments: ', len(fixed_shipments))
            #solution.post_optimize_depots()
            new_score = solution.get_total_costs()
            #print(new_score)
            number_of_trucks = solution.get_total_number_of_trucks()
            total_score += new_score
            if new_score < best_score_1:
                best_solution_1 = solution
                best_score_1 = new_score
                best_number_of_trucks = number_of_trucks
                #print('NEW best score: ', best_score_1)
            elif new_score < best_score_2 and number_of_trucks == best_number_of_trucks + 1:
                best_solution_2 = solution
                best_score_2 = new_score
                #print('NEW second best score: ', best_score_2)
            elif new_score < best_score_3 and number_of_trucks == best_number_of_trucks + 2:
                best_solution_3 = solution
                best_score_3 = new_score
                #print('NEW third best score: ', best_score_3)
        average_score = total_score / (number_iterations + 1)
        # print('average: ', average_score)
        return best_solution_1, best_solution_2, best_solution_3


