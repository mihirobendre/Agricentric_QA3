"""
VM0042 Quantification Approach 3
──────────────────────────────────────────────────────────────────────────────
N2O EMISSIONS FROM SYNTHETIC vs ORGANIC FERTILIZER APPLICATION
(Replacement of Synthetic Fertilizers with Organic Fertilizer)

Methodology:  IPCC 2006 Guidelines for National GHG Inventories
              Volume 4, Chapter 11, Section 11.2 — N2O from Managed Soils
              Equation 11.1 (Tier 1): Direct N2O from N inputs
              Equations 11.9 / 11.10 (Tier 1): Indirect N2O (volatilisation + leaching)

Key IPCC 2006 Vol.4 Ch.11 default values used:
  EF1        = 0.01   kg N2O-N (kg N input)^-1  [Table 11.1] — direct emissions
  EF4        = 0.01   kg N2O-N (kg NH3-N + NOx-N volatilised)^-1  [Table 11.3] — indirect (deposition)
  EF5        = 0.0075 kg N2O-N (kg N leached/runoff)^-1  [Table 11.3] — indirect (leaching)
  FracGASF   = 0.10   fraction of synthetic N volatilised as NH3+NOx  [Table 11.3]
  FracGASM   = 0.20   fraction of organic N volatilised as NH3+NOx    [Table 11.3]
  FracLEACH  = 0.30   fraction of N that leaches (if applicable)      [Table 11.3]

N2O-to-N2O-N conversion:
  N2O = N2O-N x (44/28)

GWP values (AR5, 100-yr):
  N2O = 265

In VM0042 Approach 3, the emission reduction from replacing synthetic
fertilizer with organic fertilizer is:
  ER_N2O = N2O_BL(synthetic) - N2O_WPS(organic)

Both direct and indirect pathways are computed separately and summed.
──────────────────────────────────────────────────────────────────────────────
"""

# ── IPCC 2006 Vol.4 Ch.11 Table 11.1 ────────────────────────────────────────
# EF1: Emission factor for direct N2O from N inputs
#   Units: kg N2O-N  (kg N input)^-1
#   Applies equally to synthetic fertilizer (FSN) and organic fertilizer (FON)
EF1 = 0.01       # [Table 11.1, default Tier 1]

# ── IPCC 2006 Vol.4 Ch.11 Table 11.3 ────────────────────────────────────────
# Indirect pathway emission factors and fractions

# EF4: N2O from atmospheric deposition of volatilised N
#   kg N2O-N (kg NH3-N + NOx-N volatilised)^-1
EF4 = 0.01       # [Table 11.3]

# EF5: N2O from N leaching and runoff
#   kg N2O-N (kg N leached)^-1
EF5 = 0.0075     # [Table 11.3]

# FracGASF: fraction of synthetic fertilizer N that volatilises as NH3 + NOx
#   kg N volatilised (kg N applied)^-1
FracGASF = 0.10  # [Table 11.3]

# FracGASM: fraction of organic fertilizer N that volatilises as NH3 + NOx
#   kg N volatilised (kg N applied)^-1
FracGASM = 0.20  # [Table 11.3]

# FracLEACH: fraction of N that is lost via leaching and runoff
#   Only applicable in regions where leaching/runoff occurs
#   kg N leached (kg N applied)^-1
FracLEACH = 0.30  # [Table 11.3]

# ── Molecular weight ratio for N2O-N -> N2O conversion ────────────────────
N2O_N_TO_N2O = 44.0 / 28.0   # = 44/28

# ── GWP (AR5, 100-yr) ──────────────────────────────────────────────────────
GWP_N2O = 265


def direct_n2o_kg(N_kg: float) -> float:
    """
    Direct N2O emissions from N applied to soil.
    IPCC 2006 Vol.4 Ch.11, Eq. 11.1 (simplified for a single N source):

        N2O-N_direct = F_N x EF1
        N2O_direct   = N2O-N_direct x (44/28)

    Parameters
    ----------
    N_kg : total nitrogen applied, kg N yr^-1

    Returns
    -------
    float : N2O emitted, kg N2O yr^-1
    """
    n2o_n = N_kg * EF1
    return n2o_n * N2O_N_TO_N2O


