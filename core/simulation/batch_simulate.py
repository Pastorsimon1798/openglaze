"""Batch simulation runner — iterates over all combos and runs chemistry simulation."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def batch_simulate(db_path: str = "glaze.db", user_id: Optional[str] = None) -> dict:
    """
    Run chemistry simulation for all unsimulated combinations.
    Returns summary of results.
    """
    from core.combinations import CombinationManager
    from core.glazes import GlazeManager
    from .runner import simulate_combo

    combo_manager = CombinationManager(db_path, user_id=user_id)
    glaze_manager = GlazeManager(db_path, user_id=user_id)

    unsimulated = combo_manager.get_unsimulated()
    if not unsimulated:
        return {"message": "All combinations already have predictions", "simulated": 0}

    results = {"simulated": 0, "updated": 0, "failed": 0, "details": []}

    for combo in unsimulated:
        try:
            base_glaze = glaze_manager.get_by_name(combo.base)
            top_glaze = glaze_manager.get_by_name(combo.top)

            prediction = simulate_combo(
                base_glaze=base_glaze, top_glaze=top_glaze, combo=combo, db_path=db_path
            )

            success = combo_manager.update(
                combo.id,
                {
                    "prediction_grade": prediction.get("prediction_grade", "unknown"),
                    "chemistry": prediction.get("chemistry_explanation"),
                    "result": prediction.get("predicted_result"),
                },
            )

            results["simulated"] += 1
            if success:
                results["updated"] += 1

            results["details"].append(
                {
                    "id": combo.id,
                    "combo": f"{combo.top} over {combo.base}",
                    "grade": prediction.get("prediction_grade", "unknown"),
                }
            )

        except Exception as e:
            logger.error(f"Failed to simulate {combo.top} over {combo.base}: {e}")
            results["failed"] += 1

    logger.info(
        f"Batch simulation complete: {results['simulated']} simulated, {results['updated']} updated, {results['failed']} failed"
    )
    return results
