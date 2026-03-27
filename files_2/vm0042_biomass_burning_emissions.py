"""
VM0042 Quantification Approach 3
──────────────────────────────────────────────────────────────────────────────
CH4 AND N2O EMISSIONS FROM BIOMASS BURNING
(Avoided Burning of Agricultural Biomass / Crop Residues)

Methodology:  IPCC 2006 Guidelines for National GHG Inventories
              Volume 4, Chapter 2, Section 2.4 — Non-CO2 Emissions from Fire
              Equation 2.27:  L_fire = A × M_B × C_f × G_ef × 10⁻³

Emission factors source:
  Table 2.5 (Vol. 4, Ch. 2) — G_ef values (g kg⁻¹ dry matter burnt)
    CH4 Cropland : 2.7  g kg⁻¹ d.m.
    N2O Cropland : 0.07 g kg⁻¹ d.m.
  Table 2.6 (Vol. 4, Ch. 2) — C_f combustion factors (dimensionless)
    Cropland     : 0.80

GWP values (AR5, 100-yr) used for CO2-equivalent conversion:
  CH4  = 28   (IPCC AR5)
  N2O  = 265  (IPCC AR5)
  (VM0042 v1.0 references AR5 GWPs)

Units throughout: tonnes unless stated otherwise.
──────────────────────────────────────────────────────────────────────────────
"""

# ── IPCC 2006 Vol.4 Ch.2 Table 2.5 ─────────────────────────────────────────
# G_ef: Emission factors for non-CO2 gases from fire
#   Units: g GHG per kg dry matter burnt
#   Source: IPCC 2006, Vol. 4, Ch. 2, Table 2.5
EMISSION_FACTORS_G_KG = {
    "Cropland": {
        "CH4": 2.7,    # Table 2.5, Temperate/Tropical Cropland
        "N2O": 0.07,   # Table 2.5, Temperate/Tropical Cropland
    },
    "Grassland_tropical_humid": {
        "CH4": 2.3,
        "N2O": 0.21,
    },
    "Grassland_tropical_dry": {
        "CH4": 1.9,
        "N2O": 0.12,
    },
    "Grassland_temperate": {
        "CH4": 1.9,
        "N2O": 0.12,
    },
}

# ── IPCC 2006 Vol.4 Ch.2 Table 2.6 ─────────────────────────────────────────
# C_f: Combustion factors (fraction of available fuel actually combusted)
#   Dimensionless.  Source: IPCC 2006, Vol. 4, Ch. 2, Table 2.6
COMBUSTION_FACTORS = {
    "Cropland":                    0.80,
    "Grassland_tropical_humid":    0.76,
    "Grassland_tropical_dry":      0.69,
    "Grassland_temperate":         0.69,
}

# ── GWP (AR5, 100-yr horizon) ──────────────────────────────────────────────
GWP = {"CH4": 28, "N2O": 265}


def calculate_biomass_burning_emissions(
    area_ha: float,
    fuel_mass_t_ha: float,
    land_type: str = "Cropland",
    scenario: str = "Baseline",
) -> dict:
    """
    Calculate CH4 and N2O emissions from biomass burning for a single year.

    IPCC 2006 Vol. 4 Ch. 2, Equation 2.27:
        L_fire = A x M_B x C_f x G_ef x 10^-3

    Parameters
    ----------
    area_ha        : area burnt, ha yr^-1
    fuel_mass_t_ha : mass of fuel available for combustion (M_B), t d.m. ha^-1
                     In VM0042 Approach 3, M_B = above-ground crop residue load.
    land_type      : one of EMISSION_FACTORS_G_KG keys
    scenario       : label for output ('Baseline' or 'Project')

    Returns
    -------
    dict with CH4 and N2O in tonnes of gas and in t CO2e
    """
    if land_type not in EMISSION_FACTORS_G_KG:
        raise ValueError(
            f"Unknown land type '{land_type}'. "
            f"Choose from: {list(EMISSION_FACTORS_G_KG.keys())}"
        )

    Cf  = COMBUSTION_FACTORS[land_type]
    Gef = EMISSION_FACTORS_G_KG[land_type]

    results = {
        "scenario": scenario,
        "land_type": land_type,
        "area_ha": area_ha,
        "fuel_mass_t_ha": fuel_mass_t_ha,
        "Cf": Cf,
    }

    total_CO2e = 0.0
    for gas in ("CH4", "N2O"):
        # Eq. 2.27 (IPCC 2006 Vol.4 Ch.2):
        # L_fire (t gas) = A (ha) x M_B (t ha^-1) x C_f x G_ef (g kg^-1) x 10^-3
        # Unit check: t d.m. x (g gas / kg d.m.) x 10^-3 = t gas  (OK)
        L_fire_t = area_ha * fuel_mass_t_ha * Cf * Gef[gas] * 1e-3
        CO2e = L_fire_t * GWP[gas]
        results[f"{gas}_t"]    = round(L_fire_t, 6)
        results[f"{gas}_CO2e"] = round(CO2e, 4)
        total_CO2e += CO2e

    results["total_CO2e"] = round(total_CO2e, 4)
    return results


