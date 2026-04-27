"""Material database with oxide compositions and molecular weights for ceramic glaze chemistry."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .data_loader import load_oxide_data, load_thermal_expansion


@dataclass
class Material:
    """A ceramic raw material with its oxide composition."""

    name: str
    aliases: List[str] = field(default_factory=list)
    oxides: Dict[str, float] = field(default_factory=dict)  # oxide_name -> percentage
    loi: float = 0.0  # loss on ignition percentage
    category: str = "other"


# Hardcoded fallback molecular weights (g/mol) — used when ceramics-foundation data unavailable
_HARDCODED_OXIDE_MW: Dict[str, float] = {
    "SiO2": 60.084,
    "Al2O3": 101.961,
    "K2O": 94.196,
    "Na2O": 61.979,
    "CaO": 56.077,
    "MgO": 40.304,
    "Fe2O3": 159.688,
    "FeO": 71.844,
    "CuO": 79.545,
    "CoO": 74.933,
    "MnO": 70.937,
    "TiO2": 79.866,
    "ZnO": 81.379,
    "BaO": 153.326,
    "SrO": 103.619,
    "Li2O": 29.881,
    "B2O3": 69.620,
    "SnO2": 150.709,
    "ZrO2": 123.218,
    "Cr2O3": 151.990,
    "P2O5": 141.944,
}

# Load from ceramics-foundation if available, otherwise use hardcoded values
_oxide_data = load_oxide_data()
if _oxide_data:
    OXIDE_MOLECULAR_WEIGHTS: Dict[str, float] = {
        name: props["mw"] for name, props in _oxide_data.items() if "mw" in props
    }
    # Ensure all expected oxides are present (merge with fallback)
    for oxide, mw in _HARDCODED_OXIDE_MW.items():
        if oxide not in OXIDE_MOLECULAR_WEIGHTS:
            OXIDE_MOLECULAR_WEIGHTS[oxide] = mw
else:
    OXIDE_MOLECULAR_WEIGHTS = dict(_HARDCODED_OXIDE_MW)

# Oxides classified as fluxes (used for UMF normalization)
FLUX_OXIDES = {"K2O", "Na2O", "CaO", "MgO", "ZnO", "BaO", "SrO", "Li2O", "FeO"}

# Thermal expansion coefficients (Appen molar coefficients, x10^-6/K)
# Loaded from ceramics-foundation/data/thermal-expansion.json if available.
# Falls back to simplified relative values if data not found.
_HARDCODED_TE: Dict[str, float] = {
    "Na2O": 1.0,
    "K2O": 1.2,
    "CaO": 0.5,
    "MgO": 0.1,
    "BaO": 0.4,
    "ZnO": 0.2,
    "Li2O": 0.9,
    "SrO": 0.4,
    "FeO": 0.3,
    "Fe2O3": 0.2,
    "Al2O3": -0.2,
    "SiO2": -0.5,
    "B2O3": -0.1,
    "TiO2": 0.0,
    "ZrO2": 0.0,
}

_te_data = load_thermal_expansion()
if _te_data:
    THERMAL_EXPANSION_COEFFICIENTS: Dict[str, float] = {
        name: props["value"]
        for name, props in _te_data.items()
        if isinstance(props, dict) and "value" in props
    }
    # Ensure all expected oxides are present (merge with fallback)
    for oxide, val in _HARDCODED_TE.items():
        if oxide not in THERMAL_EXPANSION_COEFFICIENTS:
            THERMAL_EXPANSION_COEFFICIENTS[oxide] = val
else:
    THERMAL_EXPANSION_COEFFICIENTS = dict(_HARDCODED_TE)

# Master material database
MATERIALS: Dict[str, Material] = {}

# --- Feldspars ---
MATERIALS["custer feldspar"] = Material(
    name="Custer Feldspar",
    aliases=[
        "custer",
        "k-spar",
        "kspar",
        "potassium feldspar",
        "potash feldspar",
        "feldspar",
    ],
    # Updated to current Pacer Minerals data (Digitalfire/Glazy 2024)
    oxides={
        "K2O": 10.0,
        "Na2O": 3.8,
        "Al2O3": 17.1,
        "SiO2": 68.0,
        "Fe2O3": 0.1,
        "CaO": 0.3,
    },
    loi=0.25,
    category="feldspar",
)

MATERIALS["nepheline syenite"] = Material(
    name="Nepheline Syenite",
    aliases=["neph syen", "nepheline"],
    oxides={"Na2O": 11.8, "K2O": 5.3, "Al2O3": 23.5, "SiO2": 58.1},
    loi=0.5,
    category="feldspar",
)

MATERIALS["g-200 feldspar"] = Material(
    name="G-200 Feldspar",
    aliases=["g200", "kona f-4", "kona f4", "kona feldspar"],
    oxides={"K2O": 9.1, "Na2O": 3.4, "Al2O3": 18.4, "SiO2": 68.5, "Fe2O3": 0.1},
    loi=0.2,
    category="feldspar",
)

MATERIALS["f-4 feldspar"] = Material(
    name="F-4 Feldspar",
    aliases=["f4", "minnesota feldspar", "soda feldspar"],
    oxides={"K2O": 8.0, "Na2O": 6.0, "Al2O3": 17.5, "SiO2": 68.0},
    loi=0.2,
    category="feldspar",
)

# --- Silica ---
MATERIALS["silica"] = Material(
    name="Silica",
    aliases=["flint", "quartz", "sio2", "silica sand"],
    oxides={"SiO2": 99.5},
    loi=0.1,
    category="silica",
)

# --- Fluxes ---
MATERIALS["whiting"] = Material(
    name="Whiting",
    aliases=["calcium carbonate", "caco3", "chalk", "limestone"],
    oxides={"CaO": 56.0},
    loi=44.0,
    category="flux",
)

MATERIALS["dolomite"] = Material(
    name="Dolomite",
    aliases=["dolomite carb"],
    oxides={"CaO": 30.5, "MgO": 21.9},
    loi=47.6,
    category="flux",
)

MATERIALS["talc"] = Material(
    name="Talc",
    aliases=["magnesium silicate"],
    oxides={"MgO": 31.7, "SiO2": 63.5},
    loi=4.8,
    category="flux",
)

MATERIALS["zinc oxide"] = Material(
    name="Zinc Oxide",
    aliases=["zinc", "zno"],
    oxides={"ZnO": 99.0},
    loi=0.0,
    category="flux",
)

MATERIALS["strontium carbonate"] = Material(
    name="Strontium Carbonate",
    aliases=["strontium carb", "sro3"],
    oxides={"SrO": 70.0},
    loi=30.0,
    category="flux",
)

MATERIALS["lithium carbonate"] = Material(
    name="Lithium Carbonate",
    aliases=["lithium carb", "li2co3"],
    oxides={"Li2O": 40.4},
    loi=59.6,
    category="flux",
)

MATERIALS["soda ash"] = Material(
    name="Soda Ash",
    aliases=["sodium carbonate", "na2co3"],
    oxides={"Na2O": 58.5},
    loi=41.5,
    category="flux",
)

MATERIALS["borax"] = Material(
    name="Borax",
    aliases=["sodium borate"],
    oxides={"Na2O": 16.3, "B2O3": 36.5},
    loi=47.2,
    category="flux",
)

MATERIALS["wollastonite"] = Material(
    name="Wollastonite",
    aliases=["casio3"],
    oxides={"CaO": 48.3, "SiO2": 51.7},
    loi=0.0,
    category="flux",
)

MATERIALS["bone ash"] = Material(
    name="Bone Ash",
    aliases=["calcium phosphate", "tribasic calcium phosphate"],
    oxides={"CaO": 52.0, "P2O5": 42.0},
    loi=2.0,
    category="flux",
)

# --- Clays ---
MATERIALS["epk"] = Material(
    name="EPK",
    aliases=["edgar plastic kaolin", "kaolin", "china clay", "generic kaolin"],
    oxides={"Al2O3": 37.0, "SiO2": 46.5, "K2O": 0.5, "Fe2O3": 0.8},
    loi=13.5,
    category="clay",
)

MATERIALS["ball clay"] = Material(
    name="Ball Clay",
    aliases=["om4 ball clay", "om4", "kentucky ball clay", "tennessee ball clay"],
    oxides={"Al2O3": 30.0, "SiO2": 55.0, "K2O": 1.5, "Fe2O3": 1.2},
    loi=10.0,
    category="clay",
)

MATERIALS["redart"] = Material(
    name="Redart",
    aliases=["cedar heights redart", "red art", "red art clay"],
    oxides={"SiO2": 55.0, "Al2O3": 17.0, "Fe2O3": 7.0, "K2O": 3.5, "TiO2": 1.5},
    loi=8.0,
    category="clay",
)

MATERIALS["barnard clay"] = Material(
    name="Barnard Clay",
    aliases=["blackbird clay", "barnard"],
    oxides={"SiO2": 52.0, "Al2O3": 14.0, "Fe2O3": 8.0, "K2O": 2.5, "TiO2": 1.5},
    loi=10.0,
    category="clay",
)

MATERIALS["bentonite"] = Material(
    name="Bentonite",
    aliases=["bentonite clay"],
    oxides={"Al2O3": 18.0, "SiO2": 60.0, "MgO": 3.0, "Fe2O3": 3.0},
    loi=10.0,
    category="clay",
)

# --- Colorants ---
MATERIALS["red iron oxide"] = Material(
    name="Red Iron Oxide",
    aliases=["iron oxide", "iron oxide red", "fe2o3", "red iron", "iron"],
    oxides={"Fe2O3": 95.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["black iron oxide"] = Material(
    name="Black Iron Oxide",
    aliases=["iron oxide black"],
    # Fe3O4 (magnetite) decomposes to FeO + Fe2O3 during firing
    oxides={"FeO": 31.0, "Fe2O3": 69.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["cobalt carbonate"] = Material(
    name="Cobalt Carbonate",
    aliases=["cobalt carb", "co3"],
    oxides={"CoO": 63.0},
    loi=37.0,
    category="colorant",
)

MATERIALS["cobalt oxide"] = Material(
    name="Cobalt Oxide",
    aliases=["cobalt", "cobalt ox"],
    oxides={"CoO": 93.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["copper carbonate"] = Material(
    name="Copper Carbonate",
    aliases=["copper carb", "cuco3"],
    oxides={"CuO": 65.0},
    loi=35.0,
    category="colorant",
)

MATERIALS["copper oxide"] = Material(
    name="Copper Oxide",
    aliases=["copper oxide black", "cuo", "copper"],
    oxides={"CuO": 99.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["manganese dioxide"] = Material(
    name="Manganese Dioxide",
    aliases=["manganese", "mno2", "black manganese"],
    # MnO2 decomposes to MnO during firing; this is the fired oxide contribution
    oxides={"MnO": 100.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["chromium oxide"] = Material(
    name="Chromium Oxide",
    aliases=["chrome oxide", "chrome", "cr2o3"],
    oxides={"Cr2O3": 99.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["rutile"] = Material(
    name="Rutile",
    aliases=["titanium dioxide", "tio2", "titanium"],
    oxides={"TiO2": 85.0, "Fe2O3": 10.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["titanium dioxide"] = Material(
    name="Titanium Dioxide",
    aliases=["tio2 pure", "titania"],
    oxides={"TiO2": 99.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["tin oxide"] = Material(
    name="Tin Oxide",
    aliases=["tin", "sno2"],
    oxides={"SnO2": 98.0},
    loi=0.0,
    category="colorant",
)

MATERIALS["zirconium silicate"] = Material(
    name="Zirconium Silicate",
    aliases=["zircopax", "zircon", "zircosil"],
    oxides={"ZrO2": 67.0, "SiO2": 33.0},
    loi=0.0,
    category="colorant",
)

# --- Frits ---
MATERIALS["ferro frit 3124"] = Material(
    name="Ferro Frit 3124",
    aliases=["frit 3124", "frit3124"],
    oxides={
        "Na2O": 12.0,
        "K2O": 5.0,
        "CaO": 10.0,
        "B2O3": 15.0,
        "Al2O3": 10.0,
        "SiO2": 48.0,
    },
    loi=0.0,
    category="frit",
)

MATERIALS["ferro frit 3134"] = Material(
    name="Ferro Frit 3134",
    aliases=["frit 3134", "frit3134"],
    oxides={
        "Na2O": 4.7,
        "K2O": 1.8,
        "CaO": 16.5,
        "Al2O3": 9.3,
        "B2O3": 9.1,
        "SiO2": 47.2,
        "MgO": 3.7,
    },
    loi=0.0,
    category="frit",
)

MATERIALS["alkalifritte m1233"] = Material(
    name="Alkalifritte M1233",
    aliases=["m1233"],
    oxides={
        "Na2O": 8.0,
        "K2O": 5.0,
        "CaO": 12.0,
        "Al2O3": 10.0,
        "B2O3": 8.0,
        "SiO2": 55.0,
        "ZnO": 2.0,
    },
    loi=0.0,
    category="frit",
)

# --- Other ---
MATERIALS["gerstley borate"] = Material(
    name="Gerstley Borate",
    aliases=["gb", "gerstley"],
    oxides={"B2O3": 20.0, "CaO": 25.0, "MgO": 3.0, "SiO2": 25.0},
    loi=27.0,
    category="other",
)

# Build reverse lookup: alias -> canonical name
_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, material in MATERIALS.items():
    for alias in material.aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical


def normalize_material_name(name: str) -> str:
    """Normalize a material name to its canonical form."""
    if not name:
        return name
    normalized = name.strip().lower()
    return normalized


def get_material(name: str) -> Optional[Material]:
    """Look up a material by name or alias. Returns None if not found."""
    if not name:
        return None

    normalized = normalize_material_name(name)

    # Direct match on canonical name
    if normalized in MATERIALS:
        return MATERIALS[normalized]

    # Match on alias
    if normalized in _ALIAS_TO_CANONICAL:
        canonical = _ALIAS_TO_CANONICAL[normalized]
        return MATERIALS[canonical]

    # Fuzzy: try removing common suffixes/prefixes
    for suffix in [" oxide", " carbonate", " clay", " feldspar", " carb"]:
        stripped = normalized.replace(suffix, "")
        if stripped in MATERIALS:
            return MATERIALS[stripped]
        if stripped in _ALIAS_TO_CANONICAL:
            return MATERIALS[_ALIAS_TO_CANONICAL[stripped]]

    return None


def get_all_materials() -> Dict[str, Material]:
    """Return all materials keyed by canonical name."""
    return dict(MATERIALS)
