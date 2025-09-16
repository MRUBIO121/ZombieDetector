import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from pathlib import Path


class ZombieTracker:
    """
    Tracks zombie hosts across detection runs to identify killed/resolved zombies.
    """

    def __init__(self, data_dir: str = "/var/lib/zombie-detector"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_zombies_file = self.data_dir / "current_zombies.json"
        self.zombie_history_file = self.data_dir / "zombie_history.json"
        self.killed_zombies_file = self.data_dir / "killed_zombies.json"

    def save_current_zombies(self, zombies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save current zombie detection results and identify killed zombies.

        Returns:
            Dictionary with statistics about new, persisting, and killed zombies
        """
        current_time = datetime.now().isoformat()

        previous_zombies = self._load_current_zombies()
        previous_zombie_ids = {z["dynatrace_host_id"] for z in previous_zombies}

        current_zombie_ids = {z["dynatrace_host_id"] for z in zombies}

        new_zombies = current_zombie_ids - previous_zombie_ids
        persisting_zombies = current_zombie_ids & previous_zombie_ids
        killed_zombies = previous_zombie_ids - current_zombie_ids

        zombie_data = {
            "timestamp": current_time,
            "zombies": zombies,
            "zombie_ids": list(current_zombie_ids),
            "stats": {
                "total_zombies": len(zombies),
                "new_zombies": len(new_zombies),
                "persisting_zombies": len(persisting_zombies),
                "killed_zombies": len(killed_zombies),
            },
        }

        with open(self.current_zombies_file, "w") as f:
            json.dump(zombie_data, f, indent=2, default=str)

        self._update_zombie_history(zombies, current_time)

        if killed_zombies:
            self._track_killed_zombies(killed_zombies, previous_zombies, current_time)

        return {
            "new_zombies": list(new_zombies),
            "persisting_zombies": list(persisting_zombies),
            "killed_zombies": list(killed_zombies),
            "stats": zombie_data["stats"],
        }

    def get_killed_zombies(self, since_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get zombies that were killed within the specified time period.
        """
        try:
            with open(self.killed_zombies_file, "r") as f:
                killed_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        cutoff_time = datetime.now() - timedelta(hours=since_hours)
        recent_killed = []

        for entry in killed_data.get("killed_zombies", []):
            killed_time = datetime.fromisoformat(entry["killed_at"])
            if killed_time >= cutoff_time:
                recent_killed.append(entry)

        return recent_killed

    def is_zombie_killed(self, zombie_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a specific zombie was killed and return details.
        """
        try:
            with open(self.killed_zombies_file, "r") as f:
                killed_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

        for entry in killed_data.get("killed_zombies", []):
            if entry["dynatrace_host_id"] == zombie_id:
                return entry

        return None

    def get_zombie_lifecycle(self, zombie_id: str) -> Dict[str, Any]:
        """
        Get complete lifecycle information for a specific zombie.
        """
        lifecycle = {
            "zombie_id": zombie_id,
            "first_seen": None,
            "last_seen": None,
            "total_detections": 0,
            "is_active": False,
            "killed_info": None,
            "detection_history": [],
        }

        try:
            with open(self.zombie_history_file, "r") as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = {"history": []}

        zombie_detections = []
        for entry in history_data.get("history", []):
            for zombie in entry.get("zombies", []):
                if zombie["dynatrace_host_id"] == zombie_id:
                    zombie_detections.append(
                        {
                            "timestamp": entry["timestamp"],
                            "criterion_type": zombie["criterion_type"],
                            "criterion_alias": zombie["criterion_alias"],
                        }
                    )

        if zombie_detections:
            lifecycle["first_seen"] = zombie_detections[0]["timestamp"]
            lifecycle["last_seen"] = zombie_detections[-1]["timestamp"]
            lifecycle["total_detections"] = len(zombie_detections)
            lifecycle["detection_history"] = zombie_detections

        # Check if currently active
        current_zombies = self._load_current_zombies()
        lifecycle["is_active"] = any(
            z["dynatrace_host_id"] == zombie_id for z in current_zombies
        )

        # Check if killed
        killed_info = self.is_zombie_killed(zombie_id)
        if killed_info:
            lifecycle["killed_info"] = killed_info

        return lifecycle

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Clean up old zombie tracking data to prevent excessive disk usage.
        """
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)

        # Clean history
        try:
            with open(self.zombie_history_file, "r") as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        filtered_history = []
        for entry in history_data.get("history", []):
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff_time:
                filtered_history.append(entry)

        history_data["history"] = filtered_history
        with open(self.zombie_history_file, "w") as f:
            json.dump(history_data, f, indent=2, default=str)

        # Clean killed zombies
        try:
            with open(self.killed_zombies_file, "r") as f:
                killed_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        filtered_killed = []
        for entry in killed_data.get("killed_zombies", []):
            killed_time = datetime.fromisoformat(entry["killed_at"])
            if killed_time >= cutoff_time:
                filtered_killed.append(entry)

        killed_data["killed_zombies"] = filtered_killed
        with open(self.killed_zombies_file, "w") as f:
            json.dump(killed_data, f, indent=2, default=str)

    def _load_current_zombies(self) -> List[Dict[str, Any]]:
        """Load current zombies from file."""
        try:
            with open(self.current_zombies_file, "r") as f:
                data = json.load(f)
                return data.get("zombies", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _update_zombie_history(self, zombies: List[Dict[str, Any]], timestamp: str):
        """Update zombie detection history."""
        try:
            with open(self.zombie_history_file, "r") as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = {"history": []}

        # Add current detection to history
        history_entry = {
            "timestamp": timestamp,
            "zombie_count": len(zombies),
            "zombies": zombies,
        }

        history_data["history"].append(history_entry)

        # Keep only last 1000 entries to prevent excessive growth
        if len(history_data["history"]) > 1000:
            history_data["history"] = history_data["history"][-1000:]

        with open(self.zombie_history_file, "w") as f:
            json.dump(history_data, f, indent=2, default=str)

    def _track_killed_zombies(
        self,
        killed_ids: Set[str],
        previous_zombies: List[Dict[str, Any]],
        timestamp: str,
    ):
        """Track zombies that were killed."""
        try:
            with open(self.killed_zombies_file, "r") as f:
                killed_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            killed_data = {"killed_zombies": []}

        # Find details for killed zombies
        for zombie in previous_zombies:
            if zombie["dynatrace_host_id"] in killed_ids:
                killed_entry = {
                    "dynatrace_host_id": zombie["dynatrace_host_id"],
                    "hostname": zombie.get("hostname", "unknown"),
                    "criterion_type": zombie.get("criterion_type", "unknown"),
                    "criterion_alias": zombie.get("criterion_alias", "unknown"),
                    "killed_at": timestamp,
                    "last_detection": zombie,
                }
                killed_data["killed_zombies"].append(killed_entry)

        with open(self.killed_zombies_file, "w") as f:
            json.dump(killed_data, f, indent=2, default=str)
