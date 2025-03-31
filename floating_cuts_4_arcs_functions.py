# This module contains functions associated to the KP

from floating_cuts_enums import RelativePositionEnum

###############################################################################

# Elements in the tree (m)

"""
For a sub-rectangle tree with h levels, it is possible to enumerate all indexes
of the sub-rectangles and store them in a vector M^h. Since M^h depends on the
number of levels of the tree and any cut generates a maximum of four
sub-rectangles, the number of elements of M^h is:
"""


def M(h):
    sum = 0
    for j in range(h+1):  # Up to h
        sum += pow(4, j)
    return sum

###############################################################################

# Sub-rectangles index enumeration


"""
In rectangle j, two types of cuts can be performed,
i.e., vertical and horizontal.

If a vertical cut is performed, a maximum of two new sub-rectangles is
obtained, i.e., sub-rectangle j + 1 (left) and sub-rectangle j + 2 (right),
and their dimensions are obtained considering the dimension of rectangle j.

If a horizontal cut is performed, a maximum of two new sub-rectangles is
created, i.e., sub-rectangle j + 3 (top) and sub-rectangle j + 4 (bottom),
and, similarly, their dimensions are obtained considering the dimensions of
rectangle j.

The new sub-rectangles can be further cut vertically or horizontally,
in a recursive way.

If index 0 is assigned to the root node (initial plate),
indexes 1, 2, 3, and 4 are assigned to the left, right, top and bottom
sub-rectangles (respectively).

In the same way, if sub-rectangle 1 is cut, it can result in sub-rectangles
5, 6, 7 and 8 (left, right, top, and bottom), and so forth for the other
sub-rectangles.

Every element j (not a leaf) has 4 children in the M^h vector
(left, right, top, and bottom), which can be traced:

l = 4 · j + 1
r = 4 · j + 2
t = 4 · j + 3
b = 4 · j + 4

Therefore, given an index j (∀j != 0), it is possible to obtain the
sub-rectangle’s relative position (left, right, top, and bottom):
"""


def left(j):  # Left element from j (l)
    return 4 * j + 1


def right(j):  # Right element from j (r)
    return 4 * j + 2


def top(j):  # Top element from j (t)
    return 4 * j + 3


def bottom(j):  # Bottom element from j (b)
    return 4 * j + 4

###############################################################################

# Identify the relative position of sub-rectangle j


"""
Given an index j (∀j != 0), it is possible to obtain the sub-rectangle’s
relative position (left, right, top, and bottom).
"""


def relativePosition(j):
    if j % 4 == 1:
        return RelativePositionEnum.LEFT
    if j % 4 == 2:
        return RelativePositionEnum.RIGHT
    if j % 4 == 3:
        return RelativePositionEnum.TOP
    return RelativePositionEnum.BOTTOM

###############################################################################

# Identify the father of sub-rectangle j


"""
Knowing the relative position of a given sub-rectangle j,
it is possible to identify the index of the parent of j.
"""


def father(j):
    if relativePosition(j) is RelativePositionEnum.LEFT:
        return int((j-1)/4)
    if relativePosition(j) is RelativePositionEnum.RIGHT:
        return int((j-2)/4)
    if relativePosition(j) is RelativePositionEnum.TOP:
        return int((j-3)/4)
    return int((j-4)/4)

###############################################################################

# Identify the level (h) of the tree where sub-rectangle j is located


def level(j):
    if j == 0:
        return 0

    h = 1
    while j/pow(2, 2*h) >= 1:  # j/pow(4, h)
        h += 1

    return h

###############################################################################

# Number of stages to reach sub-rectangle j (nS)


"""
The limitation on the number of stages can be considered by simply removing the
decision variables associated with the subrectangles that require the
generation of a number of stages larger than the k stage limit.
To identify these decision variables, we need to calculate how many changes in
the orientation of the cuts (horizontal or vertical) need to occur up to the
j sub-rectangle.

For example, if a sub-rectangle is generated after two vertical cuts, followed
by a horizontal cut, this corresponds to two stages.
"""


