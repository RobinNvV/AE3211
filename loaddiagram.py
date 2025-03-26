import numpy as np
import matplotlib.pyplot as plt

########################################################
# Inputs, to be changed based on aircraft/Excel calculations

# Weight in kg, CG in % MAC
components = {
    "OEW": {"weight": 13450, "cg": 0.25},   # Operating Empty Weight
    "fcargo": {"weight": 1000, "cg": -2.5}, # Front Cargo
    "rcargo": {"weight": 1000, "cg": 5},   # Rear Cargo
}

avg_weight = 80 # Average weight of a passenger
forward_cg = -2.6 # Most forward CG of a passenger
aft_cg = 4.3 # Most aft CG of a passenger
columnpassengers = 18 # Number of passengers in each column

########################################################
def cg_calculator(components):
    """
    input: List of any number of components
    output: CG and weight of the aircraft
    """

    total_weight = 0
    total_moment = 0

    for component in components:
        total_weight += component["weight"]
        total_moment += component["weight"] * component["cg"]

    cg = total_moment / total_weight
    return cg, total_weight

def passenger_cg_data(forward_cg = -2.6, aft_cg = 4.3, columnpassengers = 18):
    """
    input: starting weight and cg of the aircraft (tuple)
    input: cg of most forward and aft passenger
    input: number of passengers in each column (int)

    output: list of passengers with weight and cg
    """

    # Calculate cg for each passenger (assume even spacing)
    cg_array = np.linspace(forward_cg, aft_cg, columnpassengers)

    # Create list of all passengers in a column (the same list is used for aisle seating or window seating)
    # The 2 for each side of the aisle
    loading_lst = [{"weight": avg_weight, "cg": cg} for cg in cg_array for _ in range(2)]

    return loading_lst

fuel_loading_points = [
    cg_calculator([components["OEW"]]),
    cg_calculator([components["OEW"], components["fcargo"]]),
    cg_calculator([components["OEW"], components["rcargo"]]),
    cg_calculator([components["OEW"], components["fcargo"], components["rcargo"]]),
]

current_load = [components["OEW"], components["fcargo"], components["rcargo"]]
passenger_load_lst = passenger_cg_data(forward_cg, aft_cg, columnpassengers)

def calculate_passenger_points(passenger_load_lst, current_load):

    front_points, back_points = [], []
    for i in range(len(passenger_load_lst)):
        # Calculate loading points for front to back
        front_load = passenger_load_lst[:i+1] + current_load

        # Calculate loading points for back to front
        back_load = passenger_load_lst[i:] + current_load


        front_points.append(cg_calculator(front_load))
        back_points.append(cg_calculator(back_load))

    return front_points, back_points

# Calculate loading points for window and aisle (difference for aisle is that window is already seated)
window_front_points, window_back_points = calculate_passenger_points(passenger_load_lst, current_load)
aisle_front_points, aisle_back_points = calculate_passenger_points(passenger_load_lst, current_load + passenger_load_lst)


# Find minimum and maximum CG in all points lists
all_points = fuel_loading_points + window_front_points + window_back_points + aisle_front_points + aisle_back_points
min_cg = min(point[0] for point in all_points)
max_cg = max(point[0] for point in all_points)
min_weight = min(point[1] for point in all_points)
max_weight = max(point[1] for point in all_points)

print(f"Minimum CG: {min_cg}")
print(f"Maximum CG: {max_cg}")


# Plotting
plt.scatter(*zip(*fuel_loading_points), color='r', label="Fuel Loading")
plt.scatter(*zip(*window_front_points), color='b', label="Window Seating (Front to Back)")
plt.scatter(*zip(*window_back_points), color='g', label="Window Seating (Back to Front)")
plt.scatter(*zip(*aisle_front_points), color='y', label="Aisle Seating (Front to Back)")
plt.scatter(*zip(*aisle_back_points), color='m', label="Aisle Seating (Back to Front)")
plt.vlines([min_cg*0.98, max_cg*1.02], min_weight, max_weight, linestyles='dashed', colors='k', alpha=0.5, label="CG Limits")
plt.xlabel("CG Position")
plt.ylabel("Weight")
plt.grid()
plt.legend(loc = "upper left")
plt.title("Fuel Loading Diagram")
plt.show()
