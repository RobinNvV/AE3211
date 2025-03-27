import numpy as np
import matplotlib.pyplot as plt
from copy import copy

#Calculate LEMAC position in ac ref. sys.
xcg_wing = 12.11714 #m
xcg_mac = 0.87514 #m, distance from LEMAC
LEMAC = xcg_wing-xcg_mac #m, in ac ref. sys.

xcg_lemac = 0.38 #-, distance as % of MAC
MAC = xcg_mac/xcg_lemac #m


def conversion_in_m(inch):
    "Converts inches to meters."
    return 0.0254*inch

def conversion_m_LEMAC_percent(data,MAC=MAC,LEMAC=LEMAC):
    """
    Converts data measured in meters ac ref. sys. to fraction of MAC in LEMAC ref. sys.
    Parameters:
    data*: list of np.ndarrays with lengths in first row
    Returns:
    data* with first row converted to %LEMAC
    """

    out = data
    for i, series in enumerate(out):
        out[i] = np.vstack([(series[0] - LEMAC) / MAC, series[1]]) 
        
    return out

#All calculations in [xcg]=m from nose

#weight limits
MTOW = 22800 #kg
MPW = 7550 #kg
MFW = 5000 #kg
OEW = 13450 #kg

#static group weights and cgs
fs_group_weight = 6634.8 #kg
fs_group_xcg = 12.11401353 #m
wing_group_weight = 6543.6 #kg
wing_group_xcg = 11.46857443 #m

#PAX weight and balance
avg_pax_weight = 80 #kg including luggage
column_pax = 18 # pax per column
window_columns = 2
aisle_columns = 2
num_pax = column_pax*(window_columns+aisle_columns)

first_row_xcg = 8.494 # m, from Weight and Balance Manual page DSC 4. p.6
seat_pitch = conversion_in_m(29) #m


#generate seat cg locations
last_row_xcg = (column_pax-1)*seat_pitch+first_row_xcg
pax_cgs = np.linspace(first_row_xcg,last_row_xcg,column_pax)

#fuel cg
fuel_xcg = 14.43 #m ,from DSC 2. p.4

#cargo cg, mass
cargo_fw_xcg = 6.697 #m, same for left and right compartment, from https://pdfcoffee.com/weight-n-balance-atr-42-72-3-pdf-free.html, p.10
cargo_aft_xcg = 23.896 #m, see source above

cargo_fw_capacity = 928 #kg, from https://pdfcoffee.com/weight-n-balance-atr-42-72-3-pdf-free.html, p.10
cargo_aft_capacity = 768 #kg see source above

#pax loading, for one column
pax_load_index_fw_to_aft = np.tri(column_pax) #loading indices
pax_load_index_aft_to_fw = np.flip(pax_load_index_fw_to_aft,axis=1)

pax_loads_fw_to_aft = avg_pax_weight*pax_cgs*pax_load_index_fw_to_aft #2D array with moments of each passenger in loading condition
pax_loads_aft_to_fw = avg_pax_weight*pax_cgs*pax_load_index_aft_to_fw

pax_moments_fw_to_aft = np.sum(pax_loads_fw_to_aft,axis=1)
pax_moments_fw_to_aft = np.hstack([np.zeros(1),pax_moments_fw_to_aft])
pax_moments_aft_to_fw = np.sum(pax_loads_aft_to_fw,axis=1)
pax_moments_aft_to_fw = np.hstack([np.zeros(1),pax_moments_aft_to_fw])

pax_weights = np.sum(avg_pax_weight*pax_load_index_fw_to_aft,axis=1)
pax_weights = np.hstack([np.zeros(1),pax_weights])

#cargo loading

cargo_fw_weights = np.linspace(0,cargo_fw_capacity)
cargo_aft_weights = np.linspace(0,cargo_aft_capacity)

cargo_fw_moments =  cargo_fw_weights*cargo_fw_xcg
cargo_aft_moments =  cargo_aft_weights*cargo_aft_xcg

#fuel loading

fuel_weight_max = np.min([MFW,MTOW-OEW-cargo_aft_capacity-cargo_fw_capacity-num_pax*avg_pax_weight])

fuel_weights = np.linspace(0,fuel_weight_max)
fuel_moments = fuel_weights*fuel_xcg

class Group:
    
    def __init__(self,data,name,color=None):
        self.data = data
        self.name = name
        self.color = color

def assemble(*groups:Group,base:None|np.ndarray=None):
    """
    Returns cg location(s) for loading groups specified by groups.
    Parameters:
    groups*: size 2xN, first row containing moments, second row containing weights
    Returns: list of np.ndarrays with weight as the first row and cgs as second.
    """
    series = []
    names = []
    colors = []
    if base is None:
        base = np.zeros((2,1))

    for group in groups:
        running = group.data + base
        base = running[:,-1].reshape(2,1)
        cgs = running[0]/running[1]
        series.append(np.vstack([cgs,running[1]]))
        names.append(group.name)
        colors.append(group.color)

    return series, names, colors
    
