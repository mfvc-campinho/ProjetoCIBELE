### Imports ###
from mip import *  # Enable Python-MIP in your Python code
from numpy import *

import floating_cuts_4_arcs_functions as fc4f
import packing_io as io
import packing_utils as utils
from floating_cuts_enums import (AlgorithmEnum, ProblemEnum,
                                 RelativePositionEnum, VariantEnum)
from milp_utils import MILP_Variables

###############################################################################

# Method to generate the Floating Cuts (model 4 arcs) for packing problems


def FloatingCuts(previous_model=MILP_Variables(), instance_name='cgcut1.txt',
                 database_type='distributor', database_name='', h=4,
                 algorithm=AlgorithmEnum.ARCS4, problem=ProblemEnum.SKP,
                 stages=Infinity, rotation=False,
                 variant=VariantEnum.UNWEIGHTED, max_time=3600,
                 plot=False, weight=0, test_constraint=0, test_type='simple',
                 output_name="", reload=False):
    dir_name = 'dat/' + database_type + "/" + database_name

    # Read input file
    if database_type == 'distributor' or \
            database_type == 'instances_constraints' or \
            database_type == 'preliminary_tests':
        n, L, W, l, w, d, v = io.readDistributorInstance(
            dir_name, instance_name, problem, variant)
        id = instance_name  # They are the same here
    else:
        id, n, L, W, l, w, d, v = io.readManufacturerInstance(
            dir_name, instance_name)

    # Constants
    m = fc4f.M(h)  # Height of the tree
    # Big M used for the model when addressing rotation
    max_constant = utils.maxDimension(L, W)

    # Debug
    print(f"\n### Debug ###")
    print(f"• max_constant: {max_constant}")
    print(f"• All possible subrectangles (m): {m}")
    print(f"• Number of different item types (n): {n}")
    print(f"• Length of the large object (L): {L}")
    print(f"• Width of the large object (W): {W}")

    print(f'\nThe item types are characterized by a length(li), a width(wi), a value(vi), and a maximum demand(di).')
    for t in range(n):
        print(f"\tl: {l[t]} | w: {w[t]} | d: {d[t]} | v: {v[t]}")

    # Create MILP Model
    # class Model(name='', sense='MIN', solver_name='', solver=None)
    # sense = MAXIMIZE / MINIMIZE
    model = Model(sense=MAXIMIZE, solver_name=GRB,
                  name=problem.name+"-floating-cuts-4-arcs")

    # ---------------------------------[PARAMETERS]-----------------------------
    # Rotation case
    if rotation == True:
        # With rotation we duplicate the items to mimic rotation
        ii = [i for i in range(2 * n)]

        # Duplicating items
        l_copy = utils.copy.deepcopy(l)
        w_copy = utils.copy.deepcopy(w)

        l.extend(w_copy)
        w.extend(l_copy)
        v.extend(utils.copy.deepcopy(v))
        d.extend(utils.copy.deepcopy(d))
        # print(m, n, L, W, l, w, d, v)

    else:
        # Set of n item types indexed by i, i = 1, ..., n
        ii = [i for i in range(n)]

    # Set of m of all possible sub-rectangles j, j = 1, ..., m
    jj = [j for j in range(m)]

    # Number of items of type i placed side by side (horizontally)
    # in sub-rectangle j
    qh = []

    # Number of items of type i placed on the top of each other (vertically)
    # in sub-rectangle j
    qv = []

    # ------------------------------[BASIC VARIABLES]--------------------------
    # Domain of the decision variables
    #
    # class Var(model, idx)
    # Decision variable of the Model .
    # The creation of variables is performed calling the add_var() .
    #
    # add_var(name='', lb=0.0, ub=inf, obj=0.0, var_type='C', column=None)
    #
    # Parameters:
    # • name (str) – variable name (optional)
    # • lb (numbers.Real) – variable lower bound, default 0.0
    # • ub (numbers.Real) – variable upper bound, default infinity
    # • obj (numbers.Real) – coefficient of this variable in the objective
    # function, default 0
    # • var_type (str ) – CONTINUOUS (“C”), BINARY (“B”) or INTEGER (“I”)
    # • column (mip.Column) – constraints where this variable will appear,
    # necessary only when constraints are already created in the model and a
    # new variable will be created.

    # If sub-rectangle j is cut vertically, xj = 1, otherwise, xj = 0
    x = [model.add_var('x[%i]' % j, var_type=BINARY) for j in jj]

    # If sub-rectangle j is cut horizontally, yj = 1, otherwise, yj = 0
    y = [model.add_var('y[%i]' % j, var_type=BINARY) for j in jj]

    r = model.add_var('r', var_type=BINARY)

    # Lenght of sub-rectangle j
    L_sub = [model.add_var('L_sub[%i]' % j, var_type=INTEGER,
                           lb=0, ub=max_constant) for j in jj]  # L

    # Width of sub-rectangle j
    W_sub = [model.add_var('W_sub[%i]' % j, var_type=INTEGER,
                           lb=0, ub=max_constant) for j in jj]  # W

    # If item i is assigned to sub-rectangle j
    delta = [[model.add_var('delta[%i][%i]' % (i, j), var_type=BINARY)
              for j in jj] for i in ii]

    # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
    if test_constraint == 1:
        # ∆[i] = 1, if item i is cut from the cutting pattern or
        # ∆[i] = 0, otherwise;
        # i = 1, ..., n
        deltaI = [model.add_var('deltaI[%i]' % i, var_type=BINARY) for i in ii]

    # Test Constraint 2 - Number of Stages in the Cutting Pattern
    if test_constraint == 2:
        # Total Number of Cutting Stages in the Cutting Pattern
        phi = model.add_var('phi', var_type=INTEGER)

        # stages_plus[j] = 1, if there is additional stage,
        # or stages_plus[j] = 0, otherwise;
        # j = 0, ..., m
        stages_plus = [model.add_var(
            'stages_plus[%i]' % j, var_type=BINARY) for j in jj]

        # aux_t[i][j] = 1, if items are stacked vertically
        # or aux_t[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        aux_t = [[model.add_var('aux_t[%i][%i]' % (i, j),
                                var_type=BINARY) for j in jj] for i in ii]

        # aux_s[i][j] = 1, if items are stacked horizontally
        # or aux_s[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        aux_s = [[model.add_var('aux_s[%i][%i]' % (i, j),
                                var_type=BINARY) for j in jj] for i in ii]

        # slack_h[i][j] = 1, if an extra horizontal cut is necessary to separate the item from the waste
        # or slack_h[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        waste_h = [[model.add_var('slack_h[%i][%i]' % (i, j),
                                  var_type=BINARY) for j in jj] for i in ii]

        # slack_v[i][j] = 1, if an extra vertical cut is necessary to separate the item from the waste
        # or slack_v[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        waste_v = [[model.add_var('slack_v[%i][%i]' % (i, j),
                                  var_type=BINARY) for j in jj] for i in ii]

        # APAGAR SE DER CERTO AS NOVAS VARIÁVEIS ACIMA!
        # slack_v[i][j] = 1, if an extra vertical cut is necessary to separate the item from the waste
        # or slack_v[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        # slack_v = [[model.add_var('slack_v[%i][%i]' % (i, j),
        #                           var_type=BINARY) for j in jj] for i in ii]

        # max_v = [[model.add_var('max_v[%i][%i]' % (i, j),
        #                         var_type=INTEGER) for j in jj] for i in ii]

        # max_h = [[model.add_var('max_h[%i][%i]' % (i, j),
        #                         var_type=INTEGER) for j in jj] for i in ii]

    # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
    if test_constraint == 3:
        # ∆[i][j] = 1, if item i is in the strip j or
        # ∆ij = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        delta_barra = [[model.add_var('delta_barra[%i][%i]' % (i, j),
                                      var_type=BINARY) for j in jj] for i in ii]

        # σ[j] = 1, if subrectangle j is a strip or σ[j] = 0, otherwise;
        # j = 0, ..., m
        sigma = [model.add_var('sigma[%i]' % j, var_type=BINARY) for j in jj]

        max_delta_barra = model.add_var(
            'max_delta_barra', var_type=INTEGER)

    # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
    if test_constraint == 5:
        # Total number of cuts in a pattern
        beta = model.add_var('beta', var_type=INTEGER)

        max_v = [[model.add_var('max_v[%i][%i]' % (i, j),
                                var_type=INTEGER) for j in jj] for i in ii]

        max_h = [[model.add_var('max_h[%i][%i]' % (i, j),
                                var_type=INTEGER) for j in jj] for i in ii]

        # slack_v[i][j] = 1, if an extra vertical cut is necessary to separate the item from the waste
        # or slack_v[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        slack_v = [[model.add_var('slack_v[%i][%i]' % (i, j),
                                  var_type=BINARY) for j in jj] for i in ii]

        # slack_h[i][j] = 1, if an extra horizontal cut is necessary to separate the item from the waste
        # or slack_h[i][j] = 0, otherwise;
        # i = 1, ..., n; j = 0, ..., m
        slack_h = [[model.add_var('slack_h[%i][%i]' % (i, j),
                                  var_type=BINARY) for j in jj] for i in ii]

    """
    The Floating-Cuts model for the k-staged problem is based on the assumption
    that in a given rectangle, only three situations may occur:

        1- the rectangle is cut horizontally;
        2- the rectangle is cut vertically;
        3- or an item is assigned to the rectangle.

    If a rectangle is cut vertically, two new rectangles are obtained, i.e.,
    the left and the right sub-rectangles. The width of the new sub-rectangles
    is equal to the width of the rectangle/sub-rectangle of the previous level
    and the sum of the lengths of the left and right sub-rectangles is equal to
    the length of the rectangle/sub-rectangle of the previous level.

    Similarly, if a horizontal cut is performed, two new rectangles are
    obtained, i.e., the top and bottom sub-rectangles. Their dimensions can
    also be calculated considering the dimensions of the
    rectangle/sub-rectangle of the previous level.
    """

    ################### Index of the Item with Minimum Area ###################
    item_areas = [0] * len(ii)

    # Calculando as áreas dos itens e os desperdícios
    for i in range(len(ii)):

        # Calcula a área de cada item
        item_area = l[i] * w[i]
        item_areas[i] = item_area

    # Índice do item com a menor área
    k = item_areas.index(min(item_areas[i] for i in ii))

    ###########################################################################

