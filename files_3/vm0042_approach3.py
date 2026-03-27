"""
VM0042 Quantification Approach 3
══════════════════════════════════════════════════════════════════════════════
COMBINED GHG CALCULATOR  —  per-hectare basis
Sources covered:
  1. Biomass burning        → CH4 + N2O   (IPCC 2006 Vol.4 Ch.2, Eq. 2.27)
  2. Synthetic fertilizer   → N2O         (IPCC 2019 Refinement Vol.4 Ch.11)
  3. Organic fertilizer     → N2O (±CH4)  (IPCC 2019 Refinement Vol.4 Ch.11)
     Organic types: compost, cattle_manure_solid, cattle_manure_slurry,
                    poultry_manure, biochar

Both BASELINE and PROJECT scenarios can include any combination of:
  - Partial or full biomass burning
  - Synthetic fertilizer application
  - One or more organic fertilizer applications

Emission Reduction (ER) = Baseline total − Project total  (kg CO2e ha⁻¹ yr⁻¹)
Positive ER = net avoided / reduced emissions (project is better than baseline).

GWP (AR5, 100-yr): CH4 = 28, N2O = 265   [VM0042 v1.0]
══════════════════════════════════════════════════════════════════════════════
REFERENCES
  Biomass burning EFs : IPCC 2006 Vol.4 Ch.2 Tables 2.5 & 2.6
                        (unchanged in 2019 Refinement)
  N2O EFs & factors  : IPCC 2019 Refinement Vol.4 Ch.11 Tables 11.1 & 11.3
  Biochar suppression: Cayuela et al. 2015 meta-analysis (~38% mean)
                       NOT an IPCC Tier 1 default — use conservatively
══════════════════════════════════════════════════════════════════════════════
"""

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — CONSTANTS & EMISSION FACTORS
# ══════════════════════════════════════════════════════════════════════════════

# ── GWP (AR5, 100-yr) ───────────────────────────────────────────────────────
GWP = {"CH4": 28, "N2O": 265}

# ── N2O-N → N2O molecular weight ratio ─────────────────────────────────────
N2O_N_TO_N2O = 44.0 / 28.0

# ── IPCC 2006 Vol.4 Ch.2 Table 2.5 — Biomass burning emission factors ───────
# G_ef : g GHG per kg dry matter burnt
BURNING_GEF = {
    "Cropland":                 {"CH4": 2.7,  "N2O": 0.07},
    "Grassland_tropical_humid": {"CH4": 2.3,  "N2O": 0.21},
    "Grassland_tropical_dry":   {"CH4": 1.9,  "N2O": 0.12},
    "Grassland_temperate":      {"CH4": 1.9,  "N2O": 0.12},
}

# ── IPCC 2006 Vol.4 Ch.2 Table 2.6 — Combustion factors ────────────────────
# C_f : fraction of available fuel actually combusted (dimensionless)
COMBUSTION_FACTORS = {
    "Cropland":                 0.80,
    "Grassland_tropical_humid": 0.76,
    "Grassland_tropical_dry":   0.69,
    "Grassland_temperate":      0.69,
}

# ── IPCC 2019 Refinement Vol.4 Ch.11 Table 11.1 — Direct N2O EF ─────────────
# EF1 : kg N2O-N (kg N input)⁻¹
# Key change vs 2006: disaggregated by climate AND fertilizer type
EF1 = {
    "global_default": 0.010,   # fallback if no climate data
    "wet_synthetic":  0.016,   # wet climate, synthetic N
    "wet_organic":    0.006,   # wet climate, organic N
    "dry_all":        0.005,   # dry climate, synthetic or organic
}

# ── IPCC 2019 Refinement Vol.4 Ch.11 Table 11.3 — Indirect N2O factors ──────
# EF4 : kg N2O-N (kg NH3-N + NOx-N volatilised)⁻¹  — now climate-split
EF4 = {"wet": 0.014, "dry": 0.005}

# EF5 : kg N2O-N (kg N leached)⁻¹
EF5 = 0.011          # 2019 Refinement (was 0.0075 in 2006)

# FracGASF : volatilisation fraction, synthetic fertilizer
# Disaggregated by fertilizer chemical type in 2019 Refinement
FracGASF = {
    "all_synthetic":            0.11,
    "urea":                     0.15,
    "ammonium_nitrate":         0.02,
    "calcium_ammonium_nitrate": 0.04,
}

