import constants as c
from heuristics.Shipment import Shipment, ShipmentTW
import util


class Truck:
    id_accumulator = 1

    def __init__(self, start_depot, shipments=None):
        self.start_depot = start_depot
        self.startup_cost = c.fixed_cost_new_truck

        if shipments is not None:
            self.shipments = shipments
        else:
            self.shipments = []
        self.id = Truck.id_accumulator
        Truck.id_accumulator += 1

    def __str__(self):
        return 'Truck %2d starts at depot %6s, has total cost %s and executes the shipments: %s' % (
            self.id, self.start_depot, self.get_total_costs(),
            [shipment.id for shipment in self.shipments])

    def is_active(self):
        is_active = False
        if len(self.shipments) > 0:
            is_active = True
        return is_active

    def add_shipment(self, shipment: Shipment):
        util.insert(seq=self.shipments, item=shipment, key=lambda ship: ship.start_time)

    def remove_ith_shipment(self, i):
        del self.shipments[i]

    def remove_shipment(self, shipment: Shipment):
        if shipment not in self.shipments:
            print('Removed shipment not in truck')
        else:
            self.shipments.remove(shipment)

    def get_first_shipment(self):
        return self.shipments[0]

    def get_end_time(self):
        end_time_last_shipment = self.shipments[-1].end_time
        driving_back_time = c.time_diff_matrix.at[self.shipments[-1].end_location, self.start_depot]
        return end_time_last_shipment + driving_back_time

    def get_start_time(self):
        start_time_first_shipment = self.shipments[0].start_time
        driving_to_time = c.time_diff_matrix.at[self.start_depot, self.shipments[0].start_location]
        return start_time_first_shipment - driving_to_time

    def get_max_duration(self):
        if self.get_start_time() < 1.25:
            if self.get_waiting_time() < 1:
                max_duration = 11
            else:
                max_duration = 11.25
        else:
            if self.get_waiting_time() < 1:
                max_duration = 13.5
            else:
                max_duration = 14
        return max_duration

    def is_too_long(self):
        too_long = False
        if self.get_duration() > self.get_max_duration():
            too_long = True
        return too_long

    def is_too_short(self):
        too_short = False
        if self.get_duration() < c.min_duration_split:
            too_short = True
        return too_short

    def change_depot_to(self, depot):
        if depot == self.start_depot:
            print('Depot is already ', depot)
        else:
            self.start_depot = depot


    def is_feasible(self):
        is_feasible = True
        for i in range(len(self.shipments) - 1):
            if self.shipments[i].start_time + c.time_diff_matrix.at[
                self.shipments[i].end_location, self.shipments[i + 1].start_location] > \
                    self.shipments[i + 1].start_time:
                is_feasible = False
                infeasible_truck = str(self.id)
        # if self.is_too_long() and len(self.get_split_relief_points()) == 0:
        #     is_feasible = False
        return is_feasible

    def get_relief_points(self):
        relief_points = []
        for i in range(len(self.shipments)):
            if self.shipments[i].start_location == self.start_depot:
                relief_points.append(self.shipments[i].start_time)
            if self.shipments[i].end_location == self.start_depot:
                relief_points.append(self.shipments[i].end_time)
        return relief_points

    def get_split_relief_points(self):
        split_relief_points = []
        for relief_point in self.get_relief_points():
            if relief_point - self.get_start_time() > c.min_duration_split and \
                    self.get_end_time() - relief_point > c.min_duration_split:
                split_relief_points.append(relief_point)
        return split_relief_points

    def is_splittable(self):
        is_splittable = False
        if len(self.get_split_relief_points()) > 0:
            is_splittable = True
        return is_splittable

    def is_efficient(self):
        is_efficient = False
        if self.get_empty_driving_time() < 1 and self.get_waiting_time() < 2 and 10 < self.get_duration() < self.get_max_duration():
            is_efficient = True
        return is_efficient

    def get_empty_driving_costs(self):
        empty_driving_costs = c.weight_empty_driving_time * self.get_empty_driving_time()
        return empty_driving_costs

    def get_empty_driving_time(self):
        empty_driving_time = 0
        if self.is_active():
            empty_driving_time += c.time_diff_matrix.at[self.start_depot, self.shipments[0].start_location]
            for i in range(len(self.shipments) - 1):
                empty_driving_time += c.time_diff_matrix.at[self.shipments[i].end_location, self.shipments[i + 1].start_location]
            empty_driving_time += c.time_diff_matrix.at[self.shipments[-1].end_location, self.start_depot]
        return empty_driving_time

    def get_waiting_costs(self):
        waiting_costs = c.weight_waiting_time * self.get_waiting_time()**2
        return waiting_costs

    def get_waiting_time(self):
        waiting_time = 0
        for i in range(len(self.shipments) - 1):
            waiting_time += self.shipments[i + 1].start_time - self.shipments[i].end_time - \
                    c.time_diff_matrix.at[self.shipments[i].end_location, self.shipments[i + 1].start_location]
        if self.get_duration() < 7:
            waiting_time += 7 - self.get_duration()
        return waiting_time

    def get_length_costs(self):
        l = self.get_duration()
        if l < 14:
            costs = (0.3*(l - 11))**4
        else:
            costs = 100000
        return c.weight_length * costs


    def get_total_costs(self):
        total_costs = 0
        if self.is_active():
            #total_costs = self.startup_cost + self.get_empty_driving_costs() + self.get_waiting_costs() + self.get_length_costs()
            total_costs = self.startup_cost + self.get_empty_driving_costs() + self.get_waiting_costs()
        return int(total_costs)


    def get_duration(self):
        duration = 0
        if self.is_active():
            duration = c.time_diff_matrix.at[self.start_depot, self.shipments[0].start_location] + \
                       (self.shipments[-1].end_time - self.shipments[0].start_time) + \
                       c.time_diff_matrix.at[self.shipments[-1].end_location, self.start_depot]
        return round(duration, 2)

    def get_trip(self):
        trip = [self.start_depot] + [shipment.shipment_id for shipment in self.shipments] + [
            self.start_depot]
        return trip

#------------------------------------------------- Help Functions ----------------------------------------------------

# def shipment_to_truck(shipment):
#     if shipment.type != 'T':
#         return print('This shipment never was a truck')
#     else:
#         truck = shipment.input_truck
#     return truck
#
#
# def truck_to_shipment(truck: Truck):
#     shipment = Shipment(id='truck ' + str(truck.id),
#                         start_time=truck.shipments[0].start_time,
#                         end_time=truck.shipments[-1].end_time,
#                         start_location=truck.shipments[0].start_location,
#                         end_location=truck.shipments[-1].end_location,
#                         type='T'
#                         )
#     return shipment
#
#
# def truck_to_shipment_tw(truck: Truck):
#     shipment_tw = ShipmentTW(id='truck ' + str(truck.id),
#                           earliest_start_time=truck.shipments[0].start_time,
#                           latest_start_time=truck.shipments[0].start_time,
#                           earliest_end_time=truck.shipments[-1].end_time,
#                           latest_end_time=truck.shipments[-1].end_time,
#                           start_location=truck.shipments[0].start_location,
#                           end_location=truck.shipments[-1].end_location,
#                           type='T'
#                           )
#     return shipment_tw


