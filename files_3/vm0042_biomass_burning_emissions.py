"""
VM0042 Quantification Approach 3
══════════════════════════════════════════════════════════════════════════════
CH4 AND N2O EMISSIONS FROM BIOMASS BURNING  (per-hectare basis)
Avoided Burning of Agricultural Biomass / Crop Residues

Methodology : IPCC 2006 Guidelines, Vol. 4, Ch. 2, Section 2.4
              Equation 2.27: L_fire = M_B × C_f × G_ef × 10⁻³
              (area-normalised form: all inputs and outputs are per-ha)

Emission factors (IPCC 2006, Vol. 4, Ch. 2):
  Table 2.5  G_ef  (g GHG kg⁻¹ dry matter burnt)
  Table 2.6  C_f   combustion factor (dimensionless)

NOTE ON BIOMASS BURNING:
  The 2019 Refinement made NO changes to the non-CO2 biomass burning
  emission factors in Vol. 4 Ch. 2 (Tables 2.5 / 2.6).  The 2006
  values remain current IPCC defaults for this source category.

GWP (AR5, 100-yr):  CH4 = 28,  N2O = 265  (VM0042 v1.0 references AR5)

OUTPUTS (all per ha yr⁻¹):
  - CH4  (kg ha⁻¹ yr⁻¹  and  kg CO2e ha⁻¹ yr⁻¹)
  - N2O  (kg ha⁻¹ yr⁻¹  and  kg CO2e ha⁻¹ yr⁻¹)
  - Total CO2e  (kg CO2e ha⁻¹ yr⁻¹)
══════════════════════════════════════════════════════════════════════════════
"""

