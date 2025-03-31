# Imports
import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import Tk, filedialog, messagebox, ttk

from numpy import *
from PIL import Image, ImageTk

import mip_floating_cuts_4_arcs as fc4
import mip_floating_cuts_5_arcs as fc5
import packing_io as io
from floating_cuts_enums import (AlgorithmEnum, CutTypeEnum,
                                 OptimizationCriteriumEnum, ProblemEnum,
                                 VariantEnum)
from milp_utils import MILP_Variables
from packing_utils import *

### Funções ###
# Functions


# 1 - Simple test with graphical interface
# Performs a simple test with specific parameters and prints the results.


def singleTest(alg, prob, database_type, database_name, instance_name, weight, test_constraint, execution, plot):
    # Basic Parameters
    max_time = 3600  # Changeable!
    h = 2  # Changeable!
    stages = Infinity
    rotation = False  # Changeable!
    variant = VariantEnum.UNWEIGHTED  # Changeable!
    test_type = execution
    # plot = True  # Changeable!

    # Algorithm and Problem Selection
    algorithm = chooseAlgorithm(alg)
    problem = chooseProblem(prob)

    """
    ATTENTION:
    1 - When addressing the unweighted variant, the value of the items is
        set to:
        vi = li · wi
        If the problem type is the SKP, the maximum demand is set to one
        (di = 1).
    """
    test_constraint = int(test_constraint[0])

    if test_constraint != 0:
        weight = float(weight)

    print("\n\n##### Simple Test#####")
    print(
        "\n• Instance: " + instance_name +
        "\n• Algorithm: " + str(algorithm.name) +
        "\n• Problem: " + str(problem.name) +
        "\n• Variant: " + str(variant.name) +
        "\n• Rotation: " + str(rotation) +
        "\n• Levels of the tree (h) = " + str(h+1) +
        "\n• Number of Stages: " + str(stages) +
        "\n• Objective Function used: " + str(test_constraint) +
        "\n• Weight: " + str(weight)
    )

    if algorithm is AlgorithmEnum.ARCS4:
        totalT, z, status, variables = fc4.FloatingCuts(MILP_Variables(
        ), instance_name, database_type, database_name, h, algorithm, problem,
            stages, rotation, variant, max_time, plot, weight, test_constraint,
            test_type)
    else:
        cut_type = CutTypeEnum.NONGUILLOTINE1STORDER  # Cutting Type
        totalT, z, status, variables = fc5.FloatingCuts(MILP_Variables(
        ), instance_name, database_type, database_name, h, algorithm, problem,
            stages, rotation, variant, cut_type, max_time, True)

    print(f'\nZ value: {z} => {status} for h')

###############################################################################

# 2 - Full test H best
# Realiza um experimento completo com diferentes configurações de parâmetros,
# como tipos de algoritmo, problemas e instâncias.


def experimentTestWithHBest(alg, prob, database_type, database_name, test_constraint, weight, execution, plot):
    # Basic Parameters
    max_time = 1800  # Changeable!
    h = 2  # Changeable!
    stages = Infinity
    rotation = False  # Changeable!
    variant = VariantEnum.UNWEIGHTED  # Changeable!
    # plot = True  # Changeable!
    test_type = execution

    if weight != "":
        weight = float(weight)

    test_constraint = int(test_constraint[0])

    # Output File Name - dd.mm.YY__H_M_S
    output_name = datetime.now().strftime("%d.%m.%Y__%H_%M_%S")  # dd.mm.YY__H_M_S

    # Algorithm and Problem Selection
    algorithm = chooseAlgorithm(alg)
    problem = chooseProblem(prob)
    # problem = [chooseProblem(prob)]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    instance_directory = os.path.join(
        script_dir, 'dat', database_type, database_name)

    instances = os.listdir(instance_directory)

    # totalTests = str(len(problem)*len(h)*len(instances))
    totalTests = str(len(instances))
    currentTest = 1

    for i in range(len(instances)):
        print("\nTest " + str(currentTest) + "/" + totalTests)
        currentTest += 1

        if algorithm is AlgorithmEnum.ARCS4:
            # for weight in [0.1, 0.5, 0.9]:
            # for test_constraint in [0, 1, 2, 3, 5]:
            totalT, z, status, variables = \
                fc4.FloatingCuts(MILP_Variables(
                ), instances[i], database_type, database_name,
                    h, algorithm, problem, stages, rotation, variant,
                    max_time, plot, weight, test_constraint, test_type,
                    output_name)

    # to notify the conclusion of the experiment
    io.sendSimpleEmail(subject="Experiment concluded!",
                       msg_body="The best H experiment " +
                       output_name+" was succesfully concluded!",
                       receiver="matheus.f.campinho@inesctec.pt")


