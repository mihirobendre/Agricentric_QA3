# Full code for estimating N2O emissions from fertilizer use
# Following VM0042 v2.1 Equations 17–24 and 58

# Sources:
# - VM0042 v2.1 methodology document
# - IPCC 2019 Refinement to the 2006 Guidelines (Vol 4, Ch 11, Tables 11.1 & 11.3)
# - GWP value for N2O = 273 (IPCC AR6, 100-year time horizon)

# Assumptions:
# - Only synthetic fertilizers (urea and NPK 15-15-15) are considered in this example
# - N content for urea = 46%, for NPK 15-15-15 = 15%
# - Emission factors and fractions from IPCC 2019 Table 11.1 and Table 11.3
# - Project area is editable
# - Units are in t CO2e/ha



# Project area (ha)
percent_cropland = 1.0
actual_area = 15358

project_area_ha = actual_area * percent_cropland


#####################################################################
# BASELINE SCENARIO
#####################################################################

# -----------------------------
# Step 1: Define Input Variables
# -----------------------------

tons_per_kilo = 1/1000

# Fertilizer application (t/ha of fertilizer applied per year)
# ~400 t/ac NPK/yr ... 988 t/ha NPK/yr
urea_mass_t = 0 * tons_per_kilo * project_area_ha  # 
npk_mass_t = 988 * tons_per_kilo * project_area_ha # ~90 t/ac 
dap_mass_t = 0 * tons_per_kilo  * project_area_ha #
can_mass_t = 0 * tons_per_kilo  * project_area_ha #

# N content
urea_n_content = 0.46  # 46% N
npk_n_content = 0.15   # 15% N
dap_n_content = 0.18
can_n_content = 0.26

# Emission factors (from IPCC 2019 Table 11.1 and 11.3)
EF1 = 0.016  # Direct emissions factor for synthetic N in wet climates
EF4 = 0.014  # Emissions from volatilization in wet climates
EF5 = 0.011  # Emissions from leaching/runoff

FracGASF = 0.15  # Volatilization fraction for urea
FracLEACH = 0.24  # Leaching fraction in wet climates

# Global warming potential for N2O (AR6)
GWP_N2O = 273

# Molar mass conversion factor (N2O-N to N2O)
MM_conversion = 44 / 28

# ---------------------------------
# Step 2: Calculate Total N Applied
# Equations (20) and (21)
# ---------------------------------
N_urea_t = urea_mass_t * urea_n_content  # tonnes of N from urea
N_npk_t = npk_mass_t * npk_n_content     # tonnes of N from NPK
N_dap_t = dap_mass_t * dap_n_content
N_can_t = can_mass_t * can_n_content 

FSNbsl_it = N_urea_t + N_npk_t + N_dap_t + N_can_t # Total synthetic N applied

# ---------------------------------
# Step 3: Direct N2O emissions
# Equation (19)
# ---------------------------------
N2O_direct_total = FSNbsl_it * EF1 * MM_conversion * GWP_N2O
N2O_direct_per_ha = N2O_direct_total / project_area_ha

# ---------------------------------
# Step 4: Indirect N2O from Volatilization
# Equation (23)
# ---------------------------------
N_volatilized = FSNbsl_it * FracGASF
N2O_volat_total = N_volatilized * EF4 * MM_conversion * GWP_N2O
N2O_volat_per_ha = N2O_volat_total / project_area_ha

# ---------------------------------
# Step 5: Indirect N2O from Leaching/Runoff
# Equation (24)
# ---------------------------------
N_leached = FSNbsl_it * FracLEACH
N2O_leach_total = N_leached * EF5 * MM_conversion * GWP_N2O
N2O_leach_per_ha = N2O_leach_total / project_area_ha

# ---------------------------------
# Step 6: Total N2O from fertilizer use
# Equation (18): Total = Direct + Indirect
# Equation (58): Normalize by area
# ---------------------------------
N2O_total_t = N2O_direct_total + N2O_volat_total + N2O_leach_total
N2O_total_per_ha = N2O_total_t / project_area_ha

print("Baseline Scenario:")

