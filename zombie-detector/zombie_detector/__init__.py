import json
from .core.classifier import classify_host
from .core.state_loader import load_criterion_type_states
from .core.processor import process_host_data


def process_zombies(data_path, state_path):
    """
    Main function to process zombie detection on host data.
    """
    with open(data_path) as f:
        hosts = json.load(f)

    state_map = load_criterion_type_states(state_path)

    # Use the processor function for consistency
    enriched = process_host_data(hosts, state_map)

    return enriched
