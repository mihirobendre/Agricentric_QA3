# Methane Emissions from Biomass Burning (CH4_bbsl) - VM0042 v2.1 Equations 15 and 57
# Version with Detailed Notes and Crop-Specific Transparency

# ------------------------------------------------------------------
# 📘 BACKGROUND
# Equation (15) – Baseline Areal CH₄ Emissions:
# CH4_bbsl = (GWP_CH4 × ∑ (MB_c × CF_c × EF_c,CH4)) / (1,000,000 × A)

# Equation (57) – Emissions Reductions:
# ΔCH4_bbt = (CH4_bbsl - CH4_bbwp) × A

# All emission factors and combustion factors are from:
# 🔗 IPCC 2019 Refinement to the 2006 Guidelines
# Volume 4, Chapter 2, Table 2.5:
# https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch02_Generic%20Methods.pdf

# Global Warming Potential (100-year) from:
# 🔗 IPCC AR5:
# https://ghgprotocol.org/sites/default/files/Global-Warming-Potential-Values%20%28Feb%2016%202016%29_1.pdf

# All values are editable and clearly labeled below
# ------------------------------------------------------------------

# ------------------------------
# INPUT PARAMETERS (EDITABLE)
# ------------------------------

# IPCC AR5 100-year Global Warming Potential for CH4
GWP_CH4 = 28  # t CO2e / t CH4

# Total project area (hectares)
A = 5120

# Residue data dictionary — includes crop-specific IPCC default values
# ------------------------------
g_to_tonne = 1e-6  # Conversion from grams to tonnes

# ------------------------------
# Baseline Emissions
# ------------------------------

maintenance_c_in = 18.506
carbon_fraction = 0.45

MB = maintenance_c_in/carbon_fraction          # Mass of dry biomass burned (tons)
CF = 0.0           # Combustion factor: percent of residues burned
EF = 0.0027        # Emission factor (kg CH4 / kg dry matter)

emissions_CH4 = MB * CF * EF

# Convert g CH4 → tonnes CH4 → t CO2e
emissions_CO2e = emissions_CH4 * GWP_CH4

total_CH4_emissions = emissions_CH4 * A

print(f"CH4 Emissions Baseline (t CO2e) {total_CH4_emissions:.8f}")

# Areal mean baseline emissions
CH4_bbsl = total_CH4_emissions / A  # t CO2e/ha

# ------------------------------
# Project Emissions
# ------------------------------

maintenance_c_in = 18.506
carbon_fraction = 0.45

MB = maintenance_c_in/carbon_fraction          # Mass of dry biomass burned (tons)
CF = 0.0           # Combustion factor: percent of residues burned
EF = 0.0027        # Emission factor (kg CH4 / kg dry matter)

emissions_CH4 = MB * CF * EF

# Convert g CH4 → tonnes CH4 → t CO2e
emissions_CO2e = emissions_CH4 * GWP_CH4

total_CH4_emissions = emissions_CH4 * A

print(f"CH4 Emissions Project (t CO2e) {total_CH4_emissions:.8f}")

# Project scenario CH4 emissions from burning (set to 0 if avoided)
CH4_bbwp = total_CH4_emissions / A  # t CO2e/ha

# Emission reductions (if burning is avoided)
delta_CH4_bbt = (CH4_bbsl - CH4_bbwp) * A  # t CO2e

# ------------------------------
# OUTPUT
# ------------------------------
import pandas as pd

# Print final emission summary
print("\nSummary:")
print(f"Areal CH₄ Emissions in Project (t CO₂e/ha): {round(CH4_bbwp, 8)}")
print(f"Areal CH₄ Emissions in Baseline (t CO₂e/ha): {round(CH4_bbsl, 8)}")
print(f"Total CH₄ Emission Reductions (t CO₂e): {round(delta_CH4_bbt, 8)}")