def experiment_T_W(alg, prob, database_type, database_name, execution, plot):
    # Basic Parameters
    max_time = 1800  # Changeable!
    h = 2  # Changeable!
    stages = Infinity
    rotation = False  # Changeable!
    variant = VariantEnum.UNWEIGHTED  # Changeable!
    test_type = execution

    # Output File Name - dd.mm.YY__H_M_S
    output_name = datetime.now().strftime("%d.%m.%Y__%H_%M_%S")  # dd.mm.YY__H_M_S

    # Algorithm and Problem Selection
    algorithm = chooseAlgorithm(alg)
    problem = chooseProblem(prob)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    instance_directory = os.path.join(
        script_dir, 'dat', database_type, database_name)

    instances = os.listdir(instance_directory)

    totalTests = str(len(instances))
    currentTest = 1

    for i in range(len(instances)):
        print("\nTest " + str(currentTest) + "/" + totalTests)
        currentTest += 1

        if algorithm is AlgorithmEnum.ARCS4:
            for weight in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
                for test_constraint in [0, 1, 2, 3, 5]:
                    totalT, z, status, variables = \
                        fc4.FloatingCuts(MILP_Variables(
                        ), instances[i], database_type, database_name,
                            h, algorithm, problem, stages, rotation, variant,
                            max_time, plot, weight, test_constraint, test_type,
                            output_name)

    # to notify the conclusion of the experiment
    io.sendSimpleEmail(subject="Experiment concluded!",
                       msg_body="The best H experiment " +
                       output_name+" was succesfully concluded!",
                       receiver="matheus.f.campinho@inesctec.pt")


# 3 - Choose the best H
# Realiza um experimento para encontrar o melhor valor do parâmetro "h" em
# um loop enquanto otimiza uma função.

###############################################################################

