from heuristics.InputTW import InputTW
import constants as c
from heuristics.Config import Config

config = Config(
    shipments_file='\\test_data\Data - shipments 30.csv',
    shipments_file_time_windows='\\test_data\DataTW - shipments 237.csv',
    gap_percentage=1.0,
    time_window_interval_in_minutes=20,
    max_number_shipment_multiplication=5
)

input = InputTW(shipments_file_time_windows=config.shipments_file_time_windows, depots_file=c.depots_file)

initial_order_shipments = sorted(input.shipments_tw, key=lambda shipment_tw: shipment_tw.latest_start_time)
initial_order_ids = [ship.id for ship in initial_order_shipments]
initial_order_dict = {}
for ship_id in initial_order_ids:
    initial_order_dict[ship_id] = initial_order_ids.index(ship_id)
new_order_ids = ['BR.FC0.1', 'FC1.EM.2', 'MO.FC3.1', 'BR.FC2.1', 'MO.FC3.3', 'BR.FC1.1', 'BR.FC5.1', 'BR.FC3.1', 'MO.FC1.1', 'BR.FC4.1', 'MO.FC3.4', 'PA.FC1.1', 'MO.FC4.2', 'MO.FC2.1', 'MO.FC1.2', 'MO.FC3.5', 'FC4.YPB.6', 'MO.FC3.2', 'MO.FC1.4', 'FC1.CBL.1', 'MO.FC2.2', 'MO.FC4.1', 'MO.FC4.3', 'FC1.EM.1', 'MO.FC3.6', 'FC3.CBL.5', 'FC0.EM.1', 'FC1.EPS.1', 'FC1.FUI.1', 'FC2.CBL.1', 'FC2.EPS.2', 'FC2.EM.1', 'DC1.FC3.7', 'FC4.DC1.4', 'DC1.FC5.6', 'DC1.FC2.7', 'FC3.EDV.1', 'FC3.ARN.1', 'DC1.FC4.7', 'FC5.ALW.1', 'DC1.FC4.6', 'DC1.FC3.6', 'FC1.HFD.1', 'FC1.HFD.2', 'FC3.NIJ.1', 'FC5.ENS.1', 'FC4.DC1.3', 'FC5.BUS.2', 'VE.FC1.1', 'FC3.BRD.1', 'FC5.ZIT.1', 'FC2.LID.1', 'FC5.ALS.2', 'FC5.ALS.1', 'FC2.LID.2', 'FC3.TLB.1', 'FC2.ALK.1', 'FC2.ALE.1', 'FC2.AMN.1', 'FC3.HLM.1', 'FC5.DVR.1', 'FC5.ZWO.1', 'DC1.FC3.4', 'FC3.HLM.2', 'FC3.HTB.1', 'FC4.ZTM.1', 'FC4.CPI.1', 'FC5.BUS.1', 'FC3.DC1.4', 'FC2.HAA.1', 'FC2.HAA.2', 'FC1.GOU.1', 'FC4.ZTM.2', 'FC1.NWG.1', 'FC3.EIN.1', 'FC4.YPB.1', 'FC4.YPB.2', 'DC1.FC4.5', 'FC1.UTN.1', 'FC4.DOR.1', 'FC5.ZWO.2', 'FC1.UTS.1', 'FC2.AMW.1', 'DC1.FC5.5', 'FC4.DHG.1', 'DC1.FC2.5', 'FC3.BRD.2', 'DC1.FC5.4', 'DC1.FC4.4', 'DC1.FC5.3', 'DC1.FC3.3', 'FC4.DC1.1', 'DC1.FC1.3', 'DC1.FC1.4', 'DC1.FC4.8', 'FC5.DC1.3', 'FC2.DC1.3', 'FC4.DHG.3', 'FC3.EM.1', 'DC1.FC4.3', 'DC1.FC1.2', 'DC1.FC3.5', 'FC5.ALW.2', 'DC1.FC2.6', 'KW.FC4.1', 'FC3.NIJ.2', 'FC4.DHG.2', 'DC1.FC2.3', 'MO.FC4.4', 'FC1.DC1.3', 'KW.FC1.1', 'DC1.FC3.2', 'FC5.ZIT.2', 'FC5.ALS.3', 'FC5.ALS.4', 'FC3.EDV.2', 'DC1.FC5.2', 'FC1.APN.1', 'FC4.YPB.5', 'FC3.ARN.2', 'FC1.NWG.3', 'FC2.DC1.2', 'FC2.LID.3', 'KW.FC1.2', 'DC1.FC2.2', 'FC1.HFD.3', 'KW.FC2.2', 'FC1.GOU.3', 'FC1.APN.2', 'FC2.HAA.3', 'DC1.FC1.5', 'FC2.ALK.2', 'FC1.UTN.3', 'DC1.FC4.2', 'KW.FC2.1', 'FC3.DC1.2', 'DC1.FC5.1', 'FC1.UTS.2', 'FC2.AMW.2', 'FC4.YPB.4', 'FC1.GOU.2', 'KW.FC5.1', 'FC2.DVT.1', 'KW.FC2.3', 'EV.FC4.3', 'FC5.DC1.1', 'FC4.DHG.4', 'FC3.HTB.2', 'FC1.UTN.4', 'FC5.APE.1', 'FC3.TLB.3', 'FC2.AMN.2', 'FC1.UTS.3', 'KW.FC0.2', 'FC5.DC1.2', 'FC4.DC1.2', 'DC1.FC2.1', 'FC5.ALS.6', 'FC1.DC1.1', 'KW.FC3.4', 'FC2.LID.4', 'FC1.DC1.2', 'DC1.FC3.1', 'FC4.RSP.2', 'FC4.ZTM.3', 'VE.FC0.1', 'FC5.BUS.3', 'DC1.FC4.1', 'FC2.AMN.3', 'FC3.EDV.3', 'FC4.EM.1', 'DC1.FC1.1', 'FC5.DVR.2', 'FC3.NIJ.3', 'FC2.AMS.2', 'FC4.RSP.4', 'FC5.ALS.5', 'KW.FC5.2', 'FC5.ENS.3', 'DC1.FC2.4', 'FC5.ZIT.3', 'FC2.HAA.4', 'KW.FC2.4', 'FC4.CPI.3', 'FC1.EM.3', 'FC1.GOU.4', 'FC3.TLB.2', 'FC4.CPI.2', 'FC4.EM.2', 'EV.FC2.3', 'FC3.EM.2', 'FC3.BRD.3', 'FC5.APE.2', 'FC5.ENS.2', 'FC2.DC1.1', 'KW.FC0.1', 'FC2.AMS.1', 'FC4.CPI.4', 'FC3.DC1.1', 'FC3.EIN.2', 'FC1.NWG.2', 'KW.FC4.2', 'FC2.ALE.2', 'FC2.DVT.3', 'KW.FC3.3', 'FC1.UTN.2', 'EV.FC4.4', 'KW.FC0.3', 'FC1.EM.4', 'EV.FC2.1', 'FC4.DOR.2', 'FC2.EM.2', 'KW.FC3.1', 'FC4.SPI.2', 'FC5.APE.3', 'MO.FC1.3', 'KW.FC3.2', 'FC2.EM.3', 'FC4.DOR.3', 'FC4.RSP.3', 'FC4.SPI.1', 'KW.FC5.3', 'FC3.HTB.3', 'EV.FC2.2', 'EV.FC4.1', 'FC3.DC1.3', 'EV.FC2.5', 'FC2.DVT.2', 'FC4.YPB.3', 'EV.FC5.1', 'EV.FC5.3', 'EV.FC4.2', 'EV.FC4.5', 'FC4.RSP.1', 'EV.FC2.4', 'EV.FC5.2', 'KW.FC0.4']
count = 0
for i in range(len(initial_order_ids)):
    if initial_order_ids[i] != new_order_ids[i]:
        print(i)
        count += 1
print('Total number of differences: ', count)

print([initial_order_dict[ship_id] for ship_id in new_order_ids])

new_order = [ship for ship in input.shipments_tw for ship.id in new_order_ids]


