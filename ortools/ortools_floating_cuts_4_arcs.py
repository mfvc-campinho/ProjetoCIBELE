### Imports ###
import copy as cp
import random as rd
import time as tm
import packing_io as io
import ortools_floating_cuts_4_arcs_functions as fc4f
from floating_cuts_enums import *
from ortools.linear_solver import pywraplp
from numpy import Infinity
import sys
sys.path.append(
    r'C:\Users\Utilizador\Documents\Intercâmbio - Portugal\Documentos\Documentos INESC-TEC\Artigos e Docs - Projeto CIBELE\floating-cuts-main')


# Method to generate the Floating Cuts (model 4 arcs) for packing problems

def FloatingCuts(instance_name='cgcut1.txt', h=4, problem=ProblemEnum.SKP, stages=Infinity, rotation=False, variant=VariantEnum.UNWEIGHTED, plot=True):
    # Read input file
    dir_name = 'dat'
    n, L, W, l, w, d, v = io.readfile(
        dir_name, instance_name, h, problem, variant)
    # height of the tree
    m = fc4f.M(h)
    # print(m, n, L, W, l, w, d, v)

    # Create the mip solver with the Cplex backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Parameters
    ii = [i for i in range(n)]
    jj = [j for j in range(m)]

    # Variables
    # Basic
    x = {}
    y = {}
    r = {}
    L_sub = {}
    W_sub = {}
    for j in jj:
        x[j] = solver.IntVar(0, 1, 'x[%i]' % j)
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)
        r[j] = solver.IntVar(0, 1, 'r[%i]' % j)
        L_sub[j] = solver.IntVar(0, L, 'L_sub[%i]' % j)
        W_sub[j] = solver.IntVar(0, W, 'W_sub[%i]' % j)

    delta = {}
    for i in ii:
        for j in jj:
            delta[(i, j)] = solver.IntVar(0, 1, 'delta_%i_%i' % (i, j))

    # SLOPP
    qh = {}
    qv = {}
    if problem is ProblemEnum.SLOPP:
        z = {}
        for i in ii:
            for j in jj:
                qh[(i, j)] = solver.IntVar(0, max(d), 'qh_%i_%i' % (i, j))
                qv[(i, j)] = solver.IntVar(0, max(d), 'qv_%i_%i' % (i, j))

    # Objective function
    if problem is ProblemEnum.SKP:
        solver.Maximize(solver.Sum([v[i] * delta[(i, j)]
                        for i in ii for j in jj]))  # 1
    elif problem is ProblemEnum.SLOPP:
        solver.Maximize(([v[i] * (qh[(i, j)]+qv[(i, j)])
                        for i in ii for j in jj]))  # 39
    else:
        print("Undefined problem!")
        exit()

    # ----------------------------[BASIC CONSTRAINTS]----------------------------
    # SKP
    if problem is ProblemEnum.SKP:
        for j in jj:
            solver.Add(x[j] + y[j] + sum(delta[(i, j)] for i in ii) <= 1)  # 2
        for j in jj:
            solver.Add(sum([l[i] * delta[(i, j)] for i in ii]) <= L_sub[j])  # 3
        for j in jj:
            solver.Add(sum([w[i] * delta[(i, j)] for i in ii]) <= W_sub[j])  # 4
        for i in ii:
            solver.Add(sum(delta[(i, j)] for j in jj) <= 1)  # 5

    # SLOPP
    elif problem is ProblemEnum.SLOPP:
        #    for j in range(fc4f.M(h-1)-1):
        for j in jj:
            solver.Add(x[j] + y[j] + sum([delta[(i, j)]
                       for i in ii]) <= 1)  # 40
        for i in ii:
            solver.Add(sum(qh[(i, j)] + qv[(i, j)] for j in jj) <= d[i])  # 41

        for i in ii:
            for j in jj:
                solver.Add(qh[(i, j)] <= d[i]*delta[(i, j)])
                solver.Add(qv[(i, j)] <= d[i]*delta[(i, j)])
                solver.Add(l[i]*qh[(i, j)] <= L_sub[j])
                solver.Add(w[i]*qv[(i, j)] <= W_sub[j])
                solver.Add(l[i]*delta[(i, j)] <= L_sub[j] + L*(1-delta[(i, j)]))
                solver.Add(w[i]*delta[(i, j)] <= W_sub[j] + W*(1-delta[(i, j)]))
                solver.Add(qh[(i, j)] <= d[i]*z[j])
                solver.Add(qv[(i, j)] <= d[i]*(1-z[j]))

    # Rotation case
    if rotation == True:
        solver.Add(x[0] == 1)  # 36
        solver.Add(L_sub[0] == L * r + W * (1 - r))  # 37
        solver.Add(W_sub[0] == W * r + L * (1 - r))  # 38
    else:
        solver.Add(L_sub[0] == L)  # 6
        solver.Add(W_sub[0] == W)  # 7

    # ----------------------------[VERTICAL CUTS CONSTRAINTS]----------------------------
    for j in range(fc4f.M(h-1)):
        solver.Add(L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)]
                   <= L*(1 - x[j]) + L_sub[j])
        solver.Add(L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)]
                   >= L_sub[j] - L*(1 - x[j]))
        solver.Add(L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] <= L * x[j])
        solver.Add(W_sub[fc4f.left(j)] <= W*(1 - x[j]) + W_sub[j])
        solver.Add(W_sub[fc4f.left(j)] >= W*(x[j] - 1) + W_sub[j])
        solver.Add(W_sub[fc4f.right(j)] <= W*(1 - x[j]) + W_sub[j])
        solver.Add(W_sub[fc4f.right(j)] >= W*(x[j] - 1) + W_sub[j])
        solver.Add(W_sub[fc4f.left(j)] + W_sub[fc4f.right(j)] <= 2*W*x[j])

    # ----------------------------[HORIZONTAL CUTS CONSTRAINTS]----------------------------
    for j in range(fc4f.M(h-1)):
        solver.Add(W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)]
                   <= W*(1 - y[j]) + W_sub[j])
        solver.Add(W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)]
                   >= W_sub[j] - W*(1 - y[j]))
        solver.Add(W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] <= W * y[j])
        solver.Add(L_sub[fc4f.top(j)] <= L*(1 - y[j]) + L_sub[j])
        solver.Add(L_sub[fc4f.top(j)] >= L*(y[j] - 1) + L_sub[j])
        solver.Add(L_sub[fc4f.bottom(j)] <= L*(1 - y[j]) + L_sub[j])
        solver.Add(L_sub[fc4f.bottom(j)] >= L*(y[j] - 1) + L_sub[j])
        solver.Add(L_sub[fc4f.top(j)] + L_sub[fc4f.bottom(j)] <= 2*L*y[j])

    # ----------------------------[STAGES LIMIT]----------------------------
    if stages != Infinity:
        for j in jj:
            if (fc4f.stages(j) > stages):
                solver.Add(x[j] == False)
                solver.Add(y[j] == False)
                for i in ii:
                    solver.Add(delta[(i, j)] == False)

    # -----------------------------[MODEL STRENGTHENING]----------------------------
    # -----------------------------[LAST LEVEL RECTANGELS]-----------------------------
