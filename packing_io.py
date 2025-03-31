# Imports
import os  # 3
import random
import re  # 4
import smtplib  # 2
from datetime import datetime
from email.message import EmailMessage  # 8

import matplotlib
import matplotlib.pyplot as plt  # 1
from matplotlib.patches import Rectangle  # 5
from numpy import *  # 6

import packing_utils as utils
from floating_cuts_enums import (AlgorithmEnum, DirectionEnum,  # 7
                                 ProblemEnum, VariantEnum)

"""
# 1 - Library used for creating charts and visualizations
# 2 - Provides an interface for sending emails via the
        Simple Mail Transfer Protocol (SMTP)
# 3 - Module allows interaction with the operating system,
        including file and directory operations
# 4 - Module provides support for regular expressions,
        used for searching and manipulating strings with specific patterns
# 5 - Class used to create rectangles in charts
# 6 - Infinite value
# 7 - Imports all enumerated classes from the module
# 8 - Class used for constructing email messages
"""

###############################################################################

# Functions

# Create dir, if it does not exists
"""
The checkDir() function is used to ensure that the directory exists before
writing or reading files in it, thereby preventing "directory not found" errors
"""


def checkDir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

###############################################################################
# Create the data for the example


def create_data_model():

    # Creates an empty dictionary where the model information will be stored
    data = {}

    # List with the weights of the items to be packed
    weights = [48, 30, 42, 36, 36, 48, 42, 42, 36, 24, 30, 30, 42, 36, 36]
    data['weights'] = weights

    # List with the values of the items to be packed
    values = [10, 30, 25, 50, 35, 30, 15, 40, 30, 35, 45, 10, 20, 30, 25]
    data['values'] = values

    # This list represents the indices of the items
    data['items'] = list(range(len(weights)))
    data['num_items'] = len(weights)

    # This list represents the indices of the rectangular boards
    num_bins = 5
    data['bins'] = list(range(num_bins))
    data['bin_capacities'] = [100, 100, 100, 100, 100]
    return data

###############################################################################

# Read Distributor instance


def readDistributorInstance(dir, inst, problem, variant):
    n = 0  # Number of different item types
    L = 0  # Length of the rectangular plate
    W = 0  # Width of the rectangular plate
    l = []  # Length of the rectangular item
    w = []  # Width of the rectangular item
    d = []  # Maximum demand of each item type
    v = []  # Value of each item type

    if dir == '':
        dir = '.'

    # Regex
    regex = 'ngcut[0-9]+.txt|cgcut[0-9]+.txt'
    # SPECIAL CASE: Check the explanation just below
    pattern = re.compile(regex)
    increment_n = 0  # For the special case too

    with open(dir + "/" + inst, 'r') as file:
        # Knapsack Dimensions
        lin = file.readline().split()
        L = int(lin[0])
        W = int(lin[1])

        # Number of items
        n = int(file.readline())
        for i in range(n):
            lin = file.readline().split()

            # Items length (l)
            l.append(int(lin[0]))

            # Items width (w)
            w.append(int(lin[1]))

            # Items demand (d)
            if problem is ProblemEnum.SKP:  # Single Knapsack Problem
                d.append(1)
            else:
                d.append(int(lin[2]))

            # Items profit

            # The value of each item is equal to its area
            if variant is VariantEnum.UNWEIGHTED:
                # v.append(int(lin[0]) * int(lin[1])])
                v.append(l[len(l) - 1] * w[len(w) - 1])

            # The value of each item is not necessarily equal to its area
            else:
                v.append(int(lin[3]))

            # SPECIAL CASE FOR SKP:
            # Beasley instances and cgcut1, cgcut2, and cgcut3 must be items
            # duplicated according to its demand
            if problem is ProblemEnum.SKP:
                # Checks if the file name provided in the variable 'inst'
                # matches any of the patterns defined by the
                # regular expression 'pattern'.
                if pattern.match(inst):
                    print(f"Special case! Modifying SKP instance {(i + 1)}...")
                    # One item has already been inserted
                    real_demand = int(lin[2]) - 1

                    for t in range(0, real_demand):
                        l.append(int(lin[0]))  # Items length (l)
                        w.append(int(lin[1]))  # Items width (w)
                        d.append(1)  # Items demand (d)

                        if variant is VariantEnum.UNWEIGHTED:  # Items profit
                            # v.append(int(lin[0]) * int(lin[1])])
                            v.append(l[len(l) - 1] * w[len(w) - 1])
                        else:
                            v.append(int(lin[3]))

                        # The item included represents a new item type
                        increment_n += 1

                # else:
                #    print(f"Item {(i+1)} from {inst} is not a SPECIAL CASE!")

        # Update the n with the number of instances added
        n += increment_n

    return n, L, W, l, w, d, v

###############################################################################

# Read Manufacturer instance


