"""
VM0042 Quantification Approach 3 — MODULE 1
CH4 and N2O Emissions from Biomass Burning (Crop Residues)
===========================================================
Methodology:  IPCC 2006 GL, Volume 4, Chapter 2, Section 2.4
Equation:     Eq. 2.27
              L_fire = A × M_B × C_f × G_ef × 10⁻³

Where:
  L_fire  = GHG emissions from fire (t GHG)
  A       = area burned (ha)
  M_B     = mass of fuel available for combustion (t dry matter ha⁻¹)  [Table 2.4]
  C_f     = combustion factor — fraction of M_B actually burned         [Table 2.6]
  G_ef    = emission factor (g GHG kg⁻¹ dry matter burned)              [Table 2.5]
  10⁻³    = unit conversion (g → kg, km → t)

Default emission factors sourced from:
  Table 2.5 — Tropical/subtropical cropland residue burning
    G_ef CH4  = 2.7  g CH4  kg⁻¹ dry matter burned
    G_ef N2O  = 0.07 g N2O  kg⁻¹ dry matter burned
  Table 2.6 — Combustion factor
    C_f       = 0.80 (crop residues, default)
  Table 2.4 — Default fuel consumption
    M_B       = 3.1  t dry matter ha⁻¹ (tropical cropland residues)

  Source: IPCC 2006 Guidelines for National GHG Inventories,
          Volume 4, Chapter 2
          https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html

Emission Reduction under VM0042 Approach 3:
  ER = Baseline emissions − Project emissions
  Project scenario = burning avoided, so Project emissions = 0
  ∴ ER = Baseline CH4 + Baseline N2O (expressed as t CO2eq via GWP)

GWP (AR5, 100-yr):  CH4 = 28,  N2O = 265
"""

# ─────────────────────────────────────────────────────────────────────────────
# IPCC DEFAULT VALUES
# ─────────────────────────────────────────────────────────────────────────────

# Table 2.5 — emission factors for tropical cropland residue burning
GEF = {
    "CH4": 2.7,     # g CH4  kg⁻¹ dry matter burned
    "N2O": 0.07,    # g N2O  kg⁻¹ dry matter burned
}

# Table 2.6 — combustion factor (crop residues)
CF_DEFAULT = 0.80   # dimensionless

# Table 2.4 — default fuel load for tropical cropland residues
MB_DEFAULT = 3.1    # t dry matter ha⁻¹

# GWP 100-yr (AR5)
GWP = {"CH4": 28, "N2O": 265}


# ─────────────────────────────────────────────────────────────────────────────
# CORE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def calc_fire_emissions(
    area_ha: float,
    fuel_load_t_ha: float = MB_DEFAULT,
    combustion_factor: float = CF_DEFAULT,
    gef_ch4: float = GEF["CH4"],
    gef_n2o: float = GEF["N2O"],
    description: str = "biomass burning",
) -> dict:
    """
    Calculate CH4 and N2O emissions from biomass burning.
    Uses IPCC 2006 GL Vol.4 Ch.2 Equation 2.27.

    Parameters
    ----------
    area_ha          : Area burned (ha)
    fuel_load_t_ha   : M_B — available fuel load (t dry matter ha⁻¹)
                       Default = 3.1 t dm ha⁻¹ (IPCC Table 2.4, tropical cropland)
    combustion_factor: C_f — fraction of fuel actually burned
                       Default = 0.80 (IPCC Table 2.6, crop residues)
    gef_ch4          : G_ef for CH4 (g kg⁻¹ dry matter burned)
                       Default = 2.7 (IPCC Table 2.5, tropical cropland)
    gef_n2o          : G_ef for N2O (g kg⁻¹ dry matter burned)
                       Default = 0.07 (IPCC Table 2.5, tropical cropland)
    description      : Label for printed output

    Returns
    -------
    dict: area, fuel parameters, CH4/N2O emissions (kg and t), CO2eq (t)
    """
    # Step 1: Mass of dry matter actually burned
    #         dm_burned (kg) = area (ha) × M_B (t ha⁻¹) × C_f × 1000 (kg t⁻¹)
    dm_burned_kg = area_ha * fuel_load_t_ha * combustion_factor * 1_000

    # Step 2: GHG emissions (kg) = dm_burned (kg) × G_ef (g kg⁻¹) × 10⁻³ (g→kg)
    ch4_kg = dm_burned_kg * gef_ch4 * 1e-3
    n2o_kg = dm_burned_kg * gef_n2o * 1e-3

    ch4_t = ch4_kg / 1_000
    n2o_t = n2o_kg / 1_000

    # Step 3: CO2 equivalent
    co2eq_t = ch4_t * GWP["CH4"] + n2o_t * GWP["N2O"]

    return {
        "description":    description,
        "area_ha":         area_ha,
        "MB_t_ha":         fuel_load_t_ha,
        "Cf":              combustion_factor,
        "dm_burned_t":     dm_burned_kg / 1_000,
        "CH4_kg":          ch4_kg,
        "N2O_kg":          n2o_kg,
        "CH4_t":           ch4_t,
        "N2O_t":           n2o_t,
        "CO2eq_t":         co2eq_t,
    }