def experimentHTest(alg, prob, database_type, database_name):
    # Basic Parameters
    max_time = 900  # Changeable!
    h_maximum = 3
    criterium = OptimizationCriteriumEnum.H  # Stop Condition
    cut_type = CutTypeEnum.GUILLOTINE  # Cutting Type
    load_solution = False

    # Remember: h value represents h+1 in practice!
    # (e.g.: h_maximum = 3 represents h = 4)

    # Output File Name - dd.mm.YY__H_M_S
    output_name = datetime.now().strftime("%d.%m.%Y__%H_%M_%S")

    # Algorithm and Problem Selection
    algorithm = chooseAlgorithm(alg)
    problem = [chooseProblem(prob)]

    instances = []
    if database_type == 'distributor':
        if database_name == 'silva':
            instances = ['cgcut1.txt', 'cgcut2.txt', 'cgcut3.txt',
                         'CW1.txt', 'CW2.txt', 'CW3.txt',
                         'okp1.txt', 'okp2.txt', 'okp3.txt',
                         'okp4.txt', 'okp5.txt']
        elif database_name == 'beasley':
            instances = ['ngcut1.txt', 'ngcut2.txt', 'ngcut3.txt',
                         'ngcut4.txt', 'ngcut5.txt', 'ngcut6.txt',
                         'ngcut7.txt', 'ngcut8.txt', 'ngcut9.txt',
                         'ngcut10.txt', 'ngcut11.txt', 'ngcut12.txt']
        elif database_name == 'gcut':
            instances = ['gcut1.txt', 'gcut2.txt', 'gcut3.txt',
                         'gcut4.txt', 'gcut5.txt', 'gcut6.txt',
                         'gcut7.txt', 'gcut8.txt', 'gcut9.txt',
                         'gcut10.txt', 'gcut11.txt', 'gcut12.txt',
                         'gcut13.txt']
        elif database_name == 'literature1':
            instances = ['cu1.txt', 'cu3.txt', 'cu7.txt', 'of2.txt',
                         'cu10.txt', 'cu4.txt', 'cu8.txt', 'wang1.txt',
                         'cu11.txt', 'cu5.txt', 'cu9.txt', 'wang2.txt',
                         'cu2.txt', 'cu6.txt', 'of1.txt', 'wang3.txt']
        elif database_name == 'literature2':
            instances = ['2s.txt', 'A4.txt', 'CHL6.txt', 'Hchl4s.txt',
                         'STS4s.txt', '3s.txt', 'A5.txt', 'CHL7.txt',
                         'Hchl6s.txt', 'W.txt', 'A1s.txt', 'CHL1s.txt',
                         'CU1.txt', 'Hchl7s.txt', 'of1.txt', 'A2s.txt',
                         'CHL2s.txt', 'CU2.txt', 'Hchl8s.txt', 'of2.txt',
                         'A3.txt', 'CHL5.txt', 'Hchl3s.txt', 'STS2s.txt']
        elif database_name == 'literature3':
            instances = ['CW10.txt', 'CW4.txt', 'CW6.txt', 'CW8.txt',
                         'CW11.txt', 'CW5.txt', 'CW7.txt', 'CW9.txt']
    elif database_type == 'manufacturer':
        if database_name == 'iipp':
            # (1,60) -> 1 up to 59
            instances = ['iipp{:02d}'.format(i)+".txt" for i in range(1, 60)]
        elif database_name == 'coveriiib':
            instances = ['coveriiib{:03d}'.format(
                i)+".txt" for i in range(1, 316)]  # (1,316) -> 1 up to 315
        else:
            print(
                "\nERROR!!! Define the correct database name! \
                    [iipp|coveriiib]\n")
            exit()
    else:
        print(
            "\nERROR!!! Define the correct database type! \
                [manufacturer|distributor]\n")
        exit()

    if algorithm is AlgorithmEnum.ARCS4:
        configs = [
            getTestConfig(1),  # config 1
            getTestConfig(2),  # config 2
            getTestConfig(3),  # config 3
            getTestConfig(4),  # config 4
            getTestConfig(5)  # config 5
        ]
    elif algorithm is AlgorithmEnum.ARCS5:
        if database_type == 'distributor':
            configs = [
                getTestConfig(1),  # config 1
                getTestConfig(2),  # config 2
                getTestConfig(4),  # config 4
                getTestConfig(5)  # config 5
            ]
        else:
            configs = [
                getTestConfig(2)  # config 2 (only rotation for manufacturer)
            ]

    currentTest = 1
    for p in problem:
        for config in range(len(configs)):
            for i in range(len(instances)):
                h = 0
                last_z = 0
                status = 'FEASIBLE'
                variables = MILP_Variables()

                while status != 'OPTIMAL':
                    print("\n\nTest " + str(currentTest))
                    print("\t* Instance " + instances[i])
                    print("\t* Configs: " + str(configs[config][0]) + "/" +
                          str(configs[config][1]) + "/" +
                          str(configs[config][2].name))
                    print("\t* h = " + str(h+1))

                    # control the reload of the solution
                    if not load_solution:
                        variables = MILP_Variables()

                    if algorithm is AlgorithmEnum.ARCS4:
                        totalT, z, status, variables = fc4.FloatingCuts(
                            variables, instances[i], database_type,
                            database_name, h, algorithm, problem[0],
                            configs[config][0], configs[config][1],
                            configs[config][2], max_time, output_name)
                    else:
                        totalT, z, status, variables = fc5.FloatingCuts(
                            variables, instances[i], database_type,
                            database_name, h, algorithm, problem[0],
                            configs[config][0], configs[config][1],
                            configs[config][2], cut_type,
                            max_time, output_name)

                    # -----------------------------------------------#
                    #                 Stop conditions               #
                    # -----------------------------------------------#
                    # Repetitions required
                    # By h (tree height)
                    if criterium is OptimizationCriteriumEnum.H:
                        if h >= h_maximum:
                            status = 'OPTIMAL'
                        else:
                            status = 'FEASIBLE'
                    # Not required a number of repetitions
                    elif status != 'OPTIMAL':
                        # By objective function (not improved value)
                        if criterium is OptimizationCriteriumEnum.OBJ:
                            if last_z >= z:
                                status = 'OPTIMAL'
                            else:
                                last_z = z
                        # By time (max time)
                        elif criterium is OptimizationCriteriumEnum.TIME:
                            if totalT >= (max_time-TIME_ERROR):
                                status = 'OPTIMAL'
                    # -----------------------------------------------#

                    # next
                    currentTest += 1
                    h += 1

                print("-------------- BEST h is " +
                      str(h-1) + " -------------- ")

    # to notify the conclusion of the experiment
    io.sendSimpleEmail(subject="Experiment concluded!",
                       msg_body="The H test experiment " +
                       output_name+" was succesfully concluded!",
                       receiver="mfvc.campinho@gmail.com")

###############################################################################

# 4 - Load solution graphically
# Lê e plota resultados de soluções gráficas.


def plotResult(path):
    value = io.readResult(path)
    # print(value)

    print("\nLoading graphical solution...")
    print(
        f"\nProblem class: {value['problem'].name} \
            ({value['algorithm'].name})")
    print(
        f"Instance: {value['instance'].split('.')[0]}, \
            h={value['levels']}, \
                z={value['z']}")
    print(
        f"Variant: {value['stages']}|\
            {value['rotation']}|\
                {value['variant'].name}")

    io.plot(Rotation(float(value.get("r", 0))),
            value['L'], value['W'], value['l'],
            value['w'], value['coords'], value['items'],
            value['direc_rep'], value['z'])

###############################################################################

### Algorithm and Problem Selection ###


"""
The functions chooseAlgorithm(type) and chooseProblem(name) are used to map
the arguments passed on the command line to the appropriate values of
algorithm and problem.
"""


def chooseAlgorithm(type):
    # 1 - Choose the strategy
    if type == 'arcs4':
        return AlgorithmEnum.ARCS4
    elif type == 'arcs5':
        return AlgorithmEnum.ARCS5
    return -1


