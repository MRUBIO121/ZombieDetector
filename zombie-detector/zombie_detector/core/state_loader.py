import json
import os


def load_criterion_type_states(state_path):
    """
    Load criterion type states from a JSON file.
    Returns a mapping of criterion_type -> state value.
    """
    if not os.path.exists(state_path):
        # Return default states if file doesn't exist
        return {
            "T1": 1,  # Active
            "T2": 1,  # Active
            "T3": 1,  # Active
            "T4": 1,  # Active
            "T5": 0,  # Inactive
            "T6": 0,  # Inactive
        }

    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Return default states on error
        return {
            "T1": 1,
            "T2": 1,
            "T3": 1,
            "T4": 1,
            "T5": 0,
            "T6": 0,
        }