###############################################################################

    # SLOPP
    if problem is ProblemEnum.SLOPP:
        # Integer
        qh = [[model.add_var(name='qh[%i][%i]' % (
            i, j), var_type=INTEGER, lb=0, ub=max(d)) for j in jj] for i in ii]
        qv = [[model.add_var(name='qv[%i][%i]' % (
            i, j), var_type=INTEGER, lb=0, ub=max(d)) for j in jj] for i in ii]
        z = [model.add_var(name='z[%i]' % j, var_type=BINARY) for j in jj]

    # -----------------------------[OBJECTIVE FUNCTION]------------------------
    if problem is ProblemEnum.SKP:
        model.objective = maximize(
            xsum([v[i] * delta[i][j] for i in ii for j in jj]))  # 1

    elif problem is ProblemEnum.SLOPP:
        if database_type == 'instances_constraints' or \
                database_type == 'preliminary_tests':
            # Objective Function without Complexity Constraints (#0)
            if test_constraint == 0:

                model += xsum([v[i] * (qh[i][j] + qv[i][j])
                               for i in ii for j in jj]) / (L * W), \
                    "objective_function_SLOPP_distributor"

            # Objective Function - Number of Different Item Types in the Cutting Pattern (#1)
            elif test_constraint == 1:

                model += (1 - weight) * \
                    (xsum([v[i] * (qh[i][j] + qv[i][j])
                           for i in ii for j in jj])) / (L * W) - \
                    weight * xsum(deltaI[i] for i in ii) * (1/n), \
                    "objective_function_with_complexity_#1_SLOPP_instances"

            # Objective Function - Number of Stages in the Cutting Pattern (#2)
            elif test_constraint == 2:

                model += (1 - weight) * \
                    (xsum([v[i] * (qh[i][j] + qv[i][j])
                           for i in ii for j in jj])) / (L * W) - \
                    weight * (phi * (l[k] * w[k])) / (2 * (L * W)), \
                    "objective_function_with_complexity_#2_SLOPP_instances"

            # Objective Function - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern (#3)
            elif test_constraint == 3:

                model += (1 - weight) * \
                    (xsum([v[i] * (qh[i][j] + qv[i][j])
                          for i in ii for j in jj])) / (L * W) - \
                    weight * max_delta_barra * (1/n), \
                    "objective_function_with_complexity_#3_SLOPP_instances"

            # Objective Function - Total Number of Cuts in the Cutting Pattern (#5)
            elif test_constraint == 5:

                model += (1 - weight) * \
                    (xsum([v[i] * (qh[i][j] + qv[i][j])
                          for i in ii for j in jj])) / (L * W) - \
                    weight * (beta * (l[k] * w[k])) / (L * W), \
                    "objective_function_with_complexity_#5_SLOPP_instances"

        elif database_type == 'distributor':
            model += xsum([v[i] * (qh[i][j] + qv[i][j])
                           for i in ii for j in jj]), \
                "objective_function_SLOPP_distributor"
        else:
            model += xsum([(qh[i][j] + qv[i][j])
                           for i in ii for j in jj]), \
                "objective_function_SLOPP_manufacturer"

    else:
        print("Undefined problem!")
        exit()

    # ---------------------------[BASIC CONSTRAINTS]---------------------------
    # SKP
    if problem is ProblemEnum.SKP:
        for j in jj:
            # Constraints ensures that a sub-rectangle j can be cut vertically
            # or horizontally or an item is assigned to it.
            model += x[j] + y[j] + xsum([delta[i][j] for i in ii]) <= 1, \
                f"only_one_type{j}"  # 2

            # -> Troca qh e qv por delta?
            model += xsum(l[i] * delta[i][j]
                          for i in ii) <= L_sub[j], f"length_L_{j}"  # 3
            model += xsum(w[i] * delta[i][j]
                          for i in ii) <= W_sub[j], f"width_W_{j}"  # 4

        if rotation == True:
            for i in range(n):
                model += xsum(delta[i][j] + delta[n + i][j]
                              for j in jj) <= 1, f"upper_delta_{i}"  # 5
        else:
            for i in ii:
                model += xsum(delta[i][j]
                              for j in jj) <= 1, f"upper_delta_{i}"  # 5

    # SLOPP
    elif problem is ProblemEnum.SLOPP:
        for j in jj:
            model += x[j] + y[j] + xsum([delta[i][j] for i in ii]) <= 1, \
                f"only_one_type{j}"  # 40

        # Demand when considering rotation
        if rotation == True:
            for i in range(n):
                model += xsum(qh[i][j] + qh[n + i][j] +
                              qv[i][j] + qv[n + i][j]
                              for j in jj) <= d[i],
                f"rotation_demand_{i}"  # 41
        else:
            for i in ii:
                model += xsum(qh[i][j] + qv[i][j]
                              for j in jj) <= d[i], f"demand_{i}"  # 41

        for i in ii:
            for j in jj:
                # Constraints are used to connect decision variables qh, qv
                # and delta.
                model += qh[i][j] <= d[i] * delta[i][j], \
                    f"demand_qh_42_{i}_{j}"
                model += qv[i][j] <= d[i] * delta[i][j], \
                    f"demand_qv_43_{i}_{j}"

                model += l[i] * qh[i][j] <= L_sub[j], \
                    f"length_44_{i}_{j}"
                model += w[i] * qv[i][j] <= W_sub[j], \
                    f"width_45_{i}_{j}"

                # Constraints ensure that at least one item fits in
                # sub-rectangle j.
                model += l[i] * delta[i][j] <= L_sub[j] + max_constant * \
                    (1 - delta[i][j]), f"length_46_{i}_{j}"  # L
                model += w[i] * delta[i][j] <= W_sub[j] + max_constant * \
                    (1 - delta[i][j]), f"width_47_{i}_{j}"  # W

                # Constraints ensure that for a given sub-rectangle j only the
                # assignment of items grouped horizontally or vertically is
                # allowed.
                model += qh[i][j] <= d[i] * z[j], f"z_48_{i}_{j}"
                model += qv[i][j] <= d[i] * (1 - z[j]), f"z_49_{i}_{j}"

    # -----------------------[VERTICAL CUTS CONSTRAINTS]-----------------------
    # Constraints (46) - (53) are associated with vertical cuts performed in
    # the parent sub-rectangles.
    for j in range(fc4f.M(h - 1)):
        # Constraints (46) and (47) ensure that when a vertical cut is
        # performed, the sum of the lengths of the resulting left and right
        # sub-rectangles is equal to the length of the parent sub-rectangle.
        model += L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] <= max_constant * \
            (1 - x[j]) + L_sub[j], f"vertical_8_{j}"  # L
        model += L_sub[fc4f.left(j)] + L_sub[fc4f.right(j)] >= L_sub[j] - \
            max_constant * (1 - x[j]), f"vertical_9_{j}"  # L

        # Constraints ensure that the length of the left and right
        # sub-rectangles are set to zero, respectively, if a vertical cut is
        # not performed on the parent subrectangle (xj = 0).
        model += L_sub[fc4f.left(j)] + \
            L_sub[fc4f.right(j)] <= max_constant * x[j], \
            f"vertical_10_{j}"  # L

        # Constraints (49) - (52) ensure that when a vertical cut is performed,
        # the width of the resulting left and right sub-rectangles is equal to
        # the width of the parent sub-rectangle.
        model += W_sub[fc4f.left(j)] <= max_constant * \
            (1 - x[j]) + W_sub[j], f"vertical_11_{j}"  # W
        model += W_sub[fc4f.left(j)] >= max_constant * \
            (x[j] - 1) + W_sub[j], f"vertical_12_{j}"  # W
        model += W_sub[fc4f.right(j)] <= max_constant * \
            (1 - x[j]) + W_sub[j], f"vertical_13_{j}"  # W
        model += W_sub[fc4f.right(j)] >= max_constant * \
            (x[j] - 1) + W_sub[j], f"vertical_14_{j}"  # W

        # Constraints ensure that the width of the left and right
        # sub-rectangles are set to zero, respectively, if a vertical cut is
        # not performed on the parent subrectangle (xj = 0).
        model += W_sub[fc4f.left(j)] + W_sub[fc4f.right(j)] <= 2 * \
            max_constant * x[j], f"vertical_15_{j}"  # W

    # ----------------------[HORIZONTAL CUTS CONSTRAINTS]----------------------
    # Constraints (54) - (61) are related to horizontal cuts performed in the
    # parent sub-rectangle.
    for j in range(fc4f.M(h-1)):
        # Constraints (54) and (55) ensure that if a horizontal cut is
        # performed in the parent sub-rectangle, the sum of the width of the
        # resulting top and bottom sub-rectangles is equal to the width of the
        # parent sub-rectangle.
        model += W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] <= max_constant * \
            (1 - y[j]) + W_sub[j], f"vertical_16_{j}"  # W
        model += W_sub[fc4f.top(j)] + W_sub[fc4f.bottom(j)] >= W_sub[j] - \
            max_constant * (1 - y[j]), f"vertical_17_{j}"  # W

        # Constraints ensure that if a horizontal cut is not performed (yj = 0)
        # in the parent sub-rectangle, the width of the top and bottom
        # sub-rectangles are set to zero, respectively.
        model += W_sub[fc4f.top(j)] + \
            W_sub[fc4f.bottom(j)] <= max_constant * y[j], \
            f"vertical_18_{j}"  # W

        # Constraints (57) - (60) guarantee that the length of the resulting
        # top and bottom subrectangles is equal to the length of the parent
        # sub-rectangle.
        model += L_sub[fc4f.top(j)] <= max_constant * \
            (1 - y[j]) + L_sub[j], f"vertical_19_{j}"  # L
        model += L_sub[fc4f.top(j)] >= max_constant * \
            (y[j] - 1) + L_sub[j], f"vertical_20_{j}"  # L
        model += L_sub[fc4f.bottom(j)] <= max_constant * \
            (1 - y[j]) + L_sub[j], f"vertical_21_{j}"  # L
        model += L_sub[fc4f.bottom(j)] >= max_constant * \
            (y[j] - 1) + L_sub[j], f"vertical_22_{j}"  # L

        # Constraints ensure that if a horizontal cut is not performed (yj = 0)
        # in the parent sub-rectangle, the length of the top and bottom
        # sub-rectangles are set to zero, respectively.
        model += L_sub[fc4f.top(j)] + L_sub[fc4f.bottom(j)] <= 2 * \
            max_constant * y[j], f"vertical_23_{j}"  # L

    # ----------------------------[STAGES LIMIT]----------------------------
    model += y[0] == 1, f"initial_cut_horizontal_y0"

    if stages != Infinity:
        # Stages from 0 up to M(h-1)
        for j in range(fc4f.M(h - 1)):
            if fc4f.stages(j) > stages:
                model += x[j] + y[j] + xsum([delta[i][j]
                                            for i in ii]) <= 0, \
                    f"stage_0_to_h_minus_1_{j}"

        # Stages from M(h-1) up to M(h)
        for j in range(fc4f.M(h-1), fc4f.M(h)):
            if fc4f.stages(j) >= stages:
                model += xsum([delta[i][j]
                              for i in ii]) <= 0, f"stage_h_minus_1_to_h_{j}"

        # Special Case
        # This current version for a limited number of stages works only with
        # the first cut in the horizontal direction, i.e., x[0] = 0,
        # allowing only a first cut horizontal (y[0] = 1) or an assignment
        # (delta[i][j] = 1).
        # Specially, this version included the first cut as horizontal (y[0]=1)
        model += y[0] == 1, f"initial_cut_horizontal_y0"

        # Grouping to avoid the 3rd stage:
        #   - If 1st horizontal, next ones can't be vertical;
        #   - If 1st vertical, next ones can't be horizontal.
        # SLOPP
        if problem is ProblemEnum.SLOPP:
            for i in ii:
                for j in range(fc4f.M(h-1)):
                    model += qv[i][j] <= d[i] * (1 - y[0])
                    model += qh[i][j] <= d[i] * (1 - x[0])

    # ----------------------------[ROTATION CASE]----------------------------
    if rotation == True:
        if h > 0:  # First level, if is the last one, we cannot require this
            # 36 -> Constraint forcing the first cut to be vertical
            model += x[0] == 1, f"x0_rot"
        model += L_sub[0] == W * r + L * (1 - r), f"L0_rot"  # 37
        model += W_sub[0] == L * r + W * (1 - r), f"W0_rot"  # 38
    else:
        model += r == 0, f"no_rotation"
        model += L_sub[0] == L, f"L0"  # 6
        model += W_sub[0] == W, f"W0"  # 7

    # --------------------------[MODEL STRENGTHENING]--------------------------
    # -------------------------[LAST LEVEL RECTANGELS]-------------------------
    # Ensure that the sub-rectangles of the last level cannot be further cut,
    # i.e., only items can be assigned to them.
    for j in range(fc4f.M(h - 1), fc4f.M(h)):
        model += x[j] + y[j] == 0, f"last_level_27_{j}"

    # ---------------------------[SYMMETRY REDUCTION]--------------------------
    # Constraints are used to reduce symmetry in the generation of
    # sub-rectangles by imposing that the left (top) subrectangle is larger
    # than the right (bottom) sub-rectangle when a vertical (horizontal)
    # cut is applied.
    for j in range(fc4f.M(h - 1)):
        model += L_sub[4 * j + 1] - L_sub[4 * j + 2] >= max_constant * \
            (x[j] - 1), f"symmetry_reduction_28_{j}"
        model += W_sub[4 * j + 3] - W_sub[4 * j + 4] >= max_constant * \
            (y[j] - 1), f"symmetry_reduction_29_{j}"

    # ----------------------------[AREA BOUND]----------------------------
    # Constraints  state that the total area of the rectangles cut does not
    # exceed the area of the initial rectangle.
    if problem is ProblemEnum.SKP:

        model += xsum(l[i] * w[i] * delta[i][j]
                      for i in ii for j in jj) <= L * W, f"area_bound_30"

    else:

        model += xsum(l[i] * w[i] * (qh[i][j] + qv[i][j])
                      for i in ii for j in jj) <= L * W, f"area_bound_30"

    # ------------------------[RELATION FATHER CHILDREN]-----------------------
    # Constraints ensure that if an item is allocated to a sub-rectangle j,
    # then j has no descendants.
    # Constraints ensure that if a sub-rectangle j is not cut,
    # then j has no descendants.
    # This condition prevents a rectangle from remaining “undecided”
    # (is neither cut nor has an item assigned to it)
    # along several levels of the tree.

    for j in range(fc4f.M(h - 2)):
        model += xsum(x[4 * j + k] + y[4 * j + k] +
                      xsum(delta[i][4 * j + k] for i in ii)
                      for k in range(1, 5)) <= 2 - 2 * \
            xsum(delta[i][j] for i in ii), f"relation_31_{j}"
        model += xsum(x[4 * j + k] + y[4 * j + k] +
                      xsum(delta[i][4 * j + k] for i in ii)
                      for k in range(1, 5)) <= 2 * (x[j] + y[j]), \
            f"relation_33_{j}"

    for j in range(fc4f.M(h - 2), fc4f.M(h - 1)):
        model += xsum(delta[i][4 * j + k] for k in range(1, 5)
                      for i in ii) <= 2 - 2 * xsum(delta[i][j] for i in ii), \
            f"relation_32_{j}"
        model += xsum(delta[i][4 * j + k] for k in range(1, 5) for i in ii) \
            <= 2 * (x[j] + y[j]), f"relation_34_{j}"

    # -------------------[COMPLEXITY OF THE CUTTING PATTERNS]------------------
    # Test Constraint 0 - Objective Function without Complexity Constraints
    if test_constraint == 0:
        # Normalization Factor
        norm_factor = "-"

    # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
    if test_constraint == 1:

        # Normalization Factor
        norm_factor = 1/n

        for i in ii:
            for j in jj:
                model += deltaI[i] >= delta[i][j]

    # Test Constraint 2 - Number of Stages in the Cutting Pattern
    if test_constraint == 2:

        # Normalization Factor
        norm_factor = (l[k] * w[k]) / (2 * (L * W))

        # NOVAS RESTRIÇÕES - OVERLEAF ELSA
        for i in ii:
            for j in jj:
                # aux_t[i][j]
                model += aux_t[i][j] <= qv[i][j]
                model += d[i] * aux_t[i][j] >= qv[i][j]

                # aux_s[i][j]
                model += aux_s[i][j] <= qh[i][j]
                model += d[i] * aux_s[i][j] >= qh[i][j]

                # slack_h[i][j]
                model += waste_h[i][j] <= L_sub[j] - \
                    aux_t[i][j] * l[i] - qh[i][j] * l[i]
                model += L * waste_h[i][j] >= L_sub[j] - aux_t[i][j] * \
                    l[i] - qh[i][j] * l[i] - L * (1 - delta[i][j])
                model += waste_h[i][j] <= delta[i][j]

                # slack_v[i][j]
                model += waste_v[i][j] <= W_sub[j] - \
                    aux_s[i][j] * w[i] - qv[i][j] * w[i]
                model += W * waste_v[i][j] >= W_sub[j] - aux_s[i][j] * \
                    w[i] - qv[i][j] * w[i] - W * (1 - delta[i][j])
                model += waste_v[i][j] <= delta[i][j]

        for j in jj:
            if j > 0:
                # stage_plus[j]
                model += stages_plus[j] <= xsum([delta[i][j] for i in ii])
                model += stages_plus[j] >= xsum([waste_h[i][j]
                                                for i in ii]) - (1 - y[fc4f.father(j)])
                model += stages_plus[j] >= xsum([qh[i][j] / d[i]
                                                for i in ii]) - (1 - y[fc4f.father(j)])

                model += stages_plus[j] >= xsum([waste_v[i][j]
                                                for i in ii]) - (1 - x[fc4f.father(j)])
                model += stages_plus[j] >= xsum([qv[i][j] / d[i]
                                                for i in ii]) - (1 - x[fc4f.father(j)])

            model += phi >= (fc4f.stages(j) *
                             xsum(delta[i][j] for i in ii)) + stages_plus[j]

    # RESTRIÇÕES ANTIGAS!!!
        # for i in ii:
        #     for j in jj:
        #         # max_v[i][j] | max_h[i][j]
        #         model += max_v[i][j] >= qv[i][j]
        #         model += max_h[i][j] >= qh[i][j]

        #         # slack_v[i][j]
        #         model += slack_v[i][j] <= W_sub[j] - \
        #             max_v[i][j] * w[i] + (1 - delta[i][j])
        #         model += slack_v[i][j] >= (W_sub[j] - max_v[i][j] * w[i]) / W
        #         model += slack_v[i][j] >= 1 - delta[i][j]

        #         # # slack_h[i][j]
        #         model += slack_h[i][j] <= L_sub[j] - \
        #             max_h[i][j] * l[i] + (1 - delta[i][j])
        #         model += slack_h[i][j] >= (L_sub[j] - max_h[i][j] * l[i]) / L
        #         model += slack_h[i][j] >= 1 - delta[i][j]

        #         if j > 0:
        #             model += stages_plus[j] >= slack_v[i][j] - \
        #                 (1 - x[fc4f.father(j)])
        #             model += stages_plus[j] >= slack_h[i][j] - \
        #                 (1 - y[fc4f.father(j)])

        # for j in jj:
        #     model += stages_plus[j] <= xsum([delta[i][j] for i in ii])

        #     if j > 0:
        #         # model += stages_plus[j] >= xsum([slack_v[i][j]
        #         #                                 for i in ii]) - (1 - x[fc4f.father(j)])
        #         # model += stages_plus[j] >= xsum([slack_h[i][j]
        #         #                                 for i in ii]) - (1 - y[fc4f.father(j)])

        #         model += stages_plus[j] >= xsum([qv[i][j] -
        #                                         1 for i in ii])/n - (1 - x[fc4f.father(j)])
        #         model += stages_plus[j] >= xsum([qh[i][j] -
        #                                         1 for i in ii])/n - (1 - y[fc4f.father(j)])

        #         model += phi >= (fc4f.stages(j) *
        #                          xsum(delta[i][j] for i in ii)) + stages_plus[j]

        # Restrição Antiga - Roda OK!
        # for i in ii:
        #     for j in jj:
        #         model += phi >= fc4f.stages(j) * delta[i][j]

    # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
    if test_constraint == 3:

        # Normalization Factor
        norm_factor = 1/n

        # Minimum dimension of the items types
        dim_min = min(min(l), min(w))

        # None of the dimensions of a resulting subretangle is null
        model += L_sub[fc4f.left(j)] >= x[j] * dim_min
        model += L_sub[fc4f.right(j)] >= x[j] * dim_min
        model += W_sub[fc4f.top(j)] >= y[j] * dim_min
        model += W_sub[fc4f.bottom(j)] >= y[j] * dim_min

        # List to store descendants for each subrectangle j
        descendants_list = [[] for j in jj]
        descendants_list_level = [[] for j in jj]

        for j in jj:
            descendants = []
            descendants.append(j)
            descendants_list[j].extend(descendants)
            for level in range(h):
                current_descendants = []
                for descendant in descendants:
                    current_descendants.append(fc4f.left(descendant))
                    current_descendants.append(fc4f.right(descendant))
                    current_descendants.append(fc4f.top(descendant))
                    current_descendants.append(fc4f.bottom(descendant))
                descendants = [
                    descendant for descendant in current_descendants
                    if descendant < m]
                descendants_list_level[j].extend(descendants)
            descendants_list[j].extend(descendants_list_level[j])

        # Evaluation if a subrectangle is a strip - sigma[j]
        for j in jj:
            # 1st  Constraint
            model += sigma[j] >= - L * (L - L_sub[j]) + \
                (x[j] - y[j] + xsum([delta[i][j] for i in ii]))

            # 2nd  Constraint
            model += sigma[j] <= x[j] + xsum([delta[i][j] for i in ii])

            # 3rd Constraint
            model += sigma[j] <= 1 - y[j]

            # 4th Constraint
            model += sigma[j] <= 1 - (L - L_sub[j])/L

        # Evaluation if an item is in a subrectangle that
        # is / or belongs to a strip (sigma[j] = 1.0...)
        for i in ii:
            for j in jj:
                # 1st  Constraint
                model += delta_barra[i][j] <= sigma[j]

                # 2nd Constraint
                for j_prime in descendants_list[j]:
                    model += delta_barra[i][j] >= \
                        delta[i][j_prime] - (1 - sigma[j])

        # Evaluation of the maximum value of delta_barra
        # per strip of the pattern
        for j in jj:
            model += max_delta_barra >= -L * \
                (1 - sigma[j]) + xsum([delta_barra[i][j] for i in ii])

    # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
    if test_constraint == 5:

        # Normalization Factor
        norm_factor = (l[k] * w[k]) / (2 * (L * W))

        model += beta == xsum(x[j] + y[j] + xsum(qh[i][j] + qv[i][j] + delta[i]
                              [j] - 1 + slack_h[i][j] - 1 + slack_v[i][j] for i in ii) for j in jj)

        # max_v[i][j] | max_h[i][j]
        for i in ii:
            for j in jj:
                model += max_v[i][j] >= qv[i][j]
                model += max_h[i][j] >= qh[i][j]

        for i in ii:
            for j in jj:

                # slack_v[i][j]
                model += slack_v[i][j] <= W_sub[j] - \
                    max_v[i][j] * w[i] + (1 - delta[i][j])
                model += slack_v[i][j] >= (W_sub[j] - max_v[i][j] * w[i]) / W
                model += slack_v[i][j] >= 1 - delta[i][j]

                # slack_h[i][j]
                model += slack_h[i][j] <= L_sub[j] - \
                    max_h[i][j] * l[i] + (1 - delta[i][j])
                model += slack_h[i][j] >= (L_sub[j] - max_h[i][j] * l[i]) / L
                model += slack_h[i][j] >= 1 - delta[i][j]

    ### Initialization with a initial solution ###
    # User defined
    # if problem is ProblemEnum.SKP:
    #    MILP_Variables.test4arcs(model, x, y, r, L_sub, W_sub, delta, ii, jj)
    # else:
    #    MILP_Variables.test4arcs(model, x, y, r, L_sub, W_sub, delta, ii, jj, z, qh, qv)
    # From the previous h level

    if previous_model.has_variables():
        if problem is ProblemEnum.SKP:
            previous_model.copy_from_previous_4arcsmodel(
                model, x, y, r, L_sub, W_sub, delta)
        else:
            previous_model.copy_from_previous_4arcsmodel(
                model, x, y, r, L_sub, W_sub, delta, z, qh, qv)

    # # Check the LP - Saving, Loading and Checking Model Properties
    #
    # Model method write()  can be used to save and load, respectively,
    # MIP models.Supported file formats for models are the LP file format,
    # which is more readable and suitable for debugging, and the MPS file
    # format, which is recommended for extended compatibility, since it is an
    # older and more widely adopted format. When calling the write() method,
    # the file name extension (.lp or .mps) is used to define the file format.
    # Therefore, to save a model m using the lp file format to the file
    # model.lp we can use:

    model.write(problem.name + '-floating-cuts-4-arcs.lp')

    # Timer
    tic = utils.time.perf_counter()

    # Solve
    # print("Solving...")
    try:
        model.optimize(max_seconds=max_time)
        # print("beta =", beta.x)

    # optimize(max_seconds=inf, max_nodes=1073741824, max_solutions=1073741824,
    # max_seconds_same_incumbent=inf, max_nodes_same_incumbent=1073741824,
    # relax=False)
    #
    # Optimizes current model, optionally specifying processing limits.
    #     Parameters
    # • max_seconds (numbers.Real ) – Maximum runtime in seconds (default: inf)
    #
    # Returns optimization status, which can be OPTIMAL(0), ERROR(-1),
    # INFEASIBLE(1), UNBOUNDED(2). When optimizing problems with integer
    # variables some additional cases may happen, FEASIBLE(3) for the case when
    # a feasible solution was found but optimality was not proved,
    # INT_INFEASIBLE(4) for the case when the lp relaxation is feasible but no
    # feasible integer solution exists and NO_SOLUTION_FOUND(5) for the case
    # when an integer solution was not found in the optimization.
    # Return type mip.OptimizationStatus
    #
    # The optimize() method returns the status (OptimizationStatus) of the
    # BC search:
    # - OPTIMAL if the search was concluded and the optimal solution was found;
    # - FEASIBLE if a feasible solution was found but there was no time to
    # prove whether this solution was optimal or not;
    # - NO_SOLUTION_FOUND if in the truncated search no solution was found;
    # - INFEASIBLE or INT_INFEASIBLE if no feasible solution exists for
    # the model;
    # - UNBOUNDED if there are missing constraints or
    # - ERROR if some error occurred during optimization.

    except MemoryError as error:
        print("Writting in text file the MemoryErrors...")
        status = "STACKOVERFLOW"
        io.appendError(algorithm, problem, stages, rotation,
                       variant, instance_name, status, h, plot)
        # Stack overflow delimits the maximum h used
        return 0.0, 0.0, 'OPTIMAL', MILP_Variables()

    # Timer
    toc = utils.time.perf_counter()
    totalT = toc - tic

    # Output
    print("Calculating path relative to each item...")
    paths, items, subrectangles = fc4f.getIndividualPaths(delta, L_sub, W_sub)

    print("\nCalculating items coordinates...")
    coords = fc4f.getCoordinatesFirstItem(paths, items, L, W, r)

    print("\nCalculating directions and possible repetitions...")
    direc_rep = io.calculateDirectionAndRepetitions(
        items, subrectangles, qv, qh)

    print("r.x", r.x)

    # Write the model solution
    io.writeFile(instance_name, model, totalT, h, rotation, stages,
                 algorithm, problem, variant, weight, L, W, l, w, v,
                 coords, items, direc_rep, test_constraint, m, n, norm_factor)

