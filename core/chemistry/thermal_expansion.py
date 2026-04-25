"""Thermal expansion coefficient calculation for ceramic glazes.

Uses the Winkler-Mackenzie / Appen molar method:
  CTE = Σ (mole_fraction(oxide) × coefficient(oxide))

Mole fractions are calculated from the UMF formula by dividing each oxide's
UMF value by the sum of ALL oxide UMF values (not just fluxes).

Coefficients are from ceramics-foundation/data/thermal-expansion.json
(Appen 1950 / Sankey revisions), in units of ×10⁻⁶ /°C.
"""

from typing import Dict, Optional

from .materials import THERMAL_EXPANSION_COEFFICIENTS

# Typical clay body CTE ranges for compatibility checking
_CLAY_BODY_CTE_RANGES = {
    "porcelain": (4.0, 5.5),
    "porcelainous_stoneware": (5.0, 6.0),
    "stoneware": (5.5, 6.5),
    "sculptural_stoneware": (5.5, 7.0),
    "earthenware": (7.0, 8.5),
    "terra_cotta": (7.5, 9.0),
}


def calculate_cte(umf_formula: Dict[str, float]) -> Optional[float]:
    """Calculate thermal expansion coefficient from UMF formula.

    Args:
        umf_formula: Dict of {oxide_name: UMF_value}

    Returns:
        CTE in ×10⁻⁶ /°C, or None if no calculable oxides.
    """
    if not umf_formula:
        return None

    # Sum of all UMF values = total moles relative to flux sum = 1.0
    total_moles = sum(umf_formula.values())
    if total_moles == 0:
        return None

    cte = 0.0
    for oxide, umf_value in umf_formula.items():
        coeff = THERMAL_EXPANSION_COEFFICIENTS.get(oxide)
        if coeff is None:
            continue
        mole_fraction = umf_value / total_moles
        cte += mole_fraction * coeff

    return round(cte, 2)


def cte_compatibility(cte_a: float, cte_b: float) -> tuple:
    """Assess CTE compatibility between two glazes.

    Returns:
        (risk_level, mismatch, description)
        risk_level: 'low' | 'medium' | 'high'
        mismatch: cte_b - cte_a
        description: human-readable explanation
    """
    mismatch = round(cte_b - cte_a, 2)
    abs_mismatch = abs(mismatch)

    if abs_mismatch < 0.5:
        risk = "low"
        desc = f"Excellent thermal expansion match ({mismatch:+.2f} ×10⁻⁶/°C)"
    elif abs_mismatch < 1.5:
        risk = "medium"
        desc = f"Moderate thermal expansion mismatch ({mismatch:+.2f} ×10⁻⁶/°C) — test on tiles"
    else:
        risk = "high"
        if mismatch > 0:
            desc = f"High mismatch ({mismatch:+.2f} ×10⁻⁶/°C) — top glaze expands more than base. Crazing risk if base is stiffer."
        else:
            desc = f"High mismatch ({mismatch:+.2f} ×10⁻⁶/°C) — base glaze expands more than top. Shivering risk if top is stiffer."

    return risk, mismatch, desc


def clay_body_compatibility(cte: float, clay_type: str = "stoneware") -> dict:
    """Compare glaze CTE to typical clay body CTE range.

    Args:
        cte: Glaze CTE in ×10⁻⁶/°C
        clay_type: Key from _CLAY_BODY_CTE_RANGES

    Returns:
        Dict with fit assessment.
    """
    range_low, range_high = _CLAY_BODY_CTE_RANGES.get(clay_type, (5.5, 6.5))
    range_mid = (range_low + range_high) / 2

    if cte < range_low:
        delta = range_low - cte
        fit = "tight"
        risk = f"Glaze CTE ({cte}) is lower than typical {clay_type} body ({range_low}-{range_high}). Shivering possible if glaze is under tension."
    elif cte > range_high:
        delta = cte - range_high
        fit = "loose"
        risk = f"Glaze CTE ({cte}) is higher than typical {clay_type} body ({range_low}-{range_high}). Crazing likely."
    else:
        delta = abs(cte - range_mid)
        fit = "good"
        risk = f"Glaze CTE ({cte}) falls within typical {clay_type} body range ({range_low}-{range_high}). Good fit expected."

    return {
        "clay_type": clay_type,
        "clay_cte_range": [range_low, range_high],
        "glaze_cte": cte,
        "fit": fit,
        "delta_from_range": round(delta, 2),
        "assessment": risk,
    }


def get_clay_cte_range(clay_type: str) -> Optional[tuple]:
    """Get typical CTE range for a clay body type."""
    return _CLAY_BODY_CTE_RANGES.get(clay_type)