def stages(j, qh=None, qv=None):
    if j == 0:
        return 0

    nS = 1
    """
    The while loop is executed until the index j is equal to 0, which is, until
    it reaches the root of the tree. The condition within the loop checks
    whether there has been a change in the cutting orientation between the
    parent of j and j itself. This is done by comparing the relative positions
    between the parent of j and j. If there is a change in orientation
    (for example, if the parent is vertical and the sub-rectangle j is
    horizontal, or vice versa), it means that a new stage has started,
    so nS is incremented by 1.
    """
    while j != 0:
        if (((relativePosition(father(j)) is RelativePositionEnum.TOP or
              relativePosition(father(j)) is RelativePositionEnum.BOTTOM) and
                (relativePosition(j) is RelativePositionEnum.LEFT or
                 relativePosition(j) is RelativePositionEnum.RIGHT)) or
                ((relativePosition(father(j)) is RelativePositionEnum.LEFT or
                  relativePosition(father(j)) is RelativePositionEnum.RIGHT)
                    and (relativePosition(j) is RelativePositionEnum.TOP or
                         relativePosition(j) is RelativePositionEnum.BOTTOM))):
            nS += 1
        j = father(j)
        # Atualiza o valor de j para o índice do pai de j, permitindo que o
        # loop prossiga para o próximo nível superior na árvore.

    return nS  # Number of Stages

###############################################################################

# Calculate the path for each item in the tree


def getIndividualPaths(delta, L_sub, W_sub, debug=False):
    paths = []
    items = []
    subrectangles = []

    for i in range(len(delta)):
        for j in range(len(delta[i])):
            if delta[i][j].x is not None and delta[i][j].x > 0.5:
                items.append(i)
                subrectangles.append(j)
                node_id = j
                path = []

                while node_id != 0:
                    path.append((relativePosition(node_id),  # relative position
                                 node_id,  # current index
                                 father(node_id),  # father index
                                 L_sub[node_id].x,  # L_current
                                 W_sub[node_id].x))  # W_current
                    node_id = father(node_id)

                paths.append(path)

    if debug:
        #              0                1               2          3          4
        print("(relative position; current index; father index, L_current; W_current)")
        for i in items:  # range(len(items))
            print(f"item {i}:\t", end='')
            for el in paths[i]:
                print(el, end='\n\t\t')
            print()

    return paths, items, subrectangles

###############################################################################

# Coordinate for each item inside the bin


def getCoordinatesFirstItem(paths, items, L, W, r, debug=False):
    coords = []

    # Values based on rotation
    rotated = False if (r.x is not None and r.x <= 0.5) else True

    for i in range(len(paths)):
        left_coord = 0
        right_coord = W if rotated else L
        bottom_coord = 0
        top_coord = L if rotated else W

        if debug:
            print(f"item {items[i]} (size {len(paths[i])}):")

        for level in range(len(paths[i])-1, -1, -1):
            if paths[i][level][0] is RelativePositionEnum.LEFT:
                right_coord = left_coord + paths[i][level][3]

                if debug:
                    print(f"\tnew right_coord: {right_coord}")

            elif paths[i][level][0] is RelativePositionEnum.RIGHT:

                left_coord = right_coord - paths[i][level][3]

                if debug:
                    print(f"\tnew left_coord: {left_coord}")

            elif paths[i][level][0] is RelativePositionEnum.BOTTOM:
                top_coord = bottom_coord + paths[i][level][4]

                if debug:
                    print(f"\tnew top_coord: {top_coord}")

            elif paths[i][level][0] is RelativePositionEnum.TOP:
                bottom_coord = top_coord - paths[i][level][4]

                if debug:
                    print(f"\tnew bottom_coord: {bottom_coord}")

        coords.append((left_coord, bottom_coord))

    return coords
