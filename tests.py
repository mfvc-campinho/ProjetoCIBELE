# Number of different item types
n = 25

# Elements in the tree (m)

"""
For a sub-rectangle tree with h levels, it is possible to enumerate all indexes
of the sub-rectangles and store them in a vector M^h. Since M^h depends on the
number of levels of the tree and any cut generates a maximum of four
sub-rectangles, the number of elements of M^h is:
"""


def M(h):
    sum = 0
    for j in range(h+1):  # Up to h
        sum += pow(4, j)
    return sum


h = 2
m = M(h)  # Height of the tree

# Set of n item types indexed by i, i = 1, ..., n
ii = [i for i in range(n)]

# Set of m of all possible sub-rectangles j, j = 1, ..., m
jj = [j for j in range(m)]

print(f"• Number of different item types (n): {n}")
print(f"List of different item types (ii): {ii}\n")

print(f"• All possible subrectangles (m): {m}")
print(f"List of all possible subrectangles (jj): {jj}\n")


# Evaluation if a subrectangle is a strip - sigma[j]
sigma = [1 if j in [4, 15, 16] else 0 for j in jj]
for j in jj:
    print(f"sigma[{j}]: {sigma[j]}")

# List to store descendants for each j
descendants_list = [[] for j in jj]
descendants_list_level = [[] for j in jj]

for j in jj:
    descendants = []
    descendants.append(j)
    descendants_list[j].extend(descendants)
    print(f"\n\nInitial descendants for j={j}: {descendants}\n")
    for level in range(h):
        current_descendants = []
        for descendant in descendants:
            current_descendants.append(4 * descendant + 1)
            current_descendants.append(4 * descendant + 2)
            current_descendants.append(4 * descendant + 3)
            current_descendants.append(4 * descendant + 4)
        descendants = [
            descendant for descendant in current_descendants if descendant < m]
        descendants_list_level[j].extend(descendants)
        print(f"Descendants at level {level + 1}: {descendants}")
    descendants_list[j].extend(descendants_list_level[j])

print("\n")
# Print the descendants_list
for j, descendants in enumerate(descendants_list):
    print(f"Descendants for j={j}: {descendants}")

#########################################
delta = [[0 for j in jj] for i in ii]

delta[4][17] = 1
delta[7][15] = 1
delta[7][16] = 1
delta[13][18] = 1

# for i in ii:
#     for j in jj:
#         print(f"delta[{i}][{j}] = {delta[i][j]}")

delta_barra = [[0 for j in jj] for i in ii]

delta_barra[4][4] = 1
delta_barra[7][15] = 1
delta_barra[7][16] = 1
delta_barra[13][4] = 1

# for i in ii:
#     for j in jj:
#         print(f"delta_barra[{i}][{j}] = {delta_barra[i][j]}")

for i in ii:
    print(f'\nItem i = {i}')
    for j in jj:
        # print(f'\nSubrectangle j = {j}')
        # print(f"descendant_list[{j}] = {descendants_list[j]}")
        # print(f"\nsigma[{j}] = {sigma[j]}")
        for j_prime in descendants_list[j]:
            delta_barra[i][j] = \
                delta[i][j_prime] - (1 - sigma[j])

            if delta_barra[i][j] == 1:
                print(f'\nsubrectangle j = {j}')
                print(f"descendant_list[{j}] = {descendants_list[j]}")
                print(f"sigma[{j}] = {sigma[j]}")
                print(f"j_prime = {j_prime}")
                print(f"delta[{i}][{j_prime}] = {delta[i][j_prime]}")
                print(f"delta_barra[{i}][{j}] = {delta_barra[i][j]}")