def calculate_emission_reduction(baseline: dict, project: dict) -> dict:
    """
    Compute emission reductions from avoided burning.
    ER = Baseline emissions - Project emissions   (t CO2e yr^-1)

    In VM0042 Approach 3:
      Baseline: crop residues are burned  -> GHG emissions occur
      Project : residues mulched/retained -> emissions avoided
    """
    er = {}
    for gas in ("CH4", "N2O"):
        er[f"{gas}_ER_t"]    = round(baseline[f"{gas}_t"]    - project[f"{gas}_t"],    6)
        er[f"{gas}_ER_CO2e"] = round(baseline[f"{gas}_CO2e"] - project[f"{gas}_CO2e"], 4)
    er["total_ER_CO2e"] = round(baseline["total_CO2e"] - project["total_CO2e"], 4)
    return er


def print_scenario(label: str, r: dict):
    print(f"\n  {'-'*54}")
    print(f"  {label}")
    print(f"  {'-'*54}")
    print(f"  Area burnt             : {r['area_ha']:>10.2f}  ha")
    print(f"  Fuel load (M_B)        : {r['fuel_mass_t_ha']:>10.3f}  t d.m. ha^-1")
    print(f"  Combustion factor (Cf) : {r['Cf']:>10.2f}  (dimensionless)")
    print(f"  CH4 emitted            : {r['CH4_t']:>10.4f}  t CH4")
    print(f"  CH4 emitted            : {r['CH4_CO2e']:>10.4f}  t CO2e  (GWP={GWP['CH4']})")
    print(f"  N2O emitted            : {r['N2O_t']:>10.6f}  t N2O")
    print(f"  N2O emitted            : {r['N2O_CO2e']:>10.4f}  t CO2e  (GWP={GWP['N2O']})")
    print(f"  TOTAL                  : {r['total_CO2e']:>10.4f}  t CO2e")


# ============================================================================
# EXAMPLE CALCULATION — update these inputs for your project
# ============================================================================
if __name__ == "__main__":

    # USER INPUTS
    AREA_BASELINE_HA = 500.0    # ha where crop residues are burnt in baseline
    AREA_PROJECT_HA  = 0.0     # ha burnt in project (0 = complete avoided burning)
    FUEL_LOAD_T_HA   = 3.5     # t dry matter ha^-1 (M_B, residue load)
    LAND_TYPE        = "Cropland"

    print("=" * 60)
    print("  VM0042 Approach 3 — Avoided Biomass Burning")
    print("  CH4 & N2O  (IPCC 2006 Vol.4 Ch.2, Eq. 2.27)")
    print("=" * 60)
    print(f"\n  Land type  : {LAND_TYPE}")
    EF = EMISSION_FACTORS_G_KG[LAND_TYPE]
    print(f"  G_ef CH4   : {EF['CH4']} g kg^-1 d.m.  [IPCC 2006 Table 2.5]")
    print(f"  G_ef N2O   : {EF['N2O']} g kg^-1 d.m.  [IPCC 2006 Table 2.5]")
    print(f"  C_f        : {COMBUSTION_FACTORS[LAND_TYPE]}              [IPCC 2006 Table 2.6]")

    baseline = calculate_biomass_burning_emissions(
        AREA_BASELINE_HA, FUEL_LOAD_T_HA, LAND_TYPE, "Baseline"
    )
    project = calculate_biomass_burning_emissions(
        AREA_PROJECT_HA, FUEL_LOAD_T_HA, LAND_TYPE, "Project"
    )
    er = calculate_emission_reduction(baseline, project)

    print_scenario("BASELINE  (residues burnt)", baseline)
    print_scenario("PROJECT   (burning avoided)", project)

    print(f"\n  {'-'*54}")
    print("  EMISSION REDUCTIONS (Baseline - Project)")
    print(f"  {'-'*54}")
    print(f"  CH4 ER    : {er['CH4_ER_t']:>10.4f}  t CH4 yr^-1")
    print(f"  CH4 ER    : {er['CH4_ER_CO2e']:>10.4f}  t CO2e yr^-1")
    print(f"  N2O ER    : {er['N2O_ER_t']:>10.6f}  t N2O yr^-1")
    print(f"  N2O ER    : {er['N2O_ER_CO2e']:>10.4f}  t CO2e yr^-1")
    print(f"  TOTAL ER  : {er['total_ER_CO2e']:>10.4f}  t CO2e yr^-1")
    print()
    print("  Note: These ERs map to VM0042 Approach 3 term:")
    print("  GHG_BL,BURNING - GHG_WPS,BURNING  (avoided burning component)")
    print("=" * 60)
