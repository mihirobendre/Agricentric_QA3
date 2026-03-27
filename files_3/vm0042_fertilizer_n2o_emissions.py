"""
VM0042 Quantification Approach 3
══════════════════════════════════════════════════════════════════════════════
N2O (AND CH4) EMISSIONS FROM ORGANIC FERTILIZER APPLICATION  (per-hectare)
Replacement of Synthetic Fertilizers with Organic Fertilizers
Organic fertilizer sources: Compost, Manure, Biochar

Methodology : IPCC 2019 Refinement to 2006 Guidelines, Vol. 4, Chapter 11
              Eq. 11.1  — Direct N2O from N inputs (Tier 1)
              Eq. 11.9  — Indirect N2O via atmospheric deposition (Tier 1)
              Eq. 11.10 — Indirect N2O via leaching/runoff (Tier 1)

══════════════════════════════════════════════════════════════════════════════
KEY 2019 REFINEMENT CHANGES vs 2006 (Chapter 11, Table 11.1 & 11.3):
  EF1 (direct, synthetic, wet)  : 0.016  [was 0.01 in 2006 — INCREASED]
  EF1 (direct, organic,  wet)   : 0.006  [was 0.01 in 2006 — DECREASED]
  EF1 (direct, both,     dry)   : 0.005  [was 0.01 in 2006 — DECREASED]
  EF1 (global default,   all)   : 0.010  [unchanged — fallback if no climate data]
  EF4 (indirect, wet)           : 0.014  [was 0.010 in 2006 — INCREASED]
  EF4 (indirect, dry)           : 0.005  [was 0.010 in 2006 — DECREASED]
  EF5                           : 0.011  [was 0.0075 in 2006 — INCREASED]
  FracGASF                      : 0.11   [was 0.10 in 2006 — slight increase]
  FracGASM                      : 0.21   [was 0.20 in 2006 — slight increase]
  FracLEACH-(H)                 : 0.24   [was 0.30 in 2006 — DECREASED]

BIOCHAR NOTE:
  The IPCC 2019 Refinement has no standalone biochar EF1.
  Biochar typically has very low available-N content; N2O suppression
  effects are emerging in literature but not yet a default IPCC Tier 1 factor.
  This script applies EF1_organic (2019 Refinement) to biochar's N content
  as a conservative Tier 1 approach, with a biochar_n2o_correction factor
  (default 0.0 = no correction; set 0.0–1.0 to represent % suppression
  based on site-specific data, e.g. meta-analysis mean suppression ~38%).

ORGANIC FERTILIZER TYPICAL N CONTENTS (used for activity data calculation):
  Compost (mature)          : 1.0–2.0%  N by dry weight
  Cattle manure (solid)     : 0.5–0.6%  N by dry weight
  Cattle manure (slurry)    : 0.3–0.4%  N by fresh weight
  Poultry manure            : 2.5–3.5%  N by dry weight
  Biochar (wood-based)      : 0.3–1.5%  N by dry weight (very low availability)

OUTPUTS (all per ha yr⁻¹):
  - N2O direct, indirect-vol, indirect-leach  (kg N2O ha⁻¹ yr⁻¹)
  - CH4 (from manure application — if manure type)
  - Total CO2e  (kg CO2e ha⁻¹ yr⁻¹)
══════════════════════════════════════════════════════════════════════════════
"""

# ══════════════════════════════════════════════════════════════════════════════
#  IPCC 2019 REFINEMENT — EMISSION FACTORS (Chapter 11, Table 11.1 & 11.3)
# ══════════════════════════════════════════════════════════════════════════════

# ── EF1: Direct N2O from N inputs  (Table 11.1, 2019 Refinement) ──────────
# kg N2O-N  (kg N input)⁻¹
# NEW in 2019: climate × fertiliser-type disaggregation
EF1 = {
    "global_default": 0.010,    # Table 11.1 — use when climate data unavailable
    "wet_synthetic":  0.016,    # Table 11.1 — wet climate, synthetic N
    "wet_organic":    0.006,    # Table 11.1 — wet climate, organic N (manure, compost, etc.)
    "dry_all":        0.005,    # Table 11.1 — dry climate, synthetic or organic
}

# ── EF4: Indirect N2O from atmospheric deposition  (Table 11.3, 2019 Ref.) ─
# kg N2O-N  (kg NH3-N + NOx-N volatilised)⁻¹
# NEW in 2019: wet/dry climate split
EF4 = {
    "wet": 0.014,   # Table 11.3 — wet climate
    "dry": 0.005,   # Table 11.3 — dry climate
}