# Output Results
results = {
    "Total N from Urea (t)": round(N_urea_t, 4),
    "Total N from NPK (t)": round(N_npk_t, 4),
    "Direct N2O Emissions (t CO2e)": round(N2O_direct_total, 4),
    "Indirect N2O from Volatilization (t CO2e)": round(N2O_volat_total, 4),
    "Indirect N2O from Leaching (t CO2e)": round(N2O_leach_total, 4),
    "Total N2O Emissions (t CO2e)": round(N2O_total_t, 4),
    "Total N2O Emissions per ha (t CO2e/ha)": round(N2O_total_per_ha, 6)
}
import pprint
pprint.pprint(results)


#####################################################################
# PROJECT SCENARIO
#####################################################################

# -----------------------------
# Step 1: Define Input Variables
# -----------------------------

tons_per_kilo = 1/1000

# Fertilizer application (t/ha of fertilizer applied per year)
# ~400 t/ac NPK/yr ... 988 t/ha NPK/yr
urea_mass_t = 0 * tons_per_kilo * project_area_ha  # 
npk_mass_t = 988 * tons_per_kilo * project_area_ha # ~90 t/ac 
dap_mass_t = 0 * tons_per_kilo  * project_area_ha #
can_mass_t = 0 * tons_per_kilo  * project_area_ha #


# N content
urea_n_content = 0.46  # 46% N
npk_n_content = 0.15   # 15% N
dap_n_content = 0.18
can_n_content = 0.26

# Emission factors (from IPCC 2019 Table 11.1 and 11.3)
EF1 = 0.016  # Direct emissions factor for synthetic N in wet climates
EF4 = 0.014  # Emissions from volatilization in wet climates
EF5 = 0.011  # Emissions from leaching/runoff

FracGASF = 0.15  # Volatilization fraction for urea
FracLEACH = 0.24  # Leaching fraction in wet climates

# Global warming potential for N2O (AR6)
GWP_N2O = 273

# Molar mass conversion factor (N2O-N to N2O)
MM_conversion = 44 / 28

# ---------------------------------
# Step 2: Calculate Total N Applied
# Equations (20) and (21)
# ---------------------------------
N_urea_t = urea_mass_t * urea_n_content  # tonnes of N from urea
N_npk_t = npk_mass_t * npk_n_content     # tonnes of N from NPK
N_dap_t = dap_mass_t * dap_n_content
N_can_t = can_mass_t * can_n_content

FSNbsl_it = N_urea_t + N_npk_t + N_dap_t + N_can_t # Total synthetic N applied

# ---------------------------------
# Step 3: Direct N2O emissions
# Equation (19)
# ---------------------------------
N2O_direct_total = FSNbsl_it * EF1 * MM_conversion * GWP_N2O
N2O_direct_per_ha = N2O_direct_total / project_area_ha

# ---------------------------------
# Step 4: Indirect N2O from Volatilization
# Equation (23)
# ---------------------------------
N_volatilized = FSNbsl_it * FracGASF
N2O_volat_total = N_volatilized * EF4 * MM_conversion * GWP_N2O
N2O_volat_per_ha = N2O_volat_total / project_area_ha

# ---------------------------------
# Step 5: Indirect N2O from Leaching/Runoff
# Equation (24)
# ---------------------------------
N_leached = FSNbsl_it * FracLEACH
N2O_leach_total = N_leached * EF5 * MM_conversion * GWP_N2O
N2O_leach_per_ha = N2O_leach_total / project_area_ha

# ---------------------------------
# Step 6: Total N2O from fertilizer use
# Equation (18): Total = Direct + Indirect
# Equation (58): Normalize by area
# ---------------------------------
N2O_total_t = N2O_direct_total + N2O_volat_total + N2O_leach_total
N2O_total_per_ha = N2O_total_t / project_area_ha


print("Project Scenario:")
# Output Results
results = {
    "Total N from Urea (t)": round(N_urea_t, 4),
    "Total N from NPK (t)": round(N_npk_t, 4),
    "Direct N2O Emissions (t CO2e)": round(N2O_direct_total, 4),
    "Indirect N2O from Volatilization (t CO2e)": round(N2O_volat_total, 4),
    "Indirect N2O from Leaching (t CO2e)": round(N2O_leach_total, 4),
    "Total N2O Emissions (t CO2e)": round(N2O_total_t, 4),
    "Total N2O Emissions per ha (t CO2e/ha)": round(N2O_total_per_ha, 6)
}
import pprint

pprint.pprint(results)
