"""
VM0042 Quantification Approach 3 — MODULE 2
N2O Emissions: Replacement of Synthetic Fertilizer with Organic Fertilizer
===========================================================================
Methodology:  IPCC 2006 GL, Volume 4, Chapter 11
              Equations 11.1, 11.9, 11.10

Under VM0042 Approach 3, the project replaces synthetic N fertilizer (FSN)
with organic fertilizer (FON, e.g. compost/manure). This script calculates:

  (A) DIRECT N2O emissions (Eq. 11.1 / Tier 1)
        N2O_direct-N = (FSN + FON) x EF1
        N2O_direct   = N2O_direct-N x (44/28)

  (B) INDIRECT N2O — atmospheric deposition (Eq. 11.9)
        N2O_ATD-N = [(FSN x FracGASF) + (FON x FracGASM)] x EF4
        N2O_ATD   = N2O_ATD-N x (44/28)

  (C) INDIRECT N2O — leaching / runoff (Eq. 11.10)
        N2O_L-N = (FSN + FON) x FracLEACH x EF5
        N2O_L   = N2O_L-N x (44/28)

Emission Reduction under VM0042 Approach 3:
  ER_N2O = Baseline total N2O (synthetic fert) - Project total N2O (organic fert)

IPCC Default Factors (Tables 11.1 and 11.3, Chapter 11, Vol.4):
  EF1        = 0.01    kg N2O-N (kg N input)-1          [direct, Table 11.1]
  FracGASF   = 0.10    kg N volatilised (kg N applied)-1 [synthetic, Table 11.3]
  FracGASM   = 0.20    kg N volatilised (kg N applied)-1 [organic, Table 11.3]
  EF4        = 0.010   kg N2O-N (kg N volatilised)-1    [ATD, Table 11.3]
  FracLEACH  = 0.30    kg N leached (kg N additions)-1  [humid only, Table 11.3]
  EF5        = 0.0075  kg N2O-N (kg N leached)-1        [leaching, Table 11.3]

Note: FracLEACH = 0 for dryland/arid regions (set humid_region=False).
GWP N2O = 265 (AR5, 100-yr).
"""

# ─────────────────────────────────────────────────────────────────────────────
# IPCC 2006 DEFAULT EMISSION & PARTITIONING FACTORS
# ─────────────────────────────────────────────────────────────────────────────
EF1        = 0.01
FRAC_GASF  = 0.10
FRAC_GASM  = 0.20
EF4        = 0.010
FRAC_LEACH = 0.30
EF5        = 0.0075
MW_CONV    = 44 / 28   # N2O-N -> N2O
GWP_N2O    = 265


def n2o_direct(fsn_kg_N, fon_kg_N, ef1=EF1):
    """Direct N2O — IPCC Eq. 11.1 (Tier 1)."""
    n_total  = fsn_kg_N + fon_kg_N
    n2o_n_kg = n_total * ef1
    n2o_kg   = n2o_n_kg * MW_CONV
    return {"N_total_kg": n_total, "N2O_N_kg": n2o_n_kg,
            "N2O_kg": n2o_kg, "N2O_t": n2o_kg / 1_000}


def n2o_indirect_atd(fsn_kg_N, fon_kg_N,
                     frac_gasf=FRAC_GASF, frac_gasm=FRAC_GASM, ef4=EF4):
    """Indirect N2O via atmospheric deposition — IPCC Eq. 11.9 (Tier 1)."""
    n_vol    = fsn_kg_N * frac_gasf + fon_kg_N * frac_gasm
    n2o_n_kg = n_vol * ef4
    n2o_kg   = n2o_n_kg * MW_CONV
    return {"N_volatilised_kg": n_vol, "N2O_N_kg": n2o_n_kg,
            "N2O_kg": n2o_kg, "N2O_t": n2o_kg / 1_000}


def n2o_indirect_leach(fsn_kg_N, fon_kg_N,
                       frac_leach=FRAC_LEACH, ef5=EF5, humid_region=True):
    """Indirect N2O via leaching/runoff — IPCC Eq. 11.10 (Tier 1)."""
    fl       = frac_leach if humid_region else 0.0
    n_leach  = (fsn_kg_N + fon_kg_N) * fl
    n2o_n_kg = n_leach * ef5
    n2o_kg   = n2o_n_kg * MW_CONV
    return {"FracLEACH": fl, "N_leached_kg": n_leach, "N2O_N_kg": n2o_n_kg,
            "N2O_kg": n2o_kg, "N2O_t": n2o_kg / 1_000}


