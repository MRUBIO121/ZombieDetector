import json
import csv
from typing import List, Dict, Any
from datetime import datetime


def save_results_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save zombie detection results to a JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def save_results_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save zombie detection results to a CSV file.
    """
    if not data:
        return

    fieldnames = data[0].keys()
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_host_data(host: Dict[str, Any]) -> bool:
    """
    Validate that a host has the required fields for zombie detection.
    """
    required_fields = [
        "dynatrace_host_id",
        "hostname",
        "Recent_CPU_decrease_criterion",
        "Recent_net_traffic_decrease_criterion",
        "Sustained_Low_CPU_criterion",
        "Excessively_constant_RAM_criterion",
        "Daily_CPU_profile_lost_criterion",
    ]

    return all(field in host for field in required_fields)


def generate_report_timestamp() -> str:
    """
    Generate a timestamp string for reports.
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