def readManufacturerInstance(dir, inst):
    name = ''
    n = 0  # Number of different item types
    L = 0  # Length of the rectangular plate
    W = 0  # Width of the rectangular plate
    l = []  # Length of the rectangular item
    w = []  # Width of the rectangular item
    d = []  # Maximum demand of each item type
    v = []  # Value of each item type

    if dir == '':
        dir = '.'

    # Instance   L       W       l   w   z
    #    1	    1000	1000	205	159	 30

    with open(dir + "/" + inst, 'r') as file:
        # Discard header
        file.readline()

        # Data
        lin = file.readline().split()

        # Number of different items
        n = 1

        # Instance name
        name = lin[0]

        # Knapsack Dimensions
        L = int(lin[1])
        W = int(lin[2])

        # Items length (l)
        l.append(int(lin[3]))

        # Items width (w)
        w.append(int(lin[4]))

        # Items demand (it is always an upper bound)
        d.append(utils.areaBound(L, W, l[0], w[0]))

        # Items value (v)
        v.append(l[0] * w[0])

    return name, n, L, W, l, w, d, v

###############################################################################


def writeString(filename, string):
    # Write the output

    checkDir('res')
    with open('res/' + filename + '.txt', 'w') as file:
        file.write(string)

###############################################################################


def writeFile(*args):
    # Write the output

    # Parameters
    instance = args[0]
    model = args[1]
    time = '{:6f}'.format(args[2])
    levels = args[3] + 1
    rotation = args[4]
    stages = args[5]
    algorithm = AlgorithmEnum(args[6]).name
    problem = ProblemEnum(args[7]).name
    variant = VariantEnum(args[8]).name
    weight = str(args[9])

    # ATTENTION:
    #   levels -> Algorithm consider h (level) starting in 0,
    #   but in theory, it represents the 1st level

    if model.objective_value is not None:
        of = float(model.objective_value)
    else:
        of = 0.0

    gap = '{0:.5f}'.format(model.gap)

    # If a truncated execution was performed, i.e., the solver stopped due to
    # the time limit, you can check this dual bound which is an estimate of the
    # quality of the solution found checking the gap property.

    # Vectors
    L = int(args[10])
    W = int(args[11])
    l = args[12]
    w = args[13]
    v = args[14]
    coords = args[15]
    items = args[16]
    direc_rep = args[17]
    test_constraint = args[18]
    m = args[19]
    n = args[20]

    if test_constraint != 0:
        norm_factor = round(args[21], 4)
    else:
        norm_factor = "-"

    checkDir('res')
    # with open('res/res-' + algorithm + "_" + problem + '_' + 'weight' +
    #           str(weight) + '_' + 'h' + str(levels) + '_' + 'test' +
    #           str(test_constraint) + '_' + str(stages) + '_' +
    #           ('R' if rotation else 'F') + '_' +
    #           variant + '_' + instance, 'w', encoding='utf-8') as file:

    with open('res/res-' + os.path.splitext(instance)[0] + '_' + 'T' +
              str(test_constraint) + '_' + 'W' + str(weight) + '.txt', 'w',
              encoding='utf-8') as file:
        file.write(f'##### General Information #####')
        file.write(f'\n• Algorithm:\t{algorithm}')
        file.write(f'\n• Problem:\t{problem}')
        file.write(f'\n• Weight of Complexity:\t{weight}')
        file.write(f'\n• Normalization Factor:\t{norm_factor}')
        file.write(f'\n• Stages:\t{stages}')
        file.write(f'\n• Rotation:\t{rotation}')
        file.write(f'\n• Variant:\t{variant}')
        file.write(f'\n• Levels in the tree (h):\t{levels}')
        file.write(f'\n• Instance:\t{instance}')
        file.write(f'\n• Objective Function used:\t{test_constraint}')
        file.write(f'\n• Solver:\t{model.solver_name}')
        # OPTIMAL / FEASIBLE / NO_SOLUTION_FOUND
        file.write(f'\n• Result of the optimization:\t{model.status.name}')
        file.write(f'\n• Objective function value (Z):\t{of}')
        file.write(f'\n• Gap:\t{gap}')
        file.write(f'\n• Instance solved in (seconds):\t{time}')

        file.write(f'\n\n## Calculated values ##')
        file.write(f'\n• All possible subrectangles (m): {m}')
        file.write(f'\n• Number of different item types (n): {n}')
        file.write(f'\n• Length of the large object (L0): {L}')
        file.write(f'\n• Width of the large object (W0): {W}')

        file.write(f'\n\n• Length of the item types: {l}')
        file.write(f'\n• Width of the item types: {w}')
        file.write(f'\n• Value of the item types: {v}')
        file.write(f'\n• Coords: {coords}')
        file.write(f'\n• Item types placed: {sorted(set(items))}')

        file.write(f'\n{direc_rep}')

        file.write(f'\n\n## Calculated variables ##')
        for var in model.vars:
            if var.x is not None and var.x > 0.5:
                file.write(f'\n{var} = {var.x}')

