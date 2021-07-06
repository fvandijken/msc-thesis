import unittest

from heuristics.DeterministicCSbeforeafter import *


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.config = Config(
            shipments_file='/test_data/Data - shipments 30.csv',
            shipments_file_time_windows='/test_data/DataTW - shipments 237.csv',
            gap_percentage=1.0,
            time_window_interval_in_minutes=20,
            max_number_shipment_multiplication=5
        )

        self.input = InputTW(shipments_file_time_windows=self.config.shipments_file_time_windows,
                             depots_file=c.depots_file)
        pass

    def test_correctness_solution(self):
        shipment_1 = {
            'end_location': 'FC1'
        }
        shipment_2 = {
            'start_location': 'FC2'
        }
        # diff = driving_time_between_shipments(shipment_1, shipment_2)
        self.assertTrue(10 == 10, '10 should be equal to 10')
        # self.assertEqual(diff, 10, 'diff between shipments should be x')
        pass

    def test_false(self):
        self.assertFalse(10 == 9, '10 is equal to 9')
        pass

    def test_cheapest_in_list(self):
        # TODO assert truth of two shipments that should be compatible and assert falsehood of two shipments
        # that are not compatible
        shipment_compatible_1 = {
            'end_location': 'FC1',
            'end': '10:10'
        }
        shipment_compatible_2 = {
            'start_location': 'FC2',
            'start': '11:00'
        }
        # self.assertTrue(are_compatible(shipment_compatible_1, shipment_compatible_2))
        shipment_incompatible_1 = {
            'end_location': 'FC1'
        }
        shipment_incompatible_2 = {
            'start_location': 'FC2'
        }
        # self.assertFalse(are_compatible(shipment_incompatible_1, shipment_incompatible_2))
        pass

    def test_working_solution(self):
        working_shipments = [
            # list(filter(lambda shipment: shipment.id == 'DC1.FC5.5', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'DC1.FC4.4', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'FC4.YPB.5', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'FC4.YPB.6', self.input.shipments_tw))[0],
        ]
        working = InputTW(shipments_tw=working_shipments)
        rc = DeterministicCSbeforeafter(input=working, config=self.config)
        solution = rc.get_solution()
        self.assertEqual(len(solution.trucks), 1, 'These shipments should fit on one truck')
        print(solution)

    def test_problematic_input(self):
        problematic_shipments = [
            list(filter(lambda shipment: shipment.id == 'DC1.FC5.5', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'DC1.FC4.4', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'FC4.YPB.5', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'FC4.YPB.6', self.input.shipments_tw))[0],
            list(filter(lambda shipment: shipment.id == 'EV.FC4.3', self.input.shipments_tw))[0],
        ]
        problematic_input = InputTW(shipments_tw=problematic_shipments)
        rc = DeterministicCSbeforeafter(input=problematic_input, config=self.config)
        solution = rc.get_solution()
        self.assertEqual(len(solution.trucks), 2, 'These shipments should fit on two trucks')
        print(solution)

    def test_active_spacey_filter(self):
        start_locations = ['FC1', 'FC2', 'DC1', 'FC4']
        end_locations = ['DC1', 'AMS', 'FC5', 'Boni']
        types = ['IBDC', 'OBR', 'IBDC', 'IBOV']
        # shipments = [ShipmentTW('id_' + str(i), 10.0 + i, 11 + i, 14 + i, 15 + i, start_locations[i], end_locations[i],types[i]) for i in range(0, 4)]
        tw_1 = ShipmentTW('id_1', 10.0, 10.5, 11.5, 12.0, 'FC1', 'DC1', 'IBDC')
        shipment_1 = Shipment(input_shipment=tw_1, start_time=10.25)
        tw_2 = ShipmentTW('id_2', 12.5, 13.0, 13.5, 14.0, 'FC2', 'AMS', 'OBR')
        shipment_2 = Shipment(input_shipment=tw_2, start_time=12.75)
        tw_3 = ShipmentTW('id_3', 14.5, 15.0, 16.0, 16.5, 'DC1', 'FC5', 'IBDC')
        shipment_3 = Shipment(input_shipment=tw_3, start_time=14.75)
        tw_4 = ShipmentTW('id_4', 17.0, 17.5, 18.0, 18.5, 'FC4', 'Boni', 'IBOV')
        shipment_4 = Shipment(input_shipment=tw_4, start_time=17.25)

        truck_1 = Truck('FC1', [shipment_1, shipment_2, shipment_3, shipment_4])

        active_trucks = [truck_1]

        ship_before = ShipmentTW('id_5', 8.0, 9.0, 9.0, 10.0, 'FC1', 'DC1', 'IBDC')

        self.assertTrue(fits_before_tw(truck_1, ship_before))
        self.assertFalse(fits_after_tw(truck_1, ship_before))
        self.assertTrue(are_compatible_tw_truck(truck_1, ship_before))

        ship_after = ShipmentTW('id_6', 19.0, 19.5, 20.5, 21.0, 'FC5', 'Boni', 'IBOV')
        self.assertFalse(fits_before_tw(truck_1, ship_after))
        self.assertTrue(fits_after_tw(truck_1, ship_after))
        self.assertTrue(are_compatible_tw_truck(truck_1, ship_after))

        ship_exact_before_same_location = ShipmentTW('id_7', 9.5, 9.5, 10.25, 10.25, 'DC1', 'FC1', 'IBDC')
        self.assertTrue(fits_before_tw(truck_1, ship_exact_before_same_location))

        ship_exact_before_different_location = ShipmentTW('id_8', 9.5, 9.5, 10.25, 10.25, 'FC2', 'AMS', 'IBDC')
        self.assertFalse(fits_before_tw(truck_1, ship_exact_before_different_location))

        ship_overlap_before_same_location = ShipmentTW('id_7', 9.5, 9.5, 10.26, 10.26, 'DC1', 'FC1', 'IBDC')
        self.assertFalse(fits_before_tw(truck_1, ship_overlap_before_same_location))

        active_trucks_with_space = get_active_trucks_with_space(ship_before, active_trucks)

        # for truck in active_trucks_with_space:
        #     cheapest = cheapest_compatible_shipment_truck(truck, shipment_1)
        #     self.assertTrue(areCompatible(truck, cheapest))
