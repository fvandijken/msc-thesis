import pandas as pd
import util as util
import csv
from heuristics.Shipment import Shipment, ShipmentTW
import constants as c
import os


class InputTW:

    def __init__(self, shipments_file_time_windows='', depots_file=c.depots_file, shipments_tw=None):
        if shipments_tw is not None:
            self.shipments_tw = shipments_tw
            self.__shipments_df = pd.DataFrame(shipments_tw)
        else:
            self.shipments_tw = self.__import_shipments_tw(shipments_file_time_windows)
            self.__shipments_df = self.__get_shipments_df(shipments_file_time_windows)
            self.__depots_df = self.__get_depots_df(depots_file)
        self.depots = self.__import_depots(depots_file)

    def print(self):
        # Print input data
        N = len(self.shipments_tw)
        M = len(self.depots)
        print('DEPOTS: ')
        print('total: ', M)
        print(self.__depots_df)
        print('\n')
        print('SHIPMENTS: ')
        print('total: ', N)
        print(self.__shipments_df.head())

    def get_input_hours(self):
        total_hours = 0
        for shipment in self.shipments_tw:
            total_hours += shipment.get_length()
        return total_hours

    def __import_shipments_tw(self, shipments_file_time_windows: str):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shipments_file_time_windows = root + shipments_file_time_windows
        shipments_data = []
        with open(shipments_file_time_windows, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                shipments_data.append(ShipmentTW(id=row['shipment_id'],
                                                 earliest_start_time=float(row['earliest_start_time']),
                                                 latest_start_time=float(row['latest_start_time']),
                                                 earliest_end_time=float(row['earliest_end_time']),
                                                 latest_end_time=float(row['latest_end_time']),
                                                 start_location=row['start_location'],
                                                 end_location=row['end_location'],
                                                 type=row['type']))
            return shipments_data

    def __get_shipments_df(self, shipments_file: str):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shipments_file = root + shipments_file
        return pd.read_csv(shipments_file)

    def __get_depots_df(self, depots_file: str):
        return pd.read_csv(depots_file)

    def __import_depots(self, depots_file: str):
        with open(depots_file, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            return {row['depot']: int(row['capacity']) for row in reader}
