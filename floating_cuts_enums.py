from enum import Enum

"""
This code defines several enumeration classes that are used to represent
constants and discrete values associated with each type.
Enumerations are used to create sets of named values,
making the code more readable and maintainable.
"""

###############################################################################

# Enum Position


class RelativePositionEnum(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
    TOPLEFT = 5
    TOPRIGHT = 6
    BOTTOMRIGHT = 7
    BOTTOMLEFT = 8
    CENTER = 9

###############################################################################

# Enum Direction


"""
The Floating-Cuts model for the k-staged problem is based on the assumption
that in a given rectangle, only three situations may occur:

1 - the rectangle is cut horizontally;
2 -the rectangle is cut vertically;
3 - or an item is assigned to the rectangle.

If a rectangle is cut vertically, two new rectangles are obtained, i.e.,
the left and the right sub-rectangles.

The width of the new sub-rectangles is equal to the width of the
rectangle/sub-rectangle of the previous level
and the sum of the lengths of the left and right sub-rectangles is equal to the
length of the rectangle/sub-rectangle of the previous level.

Similarly, if a horizontal cut is performed, two new rectangles are obtained,
i.e., the top and bottom sub-rectangles.

Their dimensions can also be calculated considering the dimensions of the
rectangle/sub-rectangle of the previous level.
"""


class DirectionEnum(Enum):
    HORIZONTAL = 1  # Horizontal Cut
    VERTICAL = 2  # Vertical Cut

###############################################################################

# Enum Problem


class ProblemEnum(Enum):
    SKP = 1  # Single Knapsack Problem
    SLOPP = 2  # Single Large Object Placement Problem
    USLOPP = 3  # Unbounded Single Large Object Placement Problem

###############################################################################

# Enum Variant Problem


"""
1 - In a problem instance for the weighted SLOPP, the item types are
characterized by a length li, a width wi, a value vi, and a maximum demand di.
In the weighted SLOPP, the demand for each item is greater than 1 (di > 1),
and its value (vi) is different from its area.

2 - When addressing the unweighted variant, the value of the items is set to:
vi = li · wi
"""


class VariantEnum(Enum):
    WEIGHTED = 1  # The value of each item is not equal to its area
    UNWEIGHTED = 2  # The value of each item is equal to its area

###############################################################################

# Enum Algorithm Type


"""
1 - The Floating-Cuts model with guillotine constraints is named ‘FC4_Base’,
since from the guillotine cut, a maximum of four sub-rectangles are generated.

2 - Since five new sub-rectangles can be generated from a cut,
the FloatingCuts model will be represented by the acronym ‘FC5’.
"""


class AlgorithmEnum(Enum):
    ARCS4 = 1
    ARCS5 = 2

###############################################################################

# Criterium to stop the h-test (time or objective function value)


"""
This enumeration represents the stop criteria for the h-test
(breadth-first search test) used in the algorithm.
The criteria can be time, objective function value or a number of h-iterations.
"""


class OptimizationCriteriumEnum(Enum):
    TIME = 1
    OBJ = 2
    H = 3


###############################################################################

# Enum Cutting Type

"""
The Floating-Cuts model is general because it can address both non-guillotine
and guillotine cutting problems with an unlimited number of stages.
"""


class CutTypeEnum(Enum):
    GUILLOTINE = 1
    NONGUILLOTINE1STORDER = 2
