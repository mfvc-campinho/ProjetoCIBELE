# This module contains functions associated to the KP

from floating_cuts_enums import *

# Elements in the tree

# For a sub-rectangle tree with h levels, it is possible to enumerate all indexes of the
# sub-rectangles and store them in a vector M^h. Since M^h depends on the number of levels
# of the tree and any cut generates a maximum of five sub-rectangles, the number of elements
# of M^h is:


def M(h):
    sum = 0
    for j in range(h+1):  # Up to h
        sum += pow(5, j)
    return sum

#######################################################################################

# Sub-rectangles index enumeration

# Two special sets of indexes are considered:
# 1) element 0 is the root node and does not have a parent sub-rectangle; and
# 2) the elements of the last level of the tree, known as leaves, do not have children.
# Every element j (not a leaf) has 5 children in the M^h vector
# (top left (TL), top right (TR), bottom right (BR), bottom left (BL) and center (CC)),
# which can be traced:

# TL = 5 · j + 1
# TR = 5 · j + 2
# BR = 5 · j + 3
# BL = 5 · j + 4
# CC = 5 · j + 5

# TopLeft element from j (TL)


def TL(j):
    return 5 * j + 1

# TopRight element from j (TR)


def TR(j):
    return 5 * j + 2

# BottomRight element from j (BR)


def BR(j):
    return 5 * j + 3

# BottomLeft element from j (BL)


def BL(j):
    return 5 * j + 4

# Center element from j (CC)


def CC(j):
    return 5 * j + 5

#######################################################################################

# Identify the relative position of sub-rectangle j

# Given an index j (∀j != 0), it is possible to obtain the sub-rectangle’s
# relative position (top left, top right, bottom right, bottom left and center):


def relativePosition(j):
    if j % 5 == 1:
        return RelativePositionEnum.TOPLEFT
    if j % 5 == 2:
        return RelativePositionEnum.TOPRIGHT
    if j % 5 == 3:
        return RelativePositionEnum.BOTTOMRIGHT
    if j % 5 == 4:
        return RelativePositionEnum.BOTTOMLEFT
    return RelativePositionEnum.CENTER

#######################################################################################

# Identify the father of sub-rectangle j

# Knowing the relative position of a given sub-rectangle j, it is possible to identify the
# index of the parent of j


def father(j):
    if relativePosition(j) is RelativePositionEnum.TOPLEFT:
        return int((j-1)/5)
    if relativePosition(j) is RelativePositionEnum.TOPRIGHT:
        return int((j-2)/5)
    if relativePosition(j) is RelativePositionEnum.BOTTOMRIGHT:
        return int((j-3)/5)
    if relativePosition(j) is RelativePositionEnum.BOTTOMLEFT:
        return int((j-4)/5)
    return int((j-5)/5)

#######################################################################################

# Identify the level of the tree where sub-rectangle j is located


def level(j):
    if j == 0:
        return 0

    h = 1
    while j/pow(5, h) >= 1:
        h += 1
    return h

#######################################################################################

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
                    # relative position; current index; father index, L_current; W_current
                    path.append((relativePosition(node_id), node_id, father(
                        node_id), L_sub[node_id].x, W_sub[node_id].x))
                    node_id = father(node_id)
                paths.append(path)

    if debug:
        #              0                1               2          3           4
        print("(relative position; current index; father index, L_current; W_current)")
        for i in range(len(items)):
            print(f"item {items[i]}:\t", end='')
            for el in paths[i]:
                print(el, end='\n\t\t')
            print()

    return paths, items, subrectangles

#######################################################################################

# Coordinate for each item inside the bin


def getCoordinatesFirstItem(paths, items, L, W, L_sub, W_sub, debug=False):
    coords = []

    for i in range(len(paths)):
        left_coord = 0
        right_coord = L
        bottom_coord = 0
        top_coord = W

        if debug:
            print(f"item {items[i]} (size {len(paths[i])}):")

        for level in range(len(paths[i])-1, -1, -1):
            # RelativePositionEnum.LEFT:
            if paths[i][level][0] is RelativePositionEnum.TOPLEFT:
                right_coord = left_coord + paths[i][level][3]
                bottom_coord = top_coord - paths[i][level][4]

                if debug:
                    print(
                        f"\tnew (right_coord;bottom_coord): ({right_coord};{bottom_coord})")

            # RelativePositionEnum.RIGHT:
            elif paths[i][level][0] is RelativePositionEnum.TOPRIGHT:
                left_coord = right_coord - paths[i][level][3]
                bottom_coord = top_coord - paths[i][level][4]

                if debug:
                    print(
                        f"\tnew (left_coord;bottom_coord): ({left_coord};{bottom_coord})")

            # RelativePositionEnum.BOTTOM:
            elif paths[i][level][0] is RelativePositionEnum.BOTTOMRIGHT:
                left_coord = right_coord - paths[i][level][3]
                top_coord = bottom_coord + paths[i][level][4]

                if debug:
                    print(
                        f"\tnew (left_coord;top_coord): ({left_coord};{top_coord})")

            # RelativePositionEnum.TOP:
            elif paths[i][level][0] is RelativePositionEnum.BOTTOMLEFT:
                right_coord = left_coord + paths[i][level][3]
                top_coord = bottom_coord + paths[i][level][4]

                if debug:
                    print(
                        f"\tnew (right_coord;top_coord): ({right_coord};{top_coord})")

            elif paths[i][level][0] is RelativePositionEnum.CENTER:
                # neighbors
                tl_item_length = L_sub[TL(paths[i][level][2])].x
                bl_item_width = W_sub[BL(paths[i][level][2])].x
                # update now
                left_coord += tl_item_length
                bottom_coord += bl_item_width
                right_coord = left_coord + paths[i][level][3]
                top_coord = bottom_coord + paths[i][level][4]

                if debug:
                    print(
                        f"\tnew (left_coord;right_coord;top_coord;bottom_coord): ({left_coord};{right_coord};{top_coord};{bottom_coord})")

        coords.append((left_coord, bottom_coord))

    return coords