###############################################################################
    # Some variables (Complexity of the Cutting Patterns)...

    # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
    if test_constraint == 1:
        # item_types = set()

        # for i in range(len(coords)):
        #     for k in range(direc_rep[i][1]):
        #         item_type = items[i]
        #         item_types.add(item_type)

        # Rever!!! xsum(deltaI[i] for i in ii
        # num_item_types_pattern = len(item_types)

        # num_item_types_pattern = 0
        # for i in ii:
        #     num_item_types_pattern += deltaI[i].x

        num_item_types_pattern = round(sum(deltaI[i].x for i in ii))
        print("num_item_types_pattern = ", num_item_types_pattern)

    # Test Constraint 2 - Number of Stages in the Cutting Pattern
    def max_stages(ii, jj, delta, qh, qv):
        nS_set = []

        for j in jj:
            nS_j = 0
            for i in ii:
                if delta[i][j].x == 1:
                    nS_j = fc4f.stages(j)
                    if ((qh[i][j].x >= 1 and
                         (fc4f.relativePosition(j) is RelativePositionEnum.TOP or
                          fc4f.relativePosition(j) is RelativePositionEnum.BOTTOM))
                            or (qv[i][j].x >= 1 and
                                (fc4f.relativePosition(j) is RelativePositionEnum.LEFT or
                                 fc4f.relativePosition(j) is RelativePositionEnum.RIGHT))):
                        nS_j += 1
            nS_set.append(nS_j)

        # print("nS_set", nS_set)

        return max(nS_set)

    if test_constraint == 2:

        # Cálculos Adicionais
        num_stages_pattern = round(phi.x)
        print("phi = ", phi.x)
        print("num_stages_pattern (phi) = ", num_stages_pattern)

        # num_stages_pattern = max_stages(ii, jj, delta, qh, qv)

        # num_stages = model.var_by_name('phi').x
        # print("num_stages_pattern (phi) = ", model.var_by_name('phi').x)
        # var_by_name(name) - Searchers a variable by its name
        # Returns Variable or None if not found

    else:
        num_stages = stages

    # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
    if test_constraint == 3:

        # Cálculos Adicionais
        strips = []

        # Construção da lista strips:
        for j in range(len(sigma)):
            if sigma[j].x == 1.0:
                strips.append(j)

        # Soma dos tipos de itens em cada faixa:
        sum_item_types_strip = [0] * len(sigma)
        for j in range(len(sigma)):
            for i in ii:
                if sigma[j].x == 1.0 and delta_barra[i][j].x == 1.0:
                    sum_item_types_strip[j] += 1

        # max_delta_barra_model = max(sum_item_types_strip)
        # strip_max = sum_item_types_strip.index(max_delta_barra_model)

        strip_max = sum_item_types_strip.index(max(sum_item_types_strip))

        # strip_max = sum_item_types_strip.index(max_delta_barra.x)

        # Itens associados à faixa com mais tipos de itens:
        item_types_strip_max = []
        for i in ii:
            if delta_barra[i][strip_max].x == 1.0:
                item_types_strip_max.append(i)

        num_item_types_strip_pattern = round(max_delta_barra.x)
        print("max_delta_barra = ", max_delta_barra.x)
        print("num_item_types_strip_pattern (max_delta_barra) = ",
              num_item_types_strip_pattern)

    # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
    if test_constraint == 5:

        # Total Number of Cuts
        num_cuts_pattern = round(beta.x)
        print("beta = ", beta.x)
        print("num_cuts_pattern (beta) = ", num_cuts_pattern)

