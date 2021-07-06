import pandas as pd
import util as util
import csv
from heuristics.Shipment import Shipment
import os


class InputFixed:

    def __init__(self, shipments_file, depots_file):
        self.shipments = self.__import_shipments(shipments_file)
        self.depots = self.__import_depots(depots_file)
        self.__shipments_df = self.__get_shipments_df(shipments_file)
        self.__depots_df = self.__get_depots_df(depots_file)

    def print(self):
        # Print input data
        N = len(self.shipments)
        M = len(self.depots)
        print('DEPOTS: ')
        print('total: ', M)
        print(self.__depots_df)
        print('\n')
        print('SHIPMENTS: ')
        print('total: ', N)
        print(self.__shipments_df.head())

    # def __import_shipments(self, shipments_file: str):
    #     with open(shipments_file, newline='') as csv_file:
    #         reader = csv.DictReader(csv_file)
    #         return [{'shipment_id': row['shipment_id'],
    #                  'start_time': float(row['start_time']),
    #                  'end_time': float(row['end_time']),
    #                  'start_location': row['start_location'],
    #                  'end_location': row['end_location'],
    #                  'type': row['type']}
    #                 for row in reader]

    def __import_shipments(self, shipments_file: str):
        root = os.path.dirname(os.path.abspath(__file__))
        shipments_file = root + shipments_file
        shipments_data = []
        with open(shipments_file, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                shipments_data.append(Shipment(id=row['shipment_id'], start_time=float(row['start_time']), end_time=float(row['end_time']),
                    start_location=row['start_location'], end_location=row['end_location'], type=row['type']))
            return shipments_data

    def __get_shipments_df(self, shipments_file: str):
        return pd.read_csv(shipments_file)

    def __get_depots_df(self, depots_file: str):
        return pd.read_csv(depots_file)

    def __import_depots(self, depots_file: str):
        with open(depots_file, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            return {row['Depot']: int(row['Trucks']) for row in reader}