###############################################################################

# Append statistics in a text file


def appendStatistics(*args):
    # Parameters
    algorithm = AlgorithmEnum(args[0]).name
    problem = ProblemEnum(args[1]).name
    stages = args[2]
    rotation = args[3]
    variant = VariantEnum(args[4]).name
    instance = args[5].split('.')[0]
    model = args[6]

    status = model.status.name  # OPTIMAL / FEASIBLE / NO_SOLUTION_FOUND

    if model.objective_value is not None:
        of = float(model.objective_value)
    else:
        of = 0.0

    solver = model.solver_name
    gap = '{0:.5f}'.format(model.gap)  # .replace('.', ',')

    # Upper Bound (UB)
    if utils.math.isinf(model.gap):
        UB = Infinity
    else:
        UB = utils.math.ceil(of * (model.gap + 1))

    nvars = model.num_cols  # len(model.vars) or model.num_cols
    nconst = model.num_rows

    # Algorithm consider h starting in 0,
    # but in theory, it represents the 1st level
    h = args[7] + 1
    time = '{0:.2f}'.format(args[8])  # .replace('.', ',')

    n = args[9]  # Number of different item types
    L = args[10]  # Length of the rectangular plate
    W = args[11]  # Width of the rectangular plate
    l = args[12]  # Length of the rectangular item
    w = args[13]  # Width of the rectangular item
    d = args[14]  # Maximum demand of each item type
    items = args[15]
    direc_rep = args[16]

    tot_items = utils.getTotalItems(d, rotation)
    tot_pack = utils.getTotalPacked(direc_rep)

    output = args[17]
    id = args[18]

    weight = args[19]

    test_constraint = int(args[20])

    test_type = args[21]

    norm_factor = args[22]

    # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
    if test_constraint == 1:
        num_item_types_pattern = round(args[23])

    # Test Constraint 2 - Number of Stages in the Cutting Pattern
    if test_constraint == 2:
        num_stages_pattern = round(args[23])

    # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
    if test_constraint == 3:
        num_item_types_strip_pattern = round(args[23])

    # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
    if test_constraint == 5:
        num_cuts_pattern = round(args[23])

    # checkDir('res')
    # with open(
    #     'res/experiment-' + algorithm + "_" + problem + "_" + output + ".txt", 'a+'
    # ) as file:
    #     # The 'a+' option means that the file will be opened in append mode,
    #     # which allows writing new data to the end of the file without
    #     # overwriting the existing content.

    #     # Instance Z UB gap nvars nconst h n %ocup time solver tot_items tot_pack
    #     of_str = str(of).replace('.', ',')
    #     occup = '{:.2%}'.format(utils.calculateItemsArea(
    #         l, w, items, direc_rep) / (L * W)).replace('.', ',')

    #     file.write(f'{problem};{stages};{rotation};{variant};{instance};{status};{of_str};{UB};{gap};{nvars};{nconst};{h};{n};{occup};{time};{solver};{tot_items};{tot_pack};{id};{weight}\n')

    # Ensure the directory exists
    os.makedirs('res', exist_ok=True)

    file_path = f'res/experiment-{algorithm}_{problem}_{output}.txt'

    # Write headers if the file does not exist
    if not os.path.exists(file_path):

        if test_type == "experiment_T_W":
            with open(file_path, 'w') as file:
                headers = [
                    'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                    'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Weight', 'Status', 'Occupation (%)',
                    'Gap', 'N_Vars', 'N_Const', 'Time (s)', 'Complexity Indicator', 'Normalization Factor',
                ]
                file.write(';'.join(headers) + '\n')

        if test_type == "experiment":

            # Test Constraint 0 - Objective Function without Complexity Constraints
            if test_constraint == 0:

                with open(file_path, 'w') as file:
                    headers = [
                        'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                        'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Status', 'Occupation (%)',
                        'Gap', 'N_Vars', 'N_Const', 'Time (s)',
                    ]
                    file.write(';'.join(headers) + '\n')

            # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
            if test_constraint == 1:

                with open(file_path, 'w') as file:
                    headers = [
                        'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                        'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Weight', 'Status', 'Occupation (%)',
                        'Gap', 'N_Vars', 'N_Const', 'Time (s)', 'Number of Different Item Types in the Cutting Pattern', 'Normalization Factor',
                    ]
                    file.write(';'.join(headers) + '\n')

            # Test Constraint 2 - Number of Stages in the Cutting Pattern
            if test_constraint == 2:

                with open(file_path, 'w') as file:
                    headers = [
                        'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                        'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Weight', 'Status', 'Occupation (%)',
                        'Gap', 'N_Vars', 'N_Const', 'Time (s)', 'Number of Stages in the Cutting Pattern', 'Normalization Factor',
                    ]
                    file.write(';'.join(headers) + '\n')

            # Test Constraint 3 - Maximum of Different Item Types in a Strip of the Cutting Pattern
            if test_constraint == 3:

                with open(file_path, 'w') as file:
                    headers = [
                        'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                        'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Weight', 'Status', 'Occupation (%)',
                        'Gap', 'N_Vars', 'N_Const', 'Time (s)', 'Maximum of Different Item Types in a Strip of the Cutting Pattern', 'Normalization Factor',
                    ]
                    file.write(';'.join(headers) + '\n')

            # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
            if test_constraint == 5:

                with open(file_path, 'w') as file:
                    headers = [
                        'Instance', 'Algorithm', 'Problem', 'Variant', 'Rotation',
                        'Levels of the tree (h)', 'Number of Stages', 'Test Constraint', 'Weight', 'Status', 'Occupation (%)',
                        'Gap', 'N_Vars', 'N_Const', 'Time (s)', 'Total Number of Cuts in the Cutting Pattern', 'Normalization Factor',
                    ]
                    file.write(';'.join(headers) + '\n')

    # Test Constraint 0 - Objective function without complexity constraints
    if test_constraint == 0:

        # Append the statistics
        with open(file_path, 'a') as file:
            of_str = str(of)  # .replace('.', ',')
            occup = '{:.2%}'.format(utils.calculateItemsArea(
                l, w, items, direc_rep) / (L * W))  # .replace('.', ',')

            file.write(
                f'{instance};{algorithm};{problem};{variant};{rotation};{h};{stages};{test_constraint};-;{status};{occup};{gap};{nvars};{nconst};{time};-;{norm_factor}\n')

    # Test Constraint 1 - Number of Different Item Types in the Cutting Pattern
    if test_constraint == 1:

        # Append the statistics
        with open(file_path, 'a') as file:
            of_str = str(of)  # .replace('.', ',')
            occup = '{:.2%}'.format(utils.calculateItemsArea(
                l, w, items, direc_rep) / (L * W))  # .replace('.', ',')

            file.write(f'{instance};{algorithm};{problem};{variant};{rotation};{h};{stages};{test_constraint};{weight};{status};{occup};{gap};{nvars};{nconst};{time};{num_item_types_pattern};{norm_factor:.4f}\n')

    # Test Constraint 2 - Number of Stages in the Cutting Pattern
    if test_constraint == 2:

        # Append the statistics
        with open(file_path, 'a') as file:
            of_str = str(of)  # .replace('.', ',')
            occup = '{:.2%}'.format(utils.calculateItemsArea(
                l, w, items, direc_rep) / (L * W))  # .replace('.', ',')

            file.write(f'{instance};{algorithm};{problem};{variant};{rotation};{h};{stages};{test_constraint};{weight};{status};{occup};{gap};{nvars};{nconst};{time};{num_stages_pattern};{norm_factor:.4f}\n')

    # Test Constraint 3 - Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern
    if test_constraint == 3:

        # Append the statistics
        with open(file_path, 'a') as file:
            of_str = str(of)  # .replace('.', ',')
            occup = '{:.2%}'.format(utils.calculateItemsArea(
                l, w, items, direc_rep) / (L * W))  # .replace('.', ',')

            file.write(f'{instance};{algorithm};{problem};{variant};{rotation};{h};{stages};{test_constraint};{weight};{status};{occup};{gap};{nvars};{nconst};{time};{num_item_types_strip_pattern};{norm_factor:.4f}\n')

    # Test Constraint 5 - Total Number of Cuts in the Cutting Pattern
    if test_constraint == 5:

        # Append the statistics
        with open(file_path, 'a') as file:
            of_str = str(of)  # .replace('.', ',')
            occup = '{:.2%}'.format(utils.calculateItemsArea(
                l, w, items, direc_rep) / (L * W))  # .replace('.', ',')

            file.write(f'{instance};{algorithm};{problem};{variant};{rotation};{h};{stages};{test_constraint};{weight};{status};{occup};{gap};{nvars};{nconst};{time};{num_cuts_pattern};{norm_factor:.4f}\n')

