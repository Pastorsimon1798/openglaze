"""AI prediction generation for glaze combinations.

DISCLAIMER: Simplified chemistry-based heuristic for educational purposes.
NOT a guarantee of results. Always test in your own studio.
"""

import logging

logger = logging.getLogger(__name__)


def generate_ai_prediction(combo_info) -> tuple:
    """Generate an AI prediction for a glaze combination.

    Args:
        combo_info: Dict with glaze_a_name, glaze_b_name, glaze_a_color,
                    glaze_b_color, glaze_a_surface, glaze_b_surface

    Returns:
        (prediction_text, confidence_0_to_100)
    """
    if not combo_info:
        return "Insufficient data to predict", 30

    glaze_a = combo_info.get("glaze_a_name", "").lower()
    glaze_b = combo_info.get("glaze_b_name", "").lower()
    surface_a = combo_info.get("glaze_a_surface") or ""
    surface_b = combo_info.get("glaze_b_surface") or ""

    # High risk pairs
    high_risk_pairs = [
        ("shino", "shino"),
        ("crawl", "crawl"),
        ("tenmoku", "tenmoku"),
        ("ash", "ash"),
    ]
    for pair in high_risk_pairs:
        if pair[0] in glaze_a and pair[1] in glaze_b:
            return (
                "High risk of crawling or running due to overlapping flux chemistry. "
                "Consider thin application."
            ), 25

    # Matte + glossy contrast
    if ("matte" in surface_a and "smooth" in surface_b) or (
        "smooth" in surface_a and "matte" in surface_b
    ):
        return (
            "Matte over glossy (or vice versa) typically creates interesting "
            "surface contrast. Good compatibility expected."
        ), 70

    # Clear base combinations
    if "clear" in glaze_a or "clear" in glaze_b:
        return (
            "Clear base glaze combinations are generally reliable. The underlying "
            "glaze color will show through clearly."
        ), 75

    # Same color penalty
    color_a = (combo_info.get("glaze_a_color") or "").lower()
    color_b = (combo_info.get("glaze_b_color") or "").lower()
    if color_a and color_b and color_a == color_b:
        return (
            "Similar color pairing may lack contrast. Consider pairing with a "
            "complementary color glaze."
        ), 40

    # General prediction
    return (
        "Compatible combination based on standard oxide chemistry. Results may vary "
        "with application thickness and firing conditions."
    ), 55
