"""EF 3.1 + ReCiPe 2016 reference data for LCA validation."""

# ─── Recognised LCA Units ───

RECOGNIZED_UNITS = {
    # Mass
    "kg", "g", "t", "tonne", "ton", "mg", "µg",
    # GWP
    "kg CO2 eq", "kg CO2-eq", "CO2e", "kg CO2", "kg CO2e",
    "t CO2 eq", "t CO2-eq", "tCO2e", "g CO2 eq",
    # Energy
    "MJ", "kWh", "GJ", "TJ", "J",
    # Acidification
    "mol H+ eq", "kg SO2 eq", "kg SO2-eq",
    # Eutrophication
    "kg P eq", "kg P-eq", "kg N eq", "kg N-eq", "mol N eq",
    # Water
    "m3", "l", "litre", "liter", "L",
    # Ecotoxicity
    "CTUe",
    # Human toxicity
    "CTUh",
    # Land use
    "m2", "m2*year", "m2·year", "m²", "m²·a",
    # Ozone
    "kg CFC-11 eq", "kg CFC11 eq",
    # Particulate matter
    "disease incidence", "kg PM2.5 eq",
    # Resource use
    "kg Sb eq", "kg Sb-eq", "MJ surplus",
    # Ionising radiation
    "kBq U235 eq",
    # Photochemical ozone
    "kg NMVOC eq", "kg NMVOC-eq",
}

# Any unit string ending with "eq" is also considered valid
def is_recognized_unit(unit_str: str) -> bool:
    """Check if a unit string is a recognised LCA unit."""
    unit = unit_str.strip()
    if unit in RECOGNIZED_UNITS:
        return True
    if unit.lower().endswith("eq") or unit.lower().endswith("eq."):
        return True
    # Check partial matches
    for ru in RECOGNIZED_UNITS:
        if ru.lower() in unit.lower():
            return True
    return False


# ─── EF 3.1 Impact Categories ───

EF_31_CATEGORIES = [
    "Climate change",
    "Climate change - fossil",
    "Climate change - biogenic",
    "Climate change - land use and land use change",
    "Ozone depletion",
    "Human toxicity, cancer",
    "Human toxicity, non-cancer",
    "Particulate matter",
    "Ionising radiation",
    "Photochemical ozone formation",
    "Acidification",
    "Eutrophication, terrestrial",
    "Eutrophication, freshwater",
    "Eutrophication, marine",
    "Ecotoxicity, freshwater",
    "Land use",
    "Water use",
    "Resource use, fossils",
    "Resource use, minerals and metals",
]

# ─── ReCiPe 2016 Midpoint Categories ───

RECIPE_2016_MIDPOINT = [
    "Global warming",
    "Stratospheric ozone depletion",
    "Ionizing radiation",
    "Ozone formation, Human health",
    "Fine particulate matter formation",
    "Ozone formation, Terrestrial ecosystems",
    "Terrestrial acidification",
    "Freshwater eutrophication",
    "Marine eutrophication",
    "Terrestrial ecotoxicity",
    "Freshwater ecotoxicity",
    "Marine ecotoxicity",
    "Human carcinogenic toxicity",
    "Human non-carcinogenic toxicity",
    "Land use",
    "Mineral resource scarcity",
    "Fossil resource scarcity",
    "Water consumption",
]

# ─── Common Impact Category Aliases ───

CATEGORY_ALIASES = {
    "gwp": "Global warming",
    "global warming potential": "Global warming",
    "carbon footprint": "Climate change",
    "co2": "Climate change",
    "ap": "Acidification",
    "acidification potential": "Acidification",
    "ep": "Eutrophication, freshwater",
    "eutrophication potential": "Eutrophication, freshwater",
    "odp": "Ozone depletion",
    "ozone depletion potential": "Ozone depletion",
    "pocp": "Photochemical ozone formation",
    "htp": "Human toxicity, cancer",
    "human toxicity potential": "Human toxicity, cancer",
    "adp": "Resource use, minerals and metals",
    "abiotic depletion": "Resource use, minerals and metals",
    "water footprint": "Water use",
}

ALL_KNOWN_CATEGORIES = set(
    [c.lower() for c in EF_31_CATEGORIES]
    + [c.lower() for c in RECIPE_2016_MIDPOINT]
    + list(CATEGORY_ALIASES.keys())
)


def is_known_category(category_name: str) -> bool:
    """Check if an impact category name is a known EF 3.1 or ReCiPe 2016 category."""
    name = category_name.strip().lower()
    if name in ALL_KNOWN_CATEGORIES:
        return True
    # Fuzzy match: check if category contains a known term
    for known in ALL_KNOWN_CATEGORIES:
        if known in name or name in known:
            return True
    return False


# ─── Life Cycle Stage Codes ───

LIFE_CYCLE_STAGES = {
    "A1": "Raw material extraction",
    "A2": "Transport to manufacturer",
    "A3": "Manufacturing",
    "A4": "Transport to site",
    "A5": "Installation",
    "B1": "Use",
    "B2": "Maintenance",
    "B3": "Repair",
    "B4": "Replacement",
    "B5": "Refurbishment",
    "B6": "Operational energy use",
    "B7": "Operational water use",
    "C1": "Deconstruction",
    "C2": "Transport to waste processing",
    "C3": "Waste processing",
    "C4": "Disposal",
    "D": "Benefits beyond system boundary",
}