def chooseProblem(name):
    # 2 - Choose the problem to be solved
    if name == 'skp':
        return ProblemEnum.SKP
    elif name == 'slopp':
        return ProblemEnum.SLOPP
    return -1

###############################################################################

### Test Configuration###


"""
The code defines various test configurations with different parameters, such as
the algorithm type (ARCS4 or ARCS5), the problem (SKP or SLOPP), and various
other settings specific to the tests.
"""

# Choose the test configuration


def getTestConfig(number):
    if number == 1:
        return [Infinity, False, VariantEnum.UNWEIGHTED]  # config 1
    if number == 2:
        return [Infinity, True,  VariantEnum.UNWEIGHTED]  # config 2
    if number == 3:
        return [2,        False, VariantEnum.UNWEIGHTED]  # config 3
    if number == 4:
        return [Infinity, False, VariantEnum.WEIGHTED]  # config 4
    if number == 5:
        return [Infinity, True, VariantEnum.WEIGHTED]  # config 5
    return []

###############################################################################


### Main program ###


"""Processes the arguments passed on the command line and decides which
function to call based on these arguments.
The code also calls the plotResult() function if a result file path is
provided as an argument.
"""

# path = ""
# if len(sys.argv) == 4 or len(sys.argv) == 6:
#     algorithm = sys.argv[1]
#     problem = sys.argv[2]
#     execution = sys.argv[3]
#     database_type = ''
#     database_name = ''

#     if len(sys.argv) == 6:
#         database_type = sys.argv[4]
#         database_name = sys.argv[5]

# if len(sys.argv) == 2:
#     path = sys.argv[1]

# if len(sys.argv) != 4 and len(sys.argv) != 6 and len(sys.argv) != 2:
#     print("*** Solver or instance reader ***")
#     print("\n$ Run: python packer.py [TYPE PROBLEM EXECUTION] | [RESULT]")
#     print("\nTYPE")
#     print('\t-> arcs4:  Non-Guillotine Cuts')
#     print('\t-> arcs5:  Guillotine Cuts 1st level')
#     print("PROBLEM")
#     print('\t-> skp:    Single Knapsack Problem')
#     print('\t-> slopp:  Constrained Single Placement Problem')
#     print("EXECUTION")
#     print('\t-> simple: Simple execution with graphical output')
#     print('\t-> experiment: Complete fixed h test with text output')
#     print(
#         '\t-> htest DATABASE_TYPE DATABASE_NAME: complete h test with text'
#         'output (DATABASE_TYPE=[manufacturer|distributor] DATABASE_NAME)')
#     print("RESULT")
#     print('\t-> Path to the text file that represents some result\n')
#     exit()

# if path != "":
#     plotResult(path)
# elif execution == 'simple':
#     singleTest(algorithm, problem)
# elif execution == 'experiment':
#     experimentTestWithHBest(algorithm, problem)
# elif execution == 'htest':
#     experimentHTest(algorithm, problem, database_type, database_name)
# else:
#     print("\n\tUndefined action!")
# print("\nConcluded!")

###############################################################################

# Nova Implementação!!
# Creation of graphic interface


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 40

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text,
                         background="#64C8EB", foreground="#ffffff", relief="solid", borderwidth=1)
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


algorithm_descriptions = {
    'arcs4': 'Non-Guillotine Cuts',
    'arcs5': 'Guillotine Cuts 1st level',
}

problem_descriptions = {
    'skp': 'Single Knapsack Problem',
    'slopp': 'Constrained Single Placement Problem',
}

execution_descriptions = {
    'simple': 'Simple execution with graphical output.',
    'experiment': 'Complete fixed h test with text output.',
    'experiment_T_W': 'Experiment test for predefined Weight and Test Constraint with text output and graphical output (optional).',
    'htest': 'Complete h test with text output. If selected this type of execution you must select a database type and a database name.'
}

database_type_descriptions = {
    'manufacturer': 'Database type - Manufacturer',
    'distributor': 'Database type - Distributor',
    'instances_constraints': 'Database type - Instances Constraints',
    'preliminary_tests': 'Database name - Preliminary Tests',
}

database_name_descriptions = {
    'SLOPP_instances': 'Database name - SLOPP Instances',
    'SLOPP_instances_atualizadas': 'Database name - SLOPP Instances_atualizadas',
    'SLOPP_instances_atualizadas_teste': 'Database name - SLOPP Instances_atualizadas_teste',
}

test_constraint_descriptions = {
    '0 - Objective function without complexity constraints': 'Objective function without complexity constraints',
    '1 - Number of different item types in a pattern': 'Number of different item types in a pattern',
    '2 - Number of stages in a cutting pattern': 'Number of stages in a cutting pattern',
    '3 - Maximum number of item types in the strips of a pattern': 'Maximum number of item types in the strips of a pattern',
    # '4 - Number of different types of strips in a pattern': 'Number of different types of strips in a pattern',
    '5 - Total number of cuts in a pattern': 'Total number of cuts in a pattern'
}


