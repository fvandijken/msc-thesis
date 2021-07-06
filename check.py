from heuristics.Schedule import Schedule
from heuristics.InputTW import InputTW


def shipments_occurance(schedule: Schedule, input: InputTW):
    for ship_tw in input.shipments_tw:
        count = 0
        for truck in schedule.trucks:
            for ship in truck.shipments:
                if ship.input_shipment.id == ship_tw.id:
                    count += 1
        if count == 0:
            print(ship_tw.id + ' does not occur!')
        elif count > 1:
            print(ship_tw.id + ' occurs more than once!')
    return print('Check: all shipments occur exactly once')

def time_windows(schedule: Schedule, input: InputTW):
    for truck in schedule.trucks:
        for ship in truck.shipments:
            in_timewindow = False
            if ship.input_shipment.earliest_start_time <= ship.start_time <= ship.input_shipment.latest_start_time:
                in_timewindow = True
            if not in_timewindow:
                txt = ship.id + ' is not in timewindow \n ' + str(ship.start_time) + ' not in ' + str(ship.input_shipment.earliest_start_time) + ', ' + str(ship.input_shipment.latest_start_time)
                print(txt)
    return print('Check: All shipments in timewindow')