#    for j in range(fc4f.M(h-1), fc4f.M(h)):
#        model += lpSum(delta[(i,j)] for i in ii) <= 1, f"last_level_27_{j}"

    # ----------------------------[SYMMETRY REDUCTION]----------------------------
#    for j in range(fc4f.M(h-1)):
#        model += L_sub[4*j+1] - L_sub[4*j+2] >= L*(x[j] - 1), f"symmetry_reduction_28_{j}"
#        model += W_sub[4*j+3] - W_sub[4*j+4] >= W*(y[j] - 1), f"symmetry_reduction_29_{j}"

    # ----------------------------[AREA BOUND]----------------------------
#    model += lpSum(l[i]*w[i]*delta[(i,j)] for i in ii for j in jj) <= L*W, f"area_bound_30"

    # ----------------------------[RELATION FATHER CHILDREN]----------------------------
#    for j in range(fc4f.M(h-2)):
#        model += lpSum(x[4*j+k] + y[4*j+k] + lpSum(delta[i][4*j+k] for i in ii) for k in range(4)) <= 4 - 4 * lpSum(delta[(i,j)] for i in ii), f"relation_31_{j}"
#        model += lpSum(x[4*j+k] + y[4*j+k] + lpSum(delta[i][4*j+k] for i in ii) for k in range(4)) <= 6 * (x[j] + y[j]), f"relation_33_{j}"

#    for j in range(fc4f.M(h-2), fc4f.M(h-1)):
#        model += lpSum(delta[i][4*j+k] for k in range(4) for i in ii) <= 4 - 4 * lpSum(delta[(i,j)] for i in ii), f"relation_32_{j}"
#        model += lpSum(delta[i][4*j+k] for k in range(4) for i in ii) <= 2 * (x[j] + y[j]), f"relation_34_{j}"

    # check the LP
    # model.writeLP(problem.name + '-floating-cuts-4-arcs.lp')
    io.writeString("lp", solver.ExportModelAsLpFormat(False))

    # timer
    tic = tm.perf_counter()

    # solve
    # print(listSolvers(onlyAvailable=True))

    # OBS: imeLimit does not work with gurobi and pulp 2.4. If we use only
    # 'GUROBI', it works; however, when the time limit is found, the gurobi
    # status returns 'Not solved', i.e., the model status before optimizing.
    # solver = getSolver('GUROBI_CMD', timeLimit = 900.0, msg=output_solver)

    output_solver = True if plot == True else False
    # solver = getSolver('CPLEX_CMD', timeLimit=900, msg=output_solver)
    # print("Solving...")
    if output_solver:
        solver.EnableOutput()
    else:
        solver.SuppressOutput()
    solver.SetTimeLimit(5)
    status = solver.Solve()
    print(status)

    # timer
    toc = tm.perf_counter()
    totalT = toc - tic

    # print(model.objective.lowBound())
    # print(model.objective.upBound)
    # print(model.objective.getLb))
    # print(model.objective.getUb)

    # write the model solution
    io.writeFile(instance_name, solver, totalT, h, rotation,
                 stages, problem, variant, AlgorithmEnum.ARCS4)

    # graphical output
    if plot == True:
        print("Calculating path relative to each item...")
        paths, items, subrectangles = fc4f.getIndividualPaths(
            delta, ii, jj, L_sub, W_sub)

        print("\nCalculating items coordinates...")
        coords = fc4f.getCoordinatesFirstItem(paths, items, L, W)

        print("\nCalculating directions and possible repetitions...")
        direc_rep = fc4f.calculateDirectionAndRepetitions(
            items, subrectangles, qv, qh)

        print("\nGraphical solution...")
        io.plot(L, W, l, w, coords, items, direc_rep,
                int(solver.Objective().Value()))

    # statistics text output
    else:
        print("Writting in text file statistics...")
        io.appendStatistics(problem, stages, rotation, variant, instance_name,
                            model, h, totalT, solver, plot, AlgorithmEnum.ARCS4)
