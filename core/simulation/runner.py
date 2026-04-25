"""Chemistry simulation runner for glaze combinations."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def simulate_combo(
    base_glaze, top_glaze, combo, db_path: str = "glaze.db"
) -> Dict[str, Any]:
    """
    Run AI chemistry simulation for a glaze combination.
    Returns prediction dict with grade and detailed analysis.
    """
    # Pre-compute UMF and compatibility
    base_umf, top_umf, compat = _precompute_chemistry(base_glaze, top_glaze, combo)

    try:
        from core.ai import get_kama

        kama = get_kama()
    except Exception as e:
        logger.warning(f"AI not available for simulation: {e}")
        return _fallback_prediction_with_umf(
            base_glaze, top_glaze, combo, base_umf, top_umf, compat
        )

    # Build context from glaze data
    base_info = _glaze_context(base_glaze)
    top_info = _glaze_context(top_glaze)

    # Enhance context with UMF data if available
    if base_umf and base_umf.success:
        base_info += "\n" + _glaze_context_with_umf(base_glaze, base_umf)
    if top_umf and top_umf.success:
        top_info += "\n" + _glaze_context_with_umf(top_glaze, top_umf)

    # Load chemistry rules from DB
    rules_context = _load_chemistry_rules(db_path)

    # Load simulation prompt template
    prompt_path = Path(__file__).parent / "simulation-prompt.md"
    prompt_template = prompt_path.read_text() if prompt_path.exists() else ""

    # Build compatibility section if available
    compat_section = ""
    if compat and compat.success:
        compat_section = f"""
## COMPATIBILITY ANALYSIS (PRE-CALCULATED)

{_compatibility_context(compat)}

Use this pre-calculated data to inform your analysis. You may adjust your assessment
if your chemistry reasoning suggests a different conclusion, but explain why.
"""

    question = f"""{prompt_template}

## COMBINATION TO ANALYZE

### Base Glaze (applied first): {combo.base}
{base_info}

### Top Glaze (applied last): {combo.top}
{top_info}