def extract_extreme_cgs(*series):
    """
    Returns minimum and maximum cg. locations of a data series.
    """
    temp_min = []
    temp_max = []
    for s in series:
        for arr in s:
            loc_min = np.min(arr[0])
            loc_max = np.max(arr[0])
            temp_min.append(loc_min)
            temp_max.append(loc_max)
    
    return min(temp_min), max(temp_max)

#Groups    

#static    
Fuselage = np.vstack([fs_group_weight*fs_group_xcg,fs_group_weight])
Wing = np.vstack([wing_group_weight*wing_group_xcg,wing_group_weight])
Structure = Fuselage + Wing #acts as base
Structure[1] = OEW #set base weight manually to OEW

#dynamic
CargoF1 = Group(np.vstack([cargo_fw_moments,cargo_fw_weights]),"Load forward compartment",'maroon')
CargoA1 = Group(np.vstack([cargo_aft_moments,cargo_aft_weights]),"Load aft compartment",'mediumslateblue')
CargoF2 = copy(CargoF1)
CargoF2.name = None
CargoA2 = copy(CargoA1)
CargoA2.name = None

Pax_window_fw_to_aft = Group(window_columns*np.vstack([pax_moments_fw_to_aft,pax_weights]),"Window seats, front to back")
Pax_aisle_fw_to_aft = Group(aisle_columns*np.vstack([pax_moments_fw_to_aft,pax_weights]),"Aisle seats, front to back")
Pax_window_aft_to_fw = Group(window_columns*np.vstack([pax_moments_aft_to_fw,pax_weights]),"Window seats, back to front")
Pax_aisle_aft_to_fw = Group(aisle_columns*np.vstack([pax_moments_aft_to_fw,pax_weights]),"Aisle seats, back to front")

Fuel = Group(np.vstack([fuel_moments,fuel_weights]),"Fuel")

NullGroup = Group(np.zeros((2,1)),None)

#assembly
series01_raw, names01, colors01 = assemble(CargoF1,CargoA1,Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,Fuel,base=Structure)
series02_raw, names02, colors02 = assemble(CargoA2,CargoF2,Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,NullGroup,base=Structure)

series01 = conversion_m_LEMAC_percent(series01_raw)
series02 = conversion_m_LEMAC_percent(series02_raw)

cg_min0, cg_max0 = extract_extreme_cgs(series01,series02)
print(f"Minimum cg: {cg_min0}\nMaximum cg: {cg_max0}")


#plotting

plt.figure(figsize=(13, 7))  # Adjust figure size

# Plot the loading diagrams
for i in range(len(series01)):
    plt.plot(series01[i][0], series01[i][1], label=names01[i],color=colors01[i])
    plt.plot(series02[i][0], series02[i][1], label=names02[i],color=colors02[i])

x_margin = 0.15 * (cg_max0 - cg_min0)  # 15% extra space on x-axis
y_margin = 0.1 * (MTOW - OEW)  # 10% extra space on y-axis

plt.xlim(cg_min0 - x_margin, cg_max0 + x_margin)
plt.ylim(OEW - y_margin, MTOW + y_margin)

# Plot CG limits with labels
plt.axhline(OEW, linestyle='dashed', color='k', alpha=0.5)
plt.text(0.5*(cg_min0+cg_max0),OEW-y_margin/5, "OEW", color='k', va='top', fontsize=12)

plt.axhline(MTOW, linestyle='dashed', color='k', alpha=0.5)
plt.text(0.5*(cg_min0+cg_max0),MTOW+y_margin/5, "MTOW", color='k', va='bottom', fontsize=12)

plt.axvline(cg_min0, linestyle='dashed', color='k', alpha=0.5)
plt.text(cg_min0+x_margin/6, 0.5*(OEW+MTOW)-1000, "Min CG", color='k', ha='left', fontsize=12,rotation=-90)

plt.axvline(cg_max0, linestyle='dashed', color='k', alpha=0.5)
plt.text(cg_max0-x_margin/6, 0.5*(OEW+MTOW)-1000, "Max CG", color='k', ha='right', fontsize=12,rotation=-90)

plt.axvline(cg_min0-0.02, linestyle='dashed', color='k', alpha=0.5)
plt.text(cg_min0-0.02-x_margin/6, 0.5*(OEW+MTOW)-1000, "-2% margin", color='k', ha='right', fontsize=12,rotation=-90)

plt.axvline(cg_max0+0.02, linestyle='dashed', color='k', alpha=0.5)
plt.text(cg_max0+0.02+x_margin/6, 0.5*(OEW+MTOW)-1000, "+2% margin", color='k', ha='left', fontsize=12,rotation=-90)

plt.grid()
plt.ylabel("Loaded Mass [kg]")
plt.xlabel("CG Location [%LEMAC]")
plt.title("Loading diagram")
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.show()

