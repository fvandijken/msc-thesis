from heuristics.Config import Config
from heuristics.Truck import Truck
import constants as c
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import copy
import xlwt
from xlwt import Workbook
import inspect
from heuristics.InputTW import InputTW

# Files
from heuristics.Config import Config
from heuristics.Truck import Truck


class Schedule:
    id_accumulator = 1

    def __init__(self, config: Config, trucks: list = None):
        self.config = config
        self.trucks = trucks
        self.id = Schedule.id_accumulator
        Schedule.id_accumulator += 1

    def __str__(self):
        string = 'Total costs of schedule ' + str(self.id) + ' : ' + str(self.get_total_costs()) + ', \n'
        i = len(self.get_trucks())
        self.get_trucks().sort(key=lambda truck: truck.get_start_time(), reverse=True)
        for truck in self.get_trucks():
            string += '\n' + 'Truck %2d: ' % i + str(truck)
            if not truck.is_feasible():
                string += '  <--- not feasible'
            if truck.is_too_long():
                string += '  <--- too long'
            i -= 1
        return string

    def add_truck(self, truck: Truck):
        self.trucks.append(truck)

    def remove_truck(self, truck: Truck):
        self.trucks.remove(truck)

    def get_trucks(self):
        return self.trucks

    def get_too_long_trucks(self):
        too_long_trucks = []
        for truck in self.trucks:
            if truck.is_too_long():
                too_long_trucks.append(truck)
        return too_long_trucks

    def get_infeasible_trucks(self):
        infeasible_trucks = []
        for truck in self.trucks:
            if not truck.is_feasible():
                infeasible_trucks.append(truck)
        return infeasible_trucks


    def get_total_number_of_trucks(self):
        return len(self.trucks)

    def get_splittable_trucks(self):
        return list(filter(lambda truck: truck.is_splittable(), self.trucks))
        #return [truck for truck in self.get_too_long_trucks() if len(truck.get_split_relief_points()) > 0]

    def get_efficient_trucks(self):
        efficient_trucks = []
        for truck in self.trucks:
            if truck.is_efficient():
            #if truck.get_empty_driving_time() < 1 and truck.get_waiting_time() < 2.5 and 10 < truck.get_duration() < c.max_duration:
                efficient_trucks.append(truck)
        return efficient_trucks

    def get_depots(self):
        depot_set = set()
        for truck in self.trucks:
            depot_set.add(truck.start_depot)
        return depot_set

    def get_number_of_trucks_per_depot(self, depot):
        number = 0
        for truck in self.trucks:
            if truck.start_depot == depot:
                number += 1
        return number

    def get_depot_distribution(self):
        print('Depot distribution: ')
        for depot in self.get_depots():
            print('number of trucks based at depot ', depot, ': ', str(self.get_number_of_trucks_per_depot(depot)))

    # def get_depots_with_available_trucks(self):
    #     depots_with_available_trucks = filter(lambda depot: self.get_number_of_trucks_per_depot(depot) < 3, self.get_depots())
    #     return depots_with_available_trucks

    def get_too_long_trucks_without_split(self):
        too_long_trucks_with_split = []
        for truck in self.get_too_long_trucks():
            if len(truck.get_split_relief_points()) == 0:
                too_long_trucks_with_split.append(truck)
        return too_long_trucks_with_split

    def is_feasible(self):
        is_feasible = True
        for truck in self.trucks:
            if not truck.is_feasible():
                is_feasible = False
                print('Infeasible truck: ', str(truck))
        return is_feasible

    def get_waiting_costs(self):
        waiting_costs = 0
        for truck in self.trucks:
            waiting_costs += truck.get_waiting_costs()
        return waiting_costs

    def get_waiting_time(self):
        waiting_time = 0
        for truck in self.trucks:
            waiting_time += truck.get_waiting_time()
        return waiting_time

    def get_empty_driving_time(self):
        empty_driving_time = 0
        for truck in self.trucks:
            empty_driving_time += truck.get_empty_driving_time()
        return empty_driving_time

    def get_empty_driving_costs(self):
        empty_driving_costs = 0
        for truck in self.trucks:
            empty_driving_costs += truck.get_empty_driving_costs()
        return empty_driving_costs

    def get_total_costs(self):
        if self.is_feasible():
            total_costs = 0
            for truck in self.trucks:
                total_costs += truck.get_total_costs()
        else:
            total_costs = float('inf')
        return round(total_costs, 2)


    def post_improve_depots(self):
        depot_score_dict = {}
        for truck in self.get_trucks():
            if truck.get_start_time() > 1.25:
                for depot in self.get_depots():
                    depot_score_dict[depot] = c.time_diff_matrix.at[depot, truck.shipments[0].start_location] + \
                                              c.time_diff_matrix.at[truck.shipments[-1].end_location, depot]
                best_depot = min(self.get_depots(), key=lambda depot: depot_score_dict[depot])
                if depot_score_dict[truck.start_depot] > depot_score_dict[best_depot]:
                    # print('We can improve: ', depot_score_dict[truck.start_depot], ' ----> ', depot_score_dict[best_depot])
                    truck.change_depot_to(best_depot)

    def post_optimize_depots(self):
        pass



    def post_shift_shipments(self):
        for truck in self.trucks:
            shift_shipments_backward(truck)
            shift_shipments_forward(truck)


    # def post_equalize_day_durations(self):
    #     short_trucks = []
    #     long_trucks = []
    #     for truck in self.trucks:
    #         if truck.get_duration < 6:
    #             short_trucks.append(truck)
    #         if truck.get_duration > 11:
    #             long_trucks.append(truck)
    #     for short_truck in short_trucks:
    #         potential_shipments = []
    #         for truck in long_trucks:
    #             potential_shipments.append(truck.shipments[0])
    #             potential_shipments.append(truck.shipments[-1])
    #         best_shipment = min(potential_shipments, key=lambda shipment: cost(short_truck, shipment))

    def post_optimize_last_shipments_only(self):
        pass

    def swap_last_shipments(self, truck_1: Truck, truck_2: Truck):
        if truck_1 not in self.get_trucks() or truck_2 not in self.get_trucks():
            print('trucks to swap not found in schedule')
        else:
            truck_2.add_shipment(truck_1.shipments[-1])
            truck_1.remove_ith_shipment(-1)
            truck_1.add_shipment(truck_2.shipments[-2])
            truck_2.remove_ith_shipment(-2)

    def swap_first_shipments(self, truck_1: Truck, truck_2: Truck):
        if truck_1 not in self.get_trucks() or truck_2 not in self.get_trucks():
            print('trucks to swap not found in schedule')
        else:
            truck_2.add_shipment(truck_1.shipments[0])
            truck_1.remove_ith_shipment(0)
            truck_1.add_shipment(truck_2.shipments[1])
            truck_2.remove_ith_shipment(1)

    def swap_close_shipments(self, truck_1: Truck, truck_2: Truck):
        for ship_1 in truck_1.shipments:
            for ship_2 in truck_2.shipments:
                if abs(ship_1.start_time - ship_2.start_time) < 1.5:
                    truck_2.add_shipment(ship_1)
                    truck_1.remove_shipment(ship_1)
                    truck_1.add_shipment(ship_2)
                    truck_2.remove_shipment(ship_2)

    def get_number_of_shipments(self):
        number = 0
        for truck in self.trucks:
            for shipment in truck.shipments:
                number += 1
        return number

    def get_number_of_shipment_hours(self):
        hours = 0
        for truck in self.trucks:
            for shipment in truck.shipments:
                hours += shipment.get_length()
        return hours

    def get_total_time(self):
        time = 0
        for truck in self.trucks:
            time += truck.get_duration()
        return round(time, 2)

    def get_number_of_drivers(self):
        number_of_drivers = 0
        for truck in self.trucks:
            if truck in self.get_splittable_trucks():
                number_of_drivers += 2
            else:
                number_of_drivers += 1
        return number_of_drivers

    def get_average_driver_day_length(self):
        average_length = self.get_total_time()/self.get_number_of_drivers()
        return average_length

    def get_number_of_short_truck_days(self):
        number_of_short_truck_days = 0
        for truck in self.trucks:
            if truck.get_duration() < 7:
                number_of_short_truck_days += 1
        return number_of_short_truck_days

    def __get_total_input_hours(self):
        total_hours_input = 0
        for truck in self.trucks:
            for shipment in truck.shipments:
                ship_duration = shipment.end_time - shipment.start_time
                total_hours_input += ship_duration
        return total_hours_input

    def get_inefficiency_pc(self):
        inefficiency_pc = (self.get_waiting_time() + self.get_empty_driving_time())/self.get_total_time() * 100
        return round(inefficiency_pc, 2)

    def get_waiting_pc(self):
        waiting_pc = self.get_waiting_time() / self.get_total_time() * 100
        return round(waiting_pc, 2)

    def get_empty_driving_pc(self):
        return round(self.get_empty_driving_time() / self.get_total_time() * 100, 2)


    def metrics(self, depot_distribution=False):
        self.number_of_vehicles = len(self.trucks)
        self.trucks.sort(key=lambda truck: truck.get_start_time())

        # Initiate all metrics
        self.total_waiting_time = 0
        self.total_empty_driving_time = 0
        self.total_pull_out_time = 0
        self.total_pull_in_time = 0
        self.total_shipment_time_check = 0
        self.total_planned_time = 0
        self.truck_trip_durations = []
        self.truck_trip_driving_time = []

        for truck in self.trucks:
            S = len(truck.shipments)
            depot = truck.start_depot
            # Pull out trips
            pull_out_time = c.time_diff_matrix.at[depot, truck.shipments[0].start_location]
            self.total_pull_out_time += pull_out_time
            # Shipment trips
            shipment_time = 0
            for i in range(S):
                one_shipment_time = truck.shipments[i].end_time - truck.shipments[i].start_time
                shipment_time += one_shipment_time
            self.total_shipment_time_check += shipment_time
            # Driving empty in between shipments
            empty_driving_time = 0
            for i in range(S - 1):
                one_empty_driving_time = c.time_diff_matrix.at[
                    truck.shipments[i].end_location, truck.shipments[i + 1].start_location]
                empty_driving_time += one_empty_driving_time
            self.total_empty_driving_time += empty_driving_time
            # Waiting time in between shipments
            waiting_time = 0
            for i in range(S - 1):
                one_waiting_time = truck.shipments[i + 1].start_time - truck.shipments[i].end_time - \
                                   c.time_diff_matrix.at[
                                       truck.shipments[i].end_location, truck.shipments[i + 1].start_location]
                waiting_time += one_waiting_time
            self.total_waiting_time += waiting_time
            # Pull in trips
            pull_in_time = c.time_diff_matrix.at[truck.shipments[-1].end_location, depot]
            self.total_pull_in_time += pull_in_time
            planned_time = truck.get_end_time() - truck.get_start_time()
            self.total_planned_time += planned_time
            # Duration and driving time
            self.truck_trip_durations.append(truck.get_duration())
            driving_time = round(pull_out_time - S * c.loading_time + shipment_time + empty_driving_time + pull_in_time,
                                 2)
            self.truck_trip_driving_time.append(driving_time)

        total_hours_input = self.__get_total_input_hours()
        self.inefficiency_percentage = (self.total_planned_time - total_hours_input) / self.total_planned_time
        self.waiting_percentage = self.total_waiting_time / self.total_planned_time
        self.empty_driving_percentage = (
                                                    self.total_empty_driving_time + self.total_pull_out_time + self.total_pull_in_time) / self.total_planned_time

        depot_txt = \
            '\n' + 'Depot distribution: ' + '\n'
        for depot in self.get_depots():
            depot_txt += 'number of trucks based at depot ' + depot + ': ' + str(
                self.get_number_of_trucks_per_depot(depot)) + '\n'
        # Define txt
        txt = \
            depot_txt + \
            '\n' + 'Schedule data: ' + '\n' + \
            'The number of trucks is: ' + str(len(self.trucks)) + '\n' + \
            'The truck day durations are: ' + str(self.truck_trip_durations) + '\n' + \
            'The ' + str(len(self.get_too_long_trucks())) + ' too long trucks are: ' + str(
                ['Truck ' + str(truck.id) for truck in self.get_too_long_trucks()]) + '\n' + \
            'The ' + str(len(self.get_infeasible_trucks())) + ' infeasible trucks are: ' + str(
                ['Truck ' + str(truck.id) for truck in self.get_infeasible_trucks()]) + '\n' + \
            'The drive durations are: ' + str(self.truck_trip_driving_time) + '\n' + \
            'The total costs are: ' + str(self.get_total_costs()) + '\n' + \
            'The total number of hours: ' + str(self.get_total_time()) + '\n' + \
            'The inefficiency is: {0}%'.format(str(round(100 * self.inefficiency_percentage, 2))) + '\n' + \
            'of which {0}% waiting and {1}% empty driving'.format(str(round(100 * self.waiting_percentage, 2)),
                                                                  str(round(100 * self.empty_driving_percentage,
                                                                            2))) + '\n'

        return txt

    def visualize(self, save: bool = False, show: bool = False, with_shipment_ids: bool = False, with_truck_costs: bool = False):
        # figure parameters
        bar_height = 3
        space_between_bars = 3
        space_below_lowest_bar = 3
        space_above_highest_bar = 3

        # Constructing the figure
        fig, gnt = plt.subplots(figsize=(20, 10))
        fig = plt.subplots_adjust(right=0.58)

        plt.title('Visualization of solution')
        gnt.grid(False)

        # Constructing the axes
        # x axis
        gnt.set_xlim(-3, 23)
        gnt.set_xlabel('Time')
        gnt.set_xticks([i for i in range(0, 23)])
        gnt.set_xticklabels(
            ['04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
             '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '00:00', '01:00',
             '02:00'],
            fontsize=6, rotation=30)

        # y axis
        gnt.set_ylabel('Truck Trips')
        gnt.set_ylim(0, len(self.trucks) * (bar_height + space_between_bars) + space_above_highest_bar)
        gnt.set_yticks([space_below_lowest_bar + 0.5 * bar_height + (bar_height + space_between_bars) * i for i in
                        range(len(self.trucks))])
        gnt.set_yticklabels((i + 1 for i in range(len(self.trucks))), fontsize=8)

        # Constructing bars for different type of activities in a truck trip
        y = space_below_lowest_bar
        self.trucks.sort(key=lambda truck: truck.get_start_time())

        for truck in self.trucks:
            # Pull out trips
            S = len(truck.shipments)
            depot = truck.start_depot
            stem_color = 'tab:blue'
            if depot == 'Ermelo':
                stem_color = 'tab:blue'
            elif depot == 'DC1':
                stem_color = 'tab:blue'
            gnt.broken_barh(
                [(truck.shipments[0].start_time - c.time_diff_matrix.at[
                    depot, truck.shipments[0].start_location],
                  c.time_diff_matrix.at[depot, truck.shipments[0].start_location])],
                (y, bar_height), facecolors=stem_color, edgecolor='black')
            # Shipment trips
            for i in range(S):
                if 'IB' in truck.shipments[i].type:
                    if truck.shipments[i].type[-1] == 'S':
                        gnt.broken_barh([(truck.shipments[i].start_time,
                                          (truck.shipments[i].end_time - truck.shipments[i].start_time))],
                                        (y, bar_height), facecolors='orange', edgecolor='black')
                    else:
                        gnt.broken_barh([(truck.shipments[i].start_time,
                                          (truck.shipments[i].end_time - truck.shipments[i].start_time))],
                                        (y, bar_height), facecolors='sandybrown', edgecolor='black')
                else:
                    if truck.shipments[i].type[-1] == 'S':
                        gnt.broken_barh([(truck.shipments[i].start_time,
                                          (truck.shipments[i].end_time - truck.shipments[i].start_time))],
                                        (y, bar_height), facecolors='olivedrab', edgecolor='black')
                    else:
                        gnt.broken_barh([(truck.shipments[i].start_time,
                                          (truck.shipments[i].end_time - truck.shipments[i].start_time))],
                                        (y, bar_height), facecolors='yellowgreen', edgecolor='black')
            # Driving empty in between shipments
            for i in range(S - 1):
                gnt.broken_barh([(truck.shipments[i].end_time,
                                  c.time_diff_matrix.at[
                                      truck.shipments[i].end_location, truck.shipments[i + 1].start_location])],
                                (y, bar_height), facecolors='tab:blue', edgecolor='black')
            # Waiting time in between shipments
            for i in range(S - 1):
                gnt.broken_barh(
                    [(truck.shipments[i].end_time +
                      c.time_diff_matrix.at[
                          truck.shipments[i].end_location, truck.shipments[i + 1].start_location],
                      truck.shipments[i + 1].start_time - truck.shipments[i].end_time -
                      c.time_diff_matrix.at[
                          truck.shipments[i].end_location, truck.shipments[i + 1].start_location])],
                    (y, bar_height), facecolors='tab:grey', edgecolor='black')
            # Pull in trips
            gnt.broken_barh([(truck.shipments[-1].end_time,
                              c.time_diff_matrix.at[
                                  truck.shipments[-1].end_location, depot])],
                            (y, bar_height), facecolors=stem_color, edgecolor='black')
            # Extra waiting time too short truck days
            if truck.is_too_short():
                extra_waiting_time = 7 - truck.get_duration()
                if truck.get_end_time() < 12:
                    gnt.broken_barh([(truck.get_end_time(),
                                      extra_waiting_time)],
                                    (y, bar_height), facecolors='tab:grey', edgecolor='black', alpha=0.3)
                else:
                    gnt.broken_barh([(truck.get_start_time() - extra_waiting_time,
                                      extra_waiting_time)],
                                    (y, bar_height), facecolors='tab:grey', edgecolor='black', alpha=0.3)
            # Reliefpoints
            relief_color = 'lightgrey'
            if truck.is_too_long():
                if truck.is_splittable():
                    relief_color = 'green'
                else:
                    relief_color = 'r'
            for relief_time in truck.get_relief_points():
                gnt.annotate('', (relief_time, y + bar_height),
                             xytext=(relief_time, y + bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=3, headlength=2, facecolor=relief_color,
                                             edgecolor=relief_color,
                                             shrink=0.05), fontsize=6, horizontalalignment='right',
                             verticalalignment='top')
            for split_relief_time in truck.get_split_relief_points():
                gnt.annotate('', (split_relief_time, y + bar_height),
                             xytext=(split_relief_time, y + bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=3.5, headlength=2, facecolor='black',
                                             edgecolor='black',
                                             shrink=0.05), fontsize=6, horizontalalignment='right',
                             verticalalignment='top')

            if truck.is_too_long():
                arrow_alpha = 1
                if len(truck.get_split_relief_points()) == 0:
                    arrow_color = 'r'
                else:
                    arrow_color = 'green'
            else:
                arrow_color = 'white'
                arrow_alpha = 0
            gnt.annotate('', (truck.get_start_time(), y + 0.5 * bar_height),
                         xytext=(truck.get_start_time() - 1, y + 0.5 * bar_height),
                         arrowprops=dict(width=1.5, headwidth=3.5, headlength=2, facecolor=arrow_color,
                                         edgecolor=arrow_color,
                                         shrink=0.05, alpha=arrow_alpha), fontsize=6, horizontalalignment='right',
                         verticalalignment='top')
            gnt.annotate(truck.get_duration(), (truck.get_end_time() + 0.75, y + 0.5 * bar_height),
                         xytext=(truck.get_end_time() + 1, y + 0.5 * bar_height),
                         arrowprops=dict(width=2, headwidth=3, headlength=2, facecolor='white', edgecolor='white',
                                         shrink=0.05, alpha=0), fontsize=8, horizontalalignment='right', verticalalignment='center')
            # gnt.annotate(round(truck.get_waiting_time(),2), (truck.get_end_time() + 1.75, y + 0.5 * bar_height),
            #              xytext=(truck.get_end_time() + 2, y + 0.5 * bar_height),
            #              arrowprops=dict(width=2, headwidth=3, headlength=2, facecolor='white', edgecolor='white',
            #                              shrink=0.05, alpha=0), fontsize=8, horizontalalignment='right',
            #              verticalalignment='center')
            if with_truck_costs:
                gnt.annotate(truck.get_total_costs()-c.fixed_cost_new_truck, (truck.get_start_time() - 0.2, y + 0.5 * bar_height),
                             xytext=(truck.get_start_time() - 0.2, y + 0.5 * bar_height + 2),
                             arrowprops=dict(width=1.5, headwidth=0.1, headlength=2, facecolor='white', edgecolor='white',
                                             shrink=0.05, alpha=0), fontsize=8, horizontalalignment='right',
                             verticalalignment='top')
            if with_shipment_ids:
                for shipment in truck.shipments:
                    gnt.annotate(shipment.id, ((shipment.start_time+shipment.end_time)/2, y + 0.5 * bar_height),
                                 xytext=((shipment.start_time+shipment.end_time)/2, y + 0.5 * bar_height),
                                 arrowprops=dict(width=2, headwidth=3, headlength=2, facecolor='white', edgecolor='white',
                                                 shrink=0.05, alpha=0), fontsize=6, horizontalalignment='center',
                                 verticalalignment='center')
            y += bar_height + space_between_bars

        # Constructing the legend
        legend_elements = [Patch(edgecolor='black', facecolor='yellowgreen', linewidth=0.5, label='OB Shipment'),
                           Patch(edgecolor='black', facecolor='sandybrown', linewidth=0.5, label='IB Shipment'),
                           # Patch(edgecolor='black', facecolor='darkviolet', linewidth=0.5, label='Stem trips'),
                           Patch(edgecolor='black', facecolor='tab:blue', linewidth=0.5, label='Empty Driving'),
                           Patch(edgecolor='black', facecolor='tab:grey', linewidth=0.5, label='Waiting in between shipments'),
                           Patch(edgecolor='black', facecolor='tab:grey', linewidth=0.5, label='Waiting to fill up working day', alpha=0.3),
                           Line2D([], [], color='green', marker='$\downarrow$', markersize=8,
                                  label='Reliefpoint', lw=0),
                           Line2D([], [], color='black', marker='$\downarrow$', markersize=8,
                                  label='Split reliefpoint', lw=0)]
        gnt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

        total_hours_input = self.__get_total_input_hours()
        # Printing analytics in the gantt chart
        txt = \
            'The number of trucks is: ' + str(len(self.trucks)) + '\n' + \
            'The total costs are: ' + str(self.get_total_costs()) + '\n' + \
            'The total number of hours: ' + str(self.get_total_time()) + '\n' + \
            'The average driver day length (without extra waiting): ' + str(round(self.get_average_driver_day_length(), 2)) + '\n' + \
            'The number of short truck days (<7h): ' + str(self.get_number_of_short_truck_days()) + '\n' + \
            'The inefficiency is: {0}%'.format(str(round(self.get_inefficiency_pc(), 2))) + '\n' + \
            'of which ' + str(self.get_waiting_pc()) + '% waiting and ' + str(self.get_empty_driving_pc()) + '% empty driving'

        plt.text(1.1, 0.6, txt, horizontalalignment='left', verticalalignment='center', transform=gnt.transAxes)

        if save:
            plt.savefig(str(len(self.trucks)) + " " + str(round(self.get_inefficiency_pc(), 2)) + ".png")

        if show:
            plt.show()

    def create_sheet(self):
        # Workbook is created
        wb = Workbook()

        # add_sheet is used to create sheet.
        sheet1 = wb.add_sheet('Truck Planning')

        style = xlwt.easyxf('font: bold 1')

        # column names
        sheet1.write(0, 0, 'Trucks', style)
        sheet1.write(1, 0, 'truck id', style)
        sheet1.write(1, 1, 'start time', style)
        sheet1.write(1, 2, 'end time', style)
        sheet1.write(1, 3, 'duration', style)
        sheet1.write(1, 4, 'depot', style)
        sheet1.write(1, 5, 'pull out duration', style)
        m = max([len(truck.shipments) for truck in self.trucks])
        for k in range(m):
            sheet1.write(0, 6 + k * 6, 'Shipment ' + str(k + 1), style)
            sheet1.write(1, 6 + k * 6, 'shipment id', style)
            sheet1.write(1, 7 + k * 6, 'start time', style)
            sheet1.write(1, 8 + k * 6, 'start location', style)
            sheet1.write(1, 9 + k * 6, 'end time', style)
            sheet1.write(1, 10 + k * 6, 'end location', style)
            if k != m - 1:
                sheet1.write(1, 11 + k * 6, 'driving time duration', style)

        sheet1.write(1, 5 + m * 6, 'pull in duration', style)

        # data
        i = 2
        for truck in self.trucks:
            sheet1.write(i, 0, 'Truck ' + str(i - 1))
            sheet1.write(i, 1, to_time_moment(truck.get_start_time()))
            sheet1.write(i, 2, to_time_moment(truck.get_end_time()))
            sheet1.write(i, 3, to_time_duration(truck.get_duration()))
            sheet1.write(i, 4, truck.start_depot)
            sheet1.write(i, 5,
                         to_time_duration(c.time_diff_matrix.at[truck.start_depot, truck.shipments[0].start_location]))
            j = 1
            for shipment in truck.shipments:
                sheet1.write(i, j * 6, shipment.id)
                sheet1.write(i, 1 + j * 6, to_time_moment(shipment.start_time))
                sheet1.write(i, 2 + j * 6, shipment.start_location)
                sheet1.write(i, 3 + j * 6, to_time_moment(shipment.end_time))
                sheet1.write(i, 4 + j * 6, shipment.end_location)
                if j < len(truck.shipments):
                    sheet1.write(i, 5 + j * 6, to_time_duration(c.time_diff_matrix.at[
                                                                    shipment.end_location, truck.shipments[
                                                                        truck.shipments.index(
                                                                            shipment) + 1].start_location]))
                j += 1
            sheet1.write(i, 5 + m * 6,
                         to_time_duration(c.time_diff_matrix.at[truck.shipments[-1].end_location, truck.start_depot]))
            i += 1

        sheet2 = wb.add_sheet('Summary')

        # column names
        sheet2.write(0, 0, 'Truck distribution', style)
        sheet2.write(1, 0, 'Depot', style)
        sheet2.write(1, 1, 'Number of trucks', style)
        l = 2
        for depot in self.get_depots():
            sheet2.write(l, 0, depot)
            sheet2.write(l, 1, self.get_number_of_trucks_per_depot(depot))
            l += 1

        # input data
        sheet2.write(11, 0, 'Input', style)
        sheet2.write(12, 0, 'Number of shipments', style)
        sheet2.write(13, 0, 'Hours', style)
        sheet2.write(12, 1, self.get_number_of_shipments())
        sheet2.write(13, 1, to_time_duration(self.get_number_of_shipment_hours()))

        # output data
        sheet2.write(15, 1, 'Total planned', style)
        sheet2.write(15, 2, 'Empty driving', style)
        sheet2.write(15, 3, 'Waiting', style)
        sheet2.write(16, 0, 'Hours', style)
        sheet2.write(17, 0, 'Percentage', style)
        sheet2.write(16, 1, to_time_duration(self.total_planned_time))
        sheet2.write(16, 2, to_time_duration(
            self.total_empty_driving_time + self.total_pull_in_time + self.total_pull_out_time))
        sheet2.write(16, 3, to_time_duration(self.total_waiting_time))
        sheet2.write(17, 1, 100)
        sheet2.write(17, 2, self.empty_driving_percentage * 100)
        sheet2.write(17, 3, self.waiting_percentage * 100)

        file_name = 'Truck Planning ' + str(self.id) + '.xls'
        wb.save(file_name)