###############################################################################

# Headers
# - 'Problem',
# - Number of Stages
# - Rotation
# - Variant
# - Instance
# - Model Status
# - of_str
# - UB
# - Gap
# - N_Vars
# - N_Const
# - h
# - n
# - Occupation
# - Time (s)
# - Solver
# - Total Items
# - Total Packed
# - ID
# - Weight


###############################################################################

# Append statistics in a text file


def appendError(*args):
    algorithm = AlgorithmEnum(args[0]).name
    problem = ProblemEnum(args[1]).name
    stages = args[2]
    rotation = args[3]
    variant = VariantEnum(args[4]).name
    instance = args[5].split('.')[0]
    status = args[6]
    # Algorithm consider h starting in 0,
    # but in theory, it represents the 1st level
    h = args[7] + 1
    output = args[8]

    checkDir('res')
    with open(
        'res/experiment-' + algorithm + "_" + output + ".txt", 'a+'
    ) as file:
        file.write(f'{problem};{stages};{rotation};{variant}; \
                   {status}_{instance};{status};{h}\n')

###############################################################################


# Read the file that represents a final solution


def readResult(file_path):
    value = {}
    with open(file_path, 'r') as file:
        # Algorithm
        lin = file.readline().split("\t")
        value['algorithm'] = AlgorithmEnum.ARCS4 if lin[1].strip(
        ).lower() == "arcs4" else AlgorithmEnum.ARCS5

        # Problem
        lin = file.readline().split("\t")
        value['problem'] = ProblemEnum.SKP if lin[1].strip(
        ).lower() == "skp" else ProblemEnum.SLOPP

        # Stages
        lin = file.readline().split("\t")
        value['stages'] = Infinity if lin[1].strip(
        ) == "inf" else int(lin[1].strip())

        # Rotation
        lin = file.readline().split("\t")
        value['rotation'] = False if lin[1].strip() == 'False' else True

        # Variant
        lin = file.readline().split("\t")
        value['variant'] = VariantEnum.UNWEIGHTED if lin[1].strip(
        ).upper() == "UNWEIGHTED" else VariantEnum.WEIGHTED

        # Levels in the tree (h)
        lin = file.readline().split("\t")
        value['levels'] = int(lin[1].strip())

        # Instance
        lin = file.readline().split("\t")
        value['instance'] = lin[1].strip()

        # Solver
        lin = file.readline().split("\t")
        value['solver'] = lin[1].strip()

        # Result of the optimization
        lin = file.readline().split("\t")
        value['result'] = lin[1].strip()

        # Objective function value (Z)
        lin = file.readline().split("\t")
        value['z'] = float(lin[1].strip())

        # Gap
        lin = file.readline().split("\t")
        value['gap'] = float(lin[1].strip())

        # Instance solved in (seconds)
        lin = file.readline().split("\t")
        value['time'] = float(lin[1].strip())

        # Calculated values
        file.readline()  # Jump this comment

        # L
        value['L'] = int(file.readline().strip())

        # W
        value['W'] = int(file.readline().strip())

        # l
        line = file.readline().strip()
        line = line.lstrip('[').rstrip(']')
        value['l'] = [int(x) for x in line.split(',')]

        # w
        line = file.readline().strip()
        line = line.lstrip('[').rstrip(']')
        value['w'] = [int(x) for x in line.split(',')]

        # coords
        line = file.readline().strip()
        line = line.lstrip('[').rstrip(']')

        # (15.0, 12.0), (5.0, 12.0), (5.0, 15.0)
        value['coords'] = [(float(x.split(',')[0]),
                            float(x.split(',')[1].strip())) for x in [
            a.strip().rstrip('),') for a in line.lstrip('(').split('(')]]

        # items
        line = file.readline().strip()
        line = line.lstrip('[').rstrip(']')
        value['items'] = [int(x) for x in line.split(',')]

        # direc_rep
        line = file.readline().strip()
        line = line.lstrip('[').rstrip(']')
        value['direc_rep'] = [(DirectionEnum(int(x.split(',')[0].split(' ')[1].rstrip('>'))), int(
            x.split(',')[1].strip())) for x in [a.strip().rstrip('),') for a in line.lstrip('(').split('(')]]

        # Calculated variables
        file.readline()  # Jump this comment
        lin = file.readline()

        while lin != '':
            lin = lin.split("=")
            value[lin[0].strip()] = lin[1].strip()
            lin = file.readline()

    return value

