from operator import itemgetter
import constants as c
import util
import random
import heapq

# Files
from heuristics.Config import Config
from heuristics.InputTW import InputTW
from heuristics.Schedule import Schedule
from heuristics.Truck import Truck
from heuristics.Shipment import Shipment, ShipmentTW


# ---------------------------------------------- ConcurrentScheduler Class -----------------------------------------

class DeterministicCS:

    def __init__(self, input: InputTW, config: Config, input_trucks=None, sorted_shipments_tw=None):
        self.shipments_tw = input.shipments_tw
        self.depots = input.depots
        self.config = config
        self.trucks = input_trucks
        if sorted_shipments_tw is None:
            self.sorted_shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: (
            shipment_tw.latest_start_time, shipment_tw.latest_start_time - shipment_tw.earliest_start_time))
        else:
            self.sorted_shipments_tw = sorted_shipments_tw

    def get_solution(self):
        """
        Solve and return
        :return: Schedule
        """
        # Initiate all trucks available
        if self.trucks is None:
            trucks = [Truck(depot) for depot, number_of_trucks in self.depots.items() for _ in range(number_of_trucks)]
        else:
            trucks = self.trucks
            for depot in self.depots:
                number_still_open = self.depots[depot]
                for truck in trucks:
                    if truck.start_depot == depot:
                        number_still_open -= 1
            trucks += [Truck(depot) for depot, number_still_open in self.depots.items() for _ in range(number_still_open)]

        # Sort the shipments by increasing start time
        # self.sorted_shipments_tw = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)

        # Loop over all shipments in increasing earliest start time order
        for shipment_tw in self.sorted_shipments_tw:
            active_trucks = list(filter(lambda truck: truck.is_active(), trucks))
            inactive_trucks = list(filter(lambda truck: not truck.is_active(), trucks))
            active_trucks_with_space = get_active_trucks_with_space(shipment_tw, active_trucks)
            placed = False
            if len(active_trucks_with_space) > 0 and not placed:
                the_best_truck = min(active_trucks_with_space, key=lambda truck: cost_active_truck(truck, cheapest_compatible_shipment_truck(truck, shipment_tw)))
                the_best_truck.add_shipment(cheapest_compatible_shipment_truck(the_best_truck, shipment_tw))
                # shift_shipments_forward(the_best_truck)
                placed = True
            if not placed and len(inactive_trucks) > 0:
                shipment = Shipment(start_time=shipment_tw.earliest_start_time, input_shipment=shipment_tw)
                the_best_truck = min(inactive_trucks, key=lambda truck: cost_inactive_truck(truck, shipment))
                the_best_truck.add_shipment(shipment)
                placed = True
            if not placed:
                print("Shipment could not be placed")
                pass

            # not_finished_schedule = Schedule(config=self.config,
            #                                  trucks=[truck for truck in trucks if truck.is_active()])
            # not_finished_schedule.metrics()
            # not_finished_schedule.visualize()
        schedule = Schedule(config=self.config, trucks=[truck for truck in trucks if truck.is_active()])

        for truck in schedule.trucks:
            shift_shipments_forward(truck)
            shift_shipments_backward(truck)
        # schedule.post_optimize_depots()

        return schedule


# ----------------------------------------------- Help Functions ------------------------------------------------------

def get_active_trucks_with_space(shipment_tw, active_trucks):
    return list(filter(lambda truck: are_compatible_tw_truck(truck, shipment_tw) and
                                      duration_with_potential_shipment(truck, cheapest_compatible_shipment_truck(truck, shipment_tw)) < truck.get_max_duration(),
                       active_trucks))


def driving_time_between_shipments(left_shipment, right_shipment):
    return c.time_diff_matrix.at[left_shipment.end_location, right_shipment.start_location]


def are_compatible(ship1, ship2):
    compatibility = False
    if ship1.end_time + driving_time_between_shipments(ship1, ship2) <= ship2.start_time:
        compatibility = True
    return compatibility


def are_compatible_tw(ship: Shipment, ship_tw: ShipmentTW):
    compatibility = False
    if ship_tw.earliest_start_time - c.max_waiting_time <= ship.end_time + driving_time_between_shipments(ship,
                                                                                                          ship_tw) <= ship_tw.latest_start_time:
        compatibility = True
    return compatibility

def are_compatible_tw_truck(truck: Truck, ship_tw: ShipmentTW):
    compatibility = False
    last_shipment = truck.shipments[-1]
    first_shipment = truck.shipments[0]
    if ship_tw.earliest_start_time - c.max_waiting_time <= last_shipment.end_time + \
            driving_time_between_shipments(last_shipment, ship_tw) <= ship_tw.latest_start_time:
        compatibility = True
    # elif ship_tw.earliest_end_time + driving_time_between_shipments(ship_tw, first_shipment) \
    #     <= first_shipment.start_time <= ship_tw.latest_end_time + \
    #     driving_time_between_shipments(ship_tw, first_shipment) + c.max_waiting_time:
    #     compatibility = True
    return compatibility