def merge_schedules(schedule_1: Schedule, schedule_2: Schedule):
    merged_schedule = copy.deepcopy(schedule_1)
    for truck in schedule_2.trucks:
        merged_schedule.add_truck(truck)
    return merged_schedule


def split_schedule(schedule: Schedule):
    new_schedule = copy.copy(schedule)
    trucks_to_split = new_schedule.get_splittable_trucks()
    for truck in trucks_to_split:
        relief_time = truck.get_split_relief_points()[0]
        left_shipments = []
        right_shipments = []
        for shipment in truck.shipments:
            if shipment.start_time < relief_time:
                left_shipments.append(shipment)
            else:
                right_shipments.append(shipment)
        truck_1 = Truck(start_depot=truck.start_depot, shipments=left_shipments)
        truck_2 = Truck(start_depot=truck.start_depot, shipments=right_shipments)
        new_schedule.remove_truck(truck)
        new_schedule.add_truck(truck_1)
        new_schedule.add_truck(truck_2)
    return new_schedule


def to_time_moment(number):
    number += 4

    hours = int(number)
    minutes = (number * 60) % 60

    return "%d:%02d" % (hours, minutes)


def to_time_duration(number):
    hours = int(number)
    minutes = (number * 60) % 60

    return "%d:%02d" % (hours, minutes)

def driving_time_between_shipments(left_shipment, right_shipment):
    return c.time_diff_matrix.at[left_shipment.end_location, right_shipment.start_location]

def shift_shipments_forward(truck: Truck):
    if len(truck.shipments) > 1:
        last_shipment = truck.shipments[-1]
        for i in range(len(truck.shipments)):
            left_shipment = truck.shipments[-(i+1)]
            right_shipment = truck.shipments[-i]
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
            left_shipment = truck.shipments[i]
            right_shipment = truck.shipments[i+1]
            start_waiting = left_shipment.end_time + driving_time_between_shipments(left_shipment, right_shipment)
            end_waiting = right_shipment.start_time
            if end_waiting - start_waiting > 0:
                new_start_time = max(left_shipment.end_time + driving_time_between_shipments(left_shipment, right_shipment), right_shipment.input_shipment.earliest_start_time)
                right_shipment.set_start_time(new_start_time)
