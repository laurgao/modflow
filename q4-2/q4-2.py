import flopy
import matplotlib.pyplot as plt
import numpy as np

workspace = "./"
# Model parameters
nlay = 3
nrow = 101
ncol = 101
delr = 10.0
delc = 10.0
top = 100.0
# botm = [70.0, 60.0, 0.0]
# botm = [80, 70, 60]  # Bottom elevation of each layer
botm = [70, 60, 0]
# botm = [90, 80, 70]  # Bottom elevation of each layer
kh = 20.0
kv = 20.0
initial_head = 150.0
radius = 50

# Time parameters
nper = 1
nstp = 10
perlen = 1.04
steady = [False]

# Pumping well parameters
# Q = -58000.0 / 86400.0  # Convert to ft^3/s
Q = -58000.0
wel_loc = (1, int(nrow / 2), int(ncol / 2))

# Create the model
sim = flopy.mf6.MFSimulation(sim_name="partpen", exe_name="mf6", version="mf6", sim_ws=workspace)
tdis = flopy.mf6.ModflowTdis(sim, time_units="DAYS", nper=nper, perioddata=[(perlen, nstp, 1.0)])

# Solution group
ims = flopy.mf6.ModflowIms(sim)

# Create the groundwater flow (gwf) model
model_nam_file = "ppw"
gwf = flopy.mf6.ModflowGwf(sim, modelname=model_nam_file, save_flows=True)

# Create the discretization package
dis = flopy.mf6.ModflowGwfdis(gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm)

# Initial conditions
ic = flopy.mf6.ModflowGwfic(gwf, strt=initial_head)

# Node property flow package
npf = flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=kh, k33=kv)
# npf = flopy.mf6.ModflowGwfnpf(gwf, save_specific_discharge=True, icelltype=0, k=kh)

# Storage package
# changing this changed it :o
# sto = flopy.mf6.ModflowGwfsto(gwf, ss=0.0, sy=0.0, transient={0: True})
sto = flopy.mf6.ModflowGwfsto(gwf, ss=0.01, sy=0, iconvert=0)
# sto = flopy.mf6.ModflowGwfsto(gwf, ss=1e-6, sy=0.1, iconvert=0)


# Create the well package
wel_spd = {0: [[wel_loc, Q]]}
wel = flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)

# Output control
oc = flopy.mf6.ModflowGwfoc(
    gwf,
    budget_filerecord="ppw.cbc",
    head_filerecord="ppw.hds",
    saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
)

# Write the datasets
sim.write_simulation()

# Run the simulation
success, buff = sim.run_simulation()
if not success:
    raise Exception("MODFLOW 6 did not terminate normally.")

# Read and plot the results
headfile = "ppw.hds"
hds = flopy.utils.HeadFile(headfile)
head = hds.get_data(totim=1.04)

# Plot the head distribution
plt.figure(figsize=(10, 8))
extent = (0, ncol * delr, 0, nrow * delc)

drawdown = initial_head - head

obs_drawdown = drawdown[1, wel_loc[1] + int(radius / delr), wel_loc[2]]
print(obs_drawdown)
plt.imshow(drawdown[1, :, :], extent=extent, cmap="viridis", origin="lower")
plt.colorbar(label="Head (ft)")
plt.title("Hydraulic Head Distribution after 1.04 days")
plt.xlabel("Distance (ft)")
plt.ylabel("Distance (ft)")
plt.savefig("drawdown.png")