# FracGASM : volatilisation fraction, organic amendments
FracGASM = 0.21      # 2019 Refinement (was 0.20 in 2006)

# FracLEACH_H : leaching/runoff fraction (humid regions only)
FracLEACH_H = 0.24   # 2019 Refinement (was 0.30 in 2006)

# ── Organic fertilizer reference properties ──────────────────────────────────
# n_fraction          : kg N per kg product (dry weight unless noted)
# frac_gas            : volatilisation fraction (FracGASM unless noted)
# ch4_soil_kg_per_kg_n: CH4 from soil application (aerobic soils ≈ 0;
#                       CH4 from manure STORAGE is Ch.10, not Ch.11)
# biochar_n2o_suppression: post-EF1 correction factor (literature, not IPCC Tier 1)
ORGANIC_FERTILIZERS = {
    "compost": {
        "n_fraction":            0.015,   # 1.5% N dw (mature compost, mid-range)
        "frac_gas":              FracGASM,
        "ch4_soil_kg_per_kg_n":  0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Mature compost. Typical N: 1–2% dw.",
    },
    "cattle_manure_solid": {
        "n_fraction":            0.006,   # 0.6% N dw
        "frac_gas":              FracGASM,
        "ch4_soil_kg_per_kg_n":  0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Solid cattle dung. N ~0.5–0.6% dw. CH4 from storage in Ch.10.",
    },
    "cattle_manure_slurry": {
        "n_fraction":            0.004,   # 0.4% N fresh weight
        "frac_gas":              FracGASM,
        "ch4_soil_kg_per_kg_n":  0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Cattle slurry. N ~0.3–0.4% fresh weight.",
    },
    "poultry_manure": {
        "n_fraction":            0.030,   # 3.0% N dw
        "frac_gas":              FracGASM,
        "ch4_soil_kg_per_kg_n":  0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Broiler/layer litter. N ~2.5–3.5% dw.",
    },
    "biochar": {
        "n_fraction":            0.006,   # 0.6% N dw (wood-based)
        "frac_gas":              0.05,    # low available NH3-N
        "ch4_soil_kg_per_kg_n":  0.0,
        "biochar_n2o_suppression": 0.38,  # 38% suppression — Cayuela et al. 2015
        "notes": "Wood-based biochar. IPCC has no Tier 1 EF; "
                 "suppression from literature. Set to 0 for conservative approach.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _ef1(climate: str, fert_class: str) -> float:
    """Resolve EF1 from 2019 Refinement Table 11.1."""
    if climate == "dry":
        return EF1["dry_all"]
    if climate == "wet":
        return EF1["wet_synthetic"] if fert_class == "synthetic" else EF1["wet_organic"]
    return EF1["global_default"]


def _ef4(climate: str) -> float:
    """Resolve EF4 from 2019 Refinement Table 11.3."""
    return EF4.get(climate, EF4["wet"])


# ── Burning ─────────────────────────────────────────────────────────────────

def calc_burning(fuel_load_kg_ha: float, land_type: str = "Cropland") -> dict:
    """
    CH4 and N2O from biomass burning per hectare.
    IPCC 2006 Vol.4 Ch.2, Eq. 2.27 (per-ha form):
        L_fire = M_B × C_f × G_ef × 10⁻³   [kg gas ha⁻¹]

    Parameters
    ----------
    fuel_load_kg_ha : above-ground residue available for burning (M_B), kg d.m. ha⁻¹
                      Set to 0 if no burning occurs.
    land_type       : key of BURNING_GEF / COMBUSTION_FACTORS

    Returns
    -------
    dict — all values per ha yr⁻¹
    """
    if land_type not in BURNING_GEF:
        raise ValueError(f"Unknown land_type '{land_type}'. "
                         f"Options: {list(BURNING_GEF)}")
    Cf  = COMBUSTION_FACTORS[land_type]
    Gef = BURNING_GEF[land_type]
    out = {"source": "burning", "land_type": land_type,
           "fuel_load_kg_ha": fuel_load_kg_ha, "Cf": Cf}
    total_CO2e = 0.0
    for gas in ("CH4", "N2O"):
        kg_ha = fuel_load_kg_ha * Cf * Gef[gas] * 1e-3
        co2e  = kg_ha * GWP[gas]
        out[f"{gas}_kg_ha"]      = round(kg_ha, 5)
        out[f"{gas}_CO2e_kg_ha"] = round(co2e,  4)
        total_CO2e += co2e
    out["total_CO2e_kg_ha"] = round(total_CO2e, 4)
    return out


# ── Fertilizer ───────────────────────────────────────────────────────────────

def calc_fertilizer(
    fertilizer_type: str,
    application_rate_kg_ha: float,
    climate: str = "wet",
    apply_leaching: bool = True,
    n_fraction_override: float = None,
    synthetic_frac_gas_key: str = "urea",
) -> dict:
    """
    N2O (and CH4) emissions from fertilizer application per hectare.
    IPCC 2019 Refinement Vol.4 Ch.11, Eqs 11.1 / 11.9 / 11.10.

    Parameters
    ----------
    fertilizer_type        : 'synthetic'  or an ORGANIC_FERTILIZERS key
    application_rate_kg_ha : kg of product per ha yr⁻¹
    climate                : 'wet' | 'dry' | 'global'
    apply_leaching         : True for humid regions
    n_fraction_override    : override default N content (kg N / kg product)
    synthetic_frac_gas_key : FracGASF sub-key for synthetic fertilizer type

    Returns
    -------
    dict — all values per ha yr⁻¹
    """
    is_synthetic = (fertilizer_type == "synthetic")

    if is_synthetic:
        n_frac      = n_fraction_override or 0.46   # urea default
        frac_gas    = FracGASF.get(synthetic_frac_gas_key, FracGASF["urea"])
        ef1_val     = _ef1(climate, "synthetic")
        ch4_ref     = 0.0
        suppression = 0.0
        notes       = f"Synthetic ({synthetic_frac_gas_key}). N fraction = {n_frac*100:.0f}%."
    else:
        if fertilizer_type not in ORGANIC_FERTILIZERS:
            raise ValueError(f"Unknown fertilizer_type '{fertilizer_type}'. "
                             f"Options: synthetic, {list(ORGANIC_FERTILIZERS)}")
        fert        = ORGANIC_FERTILIZERS[fertilizer_type]
        n_frac      = n_fraction_override or fert["n_fraction"]
        frac_gas    = fert["frac_gas"]
        ef1_val     = _ef1(climate, "organic")
        ch4_ref     = fert["ch4_soil_kg_per_kg_n"]
        suppression = fert["biochar_n2o_suppression"]
        notes       = fert["notes"]

    ef4_val  = _ef4(climate)
    N_kg_ha  = application_rate_kg_ha * n_frac   # kg N ha⁻¹

    # Direct N2O (Eq. 11.1)
    direct_raw  = N_kg_ha * ef1_val * N2O_N_TO_N2O
    direct_adj  = direct_raw * (1.0 - suppression)   # biochar suppression if any

    # Indirect N2O — volatilisation (Eq. 11.9)
    ind_vol     = N_kg_ha * frac_gas * ef4_val * N2O_N_TO_N2O

    # Indirect N2O — leaching (Eq. 11.10)
    ind_leach   = (N_kg_ha * FracLEACH_H * EF5 * N2O_N_TO_N2O) if apply_leaching else 0.0

    total_n2o   = direct_adj + ind_vol + ind_leach
    n2o_co2e    = total_n2o * GWP["N2O"]

    # CH4 from soil application (aerobic soils ≈ 0; documented for transparency)
    ch4_kg_ha   = N_kg_ha * ch4_ref
    ch4_co2e    = ch4_kg_ha * GWP["CH4"]

    return {
        "source":                   "fertilizer",
        "fertilizer_type":          fertilizer_type,
        "climate":                  climate,
        "application_rate_kg_ha":   application_rate_kg_ha,
        "n_fraction":               n_frac,
        "N_applied_kg_ha":          round(N_kg_ha,       4),
        "EF1_used":                 ef1_val,
        "EF4_used":                 ef4_val,
        "frac_gas_used":            frac_gas,
        "apply_leaching":           apply_leaching,
        "direct_N2O_raw_kg_ha":     round(direct_raw,    5),
        "biochar_suppression_frac": round(suppression,   3),
        "direct_N2O_adj_kg_ha":     round(direct_adj,    5),
        "indirect_vol_N2O_kg_ha":   round(ind_vol,       5),
        "indirect_leach_N2O_kg_ha": round(ind_leach,     5),
        "total_N2O_kg_ha":          round(total_n2o,     5),
        "N2O_CO2e_kg_ha":           round(n2o_co2e,      4),
        "CH4_kg_ha":                round(ch4_kg_ha,     5),
        "CH4_CO2e_kg_ha":           round(ch4_co2e,      4),
        "total_CO2e_kg_ha":         round(n2o_co2e + ch4_co2e, 4),
        "notes":                    notes,
    }


# ── Scenario aggregation ─────────────────────────────────────────────────────

def build_scenario(
    label: str,
    burning: dict | None,
    fertilizers: list[dict],
) -> dict:
    """
    Aggregate burning + all fertilizer components into one scenario total.

    Parameters
    ----------
    label        : human-readable scenario name
    burning      : result of calc_burning(), or None if no burning
    fertilizers  : list of calc_fertilizer() results (can be empty)

    Returns
    -------
    dict with per-source breakdown and grand totals (all kg ha⁻¹ yr⁻¹)
    """
    components = []
    if burning:
        components.append(burning)
    components.extend(fertilizers)

    total_CH4_CO2e = sum(c.get("CH4_CO2e_kg_ha",   c.get("CH4_CO2e_kg_ha", 0.0)) for c in components)
    total_N2O_CO2e = sum(c.get("N2O_CO2e_kg_ha",   c.get("N2O_CO2e_kg_ha",
                         c.get("total_CO2e_kg_ha", 0.0) - c.get("CH4_CO2e_kg_ha", 0.0))) for c in components)

    # Unify keys: burning uses {CH4,N2O}_CO2e_kg_ha; fertilizer uses same
    ch4_co2e_total = 0.0
    n2o_co2e_total = 0.0
    for c in components:
        ch4_co2e_total += c.get("CH4_CO2e_kg_ha", 0.0)
        n2o_co2e_total += c.get("N2O_CO2e_kg_ha", c.get("total_CO2e_kg_ha", 0.0)
                                 - c.get("CH4_CO2e_kg_ha", 0.0))

    grand_total = ch4_co2e_total + n2o_co2e_total

    return {
        "label":               label,
        "components":          components,
        "CH4_CO2e_kg_ha":      round(ch4_co2e_total, 4),
        "N2O_CO2e_kg_ha":      round(n2o_co2e_total, 4),
        "total_CO2e_kg_ha":    round(grand_total,    4),
    }


def emission_reduction(baseline: dict, project: dict) -> dict:
    """
    ER = Baseline − Project  (kg CO2e ha⁻¹ yr⁻¹)
    Positive = net avoided emission (project is better).
    """
    return {
        "CH4_ER_CO2e_kg_ha":   round(baseline["CH4_CO2e_kg_ha"]   - project["CH4_CO2e_kg_ha"],   4),
        "N2O_ER_CO2e_kg_ha":   round(baseline["N2O_CO2e_kg_ha"]   - project["N2O_CO2e_kg_ha"],   4),
        "total_ER_CO2e_kg_ha": round(baseline["total_CO2e_kg_ha"] - project["total_CO2e_kg_ha"], 4),
    }


def scale_to_area(value_kg_ha: float, area_ha: float) -> float:
    """Convert kg ha⁻¹ yr⁻¹ → tonnes yr⁻¹ for a given area."""
    return round(value_kg_ha * area_ha / 1000.0, 4)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — DISPLAY
# ══════════════════════════════════════════════════════════════════════════════

W = 70   # output width

def _hdr(title: str):
    print(f"\n  {'═'*(W-2)}")
    print(f"  {title}")
    print(f"  {'═'*(W-2)}")

def _sep():
    print(f"  {'-'*(W-2)}")


def print_burning_component(c: dict):
    _sep()
    print(f"  [BURNING]  Land type: {c['land_type']}")
    print(f"  Fuel load (M_B)    : {c['fuel_load_kg_ha']:>10,.1f}  kg d.m. ha⁻¹")
    print(f"  Combustion fac.    : {c['Cf']:>10.2f}  [IPCC 2006 Table 2.6]")
    gef = BURNING_GEF[c['land_type']]
    print(f"  G_ef CH4 / N2O     : {gef['CH4']} / {gef['N2O']} g kg⁻¹ d.m.  [Table 2.5]")
    print(f"  CH4 emitted        : {c['CH4_kg_ha']:>10.4f}  kg CH4  ha⁻¹ yr⁻¹")
    print(f"  CH4 CO2e           : {c['CH4_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['CH4']})")
    print(f"  N2O emitted        : {c['N2O_kg_ha']:>10.5f}  kg N2O  ha⁻¹ yr⁻¹")
    print(f"  N2O CO2e           : {c['N2O_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
    print(f"  Subtotal CO2e      : {c['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")


def print_fertilizer_component(c: dict):
    _sep()
    label = c['fertilizer_type'].replace('_', ' ').title()
    print(f"  [FERTILIZER]  {label}")
    print(f"  Application rate   : {c['application_rate_kg_ha']:>10,.1f}  kg product ha⁻¹ yr⁻¹")
    print(f"  N fraction         : {c['n_fraction']*100:>10.2f}  %")
    print(f"  N applied          : {c['N_applied_kg_ha']:>10.2f}  kg N ha⁻¹ yr⁻¹")
    print(f"  EF1 used           : {c['EF1_used']*100:>10.3f}  %  [2019 Ref. Table 11.1]")
    print(f"  EF4 used           : {c['EF4_used']*100:>10.3f}  %  [2019 Ref. Table 11.3]")
    print(f"  FracGAS used       : {c['frac_gas_used']*100:>10.1f}  %  [2019 Ref. Table 11.3]")
    print(f"  Direct N2O (raw)   : {c['direct_N2O_raw_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.1]")
    if c["biochar_suppression_frac"] > 0:
        print(f"  Biochar suppress.  : {c['biochar_suppression_frac']*100:>10.1f}  %  (Cayuela et al. 2015)")
        print(f"  Direct N2O (adj)   : {c['direct_N2O_adj_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹")
    print(f"  Indirect (vol)     : {c['indirect_vol_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.9]")
    print(f"  Indirect (leach)   : {c['indirect_leach_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.10]")
    print(f"  Total N2O          : {c['total_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹")
    print(f"  N2O CO2e           : {c['N2O_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
    if c["CH4_kg_ha"] > 0:
        print(f"  CH4 (soil)         : {c['CH4_kg_ha']:>10.5f}  kg CH4  ha⁻¹ yr⁻¹")
        print(f"  CH4 CO2e           : {c['CH4_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  Subtotal CO2e      : {c['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")


def print_scenario(scenario: dict):
    _hdr(f"SCENARIO: {scenario['label']}")
    for c in scenario["components"]:
        if c["source"] == "burning":
            print_burning_component(c)
        else:
            print_fertilizer_component(c)
    _sep()
    print(f"  SCENARIO TOTAL")
    print(f"  CH4 (all sources)  : {scenario['CH4_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  N2O (all sources)  : {scenario['N2O_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  GRAND TOTAL        : {scenario['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")


def print_er(er: dict, baseline: dict, project: dict, area_ha: float):
    _hdr("EMISSION REDUCTION  (Baseline − Project)")
    print(f"  Baseline total     : {baseline['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  Project total      : {project['total_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    _sep()
    print(f"  CH4 ER             : {er['CH4_ER_CO2e_kg_ha']:>+10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  N2O ER             : {er['N2O_ER_CO2e_kg_ha']:>+10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    print(f"  TOTAL ER (per ha)  : {er['total_ER_CO2e_kg_ha']:>+10.4f}  kg CO2e ha⁻¹ yr⁻¹")
    t_er = scale_to_area(er['total_ER_CO2e_kg_ha'], area_ha)
    print(f"  TOTAL ER ({area_ha:,.0f} ha) : {t_er:>+10.4f}  t CO2e yr⁻¹")
    print()
    sign = "✓ NET REDUCTION" if er["total_ER_CO2e_kg_ha"] > 0 else "✗ NET INCREASE"
    print(f"  {sign}  ({abs(er['total_ER_CO2e_kg_ha']):.2f} kg CO2e ha⁻¹ yr⁻¹)")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — USER INPUTS & EXAMPLE RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ── GLOBAL SETTINGS ──────────────────────────────────────────────────────
    CLIMATE         = "wet"       # 'wet' | 'dry' | 'global'
    APPLY_LEACHING  = True        # True for humid/sub-humid regions
    LAND_TYPE       = "Cropland"  # vegetation type for burning EFs
    PROJECT_AREA_HA = 500.0       # for scaled ER summary

    # ══════════════════════════════════════════════════════════════════════════
    #  BASELINE SCENARIO
    #  Typical: 100% residue burning + synthetic fertilizer only
    # ══════════════════════════════════════════════════════════════════════════

    bl_burning = calc_burning(
        fuel_load_kg_ha = 3_500.0,   # kg d.m. ha⁻¹  (full residue load burnt)
        land_type       = LAND_TYPE,
    )

    bl_synthetic = calc_fertilizer(
        fertilizer_type        = "synthetic",
        application_rate_kg_ha = 200.0,          # kg urea ha⁻¹ yr⁻¹
        climate                = CLIMATE,
        apply_leaching         = APPLY_LEACHING,
        synthetic_frac_gas_key = "urea",
    )

    # Baseline may also use a small amount of organic (e.g. some manure already applied)
    bl_organic = calc_fertilizer(
        fertilizer_type        = "cattle_manure_solid",
        application_rate_kg_ha = 1_000.0,        # kg solid manure ha⁻¹ yr⁻¹  (minor)
        climate                = CLIMATE,
        apply_leaching         = APPLY_LEACHING,
    )

    BASELINE = build_scenario(
        label       = "Baseline  (burning + synthetic + minor organic)",
        burning     = bl_burning,
        fertilizers = [bl_synthetic, bl_organic],
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  PROJECT SCENARIO
    #  Improved: partial burning + reduced synthetic + more organic
    # ══════════════════════════════════════════════════════════════════════════

    wps_burning = calc_burning(
        fuel_load_kg_ha = 700.0,     # kg d.m. ha⁻¹  (80% burning avoided)
        land_type       = LAND_TYPE,
    )

    wps_synthetic = calc_fertilizer(
        fertilizer_type        = "synthetic",
        application_rate_kg_ha = 80.0,           # kg urea ha⁻¹ yr⁻¹  (reduced)
        climate                = CLIMATE,
        apply_leaching         = APPLY_LEACHING,
        synthetic_frac_gas_key = "urea",
    )

    wps_compost = calc_fertilizer(
        fertilizer_type        = "compost",
        application_rate_kg_ha = 3_000.0,        # kg compost ha⁻¹ yr⁻¹
        climate                = CLIMATE,
        apply_leaching         = APPLY_LEACHING,
    )

    wps_biochar = calc_fertilizer(
        fertilizer_type        = "biochar",
        application_rate_kg_ha = 2_000.0,        # kg biochar ha⁻¹ yr⁻¹
        climate                = CLIMATE,
        apply_leaching         = APPLY_LEACHING,
    )

    PROJECT = build_scenario(
        label       = "Project   (partial burning + reduced synthetic + compost + biochar)",
        burning     = wps_burning,
        fertilizers = [wps_synthetic, wps_compost, wps_biochar],
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  OUTPUT
    # ══════════════════════════════════════════════════════════════════════════

    print("=" * W)
    print("  VM0042 Approach 3 — Combined GHG Calculator  (per ha yr⁻¹)")
    print("  Burning: IPCC 2006 Vol.4 Ch.2 Eq.2.27")
    print("  Fertilizer N2O: IPCC 2019 Refinement Vol.4 Ch.11 Eqs.11.1/11.9/11.10")
    print("=" * W)
    print(f"\n  Climate  : {CLIMATE.upper()}")
    print(f"  Leaching : {'Yes' if APPLY_LEACHING else 'No'}")
    print(f"  Land type: {LAND_TYPE}")

    print_scenario(BASELINE)
    print_scenario(PROJECT)

    ER = emission_reduction(BASELINE, PROJECT)
    print_er(ER, BASELINE, PROJECT, PROJECT_AREA_HA)

    print("=" * W)
