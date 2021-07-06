import numpy as np
import constants as c
from heuristics.Config import Config


class ShipmentTW:
    def __init__(self, id: str, earliest_start_time: float, latest_start_time: float,
                 earliest_end_time: float, latest_end_time: float, start_location: str, end_location: str, type: str):
        # diff = earliest_end_time - earliest_start_time - (latest_end_time - latest_start_time)
        # if diff >= 0.01:
        #     print('wrong: ' + str(diff))

        self.id = id
        self.earliest_start_time = earliest_start_time
        self.latest_start_time = latest_start_time
        self.earliest_end_time = earliest_end_time
        self.latest_end_time = earliest_end_time + (latest_start_time - earliest_start_time)
        self.start_location = start_location
        self.end_location = end_location
        self.type = type

    def __str__(self):
        return 'id: ' + str(self.id) + '\n' + \
               'start window: [' + str(self.earliest_start_time) + ', ' + str(self.latest_start_time) + ']' + '\n' + \
               'end window: [' + str(self.earliest_end_time) + ', ' + str(self.latest_end_time) + ']' + '\n' + \
               'locations: ' + str(self.start_location) + ' --> ' + str(self.end_location) + '\n' + \
               'type: ' + self.type + '\n'

    def get_length(self):
        length = self.earliest_end_time - self.earliest_start_time
        return round(length, 3)

    def discretize_time_windows(self, config: Config):
        """
        Make list of regular shipments in a certain interval.
        :return:
        """
        discretized_shipments = []
        interval = int(config.time_window_interval_in_minutes * 1 / .6)
        length = int((self.latest_start_time - self.earliest_start_time) * 100)
        if config.max_number_shipment_multiplication == 1:
            if 'IB' in self.type:
                shipment = Shipment(id=self.id + '.1', input_shipment=self)
                shipment.set_start_time(self.earliest_start_time)
            else:  # 'OB' must be in self.type
                if 'OB' not in self.type:
                    raise ValueError('Neither IB nor OB is in self.type')
                shipment = Shipment(id=self.id + '.1', input_shipment=self)
            discretized_shipments.append(shipment)
        elif config.max_number_shipment_multiplication == 2:
            if 'IB' in self.type:
                shipment = Shipment(id=self.id + '.1', input_shipment=self)
                shipment.set_start_time(self.earliest_start_time)
                discretized_shipments.append(shipment)
                if length > interval:
                    shipment = Shipment(id=self.id + '.2', input_shipment=self)
                    shipment.set_start_time(round((self.earliest_start_time + self.latest_start_time) / 2, 3))
                    discretized_shipments.append(shipment)
            if 'OB' in self.type:
                shipment = Shipment(id=self.id + '.1', input_shipment=self)
                shipment.set_start_time(round((self.earliest_start_time + self.latest_start_time) / 2, 3))
                discretized_shipments.append(shipment)
                if length > interval:
                    shipment = Shipment(id=self.id + '.2', input_shipment=self)
                    shipment.set_start_time(self.latest_start_time)
                    discretized_shipments.append(shipment)
        elif config.max_number_shipment_multiplication > 2:
            i = 1  
            if np.ceil(length / interval) + 1 <= config.max_number_shipment_multiplication:
                pass
            else:
                interval = np.floor(length / (config.max_number_shipment_multiplication - 2))
            for minutes in list(range(0, length + 1, int(interval))):
                key = self.id + '.' + str(i)
                shipment = Shipment(id=key,
                                    start_time=self.earliest_start_time + minutes * 0.01,
                                    end_time=self.earliest_end_time + minutes * 0.01,
                                    start_location=self.start_location,
                                    end_location=self.end_location,
                                    type=self.type,
                                    input_shipment=self)
                discretized_shipments.append(shipment)
                i += 1
        return discretized_shipments


class Shipment:
    def __init__(self, id: str = '', start_time: float = 0, end_time: float = 0, start_location: str = '',
                 end_location: str = '', type: str = '', input_shipment: ShipmentTW = None):
        self.start_time = 0
        if input_shipment is not None:
            self.input_shipment = input_shipment
            if id != '':
                self.id = id
            else:
                self.id = input_shipment.id
            self.set_start_time(start_time)
            self.start_location = input_shipment.start_location
            self.end_location = input_shipment.end_location
            self.type = input_shipment.type
        else:
            self.input_shipment = None
            self.id = id
            self.set_start_time(start_time)
            self.end_time = end_time
            self.start_location = start_location
            self.end_location = end_location
            self.type = type

    def set_start_time(self, start_time: float):
        self.start_time = round(start_time, 3)
        if self.input_shipment is not None:
            self.end_time = round(start_time + self.input_shipment.get_length(), 3)

    def get_length(self):
        length = self.end_time - self.start_time
        return length

    def __str__(self):
        return 'id: ' + str(self.id) + '\n' + \
               'start time: ' + str(self.start_time) + ' end time: ' + str(self.end_time) + '\n' + \
               'locations: ' + str(self.start_location) + ' --> ' + str(self.end_location) + '\n' + \
               'type: ' + self.type + '\n' + \
               'input shipment: ' + self.input_shipment.id + '\n'


# -------------------------------------------- Help Functions ----------------------------------------------------

def are_compatible(ship1: Shipment, ship2: Shipment):
    compatibility = False
    if ship1.end_time + c.time_diff_matrix.at[ship1.end_location, ship2.start_location] <= ship2.start_time:
        compatibility = True
    return compatibility


