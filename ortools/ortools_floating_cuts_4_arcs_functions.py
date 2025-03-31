# This module contains functions associated to the KP
import sys
sys.path.append(r'C:\Users\Utilizador\Documents\Intercâmbio - Portugal\Documentos\Documentos INESC-TEC\Artigos e Docs - Projeto CIBELE\floating-cuts-main')

from floating_cuts_enums import *

################################################################################

# Elements in the tree
def M(h):
    sum = 0
    for j in range(h):
        sum += pow(4, j)
    return sum

################################################################################

# Left element from j
def left(j):
    return 4 * j + 1

# Right element from j
def right(j):
    return 4 * j + 2

# Top element from j
def top(j):
    return 4 * j + 3

# Bottom element from j
def bottom(j):
    return 4 * j + 4

################################################################################

# Identify the relative position of sub-rectangle j.
def relativePosition(j):
    if j%4 == 1: return RelativePositionEnum.LEFT
    if j%4 == 2: return RelativePositionEnum.RIGHT
    if j%4 == 3: return RelativePositionEnum.TOP
    return RelativePositionEnum.BOTTOM

################################################################################

# Identify the father of sub-rectangle j.
def father(j):
    if relativePosition(j) is RelativePositionEnum.LEFT: return (j-1)/4
    if relativePosition(j) is RelativePositionEnum.RIGHT: return (j-2)/4
    if relativePosition(j) is RelativePositionEnum.TOP: return (j-3)/4
    return (j-4)/4

################################################################################

# Identify the level of the tree where sub-rectangle j is located.
def level(j):
    if j == 0: return 0

    h = 1
    while  j/pow(2, 2*h) >= 1:
        h += 1

    return h

################################################################################

# Number of stages to reach sub-rectangle j.
def stages(j):
    if j == 0: return 0

    nS = 1
    while j != 0:
        if (((relativePosition(father(j)) is RelativePositionEnum.TOP or relativePosition(father(j)) is RelativePositionEnum.BOTTOM) and
                (relativePosition(j) is RelativePositionEnum.LEFT or relativePosition(j) is RelativePositionEnum.RIGHT)) or ((relativePosition(father(j)) is RelativePositionEnum.LEFT or
                relativePosition(father(j)) is RelativePositionEnum.RIGHT) and (relativePosition(j) is RelativePositionEnum.TOP or
                relativePosition(j) is RelativePositionEnum.BOTTOM))):
            nS += 1
        j = father(j)

    return nS

################################################################################

# Calculate the path for each item in the tree
def getIndividualPaths(delta, ii, jj, L_sub, W_sub, debug=False):
    paths = []
    items = []
    subrectangles = []
    for i in ii:
        for j in jj:
            if delta[(i,j)].solution_value() > 0.5:
                items.append(i)
                subrectangles.append(j)
                node_id = j
                path = []
                while node_id != 0:
                    #relative position; current index; father index, L_current; W_current
                    path.append((relativePosition(node_id), node_id, father(node_id), L_sub[node_id].value(), W_sub[node_id].value()))
                    node_id = father(node_id)
                paths.append(path)

    if debug:
        print("(relative position; current index; father index, L_current; W_current)")
        for i in items:
            print(f"item {i}:\t", end='')
            for el in paths[i]:
                print(el,end='\n\t\t')
            print()

    return paths, items, subrectangles

################################################################################

# Calculate the path for each item in the tree
def getIndividualPathsBKP(delta, L_sub, W_sub, debug=False):
    paths = []
    items = []
    subrectangles = []
    for i in range(len(delta)):
        for j in range(len(delta[i])):
            if delta[i][j].value() > 0.5:
                items.append(i)
                subrectangles.append(j)
                node_id = j
                path = []
                while node_id != 0:
                    #relative position; current index; father index, L_current; W_current
                    path.append((relativePosition(node_id), node_id, father(node_id), L_sub[node_id].value(), W_sub[node_id].value()))
                    node_id = father(node_id)
                paths.append(path)

    if debug:
        print("(relative position; current index; father index, L_current; W_current)")
        for i in items:
            print(f"item {i}:\t", end='')
            for el in paths[i]:
                print(el,end='\n\t\t')
            print()

    return paths, items, subrectangles

