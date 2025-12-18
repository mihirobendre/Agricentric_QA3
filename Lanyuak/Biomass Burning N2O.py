import pandas as pd

# --------------------------------------------------------------------------------------------------
# Python Script: N₂O Emissions from Biomass Burning (VM0042 v2.1 Equations 33 & 59)
# --------------------------------------------------------------------------------------------------

area_ha = 4636  # ha

# ----------------------------
# BASELINE INPUTS
# ----------------------------

maintenance_c_in = 17.0898
carbon_fraction = 0.45

# Biomass burned
MB_bsl = maintenance_c_in/carbon_fraction  # tC DM/ha --> t DM/ha

# Combustion factor for agricultural residue type c (proportion of prefire fuel biomass consumed)
CF = 0.05

# >> From IPCC 2006 GL Vol 4, Ch 2, Table 2.5 (Andreae & Merlet, 2001).
EF_N2O = 0.00021  # kg/kg DM

# >> IPCC AR6 WGI Table 7.15: 100‑yr GWP including climate-carbon feedbacks.
# >> See: https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7 (#Table7.15)
GWP_N2O = 273  # unitless

# Convert N₂O emissions to t CO2e per ha
n2o_co2e_bsl_per_ha = (GWP_N2O * MB_bsl * CF * EF_N2O)


# ----------------------------
# PROJECT INPUTS
# ----------------------------


maintenance_c_in = 17.0898
carbon_fraction = 0.45

# Biomass burned
MB_prj = maintenance_c_in/carbon_fraction  # tC DM/ha --> t DM/ha

# Combustion factor for agricultural residue type c (proportion of prefire fuel biomass consumed)
CF = 0.01

# >> From IPCC 2006 GL Vol 4, Ch 2, Table 2.5 (Andreae & Merlet, 2001).
EF_N2O = 0.00021  # kg/kg DM

# >> IPCC AR6 WGI Table 7.15: 100‑yr GWP including climate-carbon feedbacks.
# >> See: https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7 (#Table7.15)
GWP_N2O = 273  # unitless

# Convert N₂O emissions to t CO2e per ha
n2o_co2e_prj_per_ha = (GWP_N2O * MB_prj * CF * EF_N2O)


# ----------------------------
# TOTALS
# ----------------------------

# Total baseline emissions
total_n2o_co2e_baseline = n2o_co2e_bsl_per_ha * area_ha

# Total project emissions
total_n2o_co2e_project = n2o_co2e_prj_per_ha * area_ha

# Emission reduction achieved
total_n2o_reduction = total_n2o_co2e_baseline - total_n2o_co2e_project

print(f"Total N2O emissions (baseline) = {total_n2o_co2e_baseline:.8f}")

print(f"Total N2O emissions (project) = {total_n2o_co2e_project:.8f}")