###############################################################################

# Simple Email Sender
# https://pythonguides.com/send-email-using-python/


def sendSimpleEmail(receiver=["matheus.f.campinho@inesctec.pt"],
                    subject='Experiment Status',
                    msg_body='The experiment has finished!'):
    # Connection Informations
    # Email address used to generate password
    sender = "tiago.silveira@unifal-mg.edu.br"
    password = 'qnxlaipybylnytad'  # the 16 code generated
    smtp_server = "smtp.gmail.com"  # for Gmail
    port = 465  # for starttls

    # Action
    msg = EmailMessage()
    msg['subject'] = subject
    msg['from'] = sender
    msg['to'] = receiver
    msg.set_content(msg_body)

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
            print("Email sent!")
    except:
        print('\nInternet does not work, but...')
        print(msg_body)

###############################################################################

# Calculate the repetitions side by side an item must be placed,
# in addition to its direction


def calculateDirectionAndRepetitions(items, subrectangles, qv=[], qh=[]):
    # (direction, repetitions)
    direc_rep = []
    for i in range(len(items)):
        # SKP
        if len(qv) == 0:
            direc_rep.append((DirectionEnum.HORIZONTAL, 1))

        # SLOPP
        else:
            # increment direction
            if qv[items[i]][subrectangles[i]].x > 0.5:
                direc_rep.append((DirectionEnum.VERTICAL,   int(
                    qv[items[i]][subrectangles[i]].x)))
            else:
                direc_rep.append((DirectionEnum.HORIZONTAL, int(
                    qh[items[i]][subrectangles[i]].x)))

    return direc_rep