###############################################################################
    # Graphical Output
    if plot:
        print("\nGraphical solution...")

        # Test Constraint 0 - Objective Function without Complexity Constraints
        if test_constraint == 0:
            io.plot(algorithm, problem, stages, rotation, variant, h,
                    instance_name, totalT, r, L, W, l, w, coords, items,
                    direc_rep, model, test_constraint, test_type)

        # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
        if test_constraint == 1:
            io.plot(algorithm, problem, stages, rotation, variant, h,
                    instance_name, totalT, r, L, W, l, w, coords, items,
                    direc_rep, model, test_constraint, test_type, norm_factor,
                    weight, num_item_types_pattern, num_stages)

        # Test Constraint 2 - Number of Stages in the Cutting Pattern
        if test_constraint == 2:

            print(f'Valor de phi antes de chamar plot: {phi.x}')

            io.plot(algorithm, problem, stages, rotation, variant, h,
                    instance_name, totalT, r, L, W, l, w, coords, items,
                    direc_rep, model, test_constraint, test_type, norm_factor,
                    weight, num_stages_pattern=num_stages_pattern)

        # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
        if test_constraint == 3:
            io.plot(algorithm, problem, stages, rotation, variant, h,
                    instance_name, totalT, r, L, W, l, w, coords, items,
                    direc_rep, model, test_constraint, test_type, norm_factor,
                    weight, strips=strips, num_item_types_strip_pattern=num_item_types_strip_pattern, strip_max=strip_max,  item_types_strip_max=item_types_strip_max)

        # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
        if test_constraint == 5:

            print(f'Valor de beta antes de chamar plot: {beta.x}')

            io.plot(algorithm, problem, stages, rotation, variant, h,
                    instance_name, totalT, r, L, W, l, w, coords, items,
                    direc_rep, model, test_constraint, test_type, norm_factor,
                    weight, num_cuts_pattern=num_cuts_pattern)

    # Statistics text output
    if test_type == 'experiment' or test_type == 'experiment_T_W':

        print("Writting in text file statistics...")

        # Test Constraint 0 - Objective Function without Complexity Constraints
        if test_constraint == 0:
            io.appendStatistics(algorithm, problem, stages, rotation, variant,
                                instance_name, model, h, totalT, n, L, W, l, w, d,
                                items, direc_rep, output_name, id, weight, test_constraint, test_type, norm_factor)

        # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
        if test_constraint == 1:
            io.appendStatistics(algorithm, problem, stages, rotation, variant,
                                instance_name, model, h, totalT, n, L, W, l, w, d,
                                items, direc_rep, output_name, id, weight, test_constraint, test_type, norm_factor, num_item_types_pattern)

        # Test Constraint 2 - Number of Stages in the Cutting Pattern
        if test_constraint == 2:
            io.appendStatistics(algorithm, problem, stages, rotation, variant,
                                instance_name, model, h, totalT, n, L, W, l, w, d,
                                items, direc_rep, output_name, id, weight, test_constraint, test_type, norm_factor, phi.x)

        # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
        if test_constraint == 3:
            io.appendStatistics(algorithm, problem, stages, rotation, variant,
                                instance_name, model, h, totalT, n, L, W, l, w, d,
                                items, direc_rep, output_name, id, weight, test_constraint, test_type, norm_factor, max_delta_barra.x)

        # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
        if test_constraint == 5:
            io.appendStatistics(algorithm, problem, stages, rotation, variant,
                                instance_name, model, h, totalT, n, L, W, l, w, d,
                                items, direc_rep, output_name, id, weight, test_constraint, test_type, norm_factor, beta.x)

    tt = (totalT,)  # Convert totalT in a tuple

    # New variables object
    new_vars = MILP_Variables()
    if problem is ProblemEnum.SKP:
        new_vars.set4arcsVariables(
            x, y, r, L_sub, W_sub, delta, ii, jj)
    else:
        new_vars.set4arcsVariables(
            x, y, r, L_sub, W_sub, delta, ii, jj, z, qh, qv)

    # Tuple containing 4 values
    return tt + utils.analyseSolution(model, L, W, l, w, d,
                                      items, direc_rep, rotation) + (new_vars,)
