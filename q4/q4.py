import os

import flopy
import matplotlib.pyplot as plt

# Model parameters
n = 101  # Number of grid cells

nlay = 3  # Number of layers
nrow = n  # Number of rows
ncol = n  # Number of columns
delr = 10  # Cell size in x-direction (ft)
delc = 10  # Cell size in y-direction (ft)

top = 100  # Top of the model (ft MSL)
botm = [40, 30, 0]
# botm = [70, 60, 0]
initial_head = 150  # Initial head (ft)
K = 20  # Hydraulic conductivity (ft/day)
Q = -58000  # Pumping rate (ft^3/day), negative for extraction
S = 0.01  # Specific storage

# Stress period and time step information
perlen = 1.04  # Stress period length (days)
nstp = 10  # Number of time steps

# Create the model
model_name = "partpen"  # Shortened name
model_ws = "./"  # Model workspace
sim = flopy.mf6.MFSimulation(sim_name=model_name, sim_ws=model_ws, exe_name="mf6")
tdis = flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(perlen, nstp, 1.0)])
ims = flopy.mf6.ModflowIms(sim)
gwf = flopy.mf6.ModflowGwf(sim, modelname=model_name, save_flows=True)

# Define discretization
dis = flopy.mf6.ModflowGwfdis(gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm)

# Define initial conditions
ic = flopy.mf6.ModflowGwfic(gwf, strt=initial_head)

# Define node property flow
npf = flopy.mf6.ModflowGwfnpf(gwf, save_specific_discharge=True, icelltype=0, k=K)

# Define storage
# sto = flopy.mf6.ModflowGwfsto(gwf, ss=1e-6, sy=0.1, iconvert=0)
sto = flopy.mf6.ModflowGwfsto(gwf, ss=S, sy=0, iconvert=0)


# Define well package
wel_loc = (1, int(nrow / 2), int(ncol / 2))
wel_spd = [[wel_loc, Q]]  # Well in middle layer, center of grid
wel = flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)

# Define constant head boundaries (optional, set to initial head)
chd_spd = []
for layer in range(nlay):
    for row in range(nrow):
        if row != 0 and row != nrow - 1:  # Skip corners
            chd_spd.append([(layer, row, 0), initial_head])
            chd_spd.append([(layer, row, ncol - 1), initial_head])
    for col in range(1, ncol - 1):  # Skip first and last columns
        chd_spd.append([(layer, 0, col), initial_head])
        chd_spd.append([(layer, nrow - 1, col), initial_head])
chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd_spd)

# Define output control
oc = flopy.mf6.ModflowGwfoc(
    gwf,
    head_filerecord=f"{model_name}.hds",
    budget_filerecord=f"{model_name}.cbc",
    saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
)

# Write the model files
sim.write_simulation()

# Run the model
success, buff = sim.run_simulation()

if not success:
    print("MODFLOW 6 did not terminate normally.")
    print(buff)
else:
    print("MODFLOW 6 ran successfully.")

    # Check if output file exists
    if not os.path.exists(f"{model_name}.hds"):
        print(f"Error: {model_name}.hds file not found.")
    else:
        # Read the output
        head = flopy.utils.HeadFile(f"{model_name}.hds")
        head_data = head.get_data()

        # Calculate drawdown
        drawdown = initial_head - head_data

        obs_drawdown = drawdown[1, wel_loc[1] + 5, wel_loc[2]]  # Middle layer, 50 ft away.
        print(f"MODFLOW drawdown at observation well: {obs_drawdown:.2f} ft")

        # Plot the drawdown
        plt.imshow(drawdown[1, :, :], cmap="viridis_r")
        plt.colorbar(label="Drawdown (ft)")
        plt.title("Drawdown in Middle Layer")
        plt.xlabel("Column")
        plt.ylabel("Row")
        plt.savefig("drawdown.png")

# Compare with Hantush analysis
hantush_drawdown = 12.49
print(f"Hantush drawdown at observation well: {hantush_drawdown:.2f} ft")
print(f"Difference: {abs(obs_drawdown - hantush_drawdown):.2f} ft")
