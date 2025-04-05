import numpy as np
import matplotlib.pyplot as plt
from copy import copy
import loaddiagram_improved as ld

plot = True
save = False

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
MTOW = 23000 #kg
MPW = 6270 #kg
MFW = 5000 #kg
OEW = 14268.58 #kg

#static group weights and cgs
fs_group_weight = 8327.65 #kg
fs_group_xcg = 12.96525666 #m
wing_group_weight = 5940.92553 #kg
wing_group_xcg = 11.40063778 #m

#PAX weight and balance
avg_pax_weight = 80 #kg including luggage
column_pax = 14 # pax per column
window_columns = 2
aisle_columns = 2
num_pax = column_pax*(window_columns+aisle_columns)

first_row_xcg = 8.494-2.362 # m, from Weight and Balance Manual page DSC 4. p.6
seat_pitch = conversion_in_m(29) #m


#generate seat cg locations
last_row_xcg = (column_pax-1)*seat_pitch+first_row_xcg
pax_cgs = np.linspace(first_row_xcg,last_row_xcg,column_pax)

#fuel cg
fuel_xcg = 14.43-2.362 #m ,from DSC 2. p.4

#cargo cg, mass
cargo_fw_xcg = 6.697-2.362 #m, same for left and right compartment, from https://pdfcoffee.com/weight-n-balance-atr-42-72-3-pdf-free.html, p.10
cargo_aft_xcg = 23.896-2.362 #m, see source above

cargo_fw_capacity = 928 #kg, from https://pdfcoffee.com/weight-n-balance-atr-42-72-3-pdf-free.html, p.10(31)
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
        weigths = running[1]-Wmin+OEW
        series.append(np.vstack([cgs,weigths]))
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
Wmin = float(Structure[1])

#fuel loading

fuel_weight_max = np.min([MFW,MTOW-OEW-cargo_aft_capacity-cargo_fw_capacity-num_pax*avg_pax_weight])

fuel_weights = np.linspace(0,fuel_weight_max)
fuel_moments = fuel_weights*fuel_xcg

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

Fuel1 = Group(np.vstack([fuel_moments,fuel_weights]),"Fuel","lime")
Fuel2 = copy(Fuel1)
Fuel2.name = None

NullGroup = Group(np.zeros((2,1)),None)
print(f"Empty mass cg: {float(Structure[0]/Structure[1])} m = {float(conversion_m_LEMAC_percent([np.array([[Structure[0]/Structure[1]],[Structure[1]]]),])[0][0])} LEMAC")
#assembly

#cargo, pax, fuel
series01_raw, names01, colors01 = assemble(CargoF1,CargoA1,Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,Fuel1,base=Structure)
series02_raw, names02, colors02 = assemble(CargoA2,CargoF2,Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,Fuel2,base=Structure)

#fuel,cargo,pax
series11_raw, names11, colors11 = assemble(Fuel1,CargoF1,CargoA1,Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,base=Structure)
series12_raw, names12, colors12 = assemble(Fuel2,CargoA2,CargoF2,Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,base=Structure)

#pax,fuel,cargo
series21_raw, names21, colors21 = assemble(Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,Fuel1,CargoF1,CargoA1,base=Structure)
series22_raw, names22, colors22 = assemble(Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,Fuel2,CargoA2,CargoF2,base=Structure)

#fuel,pax,cargo
series31_raw, names31, colors31 = assemble(Fuel1,Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,CargoA1,CargoF1,base=Structure)
series32_raw, names32, colors32 = assemble(Fuel2,Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,CargoF2,CargoA2,base=Structure)

#cargo, fuel, pax
series41_raw, names41, colors41 = assemble(CargoF1,CargoA1,Fuel1,Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,base=Structure)
series42_raw, names42, colors42 = assemble(CargoA2,CargoF2,Fuel2,Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,base=Structure)

#pax,cargo,fuel
series51_raw, names51, colors51 = assemble(Pax_window_fw_to_aft,Pax_aisle_fw_to_aft,CargoF1,CargoA1,Fuel1,base=Structure)
series52_raw, names52, colors52 = assemble(Pax_window_aft_to_fw,Pax_aisle_aft_to_fw,CargoA2,CargoF2,Fuel2,base=Structure)


series01 = conversion_m_LEMAC_percent(series01_raw)
series02 = conversion_m_LEMAC_percent(series02_raw)

series11 = conversion_m_LEMAC_percent(series11_raw)
series12 = conversion_m_LEMAC_percent(series12_raw)

series21 = conversion_m_LEMAC_percent(series21_raw)
series22 = conversion_m_LEMAC_percent(series22_raw)

series31 = conversion_m_LEMAC_percent(series31_raw)
series32 = conversion_m_LEMAC_percent(series32_raw)

series41 = conversion_m_LEMAC_percent(series41_raw)
series42 = conversion_m_LEMAC_percent(series42_raw)

series51 = conversion_m_LEMAC_percent(series51_raw)
series52 = conversion_m_LEMAC_percent(series52_raw)

