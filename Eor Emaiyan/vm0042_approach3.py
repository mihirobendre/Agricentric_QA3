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

All user inputs and all outputs are in TONNES (t) per hectare per year.
  Inputs  : t d.m. ha⁻¹ (fuel load),  t product ha⁻¹ yr⁻¹ (fertilizer rates)
  Outputs : t CH4 ha⁻¹ yr⁻¹,  t N2O ha⁻¹ yr⁻¹,  t CO2e ha⁻¹ yr⁻¹

NOTE ON IPCC EFs: All IPCC emission factors are defined in kg/kg ratios
  (dimensionless) so the unit conversion is exact — multiplying t inputs by
  the same EFs gives t outputs directly. A ×10⁻³ factor in Eq.2.27 (which
  converts g kg⁻¹ to kg kg⁻¹) becomes ×10⁻³ when inputs are in tonnes too,
  giving t gas ha⁻¹ as output without any additional conversion step.

Emission Reduction (ER) = Baseline total − Project total  (t CO2e ha⁻¹ yr⁻¹)
Positive ER = net avoided / reduced emissions (project is better than baseline).

GWP (AR5, 100-yr): CH4 = 28, N2O = 265   [VM0042 v1.0]
══════════════════════════════════════════════════════════════════════════════
REFERENCES
  Biomass burning EFs : IPCC 2006 Vol.4 Ch.2 Tables 2.5 & 2.6
                        (unchanged in 2019 Refinement)
  N2O EFs & factors  : IPCC 2019 Refinement Vol.4 Ch.11 Tables 11.1 & 11.3
  Urea CO2           : IPCC 2006 Vol.4 Ch.11.4
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
# G_ef : g GHG per kg dry matter burnt  (= t GHG per t d.m. × 10⁻³ factor in Eq.2.27)
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
# EF1 : kg N2O-N (kg N input)⁻¹  = t N2O-N (t N input)⁻¹  (dimensionless ratio)
EF1 = {
    "global_default": 0.010,
    "wet_synthetic":  0.016,
    "wet_organic":    0.006,
    "dry_all":        0.005,
}

# ── IPCC 2019 Refinement Vol.4 Ch.11 Table 11.3 — Indirect N2O factors ──────
# EF4 : t N2O-N (t NH3-N + NOx-N volatilised)⁻¹  (dimensionless)
EF4 = {"wet": 0.014, "dry": 0.005}

# EF5 : t N2O-N (t N leached)⁻¹  (dimensionless)
EF5 = 0.011

