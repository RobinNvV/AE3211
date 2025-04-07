import numpy as np
import matplotlib.pyplot as plt
import loaddiagram_HE as lh

#######################################
#GENERAL INPUTS
######################################


l_h = 13.38 # Distance between aerodynamic center and horizontal tail
mac = 2.303 # Mean aerodynamic chord
VhV = 1 # Velocity ratio horizontal tail to aircraft

SM = 0.05 # Safety margin

#######################################
# STATIC STABILITY FUNCTION
#######################################

                #ATR72-600                      # ATR72-HE
Cla_h = [       4.233885381,                    4.233885381] # Lift coefficient horizontal tail
Cla_Ah_stat = [ 6.199435891,                    6.375872992] # Lift coefficient aircraft without horizontal tail stat cond
deda = [        0.265558523,                    0.227824951] # Downwash gradient
x_ac_s =[       0.058106547,                    0.039608989]# Aerodynamic center

#######################################
# CONTRALLABILITY INPUTS
#######################################
                #ATR72-600                      # ATR72-HE
CL_h = [        -0.8,                           -0.8]
Cm_ac = [       -1.068999715,                   -1.093012671] # Moment coefficient aircraft
Cl_ah_cont = [  1.890335912,                    1.890335912] # Lift coefficient aircraft with horizontal tail cont cond
x_ac_c =[       0.042576066,                    0.022027301] # Aerodynamic center


def scissorplot(x_ac_c, x_ac_s, l_h, mac, VhV, SM, Cla_h, Cla_Ah_stat, deda, CL_h, Cm_ac, Cla_ah_cont, n):
    def static_stability(x_cg, SM):

        gradient = 1/((Cla_h/Cla_Ah_stat)*(1-deda)*(l_h/mac)*VhV**2)

        ShS = gradient * (x_cg - x_ac_s + SM)
        return ShS

    def controllability(x_cg):

        gradient = 1/((CL_h/Cla_ah_cont)*(l_h/mac)*VhV**2)

        ShS = gradient * (x_cg - x_ac_c + Cm_ac/Cla_ah_cont)
        return ShS

    x_cg_values = np.linspace(0, 1, 1000)

    # Calculate Sh/S with and without safety margin
    static_with_SM = [static_stability(x_cg, SM) for x_cg in x_cg_values]

    static_without_SM = [static_stability(x_cg, 0) for x_cg in x_cg_values]

    # Calculate controllability
    controllability_values = [controllability(x_cg) for x_cg in x_cg_values]

    cg_excursion = x_cg_values[np.all([np.array(controllability_values) < 0.19, np.array(static_with_SM) < 0.19], axis=0).astype(bool)]



    # Plot the results
    plt.figure(figsize=(12, 8), constrained_layout=True)

    ylim = [0, 0.4]

    plt.plot(x_cg_values, static_with_SM, label="Stick Fixed With Safety Margin")
    plt.plot(x_cg_values, static_without_SM, label="Stick Fixed Without Safety Margin", linestyle='--')
    plt.plot(x_cg_values, controllability_values, label="Controllability")

    plt.plot(cg_excursion, 0.19*np.ones(cg_excursion.size), color='k', linestyle='--', label="$S_h/S$ = 0.19")
    plt.text(cg_excursion[0]+0.02, 0.196, f'{cg_excursion[0]}'[:6], size=12,)
    plt.text(cg_excursion[-1], 0.196, f'{cg_excursion[-1]}'[:6], size=12, horizontalalignment= 'right')
    # Fill the stable regions with green
    stable_fill = np.maximum(np.array(static_with_SM), np.array(controllability_values))
    plt.fill_between(x_cg_values, stable_fill, ylim[1],
                     color='green', alpha=0.3, label="Stability Region")

    # Fill the unstable regions with red
    unstable_fill = np.array(static_without_SM)
    plt.fill_between(x_cg_values, unstable_fill, ylim[0],
                     color='red', alpha=0.3, label="Unstable Region")

    # Fill the uncontrollable regions with blue
    uncontrollable_fill = np.array(controllability_values)
    plt.fill_between(x_cg_values, uncontrollable_fill, ylim[0],
                     color='blue', alpha=0.3, label="Uncontrollable Region")

    cgmin = np.min([lh.extract_extreme_cgs(lh.series01, lh.series02)[0],lh.extract_extreme_cgs(lh.series51, lh.series52)[0]]) 
    cgmax = np.max([lh.extract_extreme_cgs(lh.series01, lh.series02)[1],lh.extract_extreme_cgs(lh.series51, lh.series52)[1]])
    plt.axvline(cgmin-0.02, color='k', linestyle='--')
    plt.axvline(cgmax+0.02, color='k', linestyle='--')
    plt.fill_betweenx(ylim, cgmin-0.02, cgmax+0.02, color='white', alpha=0.6, label="CG Range - ATR 72-HE")

    plt.axhline(np.interp(cgmax+0.02, x_cg_values, static_with_SM), 0, 1, color='gray', linewidth=2, linestyle='--')
    plt.axhline(np.interp(cgmax+0.02, x_cg_values, static_with_SM), cgmin-0.02, cgmax+0.02, color='navy', linewidth=6)
    plt.text((cgmax-cgmin)/2, np.interp(cgmax+0.02, x_cg_values, static_with_SM)+0.01, 'CG Range ATR 72-HE', color='navy', size=12, weight='bold', horizontalalignment= 'left')
    plt.text(cgmin, np.interp(cgmax+0.02, x_cg_values, static_with_SM)+0.01, f'{cgmin-0.02}'[:6], size=12, weight='bold', color = 'navy', horizontalalignment= 'left')
    plt.text(cgmax, np.interp(cgmax+0.02, x_cg_values, static_with_SM)+0.01, f'{cgmax+0.02}'[:6], size=12, weight='bold', color = 'navy', horizontalalignment= 'right')
    plt.text(0.01, np.interp(cgmax+0.02, x_cg_values, static_with_SM)+0.005, f'{np.interp(cgmax+0.02, x_cg_values, static_with_SM)}'[:6], size=16, weight='bold', color = 'navy', verticalalignment='center', horizontalalignment= 'left')

    titles = ["ATR 72-600", "ATR 72-HE"]
    plt.title(f"Scissor Plot {titles[n]}", fontsize=13)
    plt.xlabel("$x_{cg}/\\bar{c}$ (Center of Gravity)", fontsize=13)
    plt.ylabel("$S_h/S$ (Surface Area Ratio)", fontsize=13)
    plt.ylim(ylim)
    plt.xlim(0, 1)
    plt.legend(loc='best')
    plt.grid()
    plt.savefig(f'figures/scissorplot{n}_new.pdf')
    plt.show()

n = 0
#scissorplot(x_ac_c[n], x_ac_s[n], l_h, mac, VhV, SM, Cla_h[n], Cla_Ah_stat[n], deda[n], CL_h[n], Cm_ac[n], Cl_ah_cont[n], n)
n = 1
scissorplot(x_ac_c[n], x_ac_s[n], l_h, mac, VhV, SM, Cla_h[n], Cla_Ah_stat[n], deda[n], CL_h[n], Cm_ac[n], Cl_ah_cont[n], n)