counter = 1
def plot_loaddiagram(series1,series2,names1,names2,colors1,colors2,save=False,saveName=None):
#plotting
    global counter
    cg_min, cg_max = extract_extreme_cgs(series1,series2)
    cg_min2, cg_max2 = extract_extreme_cgs(ld.series51,ld.series52)
    print(f'#{counter}: Minimum cg: {cg_min-0.02}\tMaximum cg: {cg_max+0.02}')
    counter += 1
    plt.figure(figsize=(10, 7))  # Adjust figure size
    
    # Plot the loading diagrams
    for i in range(len(series1)):
        plt.plot(series1[i][0], series1[i][1], label=names1[i],color=colors1[i])
        plt.plot(series2[i][0], series2[i][1], label=names2[i],color=colors2[i])
        plt.plot(ld.series51[i][0], ld.series51[i][1], color='gray', alpha=0.5)
        plt.plot(ld.series52[i][0], ld.series52[i][1], color='gray', alpha=0.5)
        
    plt.plot([], [], label='ATR 72-600', color='gray', alpha=0.5)
    plt.gca().set_aspect('auto')

    x_margin = 0.15 *(cg_max - cg_min)  # 15% extra space on x-axis
    y_margin = 0.1 * (MTOW - OEW)  # 10% extra space on y-axis

    plt.xlim(np.min([cg_min, cg_min2]) - x_margin, np.max([cg_max, cg_max2]) + x_margin)
    plt.ylim(OEW - y_margin, MTOW + y_margin)

    # Plot CG limits with labels
    plt.axhline(OEW, linestyle='dashed', color='k', alpha=0.5)
    plt.text(0.3*(cg_min+cg_max),OEW+y_margin/5, "OEW", color='k', va='bottom', fontsize=12)

    plt.axhline(MTOW, linestyle='dashed', color='k', alpha=0.5)
    plt.text(0.5*(cg_min+cg_max),MTOW+y_margin/5, "MTOW", color='k', va='bottom', fontsize=12)

    plt.axhline(np.max(series1[-2]), linestyle='dashed', color='k', alpha=0.5)
    plt.text(0.5*(cg_min+cg_max),np.max(series1[-2])+y_margin/5, "MZFW", color='k', va='bottom', fontsize=12)

    plt.axvline(cg_min, linestyle='dashed', color='k', alpha=0.5)
    plt.text(cg_min+x_margin/6, 0.5*(OEW+MTOW)-1000, "Min CG", color='k', ha='left', fontsize=12,rotation=-90)

    plt.axvline(cg_max, linestyle='dashed', color='k', alpha=0.5)
    plt.text(cg_max-x_margin/6, 0.5*(OEW+MTOW)-1000, "Max CG", color='k', ha='right', fontsize=12,rotation=-90)

    plt.axvline(cg_min-0.02, linestyle='dashed', color='k', alpha=0.5)
    plt.text(cg_min-0.02-x_margin/6, 0.5*(OEW+MTOW)-1000, "-2% margin", color='k', ha='right', fontsize=12,rotation=-90)

    plt.axvline(cg_max+0.02, linestyle='dashed', color='k', alpha=0.5)
    plt.text(cg_max+0.02+x_margin/6, 0.5*(OEW+MTOW)-1000, "+2% margin", color='k', ha='left', fontsize=12,rotation=-90)

    print(f"Min cg: {cg_min-0.02}\tMax cg: {cg_max+0.02}")

    plt.grid()
    plt.ylabel("Loaded Mass [kg]")
    plt.xlabel("CG Location [%LEMAC]")
    #plt.title("Loading diagram")
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()

    if save:
        plt.savefig(f'{saveName}.pdf')

if __name__=="__main__":
    #plot_loaddiagram(series01,series02,names01,names02,colors01,colors02,save=True,saveName='figures/loaddiagram_HE')
    #plot_loaddiagram(series11,series12,names11,names12,colors11,colors12)
    #plot_loaddiagram(series21,series22,names21,names22,colors21,colors22)
    #plot_loaddiagram(series31,series32,names31,names32,colors31,colors32)
    #plot_loaddiagram(series41,series42,names41,names42,colors41,colors42)
    plot_loaddiagram(series51,series52,names51,names52,colors51,colors52,save=True,saveName='figures/loaddiagram_extreme_HE')
    #plot_loaddiagram(series01,series52,names01,names52,colors01,colors52)
    if plot:
        plt.show()


"""
    # Plot the pie chart with MFW, MPW
    data = [[OEW,MTOW-OEW-MFW,MFW],[OEW,MPW,MTOW-OEW-MPW]]
    cols = ['#4f6d7a',"#d62828","#f77f00"]


    plt.figure(2)
    plt.pie(data[0],labels=["OEW","PW","MFW"],startangle=90,counterclock=False,
            autopct='%1.1f%%',colors=cols, textprops={'size': 'larger'},
        pctdistance=1.25, labeldistance=0.6)
    plt.savefig("MFW.eps")

    plt.figure(3)
    plt.pie(data[1],labels=["OEW","MPW","FW"],startangle=90,counterclock=False,
            autopct='%1.1f%%', colors=cols, textprops={'size': 'larger'},
        pctdistance=1.25, labeldistance=0.6)
    plt.savefig("MPW.eps")
"""
    #TODO: do absolute weight too