# ── SYNTHETIC FERTILIZER CATALOG ─────────────────────────────────────────────
# n_fraction : t N per t product  (same numeric value as kg N / kg product)
# frac_gas   : FracGASF from IPCC 2019 Refinement Annex 11A.7, Table 7A.3
#              (dimensionless — t N volatilised per t N applied)
# co2_ef     : t CO2 per t product from urea hydrolysis
#              IPCC 2006 Ch.11.4: EF_urea = 0.20 t C / t urea → × 44/12 = 0.733 t CO2/t
SYNTHETIC_FERTILIZERS = {
    "urea": {
        "display":    "Urea (46-0-0)",
        "n_fraction": 0.46,
        "frac_gas":   0.15,
        "co2_ef":     0.733,
        "notes": "Urea. High NH3 volatilisation risk. CO2 from hydrolysis (IPCC 2006 Ch.11.4).",
    },
    "ammonium_nitrate": {
        "display":    "Ammonium Nitrate (AN, 34-0-0)",
        "n_fraction": 0.34,
        "frac_gas":   0.02,
        "co2_ef":     0.0,
        "notes": "AN. Very low volatilisation. 50% NO3-N + 50% NH4-N.",
    },
    "calcium_ammonium_nitrate": {
        "display":    "Calcium Ammonium Nitrate (CAN, 27-0-0)",
        "n_fraction": 0.27,
        "frac_gas":   0.04,
        "co2_ef":     0.0,
        "notes": "CAN. Low-moderate volatilisation. Common in Europe.",
    },
    "ammonium_sulfate": {
        "display":    "Ammonium Sulphate (AS, 21-0-0-24S)",
        "n_fraction": 0.21,
        "frac_gas":   0.15,
        "co2_ef":     0.0,
        "notes": "AS. High NH3 risk on alkaline soils. Supplies S.",
    },
    "urea_ammonium_nitrate": {
        "display":    "Urea Ammonium Nitrate (UAN, 28-0-0 or 32-0-0)",
        "n_fraction": 0.28,
        "frac_gas":   0.12,
        "co2_ef":     0.319,
        "notes": "UAN solution. ~50% N from urea; CO2 ef scaled proportionally. "
                 "Override n_fraction_override=0.32 for UAN-32.",
    },
    "map": {
        "display":    "Monoammonium Phosphate (MAP, 11-52-0)",
        "n_fraction": 0.11,
        "frac_gas":   0.08,
        "co2_ef":     0.0,
        "notes": "MAP. Primary N is NH4+. Lower volatilisation than urea. Supplies P.",
    },
    "dap": {
        "display":    "Diammonium Phosphate (DAP, 18-46-0)",
        "n_fraction": 0.18,
        "frac_gas":   0.10,
        "co2_ef":     0.0,
        "notes": "DAP. Slightly higher pH after dissolution vs MAP → higher NH3 risk. "
                 "Widely used in sub-Saharan Africa and Asia.",
    },
    "npk_blend": {
        "display":    "NPK Blend (generic, e.g. 17-17-17)",
        "n_fraction": 0.17,
        "frac_gas":   0.11,
        "co2_ef":     0.0,
        "notes": "Generic NPK. FracGASF = IPCC blended default (0.11) — volatilisation "
                 "depends on N-form in blend. Override n_fraction_override with actual N grade.",
    },
    "anhydrous_ammonia": {
        "display":    "Anhydrous Ammonia (AA, 82-0-0)",
        "n_fraction": 0.82,
        "frac_gas":   0.09,
        "co2_ef":     0.0,
        "notes": "AA. Injected subsurface; lower surface NH3 loss than urea.",
    },
    "ammonium_bicarbonate": {
        "display":    "Ammonium Bicarbonate (ABC, 17-0-0)",
        "n_fraction": 0.17,
        "frac_gas":   0.29,
        "co2_ef":     0.0,
        "notes": "ABC. Very high NH3 volatilisation. Predominantly used in China.",
    },
    "triple_superphosphate_n": {
        "display":    "TSP + N blend (custom — N fraction varies)",
        "n_fraction": 0.11,
        "frac_gas":   0.11,
        "co2_ef":     0.0,
        "notes": "TSP has no N. If blended with N product, set n_fraction_override "
                 "to actual N content and choose the appropriate key for the N source.",
    },
}

# FracGASM : volatilisation fraction, organic amendments (dimensionless)
FracGASM = 0.21

# FracLEACH_H : leaching/runoff fraction, humid regions (dimensionless)
FracLEACH_H = 0.24

