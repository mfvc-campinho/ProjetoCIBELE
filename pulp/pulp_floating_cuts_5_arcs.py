### Imports ###
from numpy import Infinity
from pulp import *  # puplp -> Python Linear Programming
from ortools.linear_solver import pywraplp
from floating_cuts_enums import *

import floating_cuts_5_arcs_functions as fc5f
import packing_io as io
import time as tm
import random as rd
import copy as cp

###################################################################################################

# Method to generate the Floating Cuts (model 5 arcs) for packing problems
def FloatingCuts(instance_name='cgcut1.txt', h=4, problem=ProblemEnum.SKP, stages=Infinity, rotation=False, variant=VariantEnum.UNWEIGHTED, plot=True):
    ## Read input file
    dir_name = 'dat'
    n, L, W, l, w, d, v = io.readfile(dir_name, instance_name, h, problem, variant)
    
    # Height of the tree
    m = fc5f.M(h)
    #print(m, n, L, W, l, w, d, v)

    ## Create milp
    model = LpProblem(problem.name + "-floating-cuts-5-cuts", LpMaximize)

    ## Parameters
    ii = [i for i in range(n)]
    jj = [j for j in range(m)]
    qh = []
    qv = []

    ## Variables
    # Basic
    x = LpVariable.dicts("x", jj, cat='Binary')
    L_sub = LpVariable.dicts("L_sub", jj, lowBound=0, upBound=L, cat='Integer')
    W_sub = LpVariable.dicts("W_sub", jj, lowBound=0, upBound=W, cat='Integer')
    delta = LpVariable.dicts("delta", (ii, jj), cat='Binary')
    qh = LpVariable.dicts("qh", (ii, jj), lowBound=0, upBound=max(d), cat='Integer')
    qv = LpVariable.dicts("qv", (ii, jj), lowBound=0, upBound=max(d), cat='Integer')
    z = LpVariable.dicts("z", jj, cat='Binary')


    ## Objective Function
    #1
    # The objective function (# 1) maximizes the values of the items assigned to the rectangular plate.
    model += lpSum([v[i] * (qh[i][j] + qv[i][j]) for i in ii for j in jj]), "objective_function_SLOPP"

    # ----------------------------[BASIC CONSTRAINTS]----------------------------
    #2
    # Constraints (2) ensure that for each sub-rectangle j, only three scenarios can exist:
    # the sub-rectangle is cut;
    # or items of type i are assigned to the sub-rectangle;
    # or the sub-rectangle is not used.
    for j in jj:
        model += x[j] + lpSum([delta[i][j] for i in ii]) <= 1, f"only_one_type{j}"

    #3
    # Constraints (3) ensure that the demand of each item type i is not exceeded.
    for i in ii:
        model += lpSum(qh[i][j] + qv[i][j] for j in jj) <= d[i], f"demand_{i}"

    for i in ii:
        for j in jj:
            # Constraints (4) and (5) are used to connect decision variables qh, qv and delta.
            model += qh[i][j] <= d[i] * delta[i][j], f"demand_qh_4_{i}_{j}"
            model += qv[i][j] <= d[i] * delta[i][j], f"demand_qv_5_{i}_{j}"

            # It is guaranteed that the items geometrically fit in the sub-rectangle in constraints
            # (6) and (7).
            model += l[i] * qh[i][j] <= L_sub[j], f"length_6_{i}_{j}"
            model += w[i] * qv[i][j] <= W_sub[j], f"width_7_{i}_{j}"

            # Constraints ensure that for a given sub-rectangle j only the
            # assignment of items grouped horizontally or vertically is allowed.
            model += qh[i][j] <= d[i] * z[j], f"z_8_{i}_{j}"
            model += qv[i][j] <= d[i] * (1 - z[j]), f"z_9_{i}_{j}"

    # Constraints initialize the root sub-rectangle with the dimensions of the plate.
    #10
    model += L_sub[0] == L, f"L0"
    #11
    model += W_sub[0] == W, f"W0"

    # ----------------------------[LENGTH CUTS CONSTRAINTS]----------------------------
    # Constraints are associated with the length of the child sub-rectangles if sub-rectangle j is cut.
    for j in range(fc5f.M(h-1)):
        # Constraints ensure that when a cut is performed, the sum of the lengths of
        # the resulting top left and top right sub-rectangles is equal to the length of sub-rectangle j.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] <= L * (1 - x[j]) + L_sub[j], f"length_12_{j}"
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] >= L_sub[j] - L*(1 - x[j]), f"length_13_{j}"

        # Constraints ensure that when a cut is performed, the sum of the lengths of 
        # the resulting top left, center and bottom right sub-rectangles is equal to the length of sub-rectangle j.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] <= L * (1 - x[j]) + L_sub[j], f"length_14_{j}"
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L * (1 - x[j]), f"length_15_{j}"

        # Constraints ensure that if sub-rectangle j is cut, the sum of the width of
        # the top right and bottom right sub-rectangles is equal to the width of sub-rectangle j.
        model += L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] <= L*(1 - x[j]) + L_sub[j], f"length_16_{j}"
        model += L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L * (1 - x[j]), f"length_17_{j}"

        # Constraints guarantee that if sub-rectangle j is not cut, the width of the child subrectangles is equal to zero.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] + L_sub[fc5f.BR(j)] + L_sub[fc5f.BL(j)] + L_sub[fc5f.CC(j)] <= L * x[j], f"length_18_{j}"  # Não é 3 * L * x[j]?

    # ----------------------------[WIDTH CUTS CONSTRAINTS]----------------------------
    # Constraints are associated with the width of the child sub-rectangles if sub-rectangle j is cut.
    for j in range(fc5f.M(h-1)):
        # Constraints ensure that if sub-rectangle j is cut, the sum of the widths of
        # the top left and bottom left sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] <= W * (1 - x[j]) + W_sub[j], f"width_19_{j}"
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] >= W * (x[j] - 1) + W_sub[j], f"width_20_{j}"

        # Constraints ensure that if subrectangle j is cut, the sum of the width of the top right,
        # center and bottom left sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] <= W * (1 - x[j]) + W_sub[j], f"width_21_{j}"
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] >= W * (x[j] - 1) + W_sub[j], f"width_22_{j}"

        # Constraints ensure that if sub-rectangle j is cut, the sum of the width of
        # the top right and bottom right sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] <= W * (1 - x[j]) + W_sub[j], f"width_23_{j}"
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] >= W * (x[j] - 1) + W_sub[j], f"width_24_{j}"

        # Constraints guarantee that if sub-rectangle j is not cut, the width of the child subrectangles is equal to zero.
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] + W_sub[fc5f.BL(j)] + W_sub[fc5f.CC(j)] <= W * x[j], f"width_25_{j}"  # Não é 3 * L * x[j]?

    # check the LP
    # model.writeLP(problem.name + '-floating-cuts-5-cuts.lp')

    # timer
    tic = tm.perf_counter()

    # solve
    #print(listSolvers(onlyAvailable=True))

    # OBS: imeLimit does not work with gurobi and pulp 2.4. If we use only
    # 'GUROBI', it works; however, when the time limit is found, the gurobi
    # status returns 'Not solved', i.e., the model status before optimizing.
    #solver = getSolver('GUROBI_CMD', timeLimit = 900.0, msg=output_solver)

    output_solver = True if plot == True else False
    solver = getSolver('CPLEX_CMD', timeLimit=900, msg=output_solver)
    #print("Solving...")
    model.solve(solver)

    # Timer
    toc = tm.perf_counter()
    totalT = toc - tic

    # Write the model solution
    io.writeFile(instance_name, model, totalT, h, solver.name, rotation, stages, problem, variant, AlgorithmEnum.ARCS5)

    # Graphical Output
    if plot == True:
        print("Calculating path relative to each item...")
        paths, items, subrectangles = fc5f.getIndividualPaths(delta, L_sub, W_sub)

        print("\nCalculating items coordinates...")
        coords = fc5f.getCoordinatesFirstItem(paths, items, L, W)

        print("\nCalculating directions and possible repetitions...")
        direc_rep = fc5f.calculateDirectionAndRepetitions(items, subrectangles, qv, qh)

        print("\nGraphical solution...")
        io.plot(L, W, l, w, coords, items, direc_rep, int(model.objective.value()))

    # Statistics Text Output
    else:
        print("Writting in text file statistics...")
        io.appendStatistics(problem, stages, rotation, variant, instance_name, model, h, totalT, solver, plot, AlgorithmEnum.ARCS5)
