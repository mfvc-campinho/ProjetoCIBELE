### Imports ###
import sys
sys.path.append(r'C:\Users\Utilizador\Documents\Intercâmbio - Portugal\Documentos\Documentos INESC-TEC\Artigos e Docs - Projeto CIBELE\floating-cuts-main')

from numpy import Infinity
from ortools.linear_solver import pywraplp
from floating_cuts_enums import *

import floating_cuts_5_arcs_functions as fc5f
import packing_io as io
import time as tm
import random as rd
import copy as cp

# Method to generate the Floating Cuts (model 5 arcs) for packing problems
def FloatingCuts(instance_name='cgcut1.txt', h=4, problem=ProblemEnum.SKP, stages=Infinity, rotation=False, variant=VariantEnum.UNWEIGHTED, plot=True):
    ## Read input file
    dir_name = 'dat'
    n, L, W, l, w, d, v = io.readfile(dir_name, instance_name, h, problem, variant)
    #height of the tree
    m = fc5f.M(h)
    #print(m, n, L, W, l, w, d, v)

    # Create the mip solver with the Cplex backend.
    solver = pywraplp.Solver.CreateSolver('GUROBI')
    
    ##Parameters
    ii = [i for i in range(n)]
    jj = [j for j in range(m)]
    
    ## Variables
    # Basic
    x = {}
    L_sub = {}
    W_sub = {}
    z = {}
    for j in jj:
        x[j] = solver.IntVar(0,1,'x[%i]' % j)
        L_sub[j] = solver.IntVar(0, L, 'L_sub[%i]' % j)
        W_sub[j] = solver.IntVar(0, W, 'W_sub[%i]' % j)
        z[j] = solver.IntVar(0,1,'z[%i]' % j)
    delta = {}
    qh = {}
    qv = {}
    for i in ii:
        for j in jj:
            delta[(i,j)] = solver.IntVar(0,1,'delta_%i_%i' % (i, j))
            qh[(i,j)] = solver.IntVar(0, max(d), 'qh_%i_%i' % (i, j))
            qv[(i,j)] = solver.IntVar(0, max(d), 'qv_%i_%i' % (i, j))

    ## Objective function
    solver.Maximize(sum([v[i] * (qh[(i,j)]+qv[(i,j)]) for i in ii for j in jj])) #1
    
    # ----------------------------[BASIC CONSTRAINTS]----------------------------
    for j in jj:
        solver.Add( x[j] + sum([delta[(i,j)] for i in ii]) <= 1 ) #2
        
    for i in ii:
        solver.Add( sum([qh[(i,j)] + qv[(i,j)] for j in jj]) <= d[i] ) #3

    for i in ii:
        for j in jj:
            solver.Add(qh[(i,j)] <= d[i]*delta[(i,j)]) #4
            solver.Add(qv[(i,j)] <= d[i]*delta[(i,j)]) #5
            solver.Add(l[i]*qh[(i,j)] <= L_sub[j]) #6
            solver.Add(w[i]*qv[(i,j)] <= W_sub[j]) #7
            solver.Add(qh[(i,j)] <= d[i]*z[j]) #8
            solver.Add(qv[(i,j)] <= d[i]*(1-z[j])) #9

    solver.Add(L_sub[0] == L) #10
    solver.Add(W_sub[0] == W) #11

    # ----------------------------[LENGTH CUTS CONSTRAINTS]----------------------------
    for j in range(fc5f.M(h-1)):
        solver.Add(L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] <= L*(1 - x[j]) + L_sub[j]) #12
        solver.Add(L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] >= L_sub[j] - L*(1 - x[j])) #13
        solver.Add(L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] <= L*(1 - x[j]) + L_sub[j]) #14
        solver.Add(L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L*(1 - x[j])) #15
        solver.Add(L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] <= L*(1 - x[j]) + L_sub[j]) #16
        solver.Add(L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L*(1 - x[j])) #17
        solver.Add(L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] + L_sub[fc5f.BR(j)] + L_sub[fc5f.BL(j)] + L_sub[fc5f.CC(j)] <= L*x[j]) #18

    # ----------------------------[WIDTH CUTS CONSTRAINTS]----------------------------
    for j in range(fc5f.M(h-1)):
        solver.Add(W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] <= W*(1 - x[j]) + W_sub[j]) #19
        solver.Add(W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] >= W*(x[j] - 1) + W_sub[j]) #20
        solver.Add(W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] <= W*(1 - x[j]) + W_sub[j]) #21
        solver.Add(W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] >= W*(x[j] - 1) + W_sub[j]) #22
        solver.Add(W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] <= W*(1 - x[j]) + W_sub[j]) #23
        solver.Add(W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] >= W*(x[j] - 1) + W_sub[j]) #24
        solver.Add(W_sub[fc5f.TL(j)] + W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] + W_sub[fc5f.BL(j)] + W_sub[fc5f.CC(j)] <= W*x[j]) #25


    # check the LP
    # model.writeLP(problem.name + '-floating-cuts-5-cuts.lp')

    # timer
    tic = tm.perf_counter()

    # solve
    #print(listSolvers(onlyAvailable=True))
    
    #OBS: imeLimit does not work with gurobi and pulp 2.4. If we use only
    #'GUROBI', it works; however, when the time limit is found, the gurobi
    #status returns 'Not solved', i.e., the model status before optimizing.
    #solver = getSolver('GUROBI_CMD', timeLimit = 900.0, msg=output_solver)
    
    output_solver = True if plot == True else False
    #solver = getSolver('CPLEX_CMD', timeLimit=900, msg=output_solver)
    #print("Solving...")
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
    
    # write the model solution
    io.writeFile(instance_name, solver, totalT, h, status, rotation, stages, problem, variant, AlgorithmEnum.ARCS5)

    #graphical output
    if plot == True:
        print("Calculating path relative to each item...")
        paths, items, subrectangles = fc5f.getIndividualPaths(delta, L_sub, W_sub)

        print("\nCalculating items coordinates...")
        coords = fc5f.getCoordinatesFirstItem(paths, items, L, W)

        print("\nCalculating directions and possible repetitions...")
        direc_rep = fc5f.calculateDirectionAndRepetitions(items, subrectangles, qv, qh)

    
        print("\nGraphical solution...")
        io.plot(L, W, l, w, coords, items, direc_rep, int(model.objective.value()))

    #statistics text output
    else:
        print("Writting in text file statistics...")
        io.appendStatistics(problem,stages,rotation,variant,instance_name,model,h,totalT,solver,plot,AlgorithmEnum.ARCS5)
