import csv
import itertools
from enum import Enum

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from operator import itemgetter
import os
import constants as c
import random
import time
import util
import copy

# Files
from heuristics.Config import Config
from heuristics.Schedule import Schedule
from heuristics.Truck import Truck
from heuristics.DeterministicCSbeforeafter import DeterministicCSbeforeafter
from heuristics.RandomizedCSbeforeafter import RandomizedCSbeforeafter
from heuristics.RandomizedSearch import RandomizedSearch
from heuristics.DeterministicCS import DeterministicCS
from heuristics.DeterministicCSnomaxduration import DeterministicCSnomaxduration
from heuristics.InputTW import InputTW
from heuristics.RandomizedtiesCS import RandomizedtiesCS


# ------------------------------------------------ LocalSearch Class ------------------------------------------------

class ListSearch:

    def __init__(self, input: InputTW,  config: Config):
        # self.initial_order = initial_order
        self.shipments_tw = input.shipments_tw
        self.depots = input.depots
        self.input = input
        self.config = config

    def get_solution(self):
        """
        Solve and return
        :return:
        """
        start_time = time.time()
        initial_order = sorted(self.shipments_tw, key=lambda shipment_tw: (shipment_tw.latest_start_time, shipment_tw.latest_start_time - shipment_tw.earliest_start_time))
        #initial_order = sorted(self.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
        dcs = RandomizedtiesCS(input=self.input, config=self.config, sorted_shipments_tw=initial_order)
        schedule = dcs.get_solution()
        best_schedule = schedule
        best_costs = best_schedule.get_total_costs()
        #print(best_costs)
        best_order = initial_order
        count_no_new_solution = 0
        scores = []
        j = 1
        while count_no_new_solution <= 100 and j <= 5:
            #print('round', j, ':')
            for i in range(100):
                r1, r2 = random.sample(range(len(self.shipments_tw) - 2), 2)
                old_i = best_order[r1]
                old_i1 = best_order[r2]
                best_order[r1], best_order[r2] = best_order[r2], best_order[r1]
                dcs = RandomizedtiesCS(input=self.input, config=self.config,
                                                 sorted_shipments_tw=best_order)
                schedule = dcs.get_solution()
                new_costs = schedule.get_total_costs()
                scores.append(new_costs)
                if new_costs - best_costs < 0:
                    count_no_new_solution = 0
                if new_costs - best_costs <= 0:
                    best_schedule = schedule
                    best_costs = best_schedule.get_total_costs()
                    #print(best_costs)
                else:
                    best_order[r1] = old_i
                    best_order[r2] = old_i1
            current_time = time.time()
            #print(current_time - start_time)
            count_no_new_solution += 1
            j += 1

        #print([ship.id for ship in best_order])

        # plt.plot(range(len(scores)), scores)
        # plt.show()

        return best_schedule

