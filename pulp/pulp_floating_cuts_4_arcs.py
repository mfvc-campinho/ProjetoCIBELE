### Imports ###
from numpy import Infinity
from pulp import *  # puplp -> Python Linear Programming
from floating_cuts_enums import *

import floating_cuts_4_arcs_functions as fc4f
import packing_io as io
import time as tm
import random as rd
import copy as cp

# Method to generate the Floating Cuts (model 4 arcs) for packing problems
def FloatingCuts(instance_name='cgcut1.txt', h=4, problem=ProblemEnum.SKP, stages=Infinity, rotation=False, variant=VariantEnum.UNWEIGHTED, plot=True):
    ## Read input file
    dir_name = 'dat'
    n, L, W, l, w, d, v = io.readFile(dir_name, instance_name, problem, variant)
    
    # Height of the tree
    m = fc4f.M(h)
    #print(m, n, L, W, l, w, d, v)

    ## Create milp
    model = LpProblem(problem.name + "-floating-cuts-4-arcs", LpMaximize)

    ## Parameters
    ii = [i for i in range(n)]
    jj = [j for j in range(m)]
    qh = []
    qv = []

    ## Variables
    # Basic
    x = LpVariable.dicts("x", jj, cat='Binary')
    y = LpVariable.dicts("y", jj, cat='Binary')
    r = LpVariable("r", cat='Binary')
    L_sub = LpVariable.dicts("L_sub", jj, lowBound=0, upBound=L, cat='Integer')
    W_sub = LpVariable.dicts("W_sub", jj, lowBound=0, upBound=W, cat='Integer')
    delta = LpVariable.dicts("delta", (ii, jj), cat='Binary')
    
    # SLOPP
    if problem is ProblemEnum.SLOPP:
        qh = LpVariable.dicts("qh", (ii, jj), lowBound=0, upBound=max(d), cat='Integer')
        qv = LpVariable.dicts("qv", (ii, jj), lowBound=0, upBound=max(d), cat='Integer')
        z = LpVariable.dicts("z", jj, cat='Binary')

    ## Objective Function
    if problem is ProblemEnum.SKP:
        # 1
        model += lpSum([v[i] * delta[i][j] for i in ii for j in jj]), "objective_function_SKP"
    
    elif problem is ProblemEnum.SLOPP:
        # 39
        model += lpSum([v[i] * (qh[i][j]+qv[i][j]) for i in ii for j in jj]), "objective_function_SLOPP"
    
    else:
        print("Undefined problem!")
        exit()

    # ----------------------------[BASIC CONSTRAINTS]----------------------------
    # SKP
    if problem is ProblemEnum.SKP:
        # 2
        # Constraints ensures that a sub-rectangle j can be cut vertically or horizontally or an item is assigned to it.
        for j in jj:
            model += x[j] + y[j] + lpSum([delta[i][j] for i in ii]) <= 1, f"only_one_type{j}"
        # 3
        for j in jj:
            model += lpSum(l[i] * delta[i][j] for i in ii) <= L_sub[j], f"length_L_{j}"
        # 4
        for j in jj:
            model += lpSum(w[i] * delta[i][j] for i in ii) <= W_sub[j], f"width_W_{j}"
        # 5
        for i in ii:
            model += lpSum(delta[i][j] for j in jj) <= 1, f"upper_delta_{i}"

    # SLOPP
    elif problem is ProblemEnum.SLOPP:
        # 40
    #    for j in range(fc4f.M(h-1)-1):
        for j in jj:
            model += x[j] + y[j] + lpSum([delta[i][j] for i in ii]) <= 1, f"only_one_type{j}"
        # 41
        for i in ii:
            model += lpSum(qh[i][j] + qv[i][j] for j in jj) <= d[i], f"demand_{i}"

        for i in ii:
            for j in jj:
                # Constraints  are used to connect decision variables qh, qv and delta.
                model += qh[i][j] <= d[i] * delta[i][j], f"demand_qh_42_{i}_{j}"
                model += qv[i][j] <= d[i] * delta[i][j], f"demand_qv_43_{i}_{j}"

                model += l[i] * qh[i][j] <= L_sub[j], f"length_44_{i}_{j}"
                model += w[i] * qv[i][j] <= W_sub[j], f"width_45_{i}_{j}"

                # Constraints ensure that at least one item fits in sub-rectangle j.
                model += l[i] * delta[i][j] <= L_sub[j] + L * (1 - delta[i][j]), f"length_46_{i}_{j}"
                model += w[i] * delta[i][j] <= W_sub[j] + W * (1 - delta[i][j]), f"width_47_{i}_{j}"
                
                # Constraints ensure that for a given sub-rectangle j only the
                # assignment of items grouped horizontally or vertically is allowed.
                model += qh[i][j] <= d[i] * z[j], f"z_48_{i}_{j}"
                model += qv[i][j] <= d[i] * (1 - z[j]), f"z_49_{i}_{j}"

    ## Rotation Case
    if rotation == True:
        # 36
        # Constraint forcing the first cut to be vertical
        model += x[0] == 1, f"x0_rot"
        # 37
        model += L_sub[0] == L * r + W * (1 - r), f"L0_rot"
        # 38
        model += W_sub[0] == W * r + L * (1 - r), f"W0_rot"
    else:
        # 6
        model += L_sub[0] == L, f"L0"
        # 7
        model += W_sub[0] == W, f"W0"

    # ----------------------------[VERTICAL CUTS CONSTRAINTS]----------------------------
    # Constraints (46) - (53) are associated with vertical cuts performed in the parent sub-rectangles.
    for j in range(fc4f.M(h - 1)):
        # Constraints (46) and (47) ensure that when a vertical cut is performed, the sum of the lengths of the resulting 
        # left and right sub-rectangles is equal to the length of the parent sub-rectangle.
        model += L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] <= L*(1 - x[j]) + L_sub[j], f"vertical_8_{j}"
        model += L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] >= L_sub[j] - L*(1 - x[j]), f"vertical_9_{j}"

        # Constraints ensure that the length of the left and right sub-rectangles are set to zero, respectively,
        # if a vertical cut is not performed on the parent subrectangle (xj = 0).
        model += L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] <= L * x[j], f"vertical_10_{j}"

        # Constraints (49) - (52) ensure that when a vertical cut is performed, the width of the resulting
        # left and right sub-rectangles is equal to the width of the parent sub-rectangle.
        model += W_sub[fc4f.left(j)] <= W * (1 - x[j]) + W_sub[j], f"vertical_11_{j}"
        model += W_sub[fc4f.left(j)] >= W * (x[j] - 1) + W_sub[j], f"vertical_12_{j}"
        model += W_sub[fc4f.right(j)] <= W * (1 - x[j]) + W_sub[j], f"vertical_13_{j}"
        model += W_sub[fc4f.right(j)] >= W * (x[j] - 1) + W_sub[j], f"vertical_14_{j}"

        # Constraints ensure that the width of the left and right sub-rectangles are set to zero, respectively,
        # if a vertical cut is not performed on the parent subrectangle (xj = 0)
        model += W_sub[fc4f.left(j)] + W_sub[fc4f.right(j)] <= 2 * W * x[j], f"vertical_15_{j}"

    # ----------------------------[HORIZONTAL CUTS CONSTRAINTS]----------------------------
    # Constraints (54) - (61) are related to horizontal cuts performed in the parent sub-rectangle.
    for j in range(fc4f.M(h-1)):
        # Constraints (54) and (55) ensure that if a horizontal cut is performed in the parent sub-rectangle, the sum of
        # the width of the resulting top and bottom sub-rectangles is equal to the width of the parent sub-rectangle.
        model += W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] <= W * (1 - y[j]) + W_sub[j], f"vertical_16_{j}"
        model += W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] >= W_sub[j] - W * (1 - y[j]), f"vertical_17_{j}"

        # Constraints ensure that if a horizontal cut is not performed (yj = 0) in the parent sub-rectangle, 
        # the width of the top and bottom sub-rectangles are set to zero, respectively.
        model += W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] <= W * y[j], f"vertical_18_{j}"

        # Constraints (57) - (60) guarantee that the length of the resulting top and bottom subrectangles is equal
        # to the length of the parent sub-rectangle.
        model += L_sub[fc4f.top(j)] <= L * (1 - y[j]) + L_sub[j], f"vertical_19_{j}"
        model += L_sub[fc4f.top(j)] >= L * (y[j] - 1) + L_sub[j], f"vertical_20_{j}"
        model += L_sub[fc4f.bottom(j)] <= L * (1 - y[j]) + L_sub[j], f"vertical_21_{j}"
        model += L_sub[fc4f.bottom(j)] >= L * (y[j] - 1) + L_sub[j], f"vertical_22_{j}"

        # Constraints ensure that if a horizontal cut is not performed (yj = 0) in the parent sub-rectangle, 
        # the length of the top and bottom sub-rectangles are set to zero, respectively.
        model += L_sub[fc4f.top(j)] + L_sub[fc4f.bottom(j)] <= 2 * L * y[j], f"vertical_23_{j}"

    # ----------------------------[STAGES LIMIT]----------------------------
    if stages != Infinity:
        for j in jj:
            if (fc4f.stages(j) > stages):
                model += x[j] == False, f"stage_x_{j}"
                model += y[j] == False, f"stage_y_{j}"
                for i in ii:
                    model += delta[i][j] == False, f"stage_delta_{i}_{j}"

    ## -----------------------------[MODEL STRENGTHENING]----------------------------
    # -----------------------------[LAST LEVEL RECTANGELS]-----------------------------
    for j in range(fc4f.M(h - 1), fc4f.M(h)):
        model += lpSum(delta[i][j] for i in ii) <= 1, f"last_level_27_{j}"

    # ----------------------------[SYMMETRY REDUCTION]----------------------------
    # Constraints are used to reduce symmetry in the generation of sub-rectangles by imposing that the 
    # left (top) subrectangle is larger than the right (bottom) sub-rectangle when a vertical (horizontal) cut is applied.
        for j in range(fc4f.M(h-1)):
        model += L_sub[4 * j + 1] - L_sub[4 * j + 2] >= L * (x[j] - 1), f"symmetry_reduction_28_{j}"
        model += W_sub[4 * j + 3] - W_sub[4 * j + 4] >= W * (y[j] - 1), f"symmetry_reduction_29_{j}"

    # ----------------------------[AREA BOUND]----------------------------
    # Constraints  state that the total area of the rectangles cut does not exceed
    # the area of the initial rectangle.
    model += lpSum(l[i] * w[i] * delta[i][j] for i in ii for j in jj) <= L * W, f"area_bound_30"

    # ----------------------------[RELATION FATHER CHILDREN]----------------------------
    # Constraints ensure that if an item is allocated to a sub-rectangle j, then j has no descendants.
    # Constraints ensure that if a sub-rectangle j is not cut, then j has no descendants. 
    # This condition prevents a rectangle from remaining “undecided” (is neither cut nor has an item assigned to it) along several levels of the tree.

    for j in range(fc4f.M(h - 2)):
        model += lpSum(x[4 * j + k] + y[4 * j + k] + lpSum(delta[i][4 * j + k] for i in ii) for k in range(4)) <= 4 - 4 * lpSum(delta[i][j] for i in ii), f"relation_31_{j}"
        model += lpSum(x[4 * j + k] + y[4 * j + k] + lpSum(delta[i][4 * j + k] for i in ii) for k in range(4)) <= 6 * (x[j] + y[j]), f"relation_33_{j}"

    for j in range(fc4f.M(h - 2), fc4f.M(h - 1)):
        model += lpSum(delta[i][4*j+k] for k in range(4) for i in ii) <= 4 - 4 * lpSum(delta[i][j] for i in ii), f"relation_32_{j}"
        model += lpSum(delta[i][4*j+k] for k in range(4) for i in ii) <= 2 * (x[j] + y[j]), f"relation_34_{j}"

    # Check the LP
    # model.writeLP(problem.name + '-floating-cuts-4-arcs.lp')

    # timer
    tic = tm.perf_counter()

    # Solve
    #print(listSolvers(onlyAvailable=True))

    # OBS: imeLimit does not work with gurobi and pulp 2.4. If we use only
    # 'GUROBI', it works; however, when the time limit is found, the gurobi
    # status returns 'Not solved', i.e., the model status before optimizing.
    #solver = getSolver('GUROBI_CMD', timeLimit = 900.0, msg=output_solver)

    output_solver = True if plot == True else False
    #solver = getSolver(GUROBI_CMD(options=[("timeLimit", 3)]), msg=output_solver)
    #print("Solving...")
    #model.solve(solver)
    model.solve(GUROBI_CMD(options=[("timeLimit", 1),("msg",output_solver)]))

    # Timer
    toc = tm.perf_counter()
    totalT = toc - tic

    #print(model.objective.lowBound())
    #print(model.objective.upBound)
    #print(model.objective.getLb))
    #print(model.objective.getUb)

    # Write the model solution
    io.writeFile(instance_name, model, totalT, h, rotation, stages, problem, variant, AlgorithmEnum.ARCS4)

    # Graphical Output
    if plot == True:
        print("Calculating path relative to each item...")
        paths, items, subrectangles = fc4f.getIndividualPaths(delta, L_sub, W_sub)

        print("\nCalculating items coordinates...")
        coords = fc4f.getCoordinatesFirstItem(paths, items, L, W)

        print("\nCalculating directions and possible repetitions...")
        direc_rep = fc4f.calculateDirectionAndRepetitions(items, subrectangles, qv, qh)

        print("\nGraphical solution...")
        io.plot(L, W, l, w, coords, items, direc_rep, int(model.objective.value()))

    # Statistics Text Output
    else:
        print("Writting in text file statistics...")
        io.appendStatistics(problem, stages, rotation, variant, instance_name, model, h, totalT, solver, plot, AlgorithmEnum.ARCS4)
