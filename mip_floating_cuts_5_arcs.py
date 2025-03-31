### Imports ###
from numpy import Infinity
from mip import *
from floating_cuts_enums import *
from milp_utils import *

import floating_cuts_5_arcs_functions as fc5f
import packing_io as io
import packing_utils as utils

###################################################################################################

# Method to generate the Floating Cuts (model 5 arcs) for packing problems
def FloatingCuts(previous_model=MILP_Variables(), instance_name='cgcut1.txt', database_type='distributor', database_name='', h=4, algorithm=AlgorithmEnum.ARCS4, problem=ProblemEnum.SKP, stages=Infinity, rotation=False, variant=VariantEnum.UNWEIGHTED, cut_type=CutTypeEnum.NONGUILLOTINE1STORDER, max_time=3600, plot=True, reload=False):
    dir_name = 'dat/' + database_type + "/" + database_name

    ## Read input file
    if database_type == 'distributor':
        n, L, W, l, w, d, v = io.readDistributorInstance(dir_name, instance_name, problem, variant)
        id = instance_name  # They are the same here
    else:
        id, n, L, W, l, w, d, v = io.readManufacturerInstance(dir_name, instance_name)

    # Constant
    m = fc5f.M(h)  # Height of the tree

    ## Create milp
    model = Model(sense=MAXIMIZE, solver_name=GRB, name=problem.name + "-floating-cuts-5-arcs")  # Use GRB for Gurobi

    ## Parameters
    ## Rotation case: only the items will be rotated, the bin remains fixed
    r = utils.Rotation(0)
    if rotation == True:
        ii = [i for i in range(2 * n)]  # With rotation we duplicate the items to mimic rotation

        # Duplicating items
        l_copy = utils.copy.deepcopy(l)
        w_copy = utils.copy.deepcopy(w)

        l.extend(w_copy)
        w.extend(l_copy)
        v.extend(utils.copy.deepcopy(v))
        d.extend(utils.copy.deepcopy(d))
        #print(m, n, L, W, l, w, d, v)

    else:
        ii = [i for i in range(n)]  # Set of n item types indexed by i, i = 1, ..., n

    jj = [j for j in range(m)]  # Set of m of all possible sub-rectangles j, j = 1, ..., m
    qh = []  # Number of items of type i placed side by side (horizontally) in sub-rectangle j
    qv = []  # Number of items of type i placed on the top of each other (vertically) in sub-rectangle

    # Debug
    print(f"m: {m}")
    print(f"n: {n}")
    print(f"L: {L}")
    print(f"W: {W}")
    print(f"ii: {ii}")
    print(f"jj: {jj}")

    for t in ii:
        print(f"\tl: {l[t]} | w: {w[t]} | d: {d[t]} | v: {v[t]}")

    ## Variables
    # Basic
    # -> Domain of the decision variables
    x = [model.add_var(name='x[%i]' % j, var_type=BINARY) for j in jj]  # 29

    delta = [[model.add_var('delta[%i][%i]' % (i, j), var_type=BINARY) for j in jj] for i in ii]  # 30

    qh = [[model.add_var(name='qh[%i][%i]' % (i, j), var_type=INTEGER, lb=0, ub=d[i]) for j in jj] for i in ii]  # 31
    qv = [[model.add_var(name='qv[%i][%i]' % (i, j), var_type=INTEGER, lb=0, ub=d[i]) for j in jj] for i in ii]  # 31

    z = [model.add_var(name='z[%i]' % j, var_type=BINARY) for j in jj]  # 32

    L_sub = [model.add_var(name='L_sub[%i]' % j, var_type=INTEGER, lb=0, ub=L) for j in jj]  # 33
    W_sub = [model.add_var(name='W_sub[%i]' % j, var_type=INTEGER, lb=0, ub=W) for j in jj]  # 33

    if cut_type is CutTypeEnum.GUILLOTINE:
        beta = [model.add_var(name='beta[%i]' % j, var_type=BINARY) for j in jj]

    ###Constraints###
    print('Adding constraints 1...33')
    # To strengthen the Floating-Cuts MILP formulation (1)-(33), a set of valid inequalities
    # were added to the model and are described next.

    ## Objective Function
    # The objective function (# 1) maximizes the values of the items assigned to the rectangular plate.
    if database_type == 'distributor':
        model += xsum([v[i] * (qh[i][j] + qv[i][j]) for i in ii for j in jj]), "objective_function_SLOPP_5_arcs_distributor"  # 1
    else:
        model += xsum([(qh[i][j] + qv[i][j]) for i in ii for j in jj]), "objective_function_SLOPP_5_arcs_manufacturer"  # 1

    # ----------------------------[BASIC CONSTRAINTS]----------------------------
    for j in jj:
        # Constraints (2) ensure that for each sub-rectangle j, only three scenarios can exist:
        # the sub-rectangle is cut;
        # or items of type i are assigned to the sub-rectangle;
        # or the sub-rectangle is not used.
        model += x[j] + xsum([delta[i][j] for i in ii]) <= 1, f"only_one_type{j}"  # 2

        # It is guaranteed that the items geometrically fit in the sub-rectangle in constraints
        # (6) and (7).
        model += xsum(l[i] * qh[i][j] for i in ii) <= L_sub[j], f"length_6_{j}"  # 6
        model += xsum(w[i] * qv[i][j] for i in ii) <= W_sub[j], f"width_7_{j}"  # 7

    # Demand only in the 'distributor' database
    # Constraints (3) ensure that the demand of each item type i is not exceeded.
    if database_type == 'distributor':
        # Demand when considering rotation
        if rotation == True:
            for i in range(n):
                model += xsum(qh[i][j] + qh[n + i][j] + qv[i][j] + qv[n + i][j] for j in jj) <= d[i], f"rotation_demand_{i}"  # 3
        else:
            for i in ii:
                model += xsum(qh[i][j] + qv[i][j] for j in jj) <= d[i], f"demand_{i}"  # 3

    for i in ii:
        for j in jj:
            # Constraints (4) and (5) are used to connect decision variables qh, qv and delta.
            model += qh[i][j] <= d[i] * delta[i][j], f"demand_qh_4_{i}_{j}"  # 4
            model += qv[i][j] <= d[i] * delta[i][j], f"demand_qv_5_{i}_{j}"  # 5

            # Constraints (8) and (9) ensure that at least one item fits in sub-rectangle j.
            model += l[i] * delta[i][j] <= L_sub[j] + L * (1 - delta[i][j]), f"ldelta_8_{i}_{j}"  # 8
            model += w[i] * delta[i][j] <= W_sub[j] + W * (1 - delta[i][j]), f"wdelta_9_{i}_{j}"  # 9

            # Constraints (10) and (11) ensure that for a given sub-rectangle j only the
            # assignment of items grouped horizontally or vertically is allowed.
            model += qh[i][j] <= d[i] * z[j], f"z_10_{i}_{j}"  # 10
            model += qv[i][j] <= d[i] * (1 - z[j]), f"z_11_{i}_{j}"  # 11

            # Constraints (14) are used to connect qh, qv with delta, regarding the
            # quantity of items and the assignment to a sub-rectangle.
            model += qh[i][j] + qv[i][j] >= delta[i][j], f"qtt_v_delta_14_{i}_{j}"  # 14

    # Constraints (12) and (13) initialize the root sub-rectangle with the dimensions of the plate.
    model += L_sub[0] == L, f"L0"  # 12
    model += W_sub[0] == W, f"W0"  # 13

    # ----------------------------[LENGTH CUTS CONSTRAINTS]----------------------------
    # Constraints (15) - (21) are associated with the length of the child sub-rectangles if sub-rectangle j is cut.
    for j in range(fc5f.M(h - 1)):
        # Constraints (15) and (16) ensure that when a cut is performed, the sum of the lengths of
        # the resulting top left and top right sub-rectangles is equal to the length of sub-rectangle j.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] <= L * (1 - x[j]) + L_sub[j], f"length_15_{j}"
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] >= L_sub[j] - L*(1 - x[j]), f"length_16_{j}"

        # Constraints (17) and (18) ensure that when a cut is performed, the sum of the lengths of 
        # the resulting top left, center and bottom right sub-rectangles is equal to the length of sub-rectangle j.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] <= L * (1 - x[j]) + L_sub[j], f"length_17_{j}"
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.CC(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L * (1 - x[j]), f"length_18_{j}"

        # Constraints (19) and (20) ensure that when a cut is performed, the sum of the lengths of
        # the resulting bottom left and bottom right sub-rectangles is equal to the length of sub-rectangle j.        
        model += L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] <= L*(1 - x[j]) + L_sub[j], f"length_19_{j}"
        model += L_sub[fc5f.BL(j)] + L_sub[fc5f.BR(j)] >= L_sub[j] - L*(1 - x[j]), f"length_20_{j}"

        # Constraints (21) ensure that if sub-rectangle j is not cut, the length of the child sub-rectangles is equal to zero.
        model += L_sub[fc5f.TL(j)] + L_sub[fc5f.TR(j)] + L_sub[fc5f.BR(j)] + L_sub[fc5f.BL(j)] + L_sub[fc5f.CC(j)] <= 3 * L * x[j], f"length_21_{j}"

    # ----------------------------[WIDTH CUTS CONSTRAINTS]----------------------------
    # Constraints (22) - (28) are associated with the width of the child sub-rectangles if sub-rectangle j is cut.
    for j in range(fc5f.M(h-1)):
        # Constraints (22) and (23) ensure that if sub-rectangle j is cut, the sum of the widths of
        # the top left and bottom left sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] <= W * (1 - x[j]) + W_sub[j], f"width_22_{j}"
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.BL(j)] >= W * (x[j] - 1) + W_sub[j], f"width_23_{j}"

        # Constraints (24) and (25) ensure that if subrectangle j is cut, the sum of the width of
        # the top right, center and bottom left sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] <= W * (1 - x[j]) + W_sub[j], f"width_24_{j}"
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.CC(j)] + W_sub[fc5f.BL(j)] >= W * (x[j] - 1) + W_sub[j], f"width_25_{j}"

        # Constraints (26) and (27) ensure that if sub-rectangle j is cut, the sum of the width of
        # the top right and bottom right sub-rectangles is equal to the width of sub-rectangle j.
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] <= W * (1 - x[j]) + W_sub[j], f"width_26_{j}"
        model += W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] >= W * (x[j] - 1) + W_sub[j], f"width_27_{j}"

        # Constraints (28) guarantee that if sub-rectangle j is not cut, the width of the child subrectangles is equal to zero.
        model += W_sub[fc5f.TL(j)] + W_sub[fc5f.TR(j)] + W_sub[fc5f.BR(j)] + W_sub[fc5f.BL(j)] + W_sub[fc5f.CC(j)] <= 3 * W * x[j], f"width_28_{j}"

    # -------------------------------------------------------------------------------
    # ----------------------------[SYMMETRY REDUCTION]----------------------------
    # ******************************
    has_symmetry_reduction = True
    # ******************************
    if has_symmetry_reduction or cut_type is CutTypeEnum.GUILLOTINE:
        print('Adding constraints 34...39')

        # Constraints (34) and (35) are added to the model to remove the symmetry, ensuring that
        # the Floating-Cuts model generates only the first-order non-guillotine cutting pattern.
        for j in range(fc5f.M(h - 1)):
            model += L_sub[fc5f.BL(j)] >=  L_sub[fc5f.TL(j)], f"pattern_non_guillotine_34_{j}"  # 34
            model += L_sub[fc5f.TL(j)] >=  L_sub[fc5f.BR(j)], f"pattern_non_guillatine_35_{j}"  # 35

        # Area Bound
        # Constraints (36) state that the total area of the rectangles cut does not exceed
        # the area of the initial rectangle.
        # SKP
        if problem is ProblemEnum.SKP:
            model += xsum(l[i] * w[i] * xsum(delta[i][j] for j in jj) for i in ii) <= L * W, f"area_bound_skp_36_"  # 36
        # SLOPP
        elif problem is ProblemEnum.SLOPP:
            model += xsum(l[i] * w[i] * xsum(qh[i][j] + qv[i][j] for j in jj) for i in ii) <= L * W, f"area_bound_slopp_37_"  # 37

        # Fix to zero variables for subrectangles last level cuts
        # -> Sub-rectangles in the last level of the tree are not cut
        # Constraints (37) ensure that in the last level of the tree, the sub-rectangles 
        # cannot be further cut.
        # OBS: The set {|M^h−1|, ..., |M^h|} represents the sub-rectangles’ indexes 
        # belonging to the last level of the sub-rectangles tree
        for j in range(fc5f.M(h - 1), fc5f.M(h)):
            model += x[j] == 0, f"xj_0_38_{j}"  # 38

        # If a sub-rectangle is not cut (xj = 0), then it has no children
        for j in range(fc5f.M(h - 1)):
            model += xsum(x[5 * j + k] + xsum(delta[i][5 * j + k] for i in ii) for k in range(1, 6)) <= 5 * x[j], f"relation_39_{j}"  # 39

    # ----------------------------[GUILLOTINE CUTTING TYPE ONLY]----------------------------
    if cut_type is CutTypeEnum.GUILLOTINE:
        print('Adding constraints 40...41')
        # These constraints impose that the sub-rectangle on the center of a first-order 
        # non-guillotine pattern does not exist, and the cutting pattern becomes a guillotine one.

        only_once = True
        for j in range(fc5f.M(h-1)):
            # Constraints (39) ensure that if decision variable βCC(j) is equal to one,
            # the length of the sub-rectangle on the center will be zero.
            model += L_sub[fc5f.CC(j)] <=  beta[fc5f.CC(j)] * L, f"guillotine_vertical_40_{j}"  # 40

            # Constraints (40) ensure that if decision variable βCC(j) is equal to zero,
            # the width of the sub-rectangle on the center, will be zero.
            model += W_sub[fc5f.CC(j)] <=  (1 - beta[fc5f.CC(j)]) * W, f"guillotine_horizontal_41_{j}"  # 41

            # ----------------------------[SYMMETRY REDUCTION]----------------------------
            if has_symmetry_reduction:
                if only_once:
                    print('Adding constraints 42...45')
                    # The symmetric solutions may be discarded by adding constraints (41) to (44)

                    only_once = False

                model += L_sub[fc5f.BR(j)] <=  L_sub[fc5f.BL(j)] + L * (1 - beta[fc5f.CC(j)]), f"symmetry_42_{j}"  # 42
                model += L_sub[fc5f.TR(j)] <=  L_sub[fc5f.TL(j)] + L * (1 - beta[fc5f.CC(j)]), f"symmetry_43_{j}"  # 43

                model += W_sub[fc5f.BL(j)] <=  W_sub[fc5f.TL(j)] + W * beta[fc5f.CC(j)], f"symmetry_44_{j}"  # 44
                model += W_sub[fc5f.TR(j)] <=  W_sub[fc5f.BR(j)] + W * beta[fc5f.CC(j)], f"symmetry_45_{j}"  # 45


    ### Initialization with a initial solution###
    ## User defined
    #if problem is CutTypeEnum.GUILLOTINE:
    #    MILP_Variables.test5arcs(model, x, L_sub, W_sub, delta, ii, jj, z, qh, qv, beta)
    #else:
    #    MILP_Variables.test5arcs(model, x, L_sub, W_sub, delta, ii, jj, z, qh, qv)
    ## From the previous h level
    if previous_model.has_variables():
        if cut_type is CutTypeEnum.GUILLOTINE:
            previous_model.copy_from_previous_5arcsmodel(model, x, L_sub, W_sub, delta, z, qh, qv, beta)
        else:
            previous_model.copy_from_previous_5arcsmodel(model, x, L_sub, W_sub, delta, z, qh, qv)

    # Check the LP
    #model.write(problem.name + '-floating-cuts-5-cuts.lp')

    # Timer
    tic = utils.time.perf_counter()

    # Solve
    #print("Solving...")
    try:
        model.optimize(max_seconds=max_time)
    except MemoryError as error:
        print("Writting in text file the MemoryErrors...")
        status = "STACKOVERFLOW"
        io.appendError(algorithm, problem, stages, rotation, variant, instance_name, status, h, plot)
        return 0.0, 0.0, 'OPTIMAL', MILP_Variables()  # Stack overflow delimits the maximum h used

    # Timer
    toc = utils.time.perf_counter()
    totalT = toc - tic

    # Output
    print("Calculating path relative to each item...")
    paths, items, subrectangles = fc5f.getIndividualPaths(delta, L_sub, W_sub)

    print("\nCalculating items coordinates...")
    coords = fc5f.getCoordinatesFirstItem(paths, items, L, W, L_sub, W_sub)

    print("\nCalculating directions and possible repetitions...")
    direc_rep = io.calculateDirectionAndRepetitions(items, subrectangles, qv, qh)

    # Write the model solution
    io.writeFile(instance_name, model, totalT, h, rotation, stages, algorithm, problem, variant, L, W, l, w, coords, items, direc_rep)

    # Graphical Output
    if plot == True:
        print("\nGraphical solution...")
        io.plot(r, L, W, l, w, coords, items, direc_rep, float(model.objective_value))

    # Statistics text output
    else:
        print("Writting in text file statistics...")
        io.appendStatistics(algorithm, problem, stages, rotation, variant, instance_name, model, h, totalT, n, L, W, l, w, d, items, direc_rep, plot, id)

    tt = (totalT,)  # Convert totalT in a tuple

    new_vars = MILP_Variables()

    if cut_type is CutTypeEnum.GUILLOTINE:
        new_vars.set5arcsVariables(x, L_sub, W_sub, delta, ii, jj, z, qh, qv, beta)  # New variables object
    else:
        new_vars.set5arcsVariables(x, L_sub, W_sub, delta, ii, jj, z, qh, qv)  # New variables object (beta is only to guillotine cut type)

    # Tuple containing 4 values
    return tt + utils.analyseSolution(model, L, W, l, w, d, items, direc_rep, rotation) + (new_vars,)
