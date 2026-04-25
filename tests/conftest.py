"""Shared test fixtures for OpenGlaze tests."""

import os
from core.db import connect_db
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def test_db_path():
    """Create a temp SQLite DB with schema loaded and sample data seeded."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = connect_db(path)
    conn.executescript(_SCHEMA_SQL)
    conn.executescript(_SEED_SQL)
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


@pytest.fixture
def sample_glazes(test_db_path):
    """Return the 3 seeded glaze names."""
    return ["Chun Blue", "Iron Red", "Shino"]


@pytest.fixture
def sample_chemistry_rules(test_db_path):
    """Return the 2 seeded chemistry rule titles."""
    return ["Shino layering risk", "Iron oxide color prediction"]


@pytest.fixture
def sample_combinations(test_db_path):
    """Return the 1 seeded combination description."""
    return [("Tenmoku", "Chun Blue", "proven")]


# Load canonical schema from the actual schema.sql so tests never drift out of sync
_schema_path = Path(__file__).parent.parent / "core" / "schema.sql"
if _schema_path.exists():
    _SCHEMA_SQL = _schema_path.read_text()
else:
    raise RuntimeError(f"schema.sql not found at {_schema_path}")

_SEED_SQL = """
INSERT INTO glazes (id, name, family, color, chemistry, behavior, warning) VALUES
    ('glaze-1', 'Chun Blue', 'Celadon', 'blue-green', 'High silica, low iron, copper carbonate 0.5%', 'Reduction brings out blue-green', NULL),
    ('glaze-2', 'Iron Red', 'Tenmoku', 'dark red-brown', 'High iron 8%, reduction fired', 'Heavy reduction deepens red', NULL),
    ('glaze-3', 'Shino', 'Shino', 'white with pink-orange', 'High feldspar, low clay, no flux', 'Thick application crawls over non-Shino', 'Crawls over non-Shino glazes');

INSERT INTO chemistry_rules (category, rule_type, title, description, conditions, outcomes) VALUES
    ('layering_principle', 'compatibility', 'Shino layering risk', 'Shino over non-Shino glazes often crawls due to different thermal expansion.', 'Shino applied over non-Shino base', 'Glaze pulls away from surface (crawling)'),
    ('color_prediction', 'oxide_behavior', 'Iron oxide color prediction', 'Iron oxide produces different colors depending on atmosphere and concentration.', 'Iron 2% in oxidation', 'Amber/tan color. In reduction: celadon green.');

INSERT INTO combinations (base, top, type, source, result, risk, effect) VALUES
    ('Tenmoku', 'Chun Blue', 'research-backed', 'fired', 'Deep blue-green over iron-black, subtle halo effect', 'low', 'subtle');
"""
