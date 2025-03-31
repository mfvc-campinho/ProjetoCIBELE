# Imports
import numpy as np
import time as time
import random as random
import copy as copy
import math as math

# Constants
TIME_ERROR = 0.9

###############################################################################

# Common Classes

# Empty Class (used to read a solution only)


class Rotation:
    def __init__(self, x):
        self.x = x

###############################################################################

# Functions

# Calculates area of a list of items with length (l) and width (w) defined


def calculateItemsArea(l, w, items, direc_rep):
    area = 0
    for i in range(len(items)):
        area += l[items[i]] * w[items[i]] * direc_rep[i][1]
    return area

###############################################################################

# Returns the max between Length (L) and Width (W)


def maxDimension(L, W):
    return max(L, W)

###############################################################################

# Returns the real status of the solution,
# when considering the floating cuts strategy


def analyseSolution(*args):
    # Model
    model = args[0]
    # Status = model.status.name

    # Vectors
    L = int(args[1])  # Length of the rectangular plate
    W = int(args[2])  # Width of the rectangular plate
    l = args[3]  # Length if the rectangular item
    w = args[4]  # Width of the rectangular item
    d = args[5]  # Maximum demand
    items = args[6]
    direc_rep = args[7]

    # Single Value
    rotation = args[8]

    occup = calculateItemsArea(l, w, items, direc_rep) / (L * W)
    total_used = getTotalPacked(direc_rep)
    total_items = getTotalItems(d, rotation)

    if model.objective_value is not None:
        of = float(model.objective_value)
    else:
        of = 0.0

    """
    These operations are useful for analyzing and evaluating the solution found
    by the optimization model:

    - occup ->          Represents the bin occupancy efficiency
                        (the proportion of area occupied by items relative to
                        the total bin area)
    - total_used ->     Indicates how many items were effectively packed
    - total_items ->    Displays the total quantity of items to be packed,
                        considering the possibility of rotation
    - of ->             Contains the model's objective function value
                        (if provided by the solver)

    With this information, it is possible to assess the quality and efficiency 
    of the solution found by the optimization model.
    """

    # Rules for Optimal Solution:
    """
    ATTENTION: If you run the code for the h-test, this analysis will return
    the last h result (Z) equal to the before last result sometimes after
    reaching the time limit. So, you MUST consider this case in your analysis!
    """

    # print(f'Occupation: {occup}')
    # print(f'Total items used: {total_used} from {total_items} items')

    # OBS: Time and z will be taken separatedly
    #  max occupation         all items used
    if occup >= .999 or total_used == total_items:
        return of, 'OPTIMAL'

    return of, 'FEASIBLE'

###############################################################################

# Count the total number of item to be packed


"""
REMEMBER: When considering rotation, we duplicate the items,
but the total items to be packed continues to be the initial quantity.
"""


def getTotalItems(d, rotation):
    tot = sum(d)

    if rotation == False:
        return tot

    return int(tot/2)


"""
If rotation is allowed, divide the sum of the item quantities by 2,
because when rotation is allowed, items are duplicated.
"""

###############################################################################

# Count the total number of packed items


def getTotalPacked(direc_rep):
    return sum(e2(rep) for rep in direc_rep)

###############################################################################

# Area Bound


"""
This function calculates the upper limit for the quantity of items of a
specific size that can be placed in a container (bin) with given dimensions.
The calculation is based on the total available area in the container and the
area occupied by each item.

It is performed by dividing the total available area in the container (L * W)
by the area occupied by each item (l * w).

The result is rounded down (math.floor) to ensure that the quantity of items
does not exceed the maximum possible limit due to the container's dimensions.

The upper limit indicates how many items of the specified size could be ideally
placed in the container, without considering other constraints or optimizations.

This value is an integer (after applying the math.floor function) since it
is not possible to place a fractional quantity of items in the container.
"""


def areaBound(L, W, l, w):
    return math.floor(L * W / float(l * w))

###############################################################################

# Second Element


def e2(elem):
    return elem[1]