## RELEVANT CHEMISTRY RULES
{rules_context}
{compat_section}
Analyze this combination and return ONLY valid JSON with your prediction."""

    try:
        # Use non-streaming ask
        response = kama.ask(question, session_id=None, user_id=None)

        # Parse JSON from response
        prediction = _parse_json_response(response)

        if not prediction:
            return _fallback_prediction_with_umf(
                base_glaze, top_glaze, combo, base_umf, top_umf, compat
            )

        return prediction

    except Exception as e:
        logger.error(f"Simulation failed for {combo.top} over {combo.base}: {e}")
        return _fallback_prediction_with_umf(
            base_glaze, top_glaze, combo, base_umf, top_umf, compat
        )


def _precompute_chemistry(base_glaze, top_glaze, combo):
    """Pre-compute UMF and compatibility for both glazes."""
    base_umf = None
    top_umf = None
    compat = None

    try:
        from core.chemistry import calculate_umf, CompatibilityAnalyzer

        # Calculate UMF for each glaze
        base_recipe = getattr(base_glaze, "recipe", None) if base_glaze else None
        top_recipe = getattr(top_glaze, "recipe", None) if top_glaze else None

        if base_recipe:
            base_umf = calculate_umf(base_recipe)
            if not base_umf.success:
                logger.debug(
                    f"Could not calculate UMF for base {combo.base}: {base_umf.error}"
                )

        if top_recipe:
            top_umf = calculate_umf(top_recipe)
            if not top_umf.success:
                logger.debug(
                    f"Could not calculate UMF for top {combo.top}: {top_umf.error}"
                )

        # Calculate compatibility if both UMFs succeeded
        if base_umf and base_umf.success and top_umf and top_umf.success:
            analyzer = CompatibilityAnalyzer()
            compat = analyzer.analyze(
                base_recipe=base_recipe,
                top_recipe=top_recipe,
                base_name=combo.base or "",
                top_name=combo.top or "",
            )
    except Exception as e:
        logger.debug(f"UMF pre-computation failed: {e}")

    return base_umf, top_umf, compat


def _glaze_context(glaze) -> str:
    """Build context string from a glaze object."""
    if not glaze:
        return "Glaze data not available."

    parts = []
    if glaze.chemistry:
        parts.append(f"Chemistry: {glaze.chemistry}")
    if glaze.behavior:
        parts.append(f"Behavior: {glaze.behavior}")
    if glaze.layering:
        parts.append(f"Layering: {glaze.layering}")
    if glaze.warning:
        parts.append(f"Warning: {glaze.warning}")
    if glaze.recipe:
        parts.append(f"Recipe: {glaze.recipe}")

    return "\n".join(parts) if parts else "No detailed data available."


def _glaze_context_with_umf(glaze, umf_result) -> str:
    """Append UMF analysis to glaze context."""
    parts = ["UMF Analysis (calculated):"]

    if umf_result.umf_formula:
        parts.append("Unity Molecular Formula (normalized to flux=1.0):")
        for oxide, value in sorted(umf_result.umf_formula.items(), key=lambda x: -x[1]):
            parts.append(f"  {oxide}: {value:.4f}")

    if umf_result.surface_prediction:
        parts.append(f"Surface prediction: {umf_result.surface_prediction}")

    if umf_result.ratios:
        sio2_al2o3 = umf_result.ratios.get("sio2_al2o3")
        if sio2_al2o3 is not None:
            parts.append(f"SiO2:Al2O3 ratio: {sio2_al2o3}")
        knao_cao = umf_result.ratios.get("knao_cao")
        if knao_cao is not None:
            parts.append(f"KNaO:CaO ratio: {knao_cao}")

    if umf_result.limit_warnings:
        parts.append("Limit warnings:")
        for w in umf_result.limit_warnings:
            parts.append(f"  - {w}")

    return "\n".join(parts)


def _compatibility_context(compat) -> str:
    """Format compatibility analysis as text for the AI prompt."""
    parts = []

    parts.append(
        f"Compatibility score: {compat.score:.0%} ({'compatible' if compat.compatible else 'incompatible'})"
    )
    parts.append(f"Thermal expansion risk: {compat.thermal_expansion_risk}")
    parts.append(f"Fluidity interaction: {compat.fluidity_interaction}")

    if compat.risk_factors:
        parts.append("Risk factors:")
        for r in compat.risk_factors:
            parts.append(f"  - {r}")

    if compat.warnings:
        parts.append("Warnings:")
        for w in compat.warnings:
            parts.append(f"  - {w}")

    if compat.oxide_interactions:
        parts.append("Oxide interactions:")
        for o in compat.oxide_interactions:
            parts.append(f"  - {o}")

    return "\n".join(parts)


def _load_chemistry_rules(db_path: str) -> str:
    """Load relevant chemistry rules from the database."""
    from core.db import connect_db

    try:
        conn = connect_db(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, title, description, confidence
            FROM chemistry_rules
            WHERE category IN ('color_prediction', 'layering_principle', 'common_issue', 'umf_interpretation')
            AND confidence = 'high'
            ORDER BY category
            LIMIT 30
        """)
        rules = cursor.fetchall()
        conn.close()

        if not rules:
            return "No chemistry rules available."

        return "\n".join(
            f"- [{r[0]}] {r[1]}: {r[2]} (confidence: {r[3]})" for r in rules
        )
    except Exception as e:
        logger.warning(f"Failed to load chemistry rules: {e}")
        return "Could not load chemistry rules."