def run_program(algorithm, problem, execution, database_type, database_name, instance_name, weight, test_constraint, path, plot):
    print("Executing program with the following parameters:")
    print(f"Algorithm: {algorithm} - {algorithm_descriptions.get(algorithm)}")
    print(f"Problem: {problem} - {problem_descriptions.get(problem)}")
    print(f"Execution: {execution}")
    print(f"Database Type: {database_type}")
    print(f"Database Name: {database_name}")
    print(f"Weight: {weight}")
    print(f"Test Constraint: {test_constraint}")
    print(f"Path: {path}")
    print(f"Plot: {plot}")

    if path:
        plotResult(path)
    elif execution == 'simple':
        singleTest(
            algorithm, problem, database_type, database_name, instance_name, weight, test_constraint, execution, plot)
    elif execution == 'experiment':
        experimentTestWithHBest(
            algorithm, problem, database_type, database_name, test_constraint, weight, execution, plot)
    elif execution == 'experiment_T_W':
        experiment_T_W(
            algorithm, problem, database_type, database_name, execution, plot)
    elif execution == 'htest':
        experimentHTest(algorithm, problem, database_type, database_name)
    else:
        print("\n\tUndefined action!")
    print("\nConcluded!")


def browse_entry_path():
    initial_directory = 'C:\\Users\\matheus.f.campinho\\Downloads\\Documentos INESC-TEC\\floating-cuts-main_constraints'

    directory_path = filedialog.askdirectory(initialdir=initial_directory)
    entry_path.delete(0, tk.END)
    entry_path.insert(0, directory_path)


def browse_entry_inst_name():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    initial_directory = os.path.join(script_dir, 'dat')

    selected_db_type = combo_db_type.get()
    selected_db_name = combo_db_name.get()

    final_directory = os.path.join(
        initial_directory, selected_db_type, selected_db_name)

    file_path = filedialog.askopenfilename(initialdir=final_directory)
    file_name = os.path.basename(file_path)

    entry_inst_name.delete(0, tk.END)
    entry_inst_name.insert(0, file_name)


def browse_file():
    file_path = filedialog.askopenfilename()
    entry_path.delete(0, tk.END)
    entry_path.insert(0, file_path)


def execute_program():
    algorithm = combo_algorithm.get()
    problem = combo_problem.get()
    execution = combo_execution.get()
    database_type = combo_db_type.get()
    database_name = combo_db_name.get()
    instance_name = entry_inst_name.get()
    weight = entry_weight.get()
    test_constraint = combo_test_constraint.get()
    path = entry_path.get()
    plot = plot_var.get()

    # Verifica se o Database Type está vazio e, se estiver, define-o como uma string vazia
    database_type = database_type if database_type else ""

    if execution == 'simple' and not instance_name:
        messagebox.showwarning(
            "Warning", "Please select an instance for the simple test.")
        # Muda a cor para vermelho claro
        entry_inst_name.configure(bg="lightcoral")

        return

    if execution == 'simple':
        try:
            weight = float(weight)
            if weight < 0 or weight > 1:
                raise ValueError(
                    "Invalid weight range. Weight must be between 0 and 1.")
        except ValueError:
            messagebox.showerror(
                "Error", "Invalid input. Please enter a valid number between 0 and 1.")
            entry_weight.delete(0, tk.END)  # Limpa o campo de entrada
            return  # Interrompe a execução do código aqui

    if execution != "experiment_T_W" and test_constraint != '0 - Objective function without complexity constraints' and not weight:
        messagebox.showwarning(
            "Warning", "Please define a value for the weight parameter.")
        # Muda a cor para vermelho claro
        entry_weight.configure(bg="lightcoral")

    if instance_name == 'Directory not found':
        messagebox.showwarning(
            "Warning", "Please select a valid instance.")
        # Muda a cor para vermelho claro
        entry_inst_name.configure(bg="lightcoral")
        return

    try:
        run_program(algorithm, problem, execution, database_type,
                    database_name, instance_name, weight, test_constraint, path, plot)
    except ValueError as ve:
        # messagebox.showerror("Execution Error", str(ve))
        return

        # run_program(algorithm, problem, execution, database_type,
        #             database_name, instance_name, weight, test_constraint, path, plot)


def get_first_file_from_directory(directory):
    try:
        # Lista todos os arquivos no diretório e ordena em ordem alfabética
        files = sorted(f for f in os.listdir(directory)
                       if os.path.isfile(os.path.join(directory, f)))
        if files:
            return files[0]  # Retorna o primeiro arquivo da lista ordenada
        else:
            return None  # Caso não haja arquivos na pasta
    except FileNotFoundError:
        return None  # Caso o diretório não exista


