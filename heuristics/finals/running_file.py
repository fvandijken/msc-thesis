import time
from heuristics.Config import Config
import constants as c
import importlib
import random


random.seed(987654)

print('\n---------------------------------------------- 31_03 --------------------------------------------')

tic = time.time()
c.test_date = '31_03'

print('\n************* INPUT ANALYSIS *****************')
import heuristics.input_analysis as input_analysis

print('\n************* LIST SEARCH *****************')
import heuristics.finals.test_list_search as list_search

print('\n************* ILP GREEDY *****************')
import heuristics.finals.test_ilp_greedy as ilp_greedy

print('\n************* ILP GREEDY DC *****************')
import heuristics.finals.test_ilp_greedy_driver_change as ilp_greedy_dc

print('\n************* RANDOM SEARCH *****************')
import heuristics.finals.test_random_search as random_search

print('\n************* RANDOM SEARCH DC *****************')
import heuristics.finals.test_random_search_driver_change as random_search_dc

print('\n************* RANDOM SEARCH AND FIX *****************')
import heuristics.finals.test_random_search_and_fix as random_search_and_fix

print('\n************* RANDOM SEARCH AND FIX DC *****************')
import heuristics.finals.test_random_search_and_fix_driver_change as random_search_and_fix_dc

toc = time.time()
total_running_time = toc - tic
print('TOTAL RUNNING TIME: ', total_running_time)

#
for date in ['15_04', '16_04', '17_04']:
    print('\n---------------------------------------------- ', date, ' --------------------------------------------')
    c.test_date = date
    tic = time.time()
    print('\n************* INPUT ANALYSIS *****************')
    importlib.reload(input_analysis)

    print('\n************* LIST SEARCH *****************')
    importlib.reload(list_search)

    print('\n************* ILP GREEDY *****************')
    importlib.reload(ilp_greedy)

    print('\n************* ILP GREEDY DC *****************')
    importlib.reload(ilp_greedy_dc)

    print('\n************* RANDOM SEARCH *****************')
    importlib.reload(random_search)

    print('\n************* RANDOM SEARCH DC *****************')
    importlib.reload(random_search_dc)

    print('\n************* RANDOM SEARCH AND FIX *****************')
    importlib.reload(random_search_and_fix)

    print('\n************* RANDOM SEARCH AND FIX DC *****************')
    importlib.reload(random_search_and_fix_dc)
    toc = time.time()
    total_running_time = toc - tic
    print('TOTAL RUNNING TIME: ', total_running_time)








