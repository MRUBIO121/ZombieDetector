from typing import Dict, Tuple, List, FrozenSet

# 5 base criteria (fixed order is important)
CRITERIA_KEYS: List[str] = [
    "Recent_CPU_decrease_criterion",  # idx 0
    "Recent_net_traffic_decrease_criterion",  # idx 1
    "Sustained_Low_CPU_criterion",  # idx 2
    "Excessively_constant_RAM_criterion",  # idx 3
    "Daily_CPU_profile_lost_criterion",  # idx 4
]

# Human descriptions (like the docs
CRITERIA_DESCRIPTIONS: List[str] = [
    "Detectada una bajada repentina en el uso de CPU",
    "Detectada una caída brusca en el tráfico de red reciente",
    "El uso de CPU se mantiene demasiado bajo durante un tiempo prolongado",
    "El uso de RAM permanece anormalmente constante, sin variaciones",
    "El patrón diario esperado de uso de CPU no se está cumpliendo",
]

# === Code ↔ alias mapping for the named ones in the sheet ===
ALIAS_BY_CODE: Dict[str, str] = {
    "5": "Coloso",
    "4A": "Nemesis",
    "4B": "Clicker",
    "4C": "Revenant",
    "4D": "Ghoul",
    "4E": "Gael",
    "3A": "Solomon",
    "3B": "Bud",
    "3C": "Tarman",
    "3D": "Ben",
    "3E": "Fido",
    "3F": "Bloater",
    "3G": "Shambler",
    "3H": "Stalker",
    "3I": "Zeus",
    "3J": "Wights",
    # ADDED: 2-criteria zombies (Double Threat Zombies)
    "2A": "Mummy",  # CPU + Network (most common combination)
    "2B": "Wraith",  # CPU + Sustained Low CPU
    "2C": "Vampire",  # CPU + Constant RAM
    "2D": "Banshee",  # CPU + Daily Profile Lost
    "2E": "Phantom",  # Network + Sustained Low CPU
    "2F": "Specter",  # Network + Constant RAM
    "2G": "Shade",  # Network + Daily Profile Lost
    "2H": "Poltergeist",  # Sustained Low CPU + Constant RAM
    "2I": "Spirit",  # Sustained Low CPU + Daily Profile Lost
    "2J": "Apparition",  # Constant RAM + Daily Profile Lost
    # ADDED: 1-criteria zombies (Single Threat Zombies)
    "1A": "Zombie",  # Recent CPU decrease only
    "1B": "Walker",  # Recent network traffic decrease only
    "1C": "Crawler",  # Sustained low CPU only
    "1D": "Lurker",  # Excessively constant RAM only
    "1E": "Sleeper",  # Daily CPU profile lost only
    # 2* and 1* have no name in the sheet → we’ll set alias = code at runtime
    "0": "No Zombie Detected",
}

# ======= Combination → code mapping rules =======
# We map *which* criteria are active to a code.
# We use deterministic lexicographic schemes that match the sheet’s counts and ordering.

# For 4-of-5: letter = which single criterion is *missing* in index order 0..4
FOUR_OF_FIVE_MISSING_TO_CODE = {
    0: "4A",  # missing Recent_CPU
    1: "4B",  # missing Recent_net
    2: "4C",  # missing Sustained_Low_CPU
    3: "4D",  # missing Excessively_constant_RAM
    4: "4E",  # missing Daily_CPU_profile_lost
}

# For 3-of-5: map every triple (sorted tuple of indices) to letters A..J
THREE_COMBOS: List[Tuple[int, int, int]] = [
    (0, 1, 2),  # A
    (0, 1, 3),  # B
    (0, 1, 4),  # C
    (0, 2, 3),  # D
    (0, 2, 4),  # E
    (0, 3, 4),  # F
    (1, 2, 3),  # G
    (1, 2, 4),  # H
    (1, 3, 4),  # I
    (2, 3, 4),  # J
]
THREE_SET_TO_CODE: Dict[FrozenSet[int], str] = {
    frozenset(c): f"3{chr(ord('A') + i)}" for i, c in enumerate(THREE_COMBOS)
}

# For 2-of-5: pairs (sorted) → letters A..J
TWO_COMBOS: List[Tuple[int, int]] = [
    (0, 1),  # A
    (0, 2),  # B
    (0, 3),  # C
    (0, 4),  # D
    (1, 2),  # E
    (1, 3),  # F
    (1, 4),  # G
    (2, 3),  # H
    (2, 4),  # I
    (3, 4),  # J
]
TWO_SET_TO_CODE: Dict[FrozenSet[int], str] = {
    frozenset(c): f"2{chr(ord('A') + i)}" for i, c in enumerate(TWO_COMBOS)
}

# For 1-of-5: single index → letters A..E
ONE_INDEX_TO_CODE: Dict[int, str] = {
    0: "1A",
    1: "1B",
    2: "1C",
    3: "1D",
    4: "1E",
}


def _active_indices(host: Dict) -> List[int]:
    """
    Return indices (0..4) of criteria that are active (==1).
    Treat 0 and -1 as not active.
    """
    active = []
    for i, key in enumerate(CRITERIA_KEYS):
        try:
            if int(host.get(key, 0)) == 1:
                active.append(i)
        except Exception:
            # Non-int or missing values are treated as not active
            pass
    return active


