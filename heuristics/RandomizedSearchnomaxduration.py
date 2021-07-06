from heuristics.Config import Config
from heuristics.InputTW import InputTW
from heuristics.Schedule import Schedule
from heuristics.RandomizedCS import RandomizedCS
from heuristics.RandomizedCSnomaxduration import RandomizedCSnomaxduration
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter

class RandomizedSearchnomaxduration:

    def __init__(self, input: InputTW, config: Config, input_trucks=None, sorted_shipments_tw=None):
        self.input = input
        self.config = config
        self.input_trucks = input_trucks
        self.sorted_shipments_tw = sorted_shipments_tw

    def get_solution(self, number_iterations):
        cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks, sorted_shipments_tw=self.sorted_shipments_tw)
        initial_solution: Schedule = cs.get_solution()
        best_solution = initial_solution
        best_score = initial_solution.get_costs_without_feasibility()
        for i in range(number_iterations):
            new_cs = RandomizedCSnomaxduration(input=self.input, config=self.config, input_trucks=self.input_trucks, sorted_shipments_tw=self.sorted_shipments_tw)
            solution: Schedule = new_cs.get_solution()
            if solution.get_costs_without_feasibility() < best_score:
                best_solution = solution
                best_score = solution.get_costs_without_feasibility()
                solution.post_improve_depots()
                print(best_score)
        return best_solution


