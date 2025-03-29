import numpy as np
import matplotlib.pyplot as plt

#######################################
#GENERAL INPUTS
######################################
x_ac = 0.32 # Aerodynamic center

l_h = 20 # Distance between aerodynamic center and horizontal tail
mac = 2.2 # Mean aerodynamic chord
VhV = 1 # Velocity ratio horizontal tail to aircraft

SM = 0.05 # Safety margin

#######################################
# STATIC STABILITY FUNCTION
#######################################


Cla_h = 7.8 # Lift coefficient horizontal tail
Cla_Ah_stat = 5.2 # Lift coefficient aircraft without horizontal tail stat cond
deda = 0.3 # Downwash gradient


#######################################
# CONTRALLABILITY INPUTS
#######################################
CL_h = -0.8
Cm_ac = -0.25 # Moment coefficient aircraft
Cla_ah_cont = 5.4 # Lift coefficient aircraft with horizontal tail cont cond


def static_stability(x_cg):

    gradient = 1/((Cla_h/Cla_Ah_stat)*(1-deda)*(l_h/mac)*VhV**2)

    ShS = gradient * (x_cg - x_ac + SM)
    return ShS

def controllability(x_cg):

    gradient = 1/((CL_h/Cla_ah_cont)*(l_h/mac)*VhV**2)

    ShS = gradient * (x_cg - x_ac + Cm_ac/Cla_ah_cont)
    return ShS

x_cg_values = np.linspace(0, 1, 100)

# Calculate Sh/S with and without safety margin
static_with_SM = [static_stability(x_cg) for x_cg in x_cg_values]
SM = 0  # Temporarily set safety margin to 0
static_without_SM = [static_stability(x_cg) for x_cg in x_cg_values]

# Calculate controllability
controllability_values = [controllability(x_cg) for x_cg in x_cg_values]

# Plot the results
plt.figure()
plt.plot(x_cg_values, static_with_SM, label="Stick Fixed With Safety Margin")
plt.plot(x_cg_values, static_without_SM, label="Stick Fixed Without Safety Margin", linestyle='--')
plt.plot(x_cg_values, controllability_values, label="Controllability")
plt.axhline(y=0.19, color='k', linestyle='--', label="ShS = 0.19")
plt.xlabel("x_cg (Center of Gravity)")
plt.ylabel("Sh/S (Stability Margin)")
plt.ylim(0, 0.3)
plt.xlim(0, 1)
plt.legend()
plt.grid()
plt.show()