def indirect_n2o_volatilisation_kg(N_kg: float, frac_gas: float) -> float:
    """
    Indirect N2O from atmospheric deposition of volatilised N.
    IPCC 2006 Vol.4 Ch.11, Eq. 11.9:

        N2O-N_ATdep = F_N x FracGAS x EF4
        N2O_ATdep   = N2O-N_ATdep x (44/28)

    Parameters
    ----------
    N_kg     : total nitrogen applied, kg N yr^-1
    frac_gas : volatilisation fraction (FracGASF for synthetic, FracGASM for organic)

    Returns
    -------
    float : N2O emitted via deposition pathway, kg N2O yr^-1
    """
    n2o_n = N_kg * frac_gas * EF4
    return n2o_n * N2O_N_TO_N2O


def indirect_n2o_leaching_kg(N_kg: float, apply_leaching: bool = True) -> float:
    """
    Indirect N2O from N leaching and runoff.
    IPCC 2006 Vol.4 Ch.11, Eq. 11.10:

        N2O-N_LEACH = F_N x FracLEACH x EF5
        N2O_LEACH   = N2O-N_LEACH x (44/28)

    Set apply_leaching=False for dry regions where leaching does not occur.

    Parameters
    ----------
    N_kg           : total nitrogen applied, kg N yr^-1
    apply_leaching : True if region is wet enough for leaching/runoff

    Returns
    -------
    float : N2O emitted via leaching pathway, kg N2O yr^-1
    """
    if not apply_leaching:
        return 0.0
    n2o_n = N_kg * FracLEACH * EF5
    return n2o_n * N2O_N_TO_N2O


def calculate_fertilizer_n2o(
    N_applied_kg: float,
    fertilizer_type: str = "synthetic",
    apply_leaching: bool = True,
    scenario: str = "Baseline",
) -> dict:
    """
    Full N2O calculation for a fertilizer application event (Tier 1, IPCC 2006).

    Parameters
    ----------
    N_applied_kg    : kg of N applied per year (as fertilizer N content)
    fertilizer_type : 'synthetic' (uses FracGASF=0.10) or 'organic' (FracGASM=0.20)
    apply_leaching  : True if region has leaching/runoff (e.g. humid tropics)
    scenario        : 'Baseline' (synthetic) or 'Project' (organic)

    Returns
    -------
    dict with all components in kg N2O and t CO2e
    """
    frac_gas = FracGASF if fertilizer_type == "synthetic" else FracGASM

    direct_kg     = direct_n2o_kg(N_applied_kg)
    indirect_v_kg = indirect_n2o_volatilisation_kg(N_applied_kg, frac_gas)
    indirect_l_kg = indirect_n2o_leaching_kg(N_applied_kg, apply_leaching)
    total_kg      = direct_kg + indirect_v_kg + indirect_l_kg

    # Convert to tonnes
    total_t   = total_kg / 1000.0
    total_CO2e = total_t * GWP_N2O

    return {
        "scenario":           scenario,
        "fertilizer_type":    fertilizer_type,
        "N_applied_kg":       N_applied_kg,
        "frac_gas":           frac_gas,
        "apply_leaching":     apply_leaching,
        # Direct (Eq. 11.1)
        "direct_N2O_kg":      round(direct_kg, 4),
        # Indirect volatilisation (Eq. 11.9)
        "indirect_vol_N2O_kg": round(indirect_v_kg, 4),
        # Indirect leaching (Eq. 11.10)
        "indirect_leach_N2O_kg": round(indirect_l_kg, 4),
        # Totals
        "total_N2O_kg":       round(total_kg, 4),
        "total_N2O_t":        round(total_t, 6),
        "total_CO2e":         round(total_CO2e, 4),
    }


def calculate_fertilizer_er(baseline: dict, project: dict) -> dict:
    """
    Emission reduction from replacing synthetic with organic fertilizer.
    ER = BL_N2O - Project_N2O   (t CO2e yr^-1)
    """
    return {
        "direct_N2O_ER_kg":       round(baseline["direct_N2O_kg"]       - project["direct_N2O_kg"], 4),
        "indirect_vol_N2O_ER_kg": round(baseline["indirect_vol_N2O_kg"] - project["indirect_vol_N2O_kg"], 4),
        "indirect_leach_N2O_ER_kg": round(baseline["indirect_leach_N2O_kg"] - project["indirect_leach_N2O_kg"], 4),
        "total_N2O_ER_kg":        round(baseline["total_N2O_kg"]         - project["total_N2O_kg"], 4),
        "total_N2O_ER_t":         round(baseline["total_N2O_t"]          - project["total_N2O_t"], 6),
        "total_ER_CO2e":          round(baseline["total_CO2e"]           - project["total_CO2e"], 4),
    }