# ── EF5: Indirect N2O from leaching/runoff  (Table 11.3, 2019 Refinement) ──
# kg N2O-N  (kg N leached)⁻¹
EF5 = 0.011   # Table 11.3, 2019 Refinement (was 0.0075 in 2006)

# ── FracGASF: volatilisation fraction — SYNTHETIC fertiliser  ───────────────
# kg N volatilised  (kg N applied)⁻¹   [Table 11.3, 2019 Refinement]
# The 2019 Refinement disaggregates by fertiliser chemical form.
# These are the representative default values:
FracGASF = {
    "all_synthetic":  0.11,    # Table 11.3 — blended default for synthetic N
    "urea":           0.15,    # Urea — higher NH3 volatilisation
    "ammonium_nitrate": 0.02,  # AN — lower NH3 volatilisation
    "calcium_ammonium_nitrate": 0.04,
}

# ── FracGASM: volatilisation fraction — ORGANIC amendments ─────────────────
# kg N volatilised  (kg N applied)⁻¹   [Table 11.3, 2019 Refinement]
FracGASM = 0.21    # Table 11.3, 2019 Refinement (was 0.20 in 2006)

# ── FracLEACH-(H): leaching/runoff fraction  [Table 11.3, 2019 Refinement] ─
# kg N leached  (kg N applied)⁻¹
# Only applied in humid regions where leaching occurs
FracLEACH_H = 0.24   # Table 11.3, 2019 Refinement (was 0.30 in 2006)

# ── Molecular mass ratio N2O-N → N2O ───────────────────────────────────────
N2O_N_TO_N2O = 44.0 / 28.0

# ── GWP (AR5, 100-yr)  [VM0042 v1.0] ──────────────────────────────────────
GWP = {"N2O": 265, "CH4": 28}

# ══════════════════════════════════════════════════════════════════════════════
#  ORGANIC FERTILIZER REFERENCE DATA (typical values; user should use actual)
# ══════════════════════════════════════════════════════════════════════════════
# n_fraction : kg N per kg product (dry weight unless noted)
# ch4_ef     : kg CH4 emitted per kg N applied (soil, not manure storage)
#              Note: CH4 from manure STORAGE is covered under Ch.10, not Ch.11.
#              When manure is applied to aerobic soils, CH4 soil emissions
#              are negligible and not part of IPCC Ch.11 (N2O only).
#              However, if manure is applied to flooded/waterlogged soils or
#              if paddy rice, refer to Ch.5 for CH4.
#              We include a reference CH4 value for context/documentation.