################################################################################

# Coordinate for each item inside the bin
def getCoordinatesFirstItem(paths, items, L, W, debug=False):
    coords = []
    for i in range(len(paths)):
        left_coord = 0
        right_coord = L
        bottom_coord = 0
        top_coord = W
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

################################################################################

# Calculate the repetitions side by side an item must be placed, in addition to its direction
def calculateDirectionAndRepetitions(items, subrectangles, qv={}, qh={}):
    #(direction, repetitions)
    direc_rep = []
    for i in range(len(items)):
        #SKP
        if len(qv) == 0:
            direc_rep.append((DirectionEnum.HORIZONTAL, 1))

        #SLOPP
        else:
            #increment direction
            if qv[(items[i],subrectangles[i])].solution_value() > 0.5:
                direc_rep.append((DirectionEnum.VERTICAL,   int(qv[(items[i],subrectangles[i])].solution_value())))
            else:
                direc_rep.append((DirectionEnum.HORIZONTAL, int(qh[(items[i],subrectangles[i])].solution_value())))

    return direc_rep

################################################################################

# Calculate the repetitions side by side an item must be placed, in addition to its direction
def calculateDirectionAndRepetitionsBKP(items, subrectangles, qv=[], qh=[]):
    #(direction, repetitions)
    direc_rep = []
    for i in range(len(items)):
        #SKP
        if len(qv) == 0:
            direc_rep.append((DirectionEnum.HORIZONTAL, 1))

        #SLOPP
        else:
            #increment direction
            if qv[items[i]][subrectangles[i]].value() > 0.5:
                direc_rep.append((DirectionEnum.VERTICAL,   int(qv[items[i]][subrectangles[i]].value())))
            else:
                direc_rep.append((DirectionEnum.HORIZONTAL, int(qh[items[i]][subrectangles[i]].value())))

    return direc_rep

################################################################################

## Plot the knapsack and its items
#def plotSKP(L, W, l, w, coords, items, debug=False):
#    rectangles = []
#    for i in range(len(items)):
#        rectangles.append( (l[items[i]], w[items[i]]) )
#
#    if debug:
#        print(f"Rectangles sizes: {rectangles}")
#        print(f"Rectangles position: {coords}")
#        print(f"Bounding box: {L}, {W}")
#
#    fig, ax = plt.subplots()
#    #box dimension
#    ax.plot([0,L], [0, W], color="none")
#
#    for i in range(len(coords)):
#        #rectangle
#        ax.add_patch(Rectangle((coords[i][0], coords[i][1]), rectangles[i][0], rectangles[i][1], linewidth = 1.5, facecolor="lightseagreen", edgecolor='black'))
#        #label
#        centerx = coords[i][0] + 0.45*rectangles[i][0]
#        centery = coords[i][1] + 0.4*rectangles[i][1]
#        plt.text(centerx, centery, f'{items[i]}')
#
#    #bin representation
#    ax.add_patch(Rectangle((0,0), L, W, linewidth = 2.5, facecolor="none", edgecolor='black'))
#
#    #plt.axis('off')
#    ax.tick_params(axis='x', colors='white')
#    ax.tick_params(axis='y', colors='white')
#    ax.spines['bottom'].set_color('white')
#    ax.spines['top'].set_color('white')
#    ax.spines['right'].set_color('white')
#    ax.spines['left'].set_color('white')
#    plt.xlabel("Length (" + f"{L}" + ")")
#    plt.ylabel("Width (" + f"{W}" + ")")
#    titulo1 = 'Packing density '+'{:.2%}'.format(calculateItemsArea(l,w,items)/(L*W))+' ('+str(L)+' x '+str(W)+'), '+str(len(coords))+' rectangles'
#    plt.title(titulo1)
#    plt.show()
