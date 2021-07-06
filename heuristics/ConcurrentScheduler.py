from operator import itemgetter
import constants as c
import util

# Files
from heuristics.Config import Config
from heuristics.InputFixed import InputFixed
from heuristics.Schedule import Schedule
from heuristics.Truck import Truck
from heuristics.Shipment import Shipment


# ---------------------------------------------- ConcurrentScheduler Class -----------------------------------------

class ConcurrentScheduler:

    def __init__(self, input: InputFixed, config: Config):
        self.shipments = input.shipments
        self.depots = input.depots
        self.config = config

    # Import Shipments from csv to dataframe
    # Shipments is a list of all shipments that have to be executed, with their Shipment ID, start time, end time,
    # start location and end location

    def get_solution(self):
        """
        Solve and return
        :return: Schedule
        """
        # Initiate all trucks available
        trucks = [Truck(depot) for depot, number_of_trucks in self.depots.items() for _ in range(number_of_trucks)]

        # Sort the shipments by increasing start time
        sorted_shipments = sorted(self.shipments, key=lambda shipment: shipment.start_time)

        # Loop over all shipments in increasing start time order
        for shipment in sorted_shipments:
            active_trucks = list(filter(lambda truck: truck.is_active(), trucks))
            inactive_trucks = list(filter(lambda truck: not truck.is_active(), trucks))
            placed = False
            active_trucks_with_space = []
            for truck in active_trucks:
                if duration_with_potential_shipment(truck, shipment) < c.max_duration:
                        #and driving_time_with_potential_shipment(truck, shipment) < c.max_driving_time:
                    active_trucks_with_space.append(truck)
            for truck in active_trucks_with_space:
                last_shipment = truck.shipments[-1]
                if are_compatible(last_shipment, shipment) and not placed:
                    the_best_truck = min(active_trucks_with_space, key=lambda truck: cost_active_truck(truck, shipment))
                    #costs = [cost_active_truck(truck, shipment) for truck in active_trucks]
                    the_best_truck.add_shipment(shipment)
                    placed = True
                    # print('just placed on active truck: ', truck.get_id(), shipment)
            if not placed and len(inactive_trucks) > 0:
                the_best_truck = min(inactive_trucks, key=lambda truck: cost_inactive_truck(truck, shipment))
                the_best_truck.add_shipment(shipment)
                placed = True
                # print('just placed on new truck: ', the_best_truck.get_id(), shipment)
            if not placed:
                print("Shipment could not be placed")
                pass

        schedule = Schedule(config=self.config, trucks=[truck for truck in trucks if truck.is_active()])

        return schedule


#----------------------------------------------- Help Functions ------------------------------------------------------


def are_compatible(ship1, ship2):
    compatibility = False
    if ship1.end_time + c.time_diff_matrix.at[ship1.end_location, ship2.start_location] <= ship2.start_time:
        compatibility = True
    return compatibility

def driving_time_between_shipments(left_shipment, right_shipment):
    return c.time_diff_matrix.at[left_shipment.end_location, right_shipment.start_location]

def cost_active_truck(truck: Truck, shipment: Shipment):
    last_shipment = truck.shipments[-1]
    if shipment.start_time - last_shipment.end_time - driving_time_between_shipments(last_shipment, shipment) >= 0:
        return c.weight_waiting_time * (
                shipment.start_time - last_shipment.end_time - driving_time_between_shipments(
            last_shipment,
            shipment)) + \
               c.weight_empty_driving_time * driving_time_between_shipments(last_shipment, shipment)
    else:
        return 1000000000

def cost_inactive_truck(truck: Truck, shipment: Shipment):
    return truck.startup_cost + c.weight_empty_driving_time * (
        c.time_diff_matrix.at[truck.start_depot, shipment.start_location])

def duration_with_potential_shipment(truck: Truck, shipment: Shipment):
    duration_with_shipment = c.time_diff_matrix.at[
                                 truck.start_depot, truck.shipments[0].start_location] + \
                             (shipment.end_time - truck.shipments[0].start_time) + \
                             c.time_diff_matrix.at[shipment.end_location, truck.start_depot]
    return duration_with_shipment

def driving_time_with_potential_shipment(truck: Truck, shipment: Shipment):
    driving_time_with_shipment = c.time_diff_matrix.at[
        truck.start_depot, truck.shipments[0].start_location]
    for ship in truck.shipments:
        ship_duration = ship.end_time - ship.start_time - c.loading_time
        driving_time_with_shipment += ship_duration
    driving_time_with_shipment += c.time_diff_matrix.at[
        truck.shipments[-1].end_location, shipment.start_location]
    driving_time_with_shipment += (shipment.end_time - shipment.start_time) - c.loading_time
    driving_time_with_shipment += c.time_diff_matrix.at[shipment.end_location, truck.start_depot]
    return driving_time_with_shipment

