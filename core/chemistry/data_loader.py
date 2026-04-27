"""Data loader for ceramics-foundation external data.

Reads canonical ceramic data from JSON files in the ceramics-foundation submodule.
Falls back to hardcoded defaults if the submodule is not present or files are missing.
This ensures OpenGlaze works standalone while enabling data consolidation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to find ceramics-foundation data directory
# Check relative to this file (in core/chemistry/), then relative to server root
_DATA_DIR_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / "ceramics-foundation" / "data",
    Path(__file__).resolve().parent.parent.parent.parent
    / "ceramics-foundation"
    / "data",
]


def _find_data_dir() -> Optional[Path]:
    """Find the ceramics-foundation data directory."""
    for candidate in _DATA_DIR_CANDIDATES:
        if candidate.is_dir() and (candidate / "oxides.json").exists():
            return candidate
    return None


def _find_studios_dir() -> Optional[Path]:
    """Find the ceramics-foundation studios directory."""
    for candidate in _DATA_DIR_CANDIDATES:
        studios_dir = candidate.parent / "studios"
        if studios_dir.is_dir():
            return studios_dir
    return None


def _load_json(path: Path) -> Optional[Any]:
    """Load a JSON file, returning None on any error."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.debug(f"Could not load {path}: {e}")
        return None


def load_oxide_data() -> Optional[Dict[str, Dict]]:
    """Load oxide molecular weights and properties from oxides.json.

    Returns dict of oxide_name -> {mw, role, safety, ...} or None if unavailable.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "oxides.json")
    if data and "oxides" in data:
        return data["oxides"]
    return None


def load_material_data() -> Optional[Dict[str, Dict]]:
    """Load material compositions from materials.json.

    Returns dict of canonical_name -> {name, aliases, oxides, loi, category} or None.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "materials.json")
    if data and "materials" in data:
        return data["materials"]
    return None


def load_chemistry_rules() -> Optional[List[Dict]]:
    """Load chemistry rules from chemistry-rules.json.

    Returns list of rule dicts or None if unavailable.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "chemistry-rules.json")
    if data and "rules" in data:
        return data["rules"]
    return None


def load_surface_thresholds() -> Optional[Dict[str, float]]:
    """Load surface prediction thresholds from surface-prediction.json.

    Returns dict of threshold_name -> value or None if unavailable.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "surface-prediction.json")
    if data and "sio2_al2o3_thresholds" in data:
        return data["sio2_al2o3_thresholds"]
    return None


def load_studio_profile(studio_name: str) -> Optional[Dict]:
    """Load a studio profile by name.

    Returns the profile dict or None if not found.
    """
    studios_dir = _find_studios_dir()
    if studios_dir is None:
        return None
    profile_path = studios_dir / studio_name / "profile.json"
    return _load_json(profile_path)


def load_studio_glazes(studio_name: str) -> Optional[List[str]]:
    """List glaze collection files for a studio.

    Returns list of YAML filenames or None.
    """
    studios_dir = _find_studios_dir()
    if studios_dir is None:
        return None
    glazes_dir = studios_dir / studio_name / "glazes"
    if not glazes_dir.is_dir():
        return None
    return [f.name for f in glazes_dir.iterdir() if f.suffix == ".yaml"]


def load_firing_data() -> Optional[Dict]:
    """Load firing data from firing.json. Returns dict or None."""
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "firing.json")
    if data and "cones" in data:
        return data
    return None


def load_kiln_data(studio_name: str) -> Optional[Dict]:
    """Load kiln data for a studio from studios/<name>/kilns.json.

    Returns dict with 'kilns' key or None if not found.
    """
    studios_dir = _find_studios_dir()
    if studios_dir is None:
        return None
    kilns_path = studios_dir / studio_name / "kilns.json"
    return _load_json(kilns_path)


def get_community_template_path(filename: str) -> Optional[str]:
    """Get path to a community template YAML from ceramics-foundation/data/.

    Returns absolute path string or None if not found.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    template_path = data_dir / filename
    if template_path.exists():
        return str(template_path)
    return None


def get_template_path(studio_name: str, collection: str) -> Optional[str]:
    """Get the full path to a studio's glaze collection YAML file.

    Returns absolute path string or None if not found.
    """
    studios_dir = _find_studios_dir()
    if studios_dir is None:
        return None
    glaze_path = studios_dir / studio_name / "glazes" / collection
    if glaze_path.exists():
        return str(glaze_path)
    return None


def load_thermal_expansion() -> Optional[Dict[str, Dict]]:
    """Load Appen molar thermal expansion coefficients from thermal-expansion.json.

    Returns dict of oxide_name -> {value, source, notes} or None if unavailable.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "thermal-expansion.json")
    if data and "coefficients" in data:
        return data["coefficients"]
    return None


def load_umf_targets() -> Optional[Dict[str, Dict]]:
    """Load cone-specific UMF target ranges from umf-target-ranges.json.

    Returns dict with 'ranges' key (cone_name -> oxide -> {min, max}) or None.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "umf-target-ranges.json")
    if data and "ranges" in data:
        return data
    return None


def load_layering_rules() -> Optional[Dict]:
    """Load canonical layering compatibility rules from layering-rules.json.

    Returns the full rules dict or None if unavailable.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "layering-rules.json")
    return data


def load_material_substitutions() -> Optional[Dict]:
    """Load material substitution data from material-substitutions.json.

    Returns dict with 'one_to_one' and 'complex' keys or None.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "material-substitutions.json")
    if data and ("one_to_one" in data or "complex" in data):
        return data
    return None


def load_firing_schedules() -> Optional[Dict]:
    """Load firing schedule data from firing-schedules.json.

    Returns dict with bisque and glaze schedule data or None.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "firing-schedules.json")
    return data


def load_clay_bodies() -> Optional[Dict]:
    """Load clay body database from clay-bodies.json.

    Returns dict with 'clay_bodies' key or None.
    """
    data_dir = _find_data_dir()
    if data_dir is None:
        return None
    data = _load_json(data_dir / "clay-bodies.json")
    if data and "clay_bodies" in data:
        return data
    return None
