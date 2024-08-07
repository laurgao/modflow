# Import necessary packages
import flopy
from flopy.mf6.modflow import ModflowGwfic

# Create the model
name = "confined_aquifer"
model_ws = "./confined_aquifer"
sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=model_ws, exe_name="mf6")
tdis = flopy.mf6.ModflowTdis(sim)
ims = flopy.mf6.ModflowIms(sim)
gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)


# Initial Conditions
ic = ModflowGwfic(gwf, strt=140.0)  # Starting head of 140 ft everywhere

# Model grid
nlay, nrow, ncol = 1, 201, 201
delr = delc = 200  # Cell size in feet
top = 83.0
botm = 20.0

# Create discretization package
dis = flopy.mf6.ModflowGwfdis(gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm)


# Hydraulic conductivity (ft/day)
k = 50.0

# Storage coefficient
sc = 0.0030

# Specific storage (1/ft)
ss = sc / (top - botm)

# Create node property flow package
npf = flopy.mf6.ModflowGwfnpf(gwf, k=k, save_specific_discharge=True)

# Create storage package
# Create storage package
sto = flopy.mf6.ModflowGwfsto(
    gwf,
    ss=ss,
    transient={0: False, 1: True},  # First period steady, second transient
    steady_state={0: True, 1: False},  # First period steady, second transient
)

# Constant head for the river (west boundary)
# chd_spd = []
# for i in range(nrow):
#     chd_spd.append([(0, i, 0), 140.0])  # Layer, row, column, head
chd_spd = []
for i in range(nrow):
    chd_spd.append([(0, i, 0), 140.0])  # This sets only the westernmost column to constant head

chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd_spd)

# No-flow boundaries are default in MODFLOW 6

# Pumping well (50,000 gallons per day = 6,684.7 ft³/day)
wel_spd = {1: [[(0, 100, 10), -6684.7]]}  # Pumping well
# wel_spd = {1: [[(0, 100, 10), -6684.7]]}  # Layer, row, column, pumping rate
wel = flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)


# Stress Periods
perlen = [0.00001, 365.0]
nstp = [1, 20]
tsmult = [1.0, 1.0]

# Create time discretization package
tdis = flopy.mf6.ModflowTdis(
    sim,
    nper=2,
    perioddata=list(zip(perlen, nstp, tsmult)),
)

# Create IMS package
ims = flopy.mf6.ModflowIms(
    sim,
    print_option="SUMMARY",
    outer_dvclose=1e-4,
    outer_maximum=500,
    under_relaxation="NONE",
    inner_maximum=100,
    inner_dvclose=1e-4,
    rcloserecord=0.001,
    linear_acceleration="CG",
    scaling_method="NONE",
    reordering_method="NONE",
    relaxation_factor=0.97,
)

# Create observation package
# Create observation package
obs_data = {"head_obs.csv": [("obs1", "HEAD", (0, 100, 6))]}  # Name, observation type, (layer, row, column)
# obs_data = {"head_obs.csv": [("obs1", "HEAD", (0, 100, 14))]}  # Observation well

obs = flopy.mf6.ModflowUtlobs(gwf, filename="confined_aquifer.obs", continuous=obs_data)

# Write input files
sim.write_simulation()

# Run the model
success, buff = sim.run_simulation()


print(f"Hydraulic conductivity: {k} ft/day")
print(f"Storage coefficient: {sc}")
print(f"Aquifer thickness: {top - botm} ft")
print(f"Grid cell size: {delr} ft")

print(f"Number of constant head cells: {len(chd_spd)}")
print(f"Constant head value: {chd_spd[0][1]} ft")

# Check well package data
print("Well package data:")
for sp, data in wel_spd.items():
    print(f"  Stress period {sp}:")
    print(f"    Data: {data}")

# Check observation well location
print(
    f"Observation well location: Layer {obs_data['head_obs.csv'][0][2][0]}, Row {obs_data['head_obs.csv'][0][2][1]}, Column {obs_data['head_obs.csv'][0][2][2]}"
)

# Print model grid dimensions
print(f"Model grid dimensions: {nlay} layer(s), {nrow} rows, {ncol} columns")
print(f"Model domain size: {delr * ncol} ft (x-direction) by {delc * nrow} ft (y-direction)")


if success:
    print("Model run successfully completed.")
else:
    print("Model run failed.")