def emission_reductions(baseline: dict, project: dict | None = None) -> dict:
    """
    ER = Baseline − Project emissions.
    Pass project=None for full avoidance (project emissions = 0).
    """
    proj = project or {"CH4_t": 0.0, "N2O_t": 0.0, "CO2eq_t": 0.0}
    return {
        "ER_CH4_t":   baseline["CH4_t"]   - proj["CH4_t"],
        "ER_N2O_t":   baseline["N2O_t"]   - proj["N2O_t"],
        "ER_CO2eq_t": baseline["CO2eq_t"] - proj["CO2eq_t"],
    }


def print_result(r: dict):
    sep = "─" * 62
    print(f"\n{sep}")
    print(f"  Scenario : {r['description']}")
    print(sep)
    print(f"  Area burned (A)             : {r['area_ha']:>12,.2f}  ha")
    print(f"  Fuel load (M_B)             : {r['MB_t_ha']:>12.2f}  t dm ha⁻¹")
    print(f"  Combustion factor (C_f)     : {r['Cf']:>12.2f}  (dimensionless)")
    print(f"  Dry matter burned           : {r['dm_burned_t']:>12,.2f}  t dm")
    print(f"  CH4 emissions               : {r['CH4_kg']:>12,.3f}  kg  = {r['CH4_t']:.4f} t")
    print(f"  N2O emissions               : {r['N2O_kg']:>12,.3f}  kg  = {r['N2O_t']:.4f} t")
    print(f"  Total CO2eq  (AR5 GWP)      : {r['CO2eq_t']:>12,.3f}  t CO2eq")
    print(sep)


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE — REPLACE VALUES WITH YOUR PROJECT DATA
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "=" * 62)
    print("  VM0042 Approach 3 | Avoided Biomass (Crop Residue) Burning")
    print("  IPCC 2006 GL Vol.4 Ch.2, Eq. 2.27")
    print("=" * 62)

    print(f"\n  Emission factors applied (IPCC 2006 Table 2.5 — tropical cropland):")
    print(f"    G_ef CH4  = {GEF['CH4']} g CH4  kg⁻¹ dry matter burned")
    print(f"    G_ef N2O  = {GEF['N2O']} g N2O  kg⁻¹ dry matter burned")
    print(f"    C_f       = {CF_DEFAULT}  (Table 2.6, crop residues)")
    print(f"    M_B       = {MB_DEFAULT} t dm ha⁻¹ (Table 2.4, tropical cropland)")
    print(f"    GWP CH4   = {GWP['CH4']}  |  GWP N2O = {GWP['N2O']}  (AR5, 100-yr)")

    # ── Single-stratum baseline ───────────────────────────────────────────────
    # Update 'area_ha' with your project's annually burned area
    baseline = calc_fire_emissions(
        area_ha=500.0,             # <── replace with your project area (ha)
        fuel_load_t_ha=3.1,       # IPCC Table 2.4 default
        combustion_factor=0.80,   # IPCC Table 2.6 default
        description="Baseline — burning occurs (500 ha)",
    )
    print_result(baseline)

    er = emission_reductions(baseline)
    print(f"\n  EMISSION REDUCTIONS (burning fully avoided):")
    print(f"    ER CH4                    : {er['ER_CH4_t']:>10,.4f}  t CH4 yr⁻¹")
    print(f"    ER N2O                    : {er['ER_N2O_t']:>10,.4f}  t N2O yr⁻¹")
    print(f"    ER Total (CO2eq, AR5)     : {er['ER_CO2eq_t']:>10,.3f}  t CO2eq yr⁻¹")

    # ── Multi-stratum example ────────────────────────────────────────────────
    print("\n\n  MULTI-STRATUM EXAMPLE  (3 crop types, 1 year)")
    print("  " + "─" * 60)
    print(f"  {'Stratum':<24} {'Area (ha)':>9} {'CH4 (t)':>9} "
          f"{'N2O (t)':>9} {'CO2eq (t)':>10}")
    print("  " + "─" * 60)

    strata = [
        # (label,                 area_ha,  M_B,  C_f)
        ("Maize residues",         200.0,   3.1,  0.80),
        ("Wheat residues",         180.0,   3.1,  0.80),
        ("Sorghum residues",       120.0,   3.1,  0.80),
    ]

    total_ch4 = total_n2o = total_co2eq = 0.0
    for label, area, mb, cf in strata:
        r = calc_fire_emissions(area, mb, cf, description=label)
        print(f"  {label:<24} {area:>9,.1f} {r['CH4_t']:>9.3f} "
              f"{r['N2O_t']:>9.4f} {r['CO2eq_t']:>10.2f}")
        total_ch4   += r["CH4_t"]
        total_n2o   += r["N2O_t"]
        total_co2eq += r["CO2eq_t"]

    print("  " + "─" * 60)
    print(f"  {'TOTAL':<24} {'':>9} {total_ch4:>9.3f} "
          f"{total_n2o:>9.4f} {total_co2eq:>10.2f}")
    print()