def _parse_json_response(response: str) -> Optional[Dict]:
    """Parse JSON from AI response, handling markdown wrapping."""
    if not response:
        return None

    # Try direct parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    import re

    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    start = response.find("{")
    end = response.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(response[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _fallback_prediction(
    base_glaze, top_glaze, combo, base_umf=None, top_umf=None, compat=None
) -> Dict[str, Any]:
    """Generate a rule-based prediction when AI is not available."""
    return _fallback_prediction_with_umf(
        base_glaze, top_glaze, combo, base_umf, top_umf, compat
    )


def _fallback_prediction_with_umf(
    base_glaze, top_glaze, combo, base_umf=None, top_umf=None, compat=None
) -> Dict[str, Any]:
    """Generate a rule-based prediction using UMF data when available."""
    grade = "unknown"
    risk_factors = []
    predicted = "Unable to predict — no simulation data available."
    explanation = "Rule-based fallback — AI simulation not available"

    base_name = (combo.base or "").lower()
    top_name = (combo.top or "").lower()

    # If we have compatibility analysis, use it as primary signal
    if compat and compat.success:
        if compat.score >= 0.7:
            grade = "likely"
        elif compat.score < 0.4:
            grade = "unlikely"
        else:
            grade = "possible"

        risk_factors = list(compat.risk_factors)
        if compat.warnings:
            risk_factors.extend(compat.warnings)

        # Build explanation from compatibility data
        parts = []
        if compat.oxide_interactions:
            parts.append("; ".join(compat.oxide_interactions))
        if compat.fluidity_interaction and compat.fluidity_interaction != "unknown":
            parts.append(f"Fluidity: {compat.fluidity_interaction}")
        if compat.thermal_expansion_risk and compat.thermal_expansion_risk != "unknown":
            parts.append(f"Thermal risk: {compat.thermal_expansion_risk}")
        if base_umf and base_umf.surface_prediction:
            parts.append(f"Base surface: {base_umf.surface_prediction}")
        if top_umf and top_umf.surface_prediction:
            parts.append(f"Top surface: {top_umf.surface_prediction}")

        explanation = (
            "UMF-based fallback analysis: " + "; ".join(parts)
            if parts
            else "UMF-based fallback"
        )
        predicted = f"Compatibility score {compat.score:.0%} — " + (
            "glazes appear compatible for layering"
            if compat.compatible
            else "significant risks detected in this combination"
        )

        # Still check shino rule (hard override)
        if "shino" in top_name and "shino" not in base_name:
            grade = "unlikely"
            predicted = "Shino over non-Shino glazes often crawls due to high surface tension mismatch."
            risk_factors.insert(0, "Shino crawl risk — near-certain")
            explanation = "Hard rule override: shino crawl rule takes precedence over UMF analysis"

        return {
            "prediction_grade": grade,
            "predicted_result": predicted,
            "chemistry_explanation": explanation,
            "risk_factors": risk_factors,
            "food_safe_prediction": None,
            "confidence_in_prediction": (
                "high" if grade in ("likely", "unlikely") else "medium"
            ),
        }

    # No compatibility data — fall back to original string-matching rules
    if "shino" in top_name and "shino" not in base_name:
        grade = "unlikely"
        predicted = "Shino over non-Shino glazes often crawls due to high surface tension mismatch."
        risk_factors.append("Shino crawl risk — near-certain")
    elif (
        ("tenmoku" in base_name and "tenmoku" in top_name)
        or ("teadust" in base_name and "tenmoku" in top_name)
        or ("tenmoku" in base_name and "teadust" in top_name)
    ):
        grade = "unlikely"
        predicted = "Both glazes are extremely iron-rich — expect near-black with no visual distinction."
        risk_factors.append("Iron overload — too dark, muddy, uninteresting")
    elif "red" in top_name and ("tenmoku" in base_name or "teadust" in base_name):
        grade = "unlikely"
        predicted = "Iron in the base glaze will suppress copper red development in the top glaze."
        risk_factors.append("Iron kills copper red — well-documented failure mode")
    elif "white" in base_name and (
        "blue" in top_name or "jensen" in top_name or "aegean" in top_name
    ):
        grade = "likely"
        predicted = (
            "Cobalt-based blue over white — most predictable combination in ceramics."
        )
    elif "white" in base_name and (
        "froggy" in top_name or "toady" in top_name or "blugr" in top_name
    ):
        grade = "likely"
        predicted = "Copper green over white — clean, bright color expected."
    else:
        grade = "unknown"

    return {
        "prediction_grade": grade,
        "predicted_result": predicted,
        "chemistry_explanation": explanation,
        "risk_factors": risk_factors,
        "food_safe_prediction": None,
        "confidence_in_prediction": "low" if grade == "unknown" else "medium",
    }