# ── IPCC 2006 Vol.4 Ch.2 Table 2.5 ─────────────────────────────────────────
# G_ef : emission factors for non-CO2 gases from fire, g GHG kg⁻¹ d.m. burnt
EMISSION_FACTORS_G_KG = {
    "Cropland": {
        "CH4": 2.7,    # Table 2.5 — Temperate/Tropical cropland
        "N2O": 0.07,
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
# C_f : combustion factor (fraction of available fuel actually burnt)
COMBUSTION_FACTORS = {
    "Cropland":                 0.80,
    "Grassland_tropical_humid": 0.76,
    "Grassland_tropical_dry":   0.69,
    "Grassland_temperate":      0.69,
}

# ── GWP (AR5, 100-yr) ───────────────────────────────────────────────────────
GWP = {"CH4": 28, "N2O": 265}


def biomass_burning_per_ha(
    fuel_load_kg_ha: float,
    land_type: str = "Cropland",
) -> dict:
    """
    Calculate CH4 and N2O emissions from biomass burning per hectare.

    IPCC 2006 Vol.4 Ch.2, Eq. 2.27 (per-ha form):
        L_fire = M_B × C_f × G_ef × 10⁻³
        [kg gas ha⁻¹] = [kg d.m. ha⁻¹] × [dimensionless] × [g kg⁻¹] × 10⁻³

    Parameters
    ----------
    fuel_load_kg_ha : above-ground residue available for burning (M_B), kg d.m. ha⁻¹
                      Typical cropland range: 1 000–6 000 kg ha⁻¹
    land_type       : vegetation category (key of EMISSION_FACTORS_G_KG)

    Returns
    -------
    dict  — all values per hectare per year
    """
    if land_type not in EMISSION_FACTORS_G_KG:
        raise ValueError(f"Unknown land_type '{land_type}'. "
                         f"Options: {list(EMISSION_FACTORS_G_KG)}")
    Cf  = COMBUSTION_FACTORS[land_type]
    Gef = EMISSION_FACTORS_G_KG[land_type]

    result = {"land_type": land_type, "fuel_load_kg_ha": fuel_load_kg_ha, "Cf": Cf}
    total_CO2e = 0.0
    for gas in ("CH4", "N2O"):
        kg_ha = fuel_load_kg_ha * Cf * Gef[gas] * 1e-3   # kg gas ha⁻¹
        co2e  = kg_ha * GWP[gas]
        result[f"{gas}_kg_ha"]    = round(kg_ha, 5)
        result[f"{gas}_CO2e_kg_ha"] = round(co2e, 4)
        total_CO2e += co2e
    result["total_CO2e_kg_ha"] = round(total_CO2e, 4)
    return result


def emission_reduction_per_ha(baseline: dict, project: dict) -> dict:
    """ER per ha = Baseline − Project  (positive = avoided emission)."""
    er = {}
    for gas in ("CH4", "N2O"):
        er[f"{gas}_ER_kg_ha"]      = round(baseline[f"{gas}_kg_ha"]      - project[f"{gas}_kg_ha"],      5)
        er[f"{gas}_ER_CO2e_kg_ha"] = round(baseline[f"{gas}_CO2e_kg_ha"] - project[f"{gas}_CO2e_kg_ha"], 4)
    er["total_ER_CO2e_kg_ha"] = round(baseline["total_CO2e_kg_ha"] - project["total_CO2e_kg_ha"], 4)
    return er


def scale_to_area(per_ha: dict, area_ha: float) -> dict:
    """Multiply per-ha results by total area."""
    scaled = {k: round(v * area_ha, 4) if isinstance(v, float) else v
              for k, v in per_ha.items()}
    scaled["area_ha"] = area_ha
    return scaled


# ══════════════════════════════════════════════════════════════════════════════
#  EXAMPLE — update user inputs below
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ── USER INPUTS ──────────────────────────────────────────────────────────
    FUEL_LOAD_KG_HA   = 3_500.0   # kg d.m. ha⁻¹ (crop residue fuel load, M_B)
    LAND_TYPE         = "Cropland"
    BL_BURNED_FRAC    = 1.0       # fraction of area burned in baseline  (1.0 = 100%)
    WPS_BURNED_FRAC   = 0.0       # fraction of area burned in project   (0.0 = avoided)
    EXAMPLE_AREA_HA   = 500.0     # only used for the scaled-to-area summary block
    # ─────────────────────────────────────────────────────────────────────────

    Gef = EMISSION_FACTORS_G_KG[LAND_TYPE]
    Cf  = COMBUSTION_FACTORS[LAND_TYPE]

    # Effective fuel load = fuel_load × burned fraction
    bl  = biomass_burning_per_ha(FUEL_LOAD_KG_HA * BL_BURNED_FRAC,  LAND_TYPE)
    wps = biomass_burning_per_ha(FUEL_LOAD_KG_HA * WPS_BURNED_FRAC, LAND_TYPE)
    er  = emission_reduction_per_ha(bl, wps)

    w = 60
    print("=" * w)
    print("  VM0042 Approach 3 — Avoided Biomass Burning (per-ha)")
    print("  IPCC 2006 Vol.4 Ch.2, Eq. 2.27")
    print("=" * w)
    print(f"\n  Land type          : {LAND_TYPE}")
    print(f"  G_ef CH4           : {Gef['CH4']} g kg⁻¹ d.m.  [Table 2.5]")
    print(f"  G_ef N2O           : {Gef['N2O']} g kg⁻¹ d.m.  [Table 2.5]")
    print(f"  C_f                : {Cf}                [Table 2.6]")
    print(f"  Fuel load (M_B)    : {FUEL_LOAD_KG_HA:,.0f} kg d.m. ha⁻¹")

    for label, r in [("BASELINE (residues burnt)", bl), ("PROJECT  (burning avoided)", wps)]:
        print(f"\n  {'-'*(w-2)}")
        print(f"  {label}")
        print(f"  {'-'*(w-2)}")
        print(f"  Eff. fuel load     : {r['fuel_load_kg_ha']:>10,.1f}  kg d.m. ha⁻¹")
        print(f"  CH4                : {r['CH4_kg_ha']:>10.4f}  kg CH4 ha⁻¹ yr⁻¹")
        print(f"  CH4                : {r['CH4_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['CH4']})")
        print(f"  N2O                : {r['N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹")
        print(f"  N2O                : {r['N2O_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
        print(f"  TOTAL              : {r['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")

    print(f"\n  {'-'*(w-2)}")
    print("  EMISSION REDUCTION  (Baseline − Project)  — per ha")
    print(f"  {'-'*(w-2)}")
    print(f"  CH4 ER             : {er['CH4_ER_kg_ha']:>10.4f}  kg CH4  ha⁻¹ yr⁻¹")
    print(f"  CH4 ER             : {er['CH4_ER_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  N2O ER             : {er['N2O_ER_kg_ha']:>10.5f}  kg N2O  ha⁻¹ yr⁻¹")
    print(f"  N2O ER             : {er['N2O_ER_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  TOTAL ER           : {er['total_ER_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")

    # Optional: scale to a project area
    scaled = scale_to_area(er, EXAMPLE_AREA_HA)
    print(f"\n  {'─'*(w-2)}")
    print(f"  SCALED TO {EXAMPLE_AREA_HA:,.0f} ha (example area)")
    print(f"  {'─'*(w-2)}")
    print(f"  CH4 ER             : {scaled['CH4_ER_kg_ha']/1000:>10.4f}  t CH4  yr⁻¹")
    print(f"  N2O ER             : {scaled['N2O_ER_kg_ha']/1000:>10.5f}  t N2O  yr⁻¹")
    print(f"  TOTAL ER           : {scaled['total_ER_CO2e_kg_ha']/1000:>10.4f}  t CO2e yr⁻¹")
    print("=" * w)