###############################################################################


# Plot the knapsack and its items
# Usar backend que não exige interface gráfica para evitar erros do Tkinter
matplotlib.use("Agg")

# def plot(r, L, W, l, w, coords, items, direc_rep, Z, debug=False):
# def plot(algorithm, problem, stages, rotation, variant, h, instance_name,
#          totalT, r, L, W, l, w, coords, items, direc_rep, model,
#          test_constraint, *args, **kwargs):


def plot(algorithm, problem, stages, rotation, variant, h, instance_name,
         totalT, r, L, W, l, w, coords, items, direc_rep, model,
         test_constraint=None, test_type=None, norm_factor=None, weight=None, num_item_types_pattern=None,
         num_stages_pattern=None, strips=None, num_item_types_strip_pattern=None, strip_max=None,
         item_types_strip_max=None, num_cuts_pattern=None, debug=False):

    plt.close('all')  # Fecha todas as figuras abertas
    print(f"Figuras abertas: {len(plt.get_fignums())}")

    if test_type == "simple" or test_type == "experiment" or test_type == "experiment_T_W":

        # plot_folder_name = algorithm.name + '_' + problem.name + \
        #     '_' + datetime.now().strftime("%d.%m.%Y")  # dd.mm.YY

        # folder_path = os.path.join(
        #     os.path.dirname(os.path.abspath(__file__)), 'plots_res',
        #     plot_folder_name)

        folder_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'plots_res')

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    max_dim = 10.0  # Plot size (in general, a paper sheet has size 25.0)
    tikz_scale = 1.0 / (max(L, W) / max_dim)
    rectangles = []

    # Values based on rotation
    rotated = False if r.x <= 0.5 else True

    real_L = W if rotated else L
    real_W = L if rotated else W

    for i in range(len(items)):
        rectangles.append((l[items[i]], w[items[i]]))

    if debug:
        print(f"Rectangles sizes: {rectangles}")
        print(f"Rectangles FIRST position: {coords}")
        print(f"Bounding box: {real_L}, {real_W}")

    fig, ax = plt.subplots()
    # Box Dimension
    ax.plot([0, real_L], [0, real_W], color="none")

    # if test_type == "simple":
    #     if debug:
    #         print("Recovering coordinates...")
    #     else:
    #         print("\nTikz solution:")
    #         print("\\begin{tikzpicture}[scale = 1]")
    #         print(
    #             f"\\draw[fill=gray] (0,0) rectangle ({real_L * tikz_scale},\
    #                 {real_W * tikz_scale});")
    #         print("\\def \s {1};")

    # Modifiquei aqui também...
    # Criar um dicionário para mapear tipos de retângulos a cores aleatórias
    colors_by_type = {}
    item_types = set()

    for i in range(len(coords)):

        # Base Coordinates
        coord_x = coords[i][0]
        coord_y = coords[i][1]

        # for k in range(direc_rep[i][1]):
        #     # Rectangle
        #     ax.add_patch(Rectangle(
        #         (coord_x, coord_y), rectangles[i][0], rectangles[i][1],
        #         linewidth=1.5, facecolor="lightseagreen", edgecolor='black'))

        ### Modifiquei Aqui ###
        for k in range(direc_rep[i][1]):
            item_type = items[i]
            item_types.add(item_type)

            # Verificar se a cor para este tipo de item já foi gerada
            if item_type not in colors_by_type:
                # Gerar uma cor aleatória
                color = "#{:02x}{:02x}{:02x}".format(
                    random.randint(200, 255),
                    random.randint(200, 255),
                    random.randint(200, 255)
                )
                # Salvar a cor no dicionário
                colors_by_type[item_type] = color

            # Usar a cor correspondente ao tipo do item
            color = colors_by_type[item_type]

            # Adicionar o retângulo com a cor correspondente
            ax.add_patch(Rectangle(
                (coord_x, coord_y), rectangles[i][0], rectangles[i][1],
                linewidth=1.5, facecolor=color, edgecolor='black'))

            ###  Até aqui... ###

            # Tinha uma identação aqui
            """
            These rectangles visually represent the packed items in the box,
            where their coordinates indicate their positions in the figure,
            and their dimensions represent the sizes of the packed items.
            The result is a chart that illustrates the solution to the item
            packing problem in the box.
            """

            # Label
            # infs = f'{items[i]} ({l[items[i]]}x{w[items[i]]})'
            # centerx = coord_x + 0.5 * \
            #     rectangles[i][0] - \
            #     len(infs.center(l[items[i]])) / (real_L * 0.6)
            # centery = coord_y + 0.4 * rectangles[i][1]
            # plt.text(centerx, centery, infs)

            # Até aqui...

            ### Label - Modificação ###
            # Cálculo do centro x e y
            centerx = coord_x + 0.5 * rectangles[i][0]
            centery = coord_y + 0.5 * rectangles[i][1]

            # Rótulo para o número do item (centralizado no retângulo)
            item_label = f'{items[i]}'
            # Ajuste o fator 0.25 conforme necessário
            item_label_x = centerx - len(str(items[i])) * 0.5
            # Ajuste o fator 0.15 conforme necessário
            item_label_y = centery - 0.1 * rectangles[i][1]

            plt.text(item_label_x, item_label_y, item_label,
                     fontsize=10, fontdict={'weight': 'bold'})

            # Rótulo para as dimensões do item (abaixo do número do item e centralizado)
            dimensions_label = f'({l[items[i]]}x{w[items[i]]})'
            # Ajuste o fator 0.25 conforme necessário
            dimensions_label_x = centerx - len(dimensions_label) * 0.50
            # Ajuste o fator 0.2 conforme necessário
            dimensions_label_y = centery - 0.1 * rectangles[i][1]

            # Descomentar - Label das dimensões das peças no padrão!!!
            # plt.text(dimensions_label_x, dimensions_label_y,
            #          dimensions_label, fontsize=8, fontdict={'weight': 'bold'})

            ###  Até aqui... ###

            # Aqui tinha uma identação a mais até else: coor_y += w[items[i]]
            # if test_type == "simple":
            #     if debug:
            #         print(
            #             f"item {items[i]} \
            #                 l={l[items[i]]}, \
            #                     w={w[items[i]]} \
            #                         => x={coord_x}, \
            #                         y={coord_y}")
            #     else:
            #         print(
            #             f"\draw[fill=white, shift={{ ({coord_x * tikz_scale}, \
            #                 {coord_y * tikz_scale}) }}] (0,0) \
            #                     rectangle ({l[items[i]] * tikz_scale},\
            #                         {w[items[i]] * tikz_scale}) \
            #                             node[midway, scale = \s] \
            #                                     {{ {l[items[i]]} x {w[items[i]]} }};")

            if direc_rep[i][0] is DirectionEnum.HORIZONTAL:
                coord_x += l[items[i]]
            else:
                coord_y += w[items[i]]

        # Bin Representation
        ax.add_patch(Rectangle((0, 0), real_L, real_W, linewidth=2.5,
                               facecolor="none", edgecolor='black'))

        # if test_type == "simple":
        #     if not debug:
        #         print("\\end{tikzpicture}\n")

    # plt.axis('off')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    # Sets the colors of the markers on the x and y axes to white,
    # making them invisible.
    # This helps create a cleaner and more minimalist appearance.

    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')

    plt.xlabel("Length (" + f"{real_L}" + ")")
    plt.ylabel("Width (" + f"{real_W}" + ")")

    # titulo = 'Packing Density '\
    #     + '{:.2%}'.format(utils.calculateItemsArea(l, w, items, direc_rep) \
    #                       / (L * W)) + ' (' + str(real_L) + ' x ' + \
    #                         str(real_W) + ': ' + ('ROTATED' if rotated else \
    #                                               'NO ROTATED') + '), ' + \
    #                                                 str(len(coords)) + \
    #                                                     ' rectangles, Z = ' \
    #                                                         + str(Z)

    # Some calculations/modifications...
    algorithm = algorithm.name
    problem = problem.name
    variant = variant.name
    gap = '{0:.5f}'.format(model.gap)
    time = '{:.0f}'.format(totalT)
    Z = round(float(model.objective_value), 4)
    packing_density = utils.calculateItemsArea(l, w, items, direc_rep) / (L*W)
    # num_item_types_pattern = len(item_types)

    test_constraint_types = {
        0: "Objective function without complexity constraints",
        1: "Number of Different Item Types in the Cutting Pattern",
        2: "Number of Stages in the Cutting Pattern",
        3: "Maximum of Sum of Different Item Types in a Strip of the Cutting Pattern",
        5: "Total Number of Cuts in the Cutting Pattern"
    }

    test_constraint_name = test_constraint_types.get(
        test_constraint, "Unknown Constraint")

    # titulo = (
    #     f'{instance_name.split(".")[0]}'
    #     f'\n{algorithm} - {problem} - {variant} - {rotation} - h{h+1}'
    #     # OPTIMAL / FEASIBLE / NO_SOLUTION_FOUND
    #     f'\nSolution: {model.status.name}'
    # )

    titulo = (
        f'{instance_name.split(".")[0]}'
        f'\nT{test_constraint} - {test_constraint_name} - W{weight}'
        # OPTIMAL / FEASIBLE / NO_SOLUTION_FOUND
        f'\nSolution: {model.status.name}'
    )

    titulo_legenda = f'### SOLUTION INFORMATION ###'

    legenda = (
        f'\n• Instance: {instance_name}'
        f'\n• Algorithm: {algorithm}'
        f'\n• Problem: {problem}'
        f'\n• Variant: {variant}'
        f'\n• Rotation: {rotation}'
        f'\n• Levels in the tree (h): {h+1}'
        f'\n• Stages: {stages:.0f}'
        f'\n• Time Solved (seconds): {time}'
        f'\n• Gap: {gap}'
        f'\n• Packing Density: {packing_density:.2%}'
        f'\n• Objective Function value (Z): {Z}'
        f'\n '
        # f'\n• Weight of Complexity: {weight}'
        # f'\n• Number of different item types in the pattern: {num_item_types_pattern}'
        # f'\n        »» Item types: {sorted(list(item_types))}'
        # f'\n• Strips: {strips}'
        # f'\n• Maximum of the sum of different item types in a strip: {max_delta_barra}'
        # f'\n        »» Strip with most different item types: {strip_max}'
        # f'\n        »» Item types in that strip: {item_types_strip_max}'
    )

    if test_constraint == 1:
        legenda_test_constraint_1 = (
            f'\n  ## COMPLEXITY INFORMATION ##'
            f'\n• Objective Function used:'
            f'\n        »» {test_constraint_name} (#{test_constraint})'
            f'\n• Weight of Complexity: {weight}'
            f'\n• Normalization Factor: {norm_factor:.4f}'
            f'\n• Number of different item types in the pattern: {num_item_types_pattern}'
            f'\n        »» Item types: {sorted(list(item_types))}'
        )
        legenda += legenda_test_constraint_1

    elif test_constraint == 2:
        legenda_test_constraint_2 = (
            f'\n  ## COMPLEXITY INFORMATION ##'
            f'\n• Objective Function used:'
            f'\n        »» {test_constraint_name} (#{test_constraint})'
            f'\n• Weight of Complexity: {weight}'
            f'\n• Normalization Factor: {norm_factor:.4f}'
            f'\n• Stages: {num_stages_pattern}'
        )
        legenda += legenda_test_constraint_2

    elif test_constraint == 3:
        legenda_test_constraint_3 = (
            f'\n  ## COMPLEXITY INFORMATION ##'
            f'\n• Objective Function used:'
            f'\n        »» {test_constraint_name} (#{test_constraint})'
            f'\n• Weight of Complexity: {weight}'
            f'\n• Normalization Factor: {norm_factor:.4f}'
            f'\n• Strips: {strips}'
            f'\n• Maximum of the sum of different item types in a strip: {num_item_types_strip_pattern}'
            f'\n        »» Strip with most different item types: {strip_max}'
            f'\n        »» Item types in that strip: {item_types_strip_max}'
        )
        legenda += legenda_test_constraint_3

    elif test_constraint == 5:
        legenda_test_constraint_5 = (
            f'\n  ## COMPLEXITY INFORMATION ##'
            f'\n• Objective Function used:'
            f'\n        »» {test_constraint_name} (#{test_constraint})'
            f'\n• Weight of Complexity: {weight}'
            f'\n• Normalization Factor: {norm_factor:.4f}'
            f'\n• Total cuts in the pattern: {num_cuts_pattern}'
        )
        legenda += legenda_test_constraint_5

    plt.title(f'{titulo}', fontsize=12, weight='bold')

    # Ajuste o tamanho da janela pop-up
    mng = plt.get_current_fig_manager()
    # mng.window.state('zoomed')  # Abre a janela em tela cheia

    # Aplica o tight_layout() para ajustar o layout da figura
    # plt.tight_layout()

    # plt.text(50, 100, titulo_legenda, fontsize=8, ha='left', weight='bold')
    # plt.text(0.5, 0.1, legenda, fontsize=8, ha='left', style='italic')

    # plt.legend(
    #     loc='lower right',
    #     # bbox_to_anchor=(0, 0),
    #     title=titulo_legenda + legenda, title_fontsize='6'
    # )

    legenda_box = Rectangle((real_L + 10, 0), 110, 90,
                            linewidth=2.5,
                            facecolor="none",
                            edgecolor='black'
                            )
    ax.add_patch(legenda_box)
    ax.text(
        legenda_box.get_x() / 2 + 58,
        legenda_box.get_y() / 2 + 2,
        s=titulo_legenda + legenda,
        color="black",
        size=5.4
    )

    ax.set_aspect("equal")

    # if test_type == "simple":
    #     print("Ploting solution...")
    #     plt.show()
    # else:
    #     print("Saving solution plot...")
    #     output_path = os.path.join(
    #         folder_path, f"{instance_name.split('.')[0]}_plot.png")
    #     fig.savefig(output_path)

    print("Saving solution plot...")
    if test_constraint == 0:
        output_path = os.path.join(
            folder_path, f"{instance_name.split('.')[0]}_T{test_constraint}_plot.png"
        )
    else:
        output_path = os.path.join(
            folder_path, f"{instance_name.split('.')[0]}_T{test_constraint}_W{weight}_plot.png"
        )
    fig.savefig(output_path)

    plt.close(fig)  # Fecha a figura para liberar memória