# ── Organic fertilizer reference properties ──────────────────────────────────
# n_fraction          : t N per t product  (= kg N / kg product, dimensionless)
# frac_gas            : volatilisation fraction (dimensionless)
# ch4_soil_t_per_t_n  : t CH4 per t N applied to soil (aerobic soils ≈ 0)
# biochar_n2o_suppression: fraction reduction in direct N2O (literature, not IPCC Tier 1)
ORGANIC_FERTILIZERS = {
    "compost": {
        "n_fraction":              0.015,
        "frac_gas":                FracGASM,
        "ch4_soil_t_per_t_n":      0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Mature compost. Typical N: 1–2% dw.",
    },
    "cattle_manure_solid": {
        "n_fraction":              0.006,
        "frac_gas":                FracGASM,
        "ch4_soil_t_per_t_n":      0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Solid cattle dung. N ~0.5–0.6% dw. CH4 from storage in Ch.10.",
    },
    "cattle_manure_slurry": {
        "n_fraction":              0.004,
        "frac_gas":                FracGASM,
        "ch4_soil_t_per_t_n":      0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Cattle slurry. N ~0.3–0.4% fresh weight.",
    },
    "poultry_manure": {
        "n_fraction":              0.030,
        "frac_gas":                FracGASM,
        "ch4_soil_t_per_t_n":      0.0,
        "biochar_n2o_suppression": 0.0,
        "notes": "Broiler/layer litter. N ~2.5–3.5% dw.",
    },
    "biochar": {
        "n_fraction":              0.006,
        "frac_gas":                0.05,
        "ch4_soil_t_per_t_n":      0.0,
        "biochar_n2o_suppression": 0.38,
        "notes": "Wood-based biochar. IPCC has no Tier 1 EF; "
                 "38% N2O suppression from Cayuela et al. 2015. "
                 "Set to 0 for conservative (no-credit) approach.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — CALCULATION FUNCTIONS
#  All internal values and returned dict values are in TONNES per ha per year.
# ══════════════════════════════════════════════════════════════════════════════

def _ef1(climate: str, fert_class: str) -> float:
    """Resolve EF1 (dimensionless) from 2019 Refinement Table 11.1."""
    if climate == "dry":
        return EF1["dry_all"]
    if climate == "wet":
        return EF1["wet_synthetic"] if fert_class == "synthetic" else EF1["wet_organic"]
    return EF1["global_default"]


def _ef4(climate: str) -> float:
    """Resolve EF4 (dimensionless) from 2019 Refinement Table 11.3."""
    return EF4.get(climate, EF4["wet"])


# ── Burning ─────────────────────────────────────────────────────────────────

def calc_burning(fuel_load_t_ha: float, land_type: str = "Cropland") -> dict:
    """
    CH4 and N2O from biomass burning per hectare.

    IPCC 2006 Vol.4 Ch.2, Eq. 2.27 (per-ha, tonnes form):
        L_fire = M_B × C_f × G_ef × 10⁻³
        [t gas ha⁻¹] = [t d.m. ha⁻¹] × [dimensionless] × [g kg⁻¹] × 10⁻³

    The 10⁻³ factor converts g/kg → t/t (same ratio), so with M_B in tonnes
    the output is directly in tonnes of gas per hectare.

    Parameters
    ----------
    fuel_load_t_ha : above-ground dry-matter residue available for burning, t d.m. ha⁻¹
                     Typical cropland: 1–6 t ha⁻¹. Set to 0 if no burning.
    land_type      : key of BURNING_GEF / COMBUSTION_FACTORS

    Returns
    -------
    dict — all gas and CO2e values in t ha⁻¹ yr⁻¹
    """
    if land_type not in BURNING_GEF:
        raise ValueError(f"Unknown land_type '{land_type}'. "
                         f"Options: {list(BURNING_GEF)}")
    Cf  = COMBUSTION_FACTORS[land_type]
    Gef = BURNING_GEF[land_type]
    out = {"source": "burning", "land_type": land_type,
           "fuel_load_t_ha": fuel_load_t_ha, "Cf": Cf}
    total_CO2e = 0.0
    for gas in ("CH4", "N2O"):
        t_ha  = fuel_load_t_ha * Cf * Gef[gas] * 1e-3   # t gas ha⁻¹
        co2e  = t_ha * GWP[gas]                           # t CO2e ha⁻¹
        out[f"{gas}_t_ha"]      = round(t_ha,  7)
        out[f"{gas}_CO2e_t_ha"] = round(co2e,  6)
        total_CO2e += co2e
    out["total_CO2e_t_ha"] = round(total_CO2e, 6)
    return out


# ── Fertilizer ───────────────────────────────────────────────────────────────

def list_synthetic_fertilizers():
    """Print all available synthetic fertilizer keys and their properties."""
    print("\n  Available synthetic fertilizer types:")
    print(f"  {'Key':<28} {'Display name':<42} {'N%':>5} {'FracGAS':>8}")
    print(f"  {'-'*28} {'-'*42} {'-'*5} {'-'*8}")
    for k, v in SYNTHETIC_FERTILIZERS.items():
        print(f"  {k:<28} {v['display']:<42} {v['n_fraction']*100:>5.1f} {v['frac_gas']*100:>7.1f}%")


def calc_fertilizer(
    fertilizer_type: str,
    application_rate_t_ha: float,
    climate: str = "wet",
    apply_leaching: bool = True,
    n_fraction_override: float = None,
) -> dict:
    """
    N2O (+ CO2 from urea hydrolysis, CH4 for organic) per hectare.
    IPCC 2019 Refinement Vol.4 Ch.11, Eqs 11.1 / 11.9 / 11.10.

    All EFs are dimensionless ratios (t per t), so inputs and outputs
    are in the same unit — tonnes per hectare per year.

    Parameters
    ----------
    fertilizer_type       : a key of SYNTHETIC_FERTILIZERS  (e.g. 'urea', 'dap', 'npk_blend')
                            or a key of ORGANIC_FERTILIZERS (e.g. 'compost', 'biochar')
    application_rate_t_ha : tonnes of product applied per ha yr⁻¹
    climate               : 'wet' | 'dry' | 'global'
    apply_leaching        : True for humid regions where leaching/runoff occurs
    n_fraction_override   : override default N content (t N per t product);
                            useful for non-standard NPK grades

    Returns
    -------
    dict — all values in t ha⁻¹ yr⁻¹

    Available synthetic types (call list_synthetic_fertilizers() to see all):
      urea, ammonium_nitrate, calcium_ammonium_nitrate, ammonium_sulfate,
      urea_ammonium_nitrate, map, dap, npk_blend, anhydrous_ammonia,
      ammonium_bicarbonate
    """
    is_synthetic = fertilizer_type in SYNTHETIC_FERTILIZERS
    is_organic   = fertilizer_type in ORGANIC_FERTILIZERS

    if not is_synthetic and not is_organic:
        raise ValueError(
            f"Unknown fertilizer_type '{fertilizer_type}'.\n"
            f"  Synthetic options : {list(SYNTHETIC_FERTILIZERS)}\n"
            f"  Organic options   : {list(ORGANIC_FERTILIZERS)}"
        )

    if is_synthetic:
        fert        = SYNTHETIC_FERTILIZERS[fertilizer_type]
        n_frac      = n_fraction_override or fert["n_fraction"]
        frac_gas    = fert["frac_gas"]
        ef1_val     = _ef1(climate, "synthetic")
        ch4_ref     = 0.0
        suppression = 0.0
        co2_ef      = fert["co2_ef"]    # t CO2 per t product (urea hydrolysis)
        display     = fert["display"]
        notes       = fert["notes"]
    else:
        fert        = ORGANIC_FERTILIZERS[fertilizer_type]
        n_frac      = n_fraction_override or fert["n_fraction"]
        frac_gas    = fert["frac_gas"]
        ef1_val     = _ef1(climate, "organic")
        ch4_ref     = fert["ch4_soil_t_per_t_n"]
        suppression = fert["biochar_n2o_suppression"]
        co2_ef      = 0.0
        display     = fertilizer_type.replace("_", " ").title()
        notes       = fert["notes"]

    ef4_val = _ef4(climate)
    N_t_ha  = application_rate_t_ha * n_frac         # t N ha⁻¹

    # Direct N2O — Eq. 11.1  [t N2O ha⁻¹]
    direct_raw = N_t_ha * ef1_val * N2O_N_TO_N2O
    direct_adj = direct_raw * (1.0 - suppression)    # biochar suppression only

    # Indirect N2O — volatilisation — Eq. 11.9  [t N2O ha⁻¹]
    ind_vol    = N_t_ha * frac_gas * ef4_val * N2O_N_TO_N2O

    # Indirect N2O — leaching — Eq. 11.10  [t N2O ha⁻¹]
    ind_leach  = (N_t_ha * FracLEACH_H * EF5 * N2O_N_TO_N2O) if apply_leaching else 0.0

    total_n2o  = direct_adj + ind_vol + ind_leach
    n2o_co2e   = total_n2o * GWP["N2O"]              # t CO2e ha⁻¹

    # CO2 from urea/UAN hydrolysis  [t CO2 ha⁻¹]  (IPCC 2006 Ch.11.4)
    co2_t_ha   = application_rate_t_ha * co2_ef
    co2_co2e   = co2_t_ha                             # GWP of CO2 = 1

    # CH4 from soil application  [t CH4 ha⁻¹]  (aerobic soils ≈ 0)
    ch4_t_ha   = N_t_ha * ch4_ref
    ch4_co2e   = ch4_t_ha * GWP["CH4"]

    total_co2e = n2o_co2e + co2_co2e + ch4_co2e

    return {
        "source":                   "fertilizer",
        "fertilizer_type":          fertilizer_type,
        "display_name":             display,
        "is_synthetic":             is_synthetic,
        "climate":                  climate,
        "application_rate_t_ha":    application_rate_t_ha,
        "n_fraction":               n_frac,
        "N_applied_t_ha":           round(N_t_ha,        6),
        "EF1_used":                 ef1_val,
        "EF4_used":                 ef4_val,
        "frac_gas_used":            frac_gas,
        "apply_leaching":           apply_leaching,
        # N2O  [t ha⁻¹ yr⁻¹]
        "direct_N2O_raw_t_ha":      round(direct_raw,    8),
        "biochar_suppression_frac": round(suppression,   3),
        "direct_N2O_adj_t_ha":      round(direct_adj,    8),
        "indirect_vol_N2O_t_ha":    round(ind_vol,       8),
        "indirect_leach_N2O_t_ha":  round(ind_leach,     8),
        "total_N2O_t_ha":           round(total_n2o,     8),
        "N2O_CO2e_t_ha":            round(n2o_co2e,      6),
        # CO2 from urea hydrolysis  [t ha⁻¹ yr⁻¹]
        "urea_CO2_t_ha":            round(co2_t_ha,      6),
        "urea_CO2e_t_ha":           round(co2_co2e,      6),
        # CH4  [t ha⁻¹ yr⁻¹]
        "CH4_t_ha":                 round(ch4_t_ha,      8),
        "CH4_CO2e_t_ha":            round(ch4_co2e,      6),
        # Grand total  [t CO2e ha⁻¹ yr⁻¹]
        "total_CO2e_t_ha":          round(total_co2e,    6),
        "notes":                    notes,
    }


# ── Scenario aggregation ─────────────────────────────────────────────────────

def build_scenario(
    label: str,
    burning: dict | None,
    fertilizers: list[dict],
) -> dict:
    """
    Aggregate burning + fertilizer components into one scenario total.

    Parameters
    ----------
    label       : human-readable scenario name
    burning     : result of calc_burning(), or None if no burning
    fertilizers : list of calc_fertilizer() results (can be empty)

    Returns
    -------
    dict — per-source breakdown and grand totals, all t ha⁻¹ yr⁻¹
    """
    components = []
    if burning:
        components.append(burning)
    components.extend(fertilizers)

    ch4_co2e_total = 0.0
    n2o_co2e_total = 0.0
    for c in components:
        ch4_co2e_total += c.get("CH4_CO2e_t_ha", 0.0)
        # For fertilizer: N2O_CO2e + urea_CO2e make up total (CH4 ≈ 0 for aerobic soil)
        # For burning: total = CH4 + N2O; extract N2O portion
        if c["source"] == "burning":
            n2o_co2e_total += c.get("N2O_CO2e_t_ha", 0.0)
        else:
            n2o_co2e_total += c.get("N2O_CO2e_t_ha", 0.0) + c.get("urea_CO2e_t_ha", 0.0)

    grand_total = ch4_co2e_total + n2o_co2e_total

    return {
        "label":            label,
        "components":       components,
        "CH4_CO2e_t_ha":    round(ch4_co2e_total, 6),
        "N2O_CO2e_t_ha":    round(n2o_co2e_total, 6),
        "total_CO2e_t_ha":  round(grand_total,    6),
    }


def emission_reduction(baseline: dict, project: dict) -> dict:
    """
    ER = Baseline − Project  (t CO2e ha⁻¹ yr⁻¹)
    Positive = net avoided emission (project is better than baseline).
    """
    return {
        "CH4_ER_CO2e_t_ha":   round(baseline["CH4_CO2e_t_ha"]   - project["CH4_CO2e_t_ha"],   6),
        "N2O_ER_CO2e_t_ha":   round(baseline["N2O_CO2e_t_ha"]   - project["N2O_CO2e_t_ha"],   6),
        "total_ER_CO2e_t_ha": round(baseline["total_CO2e_t_ha"] - project["total_CO2e_t_ha"], 6),
    }


def scale_to_area(value_t_ha: float, area_ha: float) -> float:
    """Scale t ha⁻¹ yr⁻¹ to total t yr⁻¹ for a given project area."""
    return round(value_t_ha * area_ha, 4)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — DISPLAY  (all values printed in tonnes)
# ══════════════════════════════════════════════════════════════════════════════

W = 70

def _hdr(title: str):
    print(f"\n  {'═'*(W-2)}")
    print(f"  {title}")
    print(f"  {'═'*(W-2)}")

def _sep():
    print(f"  {'-'*(W-2)}")


def print_burning_component(c: dict):
    _sep()
    print(f"  [BURNING]  Land type: {c['land_type']}")
    gef = BURNING_GEF[c['land_type']]
    print(f"  Fuel load (M_B)    : {c['fuel_load_t_ha']:>12.4f}  t d.m. ha⁻¹")
    print(f"  Combustion fac.    : {c['Cf']:>12.2f}  [IPCC 2006 Table 2.6]")
    print(f"  G_ef CH4 / N2O     : {gef['CH4']} / {gef['N2O']} g kg⁻¹ d.m.  [Table 2.5]")
    print(f"  CH4 emitted        : {c['CH4_t_ha']:>12.6f}  t CH4  ha⁻¹ yr⁻¹")
    print(f"  CH4 CO2e           : {c['CH4_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹  (GWP={GWP['CH4']})")
    print(f"  N2O emitted        : {c['N2O_t_ha']:>12.6f}  t N2O  ha⁻¹ yr⁻¹")
    print(f"  N2O CO2e           : {c['N2O_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
    print(f"  Subtotal CO2e      : {c['total_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")


def print_fertilizer_component(c: dict):
    _sep()
    print(f"  [FERTILIZER]  {c['display_name']}")
    print(f"  Application rate   : {c['application_rate_t_ha']:>12.4f}  t product ha⁻¹ yr⁻¹")
    print(f"  N fraction         : {c['n_fraction']*100:>12.2f}  %")
    print(f"  N applied          : {c['N_applied_t_ha']:>12.6f}  t N ha⁻¹ yr⁻¹")
    print(f"  EF1 used           : {c['EF1_used']*100:>12.3f}  %  [2019 Ref. Table 11.1]")
    print(f"  EF4 used           : {c['EF4_used']*100:>12.3f}  %  [2019 Ref. Table 11.3]")
    print(f"  FracGAS used       : {c['frac_gas_used']*100:>12.1f}  %  [2019 Ref. Table 7A.3]")
    print(f"  Direct N2O (raw)   : {c['direct_N2O_raw_t_ha']:>12.8f}  t N2O ha⁻¹ yr⁻¹  [Eq.11.1]")
    if c["biochar_suppression_frac"] > 0:
        print(f"  Biochar suppress.  : {c['biochar_suppression_frac']*100:>12.1f}  %  (Cayuela et al. 2015)")
        print(f"  Direct N2O (adj)   : {c['direct_N2O_adj_t_ha']:>12.8f}  t N2O ha⁻¹ yr⁻¹")
    print(f"  Indirect (vol)     : {c['indirect_vol_N2O_t_ha']:>12.8f}  t N2O ha⁻¹ yr⁻¹  [Eq.11.9]")
    print(f"  Indirect (leach)   : {c['indirect_leach_N2O_t_ha']:>12.8f}  t N2O ha⁻¹ yr⁻¹  [Eq.11.10]")
    print(f"  Total N2O          : {c['total_N2O_t_ha']:>12.8f}  t N2O ha⁻¹ yr⁻¹")
    print(f"  N2O CO2e           : {c['N2O_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹  (GWP={GWP['N2O']})")
    if c["urea_CO2_t_ha"] > 0:
        print(f"  Urea hydrolysis CO2: {c['urea_CO2_t_ha']:>12.6f}  t CO2  ha⁻¹ yr⁻¹  [IPCC 2006 Ch.11.4]")
        print(f"  Urea CO2e          : {c['urea_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    if c["CH4_t_ha"] > 0:
        print(f"  CH4 (soil)         : {c['CH4_t_ha']:>12.8f}  t CH4  ha⁻¹ yr⁻¹")
        print(f"  CH4 CO2e           : {c['CH4_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  Subtotal CO2e      : {c['total_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")


def print_scenario(scenario: dict):
    _hdr(f"SCENARIO: {scenario['label']}")
    for c in scenario["components"]:
        if c["source"] == "burning":
            print_burning_component(c)
        else:
            print_fertilizer_component(c)
    _sep()
    print(f"  SCENARIO TOTAL")
    print(f"  CH4 (all sources)  : {scenario['CH4_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  N2O (all sources)  : {scenario['N2O_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  GRAND TOTAL        : {scenario['total_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")


def print_er(er: dict, baseline: dict, project: dict, area_ha: float):
    _hdr("EMISSION REDUCTION  (Baseline − Project)")
    print(f"  Baseline total     : {baseline['total_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  Project total      : {project['total_CO2e_t_ha']:>12.6f}  t CO2e ha⁻¹ yr⁻¹")
    _sep()
    print(f"  CH4 ER             : {er['CH4_ER_CO2e_t_ha']:>+12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  N2O ER             : {er['N2O_ER_CO2e_t_ha']:>+12.6f}  t CO2e ha⁻¹ yr⁻¹")
    print(f"  TOTAL ER (per ha)  : {er['total_ER_CO2e_t_ha']:>+12.6f}  t CO2e ha⁻¹ yr⁻¹")
    total_er = scale_to_area(er['total_ER_CO2e_t_ha'], area_ha)
    print(f"  TOTAL ER ({area_ha:,.0f} ha) : {total_er:>+12.4f}  t CO2e yr⁻¹")
    print()
    sign = "✓ NET REDUCTION" if er["total_ER_CO2e_t_ha"] > 0 else "✗ NET INCREASE"
    print(f"  {sign}  ({abs(er['total_ER_CO2e_t_ha']):.6f} t CO2e ha⁻¹ yr⁻¹)")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — USER INPUTS & EXAMPLE RUN
#  All rates below are in TONNES per hectare per year.
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ── GLOBAL SETTINGS ──────────────────────────────────────────────────────
    CLIMATE         = "wet"       # 'wet' | 'dry' | 'global'
    APPLY_LEACHING  = True        # True for humid/sub-humid regions
    LAND_TYPE       = "Cropland"  # vegetation type for burning EFs
    PROJECT_AREA_HA = 500.0       # for scaled ER summary

    # Print the fertilizer catalog at startup
    list_synthetic_fertilizers()
    print()

    # ══════════════════════════════════════════════════════════════════════════
    #  BASELINE SCENARIO
    #  Example: full residue burning + DAP + some cattle manure
    # ══════════════════════════════════════════════════════════════════════════

    bl_burning = calc_burning(
        fuel_load_t_ha = 0,         # t d.m. ha⁻¹  (full residue load)
        land_type      = LAND_TYPE,
    )

    bl_synth = calc_fertilizer(
        fertilizer_type       = "dap",          # DAP 18-46-0
        application_rate_t_ha = 0.2,          # t DAP ha⁻¹ yr⁻¹
        climate               = CLIMATE,
        apply_leaching        = APPLY_LEACHING,
    )

    bl_manure = calc_fertilizer(
        fertilizer_type       = "cattle_manure_solid",
        application_rate_t_ha = 0,            # t solid manure ha⁻¹ yr⁻¹
        climate               = CLIMATE,
        apply_leaching        = APPLY_LEACHING,
    )

    BASELINE = build_scenario(
        label       = "Baseline ",
        burning     = bl_burning,
        fertilizers = [bl_synth, bl_manure],
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  PROJECT SCENARIO
    # ══════════════════════════════════════════════════════════════════════════

    wps_burning = calc_burning(
        fuel_load_t_ha = 0,         # t d.m. ha⁻¹  (80% burning avoided)
        land_type      = LAND_TYPE,
    )

    wps_synth = calc_fertilizer(
        fertilizer_type       = "dap",  # CAN 27-0-0
        application_rate_t_ha = 0.1,          # t CAN ha⁻¹ yr⁻¹
        climate               = CLIMATE,
        apply_leaching        = APPLY_LEACHING,
    )

    wps_compost = calc_fertilizer(
        fertilizer_type       = "compost",
        application_rate_t_ha = 1.5,            # t compost ha⁻¹ yr⁻¹
        climate               = CLIMATE,
        apply_leaching        = APPLY_LEACHING,
    )

    wps_biochar = calc_fertilizer(
        fertilizer_type       = "biochar",
        application_rate_t_ha = 0.5,            # t biochar ha⁻¹ yr⁻¹
        climate               = CLIMATE,
        apply_leaching        = APPLY_LEACHING,
    )

    PROJECT = build_scenario(
        label       = "Project",
        burning     = wps_burning,
        fertilizers = [wps_synth, wps_compost, wps_biochar],
    )

    # ── OUTPUT ───────────────────────────────────────────────────────────────
    print("=" * W)
    print("  VM0042 Approach 3 — Combined GHG Calculator  (per ha yr⁻¹)")
    print("  All values in TONNES  (t ha⁻¹ yr⁻¹ unless noted)")
    print("  Burning: IPCC 2006 Vol.4 Ch.2 Eq.2.27")
    print("  Fertilizer N2O: IPCC 2019 Refinement Vol.4 Ch.11 Eqs.11.1/11.9/11.10")
    print("  Urea CO2: IPCC 2006 Vol.4 Ch.11.4")
    print("=" * W)
    print(f"\n  Climate  : {CLIMATE.upper()}")
    print(f"  Leaching : {'Yes' if APPLY_LEACHING else 'No'}")
    print(f"  Land type: {LAND_TYPE}")

    print_scenario(BASELINE)
    print_scenario(PROJECT)

    ER = emission_reduction(BASELINE, PROJECT)
    print_er(ER, BASELINE, PROJECT, PROJECT_AREA_HA)

    print("=" * W)