best_order_so_far = ['BR.FC0.1', 'BR.FC1.1', 'BR.FC2.1', 'BR.FC3.1', 'BR.FC5.1', 'BR.FC4.1', 'MO.FC3.3', 'MO.FC3.1', 'MO.FC3.2', 'FC1.EM.2', 'MO.FC3.4', 'MO.FC1.1', 'MO.FC4.2', 'MO.FC2.1', 'MO.FC1.2', 'MO.FC3.5', 'MO.FC1.3', 'MO.FC4.1', 'MO.FC1.4', 'FC1.CBL.1', 'FC1.EM.1', 'PA.FC1.1', 'MO.FC3.6', 'MO.FC2.2', 'DC1.FC5.4', 'MO.FC4.4', 'FC0.EM.1', 'FC1.EPS.1', 'FC1.FUI.1', 'FC2.CBL.1', 'FC2.EPS.2', 'FC2.EM.1', 'DC1.FC3.7', 'DC1.FC4.8', 'DC1.FC5.6', 'DC1.FC2.7', 'FC3.EDV.1', 'FC3.ARN.1', 'DC1.FC4.7', 'FC5.ALW.1', 'FC5.BUS.1', 'DC1.FC3.6', 'FC1.HFD.1', 'FC1.HFD.2', 'FC3.NIJ.1', 'FC5.ENS.1', 'DC1.FC3.5', 'FC5.BUS.3', 'DC1.FC1.5', 'FC4.RSP.3', 'FC5.ZIT.1', 'EV.FC2.5', 'FC2.LID.2', 'FC5.ALS.1', 'FC5.ALS.2', 'DC1.FC4.6', 'FC2.ALK.1', 'FC4.DHG.1', 'FC3.TLB.1', 'FC3.HLM.1', 'FC4.YPB.3', 'FC5.ZWO.1', 'FC5.ZWO.2', 'FC1.GOU.1', 'FC3.HTB.1', 'FC5.BUS.2', 'FC4.CPI.1', 'FC4.ZTM.2', 'FC2.ALE.1', 'FC2.HAA.1', 'FC2.HAA.2', 'FC5.DVR.1', 'FC2.AMW.1', 'FC1.NWG.1', 'FC3.EIN.1', 'FC4.YPB.1', 'FC4.SPI.2', 'FC2.AMN.1', 'FC1.UTN.1', 'FC1.UTN.3', 'DC1.FC3.4', 'FC1.UTS.1', 'DC1.FC4.5', 'DC1.FC5.5', 'DC1.FC1.4', 'MO.FC4.3', 'FC3.CBL.5', 'DC1.FC2.5', 'DC1.FC4.4', 'FC1.DC1.3', 'DC1.FC3.3', 'DC1.FC4.3', 'DC1.FC1.3', 'FC3.DC1.4', 'FC4.DC1.4', 'FC5.DC1.3', 'FC2.DC1.3', 'FC3.EM.1', 'VE.FC1.1', 'FC3.EDV.2', 'DC1.FC1.2', 'FC4.DC1.3', 'FC2.HAA.3', 'FC4.ZTM.1', 'DC1.FC2.4', 'FC2.AMN.3', 'FC2.AMN.2', 'DC1.FC2.3', 'FC2.DC1.2', 'DC1.FC5.3', 'KW.FC1.1', 'FC2.LID.3', 'FC5.ZIT.2', 'FC3.ARN.2', 'FC5.ALS.4', 'FC5.ALS.5', 'DC1.FC5.2', 'FC4.RSP.4', 'FC4.DHG.2', 'FC4.DHG.3', 'FC2.ALE.2', 'DC1.FC3.1', 'DC1.FC3.2', 'DC1.FC5.1', 'DC1.FC2.2', 'FC3.DC1.3', 'FC1.GOU.2', 'FC4.DOR.3', 'FC3.HTB.2', 'FC4.CPI.2', 'FC5.ALW.2', 'FC2.ALK.2', 'FC1.APN.2', 'DC1.FC4.2', 'FC3.DC1.2', 'FC3.EM.2', 'KW.FC1.2', 'KW.FC5.1', 'FC2.AMW.2', 'FC1.NWG.2', 'FC5.ENS.2', 'FC4.YPB.4', 'FC2.AMS.1', 'FC5.ALS.3', 'FC1.UTN.2', 'FC4.DOR.1', 'FC1.GOU.3', 'FC4.RSP.2', 'FC4.YPB.5', 'FC4.DC1.2', 'FC1.EM.3', 'FC4.SPI.1', 'KW.FC5.3', 'FC2.DVT.1', 'FC1.UTN.4', 'DC1.FC4.1', 'DC1.FC2.1', 'FC3.DC1.1', 'DC1.FC1.1', 'FC4.DC1.1', 'FC5.DC1.2', 'FC1.DC1.2', 'FC1.UTS.2', 'FC2.DC1.1', 'FC1.DC1.1', 'VE.FC0.1', 'FC5.DC1.1', 'KW.FC0.1', 'KW.FC2.4', 'FC3.EDV.3', 'FC5.APE.3', 'KW.FC2.1', 'FC4.DHG.4', 'FC3.NIJ.3', 'FC3.HLM.2', 'KW.FC2.3', 'FC3.BRD.2', 'FC3.BRD.3', 'FC5.ZIT.3', 'FC2.LID.4', 'FC4.DOR.2', 'FC2.HAA.4', 'EV.FC5.2', 'EV.FC4.4', 'FC4.CPI.4', 'FC1.GOU.4', 'FC3.TLB.2', 'FC4.YPB.6', 'FC5.ALS.6', 'FC2.AMS.2', 'FC5.DVR.2', 'FC1.HFD.3', 'FC3.BRD.1', 'FC5.APE.1', 'FC1.EM.4', 'FC4.EM.2', 'KW.FC2.2', 'KW.FC4.1', 'FC1.NWG.3', 'FC3.EIN.2', 'FC3.TLB.3', 'FC3.HTB.3', 'FC1.APN.1', 'FC4.ZTM.3', 'FC2.DVT.2', 'FC4.EM.1', 'FC1.UTS.3', 'KW.FC0.2', 'DC1.FC2.6', 'FC3.NIJ.2', 'FC4.RSP.1', 'FC2.DVT.3', 'KW.FC3.1', 'KW.FC3.3', 'FC5.APE.2', 'KW.FC3.2', 'KW.FC5.2', 'FC2.EM.3', 'KW.FC4.2', 'FC2.EM.2', 'KW.FC3.4', 'FC4.YPB.2', 'KW.FC0.3', 'EV.FC2.2', 'FC2.LID.1', 'EV.FC5.1', 'EV.FC5.3', 'EV.FC2.3', 'EV.FC4.1', 'FC4.CPI.3', 'EV.FC4.2', 'EV.FC2.1', 'EV.FC4.5', 'EV.FC4.3', 'EV.FC2.4', 'FC5.ENS.3', 'KW.FC0.4']
better_order = ['BR.FC0.1', 'BR.FC1.1', 'BR.FC2.1', 'MO.FC1.3', 'BR.FC5.1', 'BR.FC4.1', 'MO.FC3.3', 'MO.FC3.1', 'MO.FC3.2', 'FC1.EM.2', 'MO.FC3.4', 'MO.FC1.2', 'MO.FC4.2', 'MO.FC2.1', 'MO.FC1.1', 'MO.FC3.5', 'BR.FC3.1', 'MO.FC1.4', 'MO.FC4.1', 'FC1.CBL.1', 'MO.FC2.2', 'PA.FC1.1', 'MO.FC3.6', 'FC5.ZWO.2', 'MO.FC4.3', 'FC1.EPS.1', 'FC0.EM.1', 'FC1.EM.1', 'FC1.FUI.1', 'FC2.CBL.1', 'FC2.EPS.2', 'FC2.EM.1', 'DC1.FC3.7', 'DC1.FC4.8', 'DC1.FC5.6', 'DC1.FC2.7', 'FC3.EDV.1', 'FC3.ARN.1', 'DC1.FC4.7', 'FC5.ALW.1', 'DC1.FC1.3', 'FC5.ENS.1', 'FC1.HFD.1', 'FC1.HFD.2', 'FC3.NIJ.1', 'FC4.SPI.2', 'DC1.FC3.5', 'DC1.FC2.6', 'DC1.FC1.5', 'FC3.BRD.1', 'FC3.TLB.1', 'FC2.LID.1', 'FC2.LID.2', 'FC5.ALS.1', 'FC5.ALS.2', 'DC1.FC3.4', 'FC4.DHG.1', 'FC2.ALK.1', 'FC2.HAA.1', 'FC2.ALE.1', 'FC1.UTN.1', 'FC5.ZWO.1', 'MO.FC4.4', 'FC1.GOU.1', 'FC3.EIN.2', 'FC4.ZTM.1', 'FC4.CPI.1', 'FC4.ZTM.2', 'FC2.EM.2', 'FC5.ZIT.1', 'FC5.BUS.1', 'FC5.DVR.1', 'FC2.AMW.1', 'FC1.NWG.1', 'FC3.EIN.1', 'FC4.YPB.1', 'FC4.YPB.2', 'DC1.FC4.2', 'FC2.AMN.1', 'FC3.TLB.2', 'DC1.FC4.6', 'FC1.UTS.1', 'DC1.FC4.5', 'DC1.FC5.5', 'DC1.FC1.4', 'DC1.FC2.5', 'FC3.CBL.5', 'DC1.FC5.4', 'DC1.FC4.4', 'DC1.FC5.3', 'DC1.FC3.3', 'DC1.FC4.3', 'DC1.FC1.2', 'FC5.DC1.3', 'KW.FC1.1', 'FC3.DC1.4', 'FC3.HTB.1', 'FC3.EM.1', 'FC5.ALW.2', 'FC2.LID.3', 'FC2.HAA.2', 'FC4.DC1.3', 'VE.FC1.1', 'FC5.BUS.2', 'FC2.DC1.2', 'FC4.YPB.6', 'FC3.EDV.2', 'DC1.FC2.3', 'DC1.FC2.4', 'FC1.DC1.3', 'FC4.DC1.4', 'FC3.ARN.2', 'FC5.ZIT.2', 'FC5.ALS.3', 'FC5.ALS.4', 'FC5.ALS.5', 'DC1.FC5.2', 'FC1.NWG.2', 'FC4.DHG.2', 'FC4.DHG.3', 'KW.FC2.3', 'FC4.YPB.5', 'FC2.ALE.2', 'DC1.FC5.1', 'FC1.APN.1', 'FC3.DC1.3', 'FC1.GOU.2', 'FC3.HTB.2', 'FC1.GOU.3', 'FC4.CPI.2', 'FC2.HAA.3', 'FC5.APE.1', 'FC1.APN.2', 'FC3.BRD.3', 'FC3.DC1.2', 'FC3.EM.2', 'FC4.ZTM.3', 'FC2.AMW.2', 'FC4.RSP.2', 'FC5.ENS.3', 'FC4.YPB.3', 'FC2.AMN.2', 'FC2.AMS.1', 'FC4.YPB.4', 'FC1.UTN.2', 'FC1.UTN.3', 'FC5.APE.3', 'FC2.ALK.2', 'KW.FC1.2', 'DC1.FC1.1', 'KW.FC5.1', 'FC4.SPI.1', 'DC1.FC3.6', 'FC2.DVT.1', 'FC1.UTN.4', 'DC1.FC4.1', 'KW.FC2.1', 'KW.FC3.1', 'FC4.RSP.3', 'FC4.DC1.1', 'FC5.DC1.2', 'FC1.DC1.2', 'FC4.EM.1', 'FC2.DC1.1', 'DC1.FC2.1', 'VE.FC0.1', 'FC2.DC1.3', 'FC4.EM.2', 'FC2.HAA.4', 'FC3.EDV.3', 'FC5.BUS.3', 'FC1.DC1.1', 'FC1.HFD.3', 'FC3.NIJ.3', 'FC5.ENS.2', 'FC1.UTS.3', 'KW.FC2.2', 'FC2.DVT.2', 'FC5.ZIT.3', 'FC2.AMS.2', 'FC4.DHG.4', 'DC1.FC3.2', 'FC1.GOU.4', 'FC5.DC1.1', 'FC3.BRD.2', 'KW.FC2.4', 'FC5.DVR.2', 'FC3.NIJ.2', 'FC5.ALS.6', 'FC2.EM.3', 'FC4.CPI.3', 'FC1.EM.3', 'FC4.DC1.2', 'FC4.DOR.2', 'FC4.RSP.1', 'KW.FC0.1', 'DC1.FC2.2', 'KW.FC4.1', 'FC1.NWG.3', 'FC3.HLM.2', 'KW.FC5.2', 'FC2.DVT.3', 'FC4.RSP.4', 'KW.FC3.2', 'EV.FC4.3', 'FC1.UTS.2', 'EV.FC4.5', 'FC5.APE.2', 'FC1.EM.4', 'FC2.AMN.3', 'FC4.DOR.3', 'FC3.HTB.3', 'EV.FC2.4', 'KW.FC4.2', 'KW.FC0.2', 'DC1.FC3.1', 'FC3.HLM.1', 'EV.FC5.1', 'EV.FC5.3', 'FC3.TLB.3', 'KW.FC3.4', 'KW.FC5.3', 'KW.FC0.3', 'EV.FC2.1', 'EV.FC2.5', 'FC2.LID.4', 'EV.FC4.1', 'EV.FC2.3', 'FC4.CPI.4', 'FC3.DC1.1', 'EV.FC4.2', 'EV.FC2.2', 'KW.FC3.3', 'FC4.DOR.1', 'EV.FC4.4', 'EV.FC5.2', 'KW.FC0.4']

# ----------------------------------------------- Help Functions ------------------------------------------------------