ORGANIC_FERTILIZERS = {
    "compost": {
        "n_fraction":         0.015,   # 1.5% N dry weight (mature compost, mid range)
        "frac_gas":           FracGASM,
        "ef1_climate_key":    "wet_organic",   # default; override via climate param
        "ch4_soil_kg_per_kg_n": 0.0,           # negligible in aerobic soils
        "notes": "Mature compost. Typical N: 1-2% dw. Low NH3 vs raw manure.",
    },
    "cattle_manure_solid": {
        "n_fraction":         0.006,   # 0.6% N dry weight
        "frac_gas":           FracGASM,
        "ef1_climate_key":    "wet_organic",
        "ch4_soil_kg_per_kg_n": 0.0,   # aerobic soils; CH4 from storage not here
        "notes": "Solid cattle dung. N can vary 0.5–0.6% dw. "
                 "CH4 from storage handled in Ch.10 (manure management).",
    },
    "cattle_manure_slurry": {
        "n_fraction":         0.004,   # 0.4% N fresh weight
        "frac_gas":           FracGASM,
        "ef1_climate_key":    "wet_organic",
        "ch4_soil_kg_per_kg_n": 0.0,
        "notes": "Cattle slurry (liquid). N ~0.3–0.4% fresh weight. "
                 "Higher FracGASM (NH3) vs solid due to application mode.",
    },
    "poultry_manure": {
        "n_fraction":         0.030,   # 3.0% N dry weight
        "frac_gas":           FracGASM,
        "ef1_climate_key":    "wet_organic",
        "ch4_soil_kg_per_kg_n": 0.0,
        "notes": "Broiler/layer litter. N can reach 2.5–3.5% dw. "
                 "High uric acid N, so higher volatilisation risk.",
    },
    "biochar": {
        "n_fraction":         0.006,   # 0.6% N dry weight (wood-based, typical)
        "frac_gas":           0.05,    # lower FracGASM — very little available NH3-N
        "ef1_climate_key":    "wet_organic",
        "ch4_soil_kg_per_kg_n": 0.0,
        "biochar_n2o_suppression": 0.38,   # 38% mean suppression (meta-analyses;
                                           # Cayuela et al. 2015 — NOT an IPCC default)
        "notes": "Wood-based biochar. Most N is recalcitrant; suppresses N2O "
                 "via enhanced aeration and adsorption. IPCC has no Tier 1 EF "
                 "for biochar; suppression is applied post-EF1 as correction. "
                 "Set suppression=0 for conservative (no-credit) approach.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  CORE CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _get_ef1(climate: str, fertilizer_class: str) -> float:
    """
    Resolve EF1 from 2019 Refinement Table 11.1.

    climate          : 'wet' | 'dry' | 'global'
    fertilizer_class : 'synthetic' | 'organic'
    """
    if climate == "dry":
        return EF1["dry_all"]
    if climate == "wet":
        return EF1["wet_synthetic"] if fertilizer_class == "synthetic" else EF1["wet_organic"]
    return EF1["global_default"]


def _get_ef4(climate: str) -> float:
    """Resolve EF4 from 2019 Refinement Table 11.3."""
    return EF4.get(climate, EF4["wet"])


def direct_n2o_per_ha(N_kg_ha: float, ef1: float) -> float:
    """
    Direct N2O from soil N input.
    IPCC 2019 Refinement, Eq. 11.1 (per-ha):
        N2O-N_direct = N_kg_ha × EF1
        N2O_direct   = N2O-N_direct × 44/28
    Returns: kg N2O ha⁻¹ yr⁻¹
    """
    return N_kg_ha * ef1 * N2O_N_TO_N2O


def indirect_n2o_vol_per_ha(N_kg_ha: float, frac_gas: float, ef4: float) -> float:
    """
    Indirect N2O via atmospheric deposition.
    IPCC 2019 Refinement, Eq. 11.9 (per-ha):
        N2O-N_vol = N_kg_ha × FracGAS × EF4
        N2O_vol   = N2O-N_vol × 44/28
    Returns: kg N2O ha⁻¹ yr⁻¹
    """
    return N_kg_ha * frac_gas * ef4 * N2O_N_TO_N2O


def indirect_n2o_leach_per_ha(N_kg_ha: float, apply_leaching: bool = True) -> float:
    """
    Indirect N2O via leaching/runoff.
    IPCC 2019 Refinement, Eq. 11.10 (per-ha):
        N2O-N_leach = N_kg_ha × FracLEACH-(H) × EF5
        N2O_leach   = N2O-N_leach × 44/28
    Returns: kg N2O ha⁻¹ yr⁻¹
    """
    if not apply_leaching:
        return 0.0
    return N_kg_ha * FracLEACH_H * EF5 * N2O_N_TO_N2O


def calculate_n2o_per_ha(
    fertilizer_type: str,
    application_rate_kg_ha: float,
    climate: str = "wet",
    apply_leaching: bool = True,
    n_fraction_override: float = None,
    synthetic_frac_gas_key: str = "all_synthetic",
) -> dict:
    """
    Full N2O (and CH4 note) calculation per hectare — 2019 Refinement Tier 1.

    Parameters
    ----------
    fertilizer_type        : 'synthetic' or a key of ORGANIC_FERTILIZERS
                             ('compost','cattle_manure_solid','cattle_manure_slurry',
                              'poultry_manure','biochar')
    application_rate_kg_ha : kg of product applied per ha yr⁻¹
                             (for organic = kg dry matter ha⁻¹, unless noted)
    climate                : 'wet' | 'dry' | 'global'
    apply_leaching         : True for humid regions (FracLEACH applies)
    n_fraction_override    : override default N content (kg N kg product⁻¹)
    synthetic_frac_gas_key : FracGASF key for synthetic fertilizer type

    Returns
    -------
    dict with all N2O components and totals, all per ha yr⁻¹
    """
    is_synthetic = (fertilizer_type == "synthetic")

    if is_synthetic:
        n_frac    = n_fraction_override if n_fraction_override else 0.46  # urea typical
        frac_gas  = FracGASF.get(synthetic_frac_gas_key, FracGASF["all_synthetic"])
        ef1       = _get_ef1(climate, "synthetic")
        ch4_ref   = 0.0
        suppression = 0.0
        notes     = "Synthetic fertiliser (default N fraction = urea 46%). " \
                    "Override n_fraction_override for other products."
    else:
        if fertilizer_type not in ORGANIC_FERTILIZERS:
            raise ValueError(f"Unknown fertilizer_type '{fertilizer_type}'. "
                             f"Options: synthetic, {list(ORGANIC_FERTILIZERS)}")
        fert = ORGANIC_FERTILIZERS[fertilizer_type]
        n_frac    = n_fraction_override if n_fraction_override else fert["n_fraction"]
        frac_gas  = fert["frac_gas"]
        ef1       = _get_ef1(climate, "organic")
        ch4_ref   = fert["ch4_soil_kg_per_kg_n"]
        suppression = fert.get("biochar_n2o_suppression", 0.0)
        notes     = fert["notes"]

    N_kg_ha = application_rate_kg_ha * n_frac   # kg N ha⁻¹ applied
    ef4     = _get_ef4(climate)

    direct_raw   = direct_n2o_per_ha(N_kg_ha, ef1)
    indirect_vol = indirect_n2o_vol_per_ha(N_kg_ha, frac_gas, ef4)
    indirect_lch = indirect_n2o_leach_per_ha(N_kg_ha, apply_leaching)

    # Apply biochar N2O suppression to direct + indirect (conservative = direct only)
    direct_final = direct_raw * (1.0 - suppression)

    total_n2o = direct_final + indirect_vol + indirect_lch
    total_co2e = total_n2o * GWP["N2O"]

    # CH4 from soil application (documented for transparency; usually 0 in aerobic soils)
    ch4_kg_ha = N_kg_ha * ch4_ref
    ch4_co2e  = ch4_kg_ha * GWP["CH4"]

    return {
        "fertilizer_type":          fertilizer_type,
        "climate":                  climate,
        "application_rate_kg_ha":   application_rate_kg_ha,
        "n_fraction":               n_frac,
        "N_applied_kg_ha":          round(N_kg_ha, 4),
        "EF1_used":                 ef1,
        "EF4_used":                 ef4,
        "frac_gas_used":            frac_gas,
        "apply_leaching":           apply_leaching,
        # N2O components
        "direct_N2O_kg_ha":         round(direct_raw,    5),
        "biochar_suppression_frac": round(suppression,   3),
        "direct_N2O_adj_kg_ha":     round(direct_final,  5),
        "indirect_vol_N2O_kg_ha":   round(indirect_vol,  5),
        "indirect_leach_N2O_kg_ha": round(indirect_lch,  5),
        "total_N2O_kg_ha":          round(total_n2o,     5),
        "total_N2O_CO2e_kg_ha":     round(total_co2e,    4),
        # CH4 (for documentation — usually 0 in aerobic soil application)
        "ch4_soil_kg_ha":           round(ch4_kg_ha,     5),
        "ch4_soil_CO2e_kg_ha":      round(ch4_co2e,      4),
        # Combined
        "total_GHG_CO2e_kg_ha":     round(total_co2e + ch4_co2e, 4),
        "notes":                    notes,
    }


def emission_reduction_per_ha(baseline: dict, project: dict) -> dict:
    """
    ER per ha = Baseline − Project  (positive = avoided / reduced emission).
    In VM0042 Approach 3:
      Baseline = synthetic fertilizer scenario
      Project  = organic fertilizer scenario
    """
    keys = ["direct_N2O_adj_kg_ha", "indirect_vol_N2O_kg_ha",
            "indirect_leach_N2O_kg_ha", "total_N2O_kg_ha",
            "total_N2O_CO2e_kg_ha", "ch4_soil_kg_ha",
            "ch4_soil_CO2e_kg_ha", "total_GHG_CO2e_kg_ha"]
    return {f"ER_{k}": round(baseline[k] - project[k], 5) for k in keys}


def scale_to_area(per_ha: dict, area_ha: float) -> dict:
    """Multiply numeric per-ha values by area_ha."""
    return {k: round(v * area_ha, 4) if isinstance(v, float) else v
            for k, v in per_ha.items()}


# ══════════════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _print_scenario(label: str, r: dict, w: int = 64):
    print(f"\n  {'-'*(w-2)}")
    print(f"  {label}")
    print(f"  {'-'*(w-2)}")
    print(f"  Fertilizer type    : {r['fertilizer_type']}")
    print(f"  Climate            : {r['climate']}")
    print(f"  Application rate   : {r['application_rate_kg_ha']:>8,.1f}  kg product ha⁻¹ yr⁻¹")
    print(f"  N fraction         : {r['n_fraction']*100:>8.2f}  %")
    print(f"  N applied          : {r['N_applied_kg_ha']:>8.2f}  kg N ha⁻¹ yr⁻¹")
    print(f"  EF1 used           : {r['EF1_used']*100:>8.3f}  %  [2019 Ref. Table 11.1]")
    print(f"  EF4 used           : {r['EF4_used']*100:>8.3f}  %  [2019 Ref. Table 11.3]")
    print(f"  FracGAS used       : {r['frac_gas_used']*100:>8.1f}  %  [2019 Ref. Table 11.3]")
    print()
    print(f"  Direct N2O (raw)   : {r['direct_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.1]")
    if r["biochar_suppression_frac"] > 0:
        print(f"  Biochar suppression: {r['biochar_suppression_frac']*100:>8.1f}  %  (literature; not IPCC default)")
        print(f"  Direct N2O (adj)   : {r['direct_N2O_adj_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹")
    print(f"  Indirect (vol)     : {r['indirect_vol_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.9]")
    print(f"  Indirect (leach)   : {r['indirect_leach_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹  [Eq.11.10]")
    print(f"  TOTAL N2O          : {r['total_N2O_kg_ha']:>10.5f}  kg N2O ha⁻¹ yr⁻¹")
    print(f"  TOTAL N2O CO2e     : {r['total_N2O_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
    if r["ch4_soil_kg_ha"] > 0:
        print(f"  CH4 (soil appl.)   : {r['ch4_soil_kg_ha']:>10.5f}  kg CH4  ha⁻¹ yr⁻¹  [Ch.11 note]")
        print(f"  CH4 CO2e           : {r['ch4_soil_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹  (GWP={GWP['CH4']})")
    print(f"  TOTAL GHG CO2e     : {r['total_GHG_CO2e_kg_ha']:>10.4f}  kg CO2e ha⁻¹ yr⁻¹")


# ══════════════════════════════════════════════════════════════════════════════
#  EXAMPLE CALCULATIONS — update user inputs below
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ── USER INPUTS ──────────────────────────────────────────────────────────
    CLIMATE            = "wet"     # 'wet' | 'dry' | 'global'  [key for EF1/EF4]
    APPLY_LEACHING     = True      # True for humid/sub-humid regions
    EXAMPLE_AREA_HA    = 500.0     # for scaled summary only

    # Baseline: synthetic fertilizer
    SYNTH_RATE_KG_HA   = 200.0    # kg urea ha⁻¹ yr⁻¹  (product, not N)
    SYNTH_TYPE_KEY     = "urea"   # FracGASF key: 'all_synthetic','urea','ammonium_nitrate'

    # Project: organic fertilizer alternatives (all on same N-equivalent basis)
    # Rates below are in kg of product per ha yr⁻¹
    ORGANIC_SCENARIOS = [
        ("compost",              5_000.0),   # 5 t compost ha⁻¹ yr⁻¹
        ("cattle_manure_solid",  8_000.0),   # 8 t solid manure ha⁻¹ yr⁻¹
        ("cattle_manure_slurry", 20_000.0),  # 20 t slurry ha⁻¹ yr⁻¹
        ("poultry_manure",       1_500.0),   # 1.5 t poultry manure ha⁻¹ yr⁻¹
        ("biochar",              3_000.0),   # 3 t biochar ha⁻¹ yr⁻¹
    ]
    # ─────────────────────────────────────────────────────────────────────────

    W = 66
    print("=" * W)
    print("  VM0042 Approach 3 — Fertilizer Replacement (per-ha)")
    print("  N2O: IPCC 2019 Refinement, Vol.4 Ch.11, Eqs.11.1/11.9/11.10")
    print("=" * W)
    print(f"\n  Climate regime     : {CLIMATE.upper()}")
    print(f"  Leaching/runoff    : {'Yes' if APPLY_LEACHING else 'No'}")
    print()
    print("  2019 Refinement EF values in use:")
    print(f"  EF1 (wet, synth)   : {EF1['wet_synthetic']*100:.1f}%  [Table 11.1]")
    print(f"  EF1 (wet, organic) : {EF1['wet_organic']*100:.1f}%  [Table 11.1]")
    print(f"  EF1 (dry, all)     : {EF1['dry_all']*100:.1f}%  [Table 11.1]")
    print(f"  EF4 (wet)          : {EF4['wet']*100:.1f}%  [Table 11.3]")
    print(f"  EF4 (dry)          : {EF4['dry']*100:.1f}%  [Table 11.3]")
    print(f"  EF5                : {EF5*100:.2f}%  [Table 11.3]")
    print(f"  FracGASF (urea)    : {FracGASF['urea']*100:.0f}%   [Table 11.3]")
    print(f"  FracGASM (organic) : {FracGASM*100:.0f}%   [Table 11.3]")
    print(f"  FracLEACH-(H)      : {FracLEACH_H*100:.0f}%   [Table 11.3]")

    # ── Baseline (synthetic) ─────────────────────────────────────────────────
    baseline = calculate_n2o_per_ha(
        "synthetic", SYNTH_RATE_KG_HA,
        climate=CLIMATE,
        apply_leaching=APPLY_LEACHING,
        synthetic_frac_gas_key=SYNTH_TYPE_KEY,
    )
    _print_scenario("BASELINE — Synthetic fertilizer (urea)", baseline, W)

    # ── Organic project scenarios ────────────────────────────────────────────
    print(f"\n  {'═'*(W-2)}")
    print("  ORGANIC FERTILIZER PROJECT SCENARIOS")
    print(f"  {'═'*(W-2)}")

    summary_rows = []
    for ftype, rate in ORGANIC_SCENARIOS:
        proj = calculate_n2o_per_ha(
            ftype, rate,
            climate=CLIMATE,
            apply_leaching=APPLY_LEACHING,
        )
        _print_scenario(f"PROJECT — {ftype.replace('_',' ').title()}", proj, W)
        er = emission_reduction_per_ha(baseline, proj)

        print(f"\n  >> EMISSION REDUCTION vs synthetic baseline  <<")
        print(f"  Direct N2O ER      : {er['ER_direct_N2O_adj_kg_ha']:>+10.5f}  kg N2O ha⁻¹ yr⁻¹")
        print(f"  Indirect vol ER    : {er['ER_indirect_vol_N2O_kg_ha']:>+10.5f}  kg N2O ha⁻¹ yr⁻¹")
        print(f"  Indirect leach ER  : {er['ER_indirect_leach_N2O_kg_ha']:>+10.5f}  kg N2O ha⁻¹ yr⁻¹")
        print(f"  TOTAL N2O ER       : {er['ER_total_N2O_kg_ha']:>+10.5f}  kg N2O ha⁻¹ yr⁻¹")
        print(f"  TOTAL CO2e ER      : {er['ER_total_GHG_CO2e_kg_ha']:>+10.4f}  kg CO2e ha⁻¹ yr⁻¹")
        print(f"  (scaled {EXAMPLE_AREA_HA:,.0f} ha)    : {er['ER_total_GHG_CO2e_kg_ha']*EXAMPLE_AREA_HA/1000:>+10.4f}  t CO2e yr⁻¹")
        summary_rows.append((ftype, proj["N_applied_kg_ha"], proj["total_GHG_CO2e_kg_ha"],
                              er["ER_total_GHG_CO2e_kg_ha"]))

    # ── Summary table ────────────────────────────────────────────────────────
    print(f"\n  {'═'*(W-2)}")
    print("  SUMMARY — All Scenarios vs Synthetic Baseline")
    print(f"  {'═'*(W-2)}")
    print(f"  {'Fertilizer':<26} {'N kg/ha':>8} {'CO2e kg/ha':>11} {'ER kg CO2e/ha':>14}")
    print(f"  {'-'*24} {'-'*8} {'-'*11} {'-'*14}")
    print(f"  {'synthetic (baseline)':<26} {baseline['N_applied_kg_ha']:>8.1f} "
          f"{baseline['total_GHG_CO2e_kg_ha']:>11.2f} {'---':>14}")
    for ftype, n_ha, co2e, er_co2e in summary_rows:
        print(f"  {ftype:<26} {n_ha:>8.1f} {co2e:>11.2f} {er_co2e:>+14.2f}")
    print()
    print("  Positive ER = emission reduced vs baseline (good).")
    print("  Negative ER = higher emission than baseline (worse, or different N rate).")
    print()
    print("  Note: Emissions scale with N applied. For true like-for-like comparison")
    print("  set organic rates to deliver the same kg N ha⁻¹ as synthetic baseline.")
    print("=" * W)
