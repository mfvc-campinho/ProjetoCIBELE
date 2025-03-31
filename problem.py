from mip import INTEGER, Model, minimize, xsum

# Create a model
model = Model()

# Define variables
x = [model.add_var(var_type=INTEGER, lb=0) for i in range(3)]

# Define constraints
model += xsum(x[i] for i in range(3)) <= 10

# Define objective function
model.objective = minimize(xsum(i * x[i] for i in range(3)))

# Solve the model
status = model.optimize()

# Print the solution
if status == OptimizationStatus.OPTIMAL:
    print("Optimal Solution:")
    for i in range(3):
        print(f"x[{i}] = {x[i].x}")
