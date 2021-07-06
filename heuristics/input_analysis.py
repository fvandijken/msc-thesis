from heuristics.Config import Config
from heuristics.DeterministicCS import DeterministicCS
from heuristics.InputTW import InputTW
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.RandomizedtiesCSnomaxduration import RandomizedtiesCSnomaxduration
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
import constants as c
from heuristics.Schedule import Schedule
import check
import time

config = Config(
    shipments_file_time_windows='/test_data/Data ' + c.test_date + ' - Shipments.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)
input.print()

number_of_IBOV = 0
number_of_IBDC = 0
number_of_OBR = 0
number_of_OBM = 0
for shipment_tw in input.shipments_tw:
    if shipment_tw.type == 'IBOV':
        number_of_IBOV += 1
    elif shipment_tw.type == 'IBDC':
        number_of_IBDC += 1
    elif shipment_tw.type == 'OBR':
        number_of_OBR += 1
    else:
        number_of_OBM += 1
print('number of total, IBOV, IBDC, OBR, OBM: ')
print(len(input.shipments_tw))
print(number_of_IBOV)
print(number_of_IBDC)
print(number_of_OBR)
print(number_of_OBM)