def _code_for_active(active_idxs: List[int]) -> str:
    n = len(active_idxs)
    if n == 5:
        return "5"
    if n == 4:
        missing = ({0, 1, 2, 3, 4} - set(active_idxs)).pop()
        return FOUR_OF_FIVE_MISSING_TO_CODE[missing]
    if n == 3:
        return THREE_SET_TO_CODE[frozenset(active_idxs)]
    if n == 2:
        return TWO_SET_TO_CODE[frozenset(active_idxs)]
    if n == 1:
        return ONE_INDEX_TO_CODE[active_idxs[0]]
    return "0"


def _alias_for_code(code: str) -> str:
    """Get the human-readable alias/name for a zombie classification code."""
    return ALIAS_BY_CODE.get(code, code)  # fallback: alias = code (for 2*,1*)


def _description_for_active(active_idxs: List[int]) -> str:
    """Generate Spanish description for active criteria."""
    # Join the Spanish fragments for the active criteria in index order
    parts = [CRITERIA_DESCRIPTIONS[i] for i in active_idxs]
    return ", ".join(parts) if parts else "Sin criterios de zombie activos"


def classify_host(host: Dict) -> Tuple[str, str, str]:
    """
    Classify a host to the real Excel codes and return:
      (criterion_code, criterion_alias, criterion_description)

    Args:
        host: Host data dictionary with criterion fields

    Returns:
        Tuple of (code, alias, description) where:
        - code: Classification code like "2A", "1B", etc.
        - alias: Human-readable name like "Ghoul", "Wraith", etc.
        - description: Spanish description of active criteria
    """
    active = _active_indices(host)
    code = _code_for_active(active)
    alias = _alias_for_code(code)
    description = _description_for_active(active)
    return code, alias, description


def get_all_zombie_types() -> Dict[str, str]:
    """
    Get all available zombie types and their aliases.

    Returns:
        Dictionary mapping codes to aliases
    """
    return ALIAS_BY_CODE.copy()


def get_zombie_types_by_criteria_count() -> Dict[int, Dict[str, str]]:
    """
    Get zombie types grouped by number of active criteria.

    Returns:
        Dictionary with criteria count as key and {code: alias} as value
    """
    grouped = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}}

    for code, alias in ALIAS_BY_CODE.items():
        if code == "0":
            grouped[0][code] = alias
        elif code == "5":
            grouped[5][code] = alias
        elif code.startswith("4"):
            grouped[4][code] = alias
        elif code.startswith("3"):
            grouped[3][code] = alias
        elif code.startswith("2"):
            grouped[2][code] = alias
        elif code.startswith("1"):
            grouped[1][code] = alias

    return grouped


def get_criteria_combinations() -> Dict[str, List[str]]:
    """
    Get the criteria combinations for each zombie type.

    Returns:
        Dictionary mapping codes to list of criteria names
    """
    combinations = {}

    # Add detailed combinations for documentation
    combinations.update(
        {
            # Single criteria
            "1A": ["Recent_CPU_decrease_criterion"],
            "1B": ["Recent_net_traffic_decrease_criterion"],
            "1C": ["Sustained_Low_CPU_criterion"],
            "1D": ["Excessively_constant_RAM_criterion"],
            "1E": ["Daily_CPU_profile_lost_criterion"],
            # Double criteria
            "2A": [
                "Recent_CPU_decrease_criterion",
                "Recent_net_traffic_decrease_criterion",
            ],
            "2B": ["Recent_CPU_decrease_criterion", "Sustained_Low_CPU_criterion"],
            "2C": [
                "Recent_CPU_decrease_criterion",
                "Excessively_constant_RAM_criterion",
            ],
            "2D": ["Recent_CPU_decrease_criterion", "Daily_CPU_profile_lost_criterion"],
            "2E": [
                "Recent_net_traffic_decrease_criterion",
                "Sustained_Low_CPU_criterion",
            ],
            "2F": [
                "Recent_net_traffic_decrease_criterion",
                "Excessively_constant_RAM_criterion",
            ],
            "2G": [
                "Recent_net_traffic_decrease_criterion",
                "Daily_CPU_profile_lost_criterion",
            ],
            "2H": ["Sustained_Low_CPU_criterion", "Excessively_constant_RAM_criterion"],
            "2I": ["Sustained_Low_CPU_criterion", "Daily_CPU_profile_lost_criterion"],
            "2J": [
                "Excessively_constant_RAM_criterion",
                "Daily_CPU_profile_lost_criterion",
            ],
        }
    )

    # Add triple criteria combinations
    for combo_tuple, code in THREE_SET_TO_CODE.items():
        criteria_list = [CRITERIA_KEYS[i] for i in sorted(combo_tuple)]
        combinations[code] = criteria_list

    # Add quad criteria combinations (missing one)
    for missing_idx, code in FOUR_OF_FIVE_MISSING_TO_CODE.items():
        all_indices = {0, 1, 2, 3, 4}
        active_indices = all_indices - {missing_idx}
        criteria_list = [CRITERIA_KEYS[i] for i in sorted(active_indices)]
        combinations[code] = criteria_list

    # Add all criteria combination
    combinations["5"] = CRITERIA_KEYS.copy()

    # Add no criteria combination
    combinations["0"] = []

    return combinations
