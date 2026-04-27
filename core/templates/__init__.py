"""OpenGlaze Templates Module."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


def load_template(template_id: str) -> Optional[Dict]:
    """Load a template by ID."""
    template_path = Path(__file__).parent / f"{template_id}.yaml"
    if template_path.exists():
        with open(template_path, "r") as f:
            return yaml.safe_load(f)
    return None


def list_templates() -> List[str]:
    """List available template IDs."""
    templates_dir = Path(__file__).parent
    return [f.stem for f in templates_dir.glob("*.yaml")]


def get_community_glazes() -> Dict:
    """Get the 44 community glazes template."""
    return load_template("community-glazes")


__all__ = ["load_template", "list_templates", "get_community_glazes"]