def total_n2o(fsn_kg_N, fon_kg_N,
              ef1=EF1, frac_gasf=FRAC_GASF, frac_gasm=FRAC_GASM,
              ef4=EF4, frac_leach=FRAC_LEACH, ef5=EF5,
              humid_region=True, label=""):
    """Aggregate direct + indirect N2O for a given N-input scenario."""
    d  = n2o_direct(fsn_kg_N, fon_kg_N, ef1)
    ia = n2o_indirect_atd(fsn_kg_N, fon_kg_N, frac_gasf, frac_gasm, ef4)
    il = n2o_indirect_leach(fsn_kg_N, fon_kg_N, frac_leach, ef5, humid_region)
    total_t = d["N2O_t"] + ia["N2O_t"] + il["N2O_t"]
    return {
        "label": label, "FSN_kg_N": fsn_kg_N, "FON_kg_N": fon_kg_N,
        "direct_N2O_t": d["N2O_t"],
        "indirect_ATD_N2O_t": ia["N2O_t"],
        "indirect_L_N2O_t": il["N2O_t"],
        "total_N2O_t": total_t,
        "total_CO2eq_t": total_t * GWP_N2O,
        "_direct": d, "_indirect_ATD": ia, "_indirect_L": il,
    }


def emission_reductions_n2o(baseline, project):
    """ER = Baseline - Project (tonnes N2O and CO2eq)."""
    er = baseline["total_N2O_t"] - project["total_N2O_t"]
    return {"ER_N2O_t": er, "ER_CO2eq_t": er * GWP_N2O}


def print_scenario(r):
    sep = "-" * 62
    print(f"\n{sep}")
    print(f"  Scenario: {r['label']}")
    print(sep)
    print(f"  Synthetic N applied (FSN)    : {r['FSN_kg_N']:>12,.2f}  kg N yr-1")
    print(f"  Organic N applied   (FON)    : {r['FON_kg_N']:>12,.2f}  kg N yr-1")
    print(f"  Direct N2O  (Eq.11.1)        : {r['direct_N2O_t']:>12,.5f}  t N2O yr-1")
    print(f"  Indirect N2O-ATD (Eq.11.9)   : {r['indirect_ATD_N2O_t']:>12,.5f}  t N2O yr-1")
    print(f"  Indirect N2O-L   (Eq.11.10)  : {r['indirect_L_N2O_t']:>12,.5f}  t N2O yr-1")
    print(f"  TOTAL N2O                    : {r['total_N2O_t']:>12,.5f}  t N2O yr-1")
    print(f"  TOTAL CO2eq (AR5 GWP=265)    : {r['total_CO2eq_t']:>12,.3f}  t CO2eq yr-1")
    print(sep)


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE — REPLACE WITH YOUR PROJECT-SPECIFIC INPUTS
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n" + "=" * 62)
    print("  VM0042 Approach 3 | Synthetic -> Organic Fertilizer")
    print("  IPCC 2006 GL Vol.4 Ch.11, Eqs. 11.1, 11.9, 11.10")
    print("=" * 62)

    print(f"\n  IPCC default factors (Tables 11.1 & 11.3):")
    print(f"    EF1        = {EF1}    direct N2O-N emission factor")
    print(f"    FracGASF   = {FRAC_GASF}    synthetic N volatilisation fraction")
    print(f"    FracGASM   = {FRAC_GASM}    organic N volatilisation fraction")
    print(f"    EF4        = {EF4}  atmospheric deposition EF")
    print(f"    FracLEACH  = {FRAC_LEACH}    leaching fraction (humid regions)")
    print(f"    EF5        = {EF5} leaching/runoff EF")
    print(f"    GWP N2O    = {GWP_N2O}   (AR5, 100-yr)")

    # Update these values with your project's annual N application rates
    TOTAL_N_KG = 5_000.0   # kg N yr-1 (total N applied to project area)

    # BASELINE: all N as synthetic fertilizer
    baseline = total_n2o(
        fsn_kg_N   = TOTAL_N_KG,
        fon_kg_N   = 0.0,
        humid_region = True,       # set False for dryland/arid sites
        label = "Baseline -- synthetic fertilizer only",
    )

    # PROJECT: all N as organic fertilizer (compost / manure)
    project = total_n2o(
        fsn_kg_N   = 0.0,
        fon_kg_N   = TOTAL_N_KG,
        humid_region = True,
        label = "Project -- organic fertilizer (compost/manure)",
    )

    print_scenario(baseline)
    print_scenario(project)

    er = emission_reductions_n2o(baseline, project)
    print(f"\n  EMISSION REDUCTIONS  (Baseline - Project):")
    print(f"    ER N2O                     : {er['ER_N2O_t']:>10,.5f}  t N2O yr-1")
    print(f"    ER CO2eq (AR5 GWP=265)     : {er['ER_CO2eq_t']:>10,.3f}  t CO2eq yr-1")

    print("\n\n  PARTIAL SHIFT SCENARIOS (5000 kg N total, humid region)")
    print("  " + "-" * 62)
    print(f"  {'% Organic':>9} {'FSN (kg N)':>11} {'FON (kg N)':>11} "
          f"{'N2O total (t)':>14} {'CO2eq (t)':>10}")
    print("  " + "-" * 62)
    for pct in [0, 25, 50, 75, 100]:
        fon = TOTAL_N_KG * pct / 100
        fsn = TOTAL_N_KG - fon
        r   = total_n2o(fsn, fon, humid_region=True)
        print(f"  {pct:>8}%  {fsn:>11,.0f}  {fon:>11,.0f}  "
              f"{r['total_N2O_t']:>14,.5f}  {r['total_CO2eq_t']:>10,.2f}")
    print()
