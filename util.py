import constants as c
from bisect import bisect_left
import random

def second_choice_decision():
    return random.random() < c.prob_second_choice

def third_choice_decision():
    return random.random() < c.prob_third_choice

def random_0_or_1_or_2():
    if random.random() <= c.prob_second_choice:
        return 1
    elif random.random() <= c.prob_third_choice:
        return 2
    else:
        return 0

# Format function for dictionary
def format_dict(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            format_dict(value, indent + 1)
        else:
            print('\t' * (indent + 1) + str(value))


def min_but_one(iterable: list, key=lambda x: x):
    minimum_obj = None
    minimum_but_one_obj = None
    minimum = minimum_but_one = float('inf')
    for i in range(len(iterable)):
        value = key(iterable[i])
        if value < minimum:
            minimum_but_one = minimum
            minimum_but_one_obj = minimum_obj
            minimum = value
            minimum_obj = iterable[i]
        elif value < minimum_but_one and value != minimum:
            minimum_but_one = value
            minimum_but_one_obj = iterable[i]
        else:
            pass
    return minimum_but_one_obj



def insert(seq, item, key=lambda v: v):
    k = key(item)  # Get key.
    keys = [key(s) for s in seq]
    i = bisect_left(keys, k)  # Determine where to insert item.
    keys.insert(i, k)  # Insert key of item to keys list.
    seq.insert(i, item)  # Insert the item itself in the corresponding place.

def flatten(list_of_lists):
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten(list_of_lists[0]) + flatten(list_of_lists[1:])
    return list_of_lists[:1] + flatten(list_of_lists[1:])