def print_fertilizer_scenario(r: dict):
    print(f"\n  {'-'*58}")
    print(f"  {r['scenario'].upper()}  ({r['fertilizer_type']} fertilizer)")
    print(f"  {'-'*58}")
    print(f"  N applied           : {r['N_applied_kg']:>10.2f}  kg N yr^-1")
    print(f"  Volatilisation frac : {r['frac_gas']:>10.2f}  [IPCC Table 11.3]")
    print(f"  Leaching applied    : {'Yes' if r['apply_leaching'] else 'No'}")
    print()
    print(f"  Direct N2O (Eq.11.1):       {r['direct_N2O_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  Indirect (vol, Eq.11.9):    {r['indirect_vol_N2O_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  Indirect (leach, Eq.11.10): {r['indirect_leach_N2O_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  TOTAL N2O           : {r['total_N2O_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  TOTAL N2O           : {r['total_N2O_t']:>10.6f}  t N2O yr^-1")
    print(f"  TOTAL               : {r['total_CO2e']:>10.4f}  t CO2e yr^-1  (GWP={GWP_N2O})")


# ============================================================================
# EXAMPLE CALCULATION — update these inputs for your project
# ============================================================================
if __name__ == "__main__":

    # USER INPUTS
    N_SYNTHETIC_KG = 5000.0   # kg N yr^-1 applied as synthetic fertilizer (baseline)
    N_ORGANIC_KG   = 5000.0   # kg N yr^-1 applied as organic fertilizer   (project)
                               # (same total N is common assumption in VM0042)
    APPLY_LEACHING = True      # Set False for arid/semi-arid regions

    print("=" * 62)
    print("  VM0042 Approach 3 — Fertilizer Replacement")
    print("  N2O Emissions: Synthetic vs Organic Fertilizer")
    print("  IPCC 2006 Vol.4 Ch.11, Eqs. 11.1 / 11.9 / 11.10")
    print("=" * 62)
    print()
    print("  IPCC 2006 Vol.4 Ch.11 Emission Factors Used:")
    print(f"  EF1       = {EF1}    [Table 11.1] — direct, kg N2O-N (kg N)^-1")
    print(f"  EF4       = {EF4}    [Table 11.3] — indirect deposition, kg N2O-N (kg N vol.)^-1")
    print(f"  EF5       = {EF5}  [Table 11.3] — indirect leaching, kg N2O-N (kg N leach)^-1")
    print(f"  FracGASF  = {FracGASF}    [Table 11.3] — synthetic volatilisation fraction")
    print(f"  FracGASM  = {FracGASM}    [Table 11.3] — organic volatilisation fraction")
    print(f"  FracLEACH = {FracLEACH}    [Table 11.3] — leaching/runoff fraction")

    baseline = calculate_fertilizer_n2o(
        N_SYNTHETIC_KG, fertilizer_type="synthetic",
        apply_leaching=APPLY_LEACHING, scenario="Baseline"
    )
    project = calculate_fertilizer_n2o(
        N_ORGANIC_KG, fertilizer_type="organic",
        apply_leaching=APPLY_LEACHING, scenario="Project"
    )
    er = calculate_fertilizer_er(baseline, project)

    print_fertilizer_scenario(baseline)
    print_fertilizer_scenario(project)

    print(f"\n  {'-'*58}")
    print("  EMISSION REDUCTIONS (Baseline - Project)")
    print(f"  {'-'*58}")
    print(f"  Direct ER           : {er['direct_N2O_ER_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  Indirect (vol) ER   : {er['indirect_vol_N2O_ER_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  Indirect (leach) ER : {er['indirect_leach_N2O_ER_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  TOTAL N2O ER        : {er['total_N2O_ER_kg']:>10.4f}  kg N2O yr^-1")
    print(f"  TOTAL N2O ER        : {er['total_N2O_ER_t']:>10.6f}  t N2O yr^-1")
    print(f"  TOTAL ER            : {er['total_ER_CO2e']:>10.4f}  t CO2e yr^-1")
    print()
    print("  Note: These ERs map to VM0042 Approach 3 term:")
    print("  GHG_BL,FERTILIZER - GHG_WPS,FERTILIZER  (fertilizer replacement component)")
    print()
    print("  Key assumption: Organic fertilizer replaces synthetic on a")
    print("  kg-N-for-kg-N basis. If N rates differ, update N_ORGANIC_KG.")
    print("=" * 62)