def update_test_constraint(*args):
    if combo_execution.get() == 'experiment_T_W':
        combo_test_constraint.delete(0, tk.END)
        combo_test_constraint.config(
            state='disabled', style='Disabled.TCombobox')
        test_constraint_tooltip.text = "Execution must be different to define this parameter"
    else:
        combo_test_constraint.config(state='normal', style='TCombobox')
        # Definindo um valor padrão
        combo_test_constraint.set(
            '0 - Objective function without complexity constraints')
        test_constraint_tooltip.text = "Choose the objective function for the specific constraint tested"


def update_instance_name():
    # Obtém os valores selecionados para Database Type e Database Name
    selected_db_type = combo_db_type.get()
    selected_db_name = combo_db_name.get()

    # Define o diretório base e caminho final de acordo com as seleções
    script_dir = os.path.dirname(os.path.abspath(__file__))
    initial_directory = os.path.join(
        script_dir, 'dat', selected_db_type, selected_db_name)

    # Verifica se o diretório existe
    if os.path.isdir(initial_directory):
        # Busca o primeiro arquivo da pasta em ordem alfabética
        files = sorted(os.listdir(initial_directory))
        if files:
            first_file = files[0]  # Primeiro arquivo em ordem alfabética
            entry_inst_name.delete(0, tk.END)
            entry_inst_name.insert(0, first_file)
        else:
            entry_inst_name.delete(0, tk.END)
            entry_inst_name.insert(0, "No files found")
    else:
        entry_inst_name.delete(0, tk.END)
        entry_inst_name.insert(0, "Directory not found")

    # Verifica o valor contido no campo entry_inst_name
    if entry_inst_name.get() == 'Directory not found':
        entry_inst_name.configure(bg="lightcoral")
    else:
        # Volta para a cor padrão se o diretório for válido
        entry_inst_name.configure(bg="white")  # Ou a cor que preferir


def set_default_values():
    combo_algorithm.set('arcs4')
    combo_problem.set('slopp')
    combo_execution.set('experiment_T_W')  # experiment # simple
    combo_db_type.set('preliminary_tests')  # instances_constraints
    combo_db_name.set('SLOPP_instances_atualizadas_teste')  # SLOPP_instances
    entry_weight.insert(0, '0.0')  # Can do #
    combo_test_constraint.set(
        '0 - Objective function without complexity constraints')
    # 0 - Objective function without complexity constraints
    # 1 - Number of different item types in a pattern
    # 2 - Number of stages in a cutting pattern
    # 3 - Maximum number of item types in the strips of a pattern
    # 5 - Total number of cuts in a pattern

    # Diretório base onde os arquivos estão localizados
    script_dir = os.path.dirname(os.path.abspath(__file__))
    initial_directory = os.path.join(
        script_dir, 'dat', 'preliminary_tests', 'SLOPP_instances_atualizadas_teste')

    # Obtém o primeiro arquivo no diretório
    first_file = get_first_file_from_directory(initial_directory)

    if first_file:
        # Insere o nome do arquivo na entrada de nome da instância
        entry_inst_name.insert(0, first_file)
    else:
        # Caso não encontre nenhum arquivo, exibe uma mensagem padrão
        entry_inst_name.insert(0, 'No file found')


root = tk.Tk()
root.configure(background="#0091BE")

#####
# Set window size and position
window_width = 600
window_height = 440

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x_coordinate = (screen_width - window_width) // 2
y_coordinate = (screen_height - window_height) // 2 - 30

root.geometry(f'{window_width}x{window_height}+{x_coordinate}+{y_coordinate}')

# Load and resize background image
script_dir = os.path.dirname(os.path.abspath(__file__))
background_image_path = os.path.join(
    script_dir, 'INESC_TEC_Background_Image.jpg')

background_image = Image.open(background_image_path)

# Resize the image to match the window size
background_image = background_image.resize(
    (window_width, window_height), Image.LANCZOS)

background_photo = ImageTk.PhotoImage(background_image)

# Ensure the image reference is stored
background_label = tk.Label(root, image=background_photo)
background_label.image = background_photo  # Prevent garbage collection
background_label.place(x=0, y=0, relwidth=1, relheight=1)
######

root.title("Projeto CIBELE - INESC-TEC Floating Cuts")

root.bind('<Return>', lambda event=None: execute_program())

# Configurações de estilo
style = ttk.Style(root)
style.theme_use("default")
style.configure('TLabel', font=('Effra', 10, 'bold'))
style.configure('TCombobox', font=('Effra', 10, 'bold'))
style.configure('Disabled.TCombobox', fieldbackground='#FF5050')
style.map("Custom.TButton",
          background=[("active", "#FFA500")])


# Labels and Combobox