def fits_after(truck: Truck, ship_tw: ShipmentTW):
    after = False
    last_shipment = truck.shipments[-1]
    if not are_compatible_tw_truck(truck, ship_tw):
        raise ValueError('Shipments are not compatible')
    if ship_tw.earliest_start_time - c.max_waiting_time <= last_shipment.end_time + \
            driving_time_between_shipments(last_shipment, ship_tw) <= ship_tw.latest_start_time:
        after = True
    return after

def cheapest_compatible_shipment_truck(truck: Truck, ship_tw: ShipmentTW):
    first_shipment = truck.shipments[0]
    last_shipment = truck.shipments[-1]
    if not are_compatible_tw_truck(truck, ship_tw):
        raise ValueError('Shipments are not compatible')
    cheapest_shipment = Shipment(input_shipment=ship_tw)
    # if fits_before(truck, ship_tw):
    #     cheapest_shipment.set_start_time(min(first_shipment.start_time - driving_time_between_shipments(ship_tw, first_shipment) - ship_tw.get_length(), ship_tw.latest_start_time))
    # else:
    cheapest_shipment.set_start_time(max(last_shipment.end_time + driving_time_between_shipments(last_shipment, ship_tw), ship_tw.earliest_start_time))
    return cheapest_shipment

def cheapest_compatible_shipment(ship: Shipment, ship_tw: ShipmentTW):
    if not are_compatible_tw(ship, ship_tw):
        raise ValueError('Shipments are not compatible')
    cheapest_shipment = Shipment(input_shipment=ship_tw)
    cheapest_shipment.set_start_time(max(ship.end_time + driving_time_between_shipments(ship, ship_tw), ship_tw.earliest_start_time))
    return cheapest_shipment


def cost_active_truck(truck: Truck, shipment: Shipment):
    last_shipment = truck.shipments[-1]
    if are_compatible(last_shipment, shipment):
        cost = c.weight_waiting_time * (
                shipment.start_time - last_shipment.end_time - driving_time_between_shipments(last_shipment,
                                                                                              shipment)) + \
               c.weight_empty_driving_time * driving_time_between_shipments(last_shipment, shipment)
        if shipment.start_time > c.start_time_last_shipment + 8 or \
                duration_with_potential_shipment(truck, shipment) > c.day_duration_last_shipment:
            cost += c.weight_empty_driving_time * c.time_diff_matrix.at[shipment.end_location, truck.start_depot]
        return cost
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


def duration_with_potential_shipment_tw(truck: Truck, shipment_tw: ShipmentTW):
    last_shipment = truck.shipments[-1]
    if are_compatible_tw(last_shipment, shipment_tw):
        shipment = cheapest_compatible_shipment(truck.shipments[-1], shipment_tw)
        duration_with_shipment = c.time_diff_matrix.at[
                                     truck.start_depot, truck.shipments[0].start_location] + \
                                 (shipment.end_time - truck.shipments[0].start_time) + \
                                 c.time_diff_matrix.at[shipment.end_location, truck.start_depot]
    else:
        duration_with_shipment = 10000
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

def shift_first_shipment(truck: Truck):
    if len(truck.shipments) > 1:
        first_shipment: Shipment = truck.shipments[0]
        second_shipment: Shipment = truck.shipments[1]
        start_waiting = first_shipment.end_time + driving_time_between_shipments(first_shipment, second_shipment)
        end_waiting = second_shipment.start_time
        if end_waiting - start_waiting > 0:
            potential_latest_start_waiting = first_shipment.input_shipment.latest_end_time + \
                                             driving_time_between_shipments(first_shipment, second_shipment)
            new_start_waiting = min(second_shipment.start_time, potential_latest_start_waiting)
            new_start_time = new_start_waiting - driving_time_between_shipments(first_shipment, second_shipment) - first_shipment.get_length()
            first_shipment.set_start_time(new_start_time)

def shift_shipments_forward(truck: Truck):
    if len(truck.shipments) > 1:
        last_shipment = truck.shipments[-1]
        for i in range(len(truck.shipments)):
            left_shipment: Shipment = truck.shipments[-(i+1)]
            right_shipment: Shipment = truck.shipments[-i]
            start_waiting = left_shipment.end_time + driving_time_between_shipments(left_shipment, right_shipment)
            end_waiting = right_shipment.start_time
            if end_waiting - start_waiting > 0:
                potential_latest_start_waiting = left_shipment.input_shipment.latest_end_time + \
                                                 driving_time_between_shipments(left_shipment, right_shipment)
                new_start_waiting = min(right_shipment.start_time, potential_latest_start_waiting)
                new_start_time = new_start_waiting - driving_time_between_shipments(left_shipment, right_shipment) - left_shipment.get_length()
                left_shipment.set_start_time(new_start_time)

def shift_shipments_backward(truck: Truck):
    if len(truck.shipments) > 1:
        for i in range(len(truck.shipments)-1):
            left_shipment: Shipment = truck.shipments[i]
            right_shipment: Shipment = truck.shipments[i+1]
            start_waiting = left_shipment.end_time + driving_time_between_shipments(left_shipment, right_shipment)
            end_waiting = right_shipment.start_time
            if end_waiting - start_waiting > 0:
                new_start_time = max(left_shipment.end_time + driving_time_between_shipments(left_shipment, right_shipment), right_shipment.input_shipment.earliest_start_time)
                right_shipment.set_start_time(new_start_time)