tk.Label(root, text="Projeto CIBELE - INESC-TEC - Floating Cuts",
         font=('Effra', 12, 'bold'), background="#0091BE", foreground="#ffffff", borderwidth=5, relief='groove').grid(row=0, column=0, columnspan=3, pady=10)

tk.Label(root, text="Algorithm:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=1, column=0, pady=5, sticky='e')
combo_algorithm = ttk.Combobox(root, values=list(
    algorithm_descriptions.keys()), style='TCombobox')
combo_algorithm.grid(row=1, column=1, pady=5, sticky='w')

tk.Label(root, text="Problem:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=2, column=0, pady=5, sticky='e')
combo_problem = ttk.Combobox(root, values=list(
    problem_descriptions.keys()), style='TCombobox')
combo_problem.grid(row=2, column=1, pady=5, sticky='w')

tk.Label(root, text="Execution:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=3, column=0, pady=5, sticky='e')
combo_execution = ttk.Combobox(
    root, values=list(execution_descriptions.keys()), style='TCombobox')
combo_execution.grid(row=3, column=1, pady=5, sticky='w')

tk.Label(root, text="Database Type:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=4, column=0, pady=5, sticky='e')
combo_db_type = ttk.Combobox(
    root, values=list(database_type_descriptions.keys()), style='TCombobox')
combo_db_type.grid(row=4, column=1, pady=5, sticky='w')

tk.Label(root, text="Database Name:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=5, column=0, pady=5, sticky='e')
combo_db_name = ttk.Combobox(
    root, values=list(database_name_descriptions.keys()), style='TCombobox', width=35)
combo_db_name.grid(row=5, column=1, pady=5, sticky='w')

tk.Label(root, text="Instance Name (Single Test):", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=6, column=0, pady=5, sticky='e')
entry_inst_name = tk.Entry(root, width=50)
entry_inst_name.grid(row=6, column=1, pady=5, sticky='w')
button_browse_entry_inst_name = ttk.Button(
    root, text="Browse", command=browse_entry_inst_name, cursor="hand2", style="Custom.TButton")
button_browse_entry_inst_name.grid(row=6, column=2, pady=5, padx=(10, 0))

tk.Label(root, text="Weight of Complexity:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=7, column=0, pady=5, sticky='e')
entry_weight = tk.Entry(root)
entry_weight.grid(row=7, column=1, pady=5, sticky='w')

tk.Label(root, text="Test Constraint:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=8, column=0, pady=5, sticky='e')
combo_test_constraint = ttk.Combobox(root, values=list(
    test_constraint_descriptions.keys()), style='TCombobox', width=60)
combo_test_constraint.grid(row=8, column=1, pady=5, columnspan=2, sticky='w')

tk.Label(root, text="Path:", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=9, column=0, pady=5, sticky='e')
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=9, column=1, pady=5)
button_browse_entry_path = ttk.Button(
    root, text="Browse", command=browse_entry_path, cursor="hand2", style="Custom.TButton")
button_browse_entry_path.grid(row=9, column=2, pady=5, padx=(10, 0))

tk.Label(root, text="Plot?", font=('Effra', 10, 'bold'),
         background="#0091BE", foreground="#ffffff").grid(row=10, column=0, pady=5, sticky='e')
plot_var = tk.BooleanVar()
plot_var.set(True)
plot_checkbox = ttk.Checkbutton(
    root, text="Yes!", variable=plot_var, style='Custom.TCheckbutton')
plot_checkbox.grid(row=10, column=1, pady=5, columnspan=2, sticky='w')

set_default_values()
update_instance_name()  # Preenche o instance name automaticamente na inicialização

tk.Button(root, width=50, height=2, text="Execute Program", command=execute_program, cursor="hand2",
          background="#64C8EB", foreground="#ffffff").grid(row=11, column=0, columnspan=3, pady=10)


# Adiciona dicas de ferramentas às caixas de seleção e entradas
algorithm_tooltip = ToolTip(combo_algorithm,
                            "Choose the algorithm type")
problem_tooltip = ToolTip(combo_problem,
                          "Choose the problem type")
execution_tooltip = ToolTip(combo_execution,
                            "Choose the execution type")
db_type_tooltip = ToolTip(combo_db_type,
                          "Enter the database type")
db_name_tooltip = ToolTip(combo_db_name,
                          "Enter the database name")
inst_name_tooltip = ToolTip(entry_inst_name,
                            "Enter the instance name or click the buttom to browse")
weight_tooltip = ToolTip(entry_weight,
                         "Enter the weight value for the complexity constraints")
test_constraint_tooltip = ToolTip(combo_test_constraint,
                                  "Choose the objective function for the specific constraint tested")
path_tooltip = ToolTip(entry_path,
                       "Enter the path or click the buttom to browse")
button_browse_entry_inst_name_tooltip = ToolTip(button_browse_entry_inst_name,
                                                "Browse for a file")
button_browse_entry_path_tooltip = ToolTip(button_browse_entry_path,
                                           "Browse for a directory")
plot_checkbox_tooltip = ToolTip(plot_checkbox,
                                'Click "yes!" to plot graphical results')


def toggle_entry_state():
    if combo_execution.get() == 'simple':
        entry_inst_name.config(state='normal', bg='white')
        button_browse_entry_inst_name.config(state='normal')

        # Atualiza o valor do instance name para o primeiro arquivo na pasta
        if combo_test_constraint.get() == "":
            update_instance_name()

        # Atualiza os tooltips
        inst_name_tooltip.text = "Enter the instance name or click the button to browse"
        button_browse_entry_inst_name_tooltip.text = "Browse for a file"
    else:
        entry_inst_name.delete(0, tk.END)
        entry_inst_name.config(state='disabled', bg='#FF5050')
        button_browse_entry_inst_name.config(state='disabled')

        # Atualiza os tooltips
        inst_name_tooltip.text = "Execution must be set to 'Simple Test' to define this value"
        button_browse_entry_inst_name_tooltip.text = "Execution must be set to 'Simple Test' to define this value"

    if combo_execution.get() == 'experiment_T_W':
        entry_inst_name.delete(0, tk.END)
        entry_inst_name.config(state='disabled', bg='#FF5050')
        button_browse_entry_inst_name.config(state='disabled')

        combo_test_constraint.delete(0, tk.END)
        combo_test_constraint.config(
            state='disabled', style='Disabled.TCombobox')
        test_constraint_tooltip.text = "Execution must be different to define this parameter"
    else:
        combo_test_constraint.config(
            state='normal', style='TCombobox')
        test_constraint_tooltip.text = "Choose the objective function for the specific constraint tested"

    # Se a restrição de teste não for a função objetivo 0, habilita o campo de peso
    if combo_test_constraint.get() != '0 - Objective function without complexity constraints':
        entry_weight.config(state='normal', bg='white')
        entry_weight.delete(0, tk.END)
        entry_weight.insert(0, '0.00')
        weight_tooltip.text = "Enter the weight value for the complexity constraints"
    else:
        entry_weight.delete(0, tk.END)
        entry_weight.config(state='disabled', bg='#FF5050')
        weight_tooltip.text = "Test constraint must be set with a complexity indicator to define this value"


# Desativa os campos inicialmente se a execução não for 'simple'
if combo_execution.get() != 'simple':
    entry_inst_name.delete(0, tk.END)
    entry_inst_name.config(state='disabled', bg='#FF5050')
    button_browse_entry_inst_name.config(state='disabled')

    entry_inst_name.config(state='disabled', bg='#FF5050')
    button_browse_entry_inst_name.config(state='disabled')
    inst_name_tooltip.text = "Execution must be set to 'Simple Test' to define this value"
    button_browse_entry_inst_name_tooltip.text = "Execution must be set to 'Simple Test' to define this value"

# Desativa o campo de peso se a restrição de teste for a função objetivo 0
if combo_test_constraint.get() == '0 - Objective function without complexity constraints':
    entry_weight.delete(0, tk.END)
    entry_weight.config(state='disabled', bg='#FF5050')
    weight_tooltip.text = "Test constraint must be set with a complexity indicator to define this value"

# Liga a função de toggle quando o combobox de execução é alterado
combo_execution.bind("<<ComboboxSelected>>",
                     lambda event: toggle_entry_state())
combo_test_constraint.bind("<<ComboboxSelected>>",
                           lambda event: toggle_entry_state())

# Atualiza o Instance Name sempre que Database Type ou Database Name forem modificados
combo_db_type.bind("<<ComboboxSelected>>",
                   lambda event: update_instance_name())
combo_db_name.bind("<<ComboboxSelected>>",
                   lambda event: update_instance_name())


# Evento ao clicar na caixa de texto (FocusIn)
entry_weight.bind(
    "<FocusIn>", lambda event: entry_weight.configure(bg="white"))

# Evento ao começar a digitar (KeyRelease)
entry_weight.bind(
    "<KeyRelease>", lambda event: entry_weight.configure(bg="white"))

# Evento ao clicar na caixa de texto (FocusIn)
entry_inst_name.bind(
    "<FocusIn>", lambda event: entry_weight.configure(bg="white"))

# Evento ao começar a digitar (KeyRelease)
entry_inst_name.bind(
    "<KeyRelease>", lambda event: entry_weight.configure(bg="white"))

combo_execution.bind("<<ComboboxSelected>>", update_test_constraint)


# Configura a geometria da tela
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = 600
window_height = 440

x_coordinate = (screen_width - window_width) // 2
y_coordinate = (screen_height - window_height) // 2 - 30

root.geometry(f'{window_width}x{window_height}+{x_coordinate}+{y_coordinate}')

root.mainloop()
