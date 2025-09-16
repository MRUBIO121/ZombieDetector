import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from zombie_detector.core.zombie_tracker import ZombieTracker


class TestZombieTracking:
    def test_zombie_tracking_lifecycle(self):
        """Test complete zombie tracking lifecycle."""

        # Create temporary data directory
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ZombieTracker(temp_dir)

            # First detection - new zombies
            zombies_round1 = [
                {
                    "dynatrace_host_id": "HOST-1",
                    "hostname": "hostname1",
                    "criterion_type": "T1",
                    "criterion_alias": "CPU Performance Decline",
                    "is_zombie": True,
                },
                {
                    "dynatrace_host_id": "HOST-2",
                    "hostname": "hostname2",
                    "criterion_type": "T2",
                    "criterion_alias": "Network and CPU Decline",
                    "is_zombie": True,
                },
            ]

            tracking_info1 = tracker.save_current_zombies(zombies_round1)

            assert len(tracking_info1["new_zombies"]) == 2
            assert len(tracking_info1["persisting_zombies"]) == 0
            assert len(tracking_info1["killed_zombies"]) == 0
            assert "HOST-1" in tracking_info1["new_zombies"]
            assert "HOST-2" in tracking_info1["new_zombies"]

            # Second detection - one persists, one killed, one new
            zombies_round2 = [
                {
                    "dynatrace_host_id": "HOST-1",  # Persisting
                    "hostname": "hostname1",
                    "criterion_type": "T1",
                    "criterion_alias": "CPU Performance Decline",
                    "is_zombie": True,
                },
                {
                    "dynatrace_host_id": "HOST-3",  # New
                    "hostname": "hostname3",
                    "criterion_type": "T3",
                    "criterion_alias": "Resource Stagnation",
                    "is_zombie": True,
                },
                # HOST-2 is missing (killed)
            ]

            tracking_info2 = tracker.save_current_zombies(zombies_round2)

            assert len(tracking_info2["new_zombies"]) == 1
            assert len(tracking_info2["persisting_zombies"]) == 1
            assert len(tracking_info2["killed_zombies"]) == 1
            assert "HOST-3" in tracking_info2["new_zombies"]
            assert "HOST-1" in tracking_info2["persisting_zombies"]
            assert "HOST-2" in tracking_info2["killed_zombies"]

    def test_killed_zombie_detection(self):
        """Test detection of killed zombies."""

        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ZombieTracker(temp_dir)

            # Initial zombies
            initial_zombies = [
                {
                    "dynatrace_host_id": "HOST-1",
                    "hostname": "hostname1",
                    "criterion_type": "T1",
                    "criterion_alias": "CPU Performance Decline",
                    "is_zombie": True,
                }
            ]
            tracker.save_current_zombies(initial_zombies)

            # Remove the zombie (simulate killing)
            tracker.save_current_zombies([])  # No zombies

            # Check if zombie was killed
            killed_info = tracker.is_zombie_killed("HOST-1")
            assert killed_info is not None
            assert killed_info["dynatrace_host_id"] == "HOST-1"
            assert killed_info["hostname"] == "hostname1"
            assert "killed_at" in killed_info

            # Check killed zombies list
            killed_zombies = tracker.get_killed_zombies(24)
            assert len(killed_zombies) == 1
            assert killed_zombies[0]["dynatrace_host_id"] == "HOST-1"

    def test_zombie_lifecycle_tracking(self):
        """Test zombie lifecycle tracking."""

        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ZombieTracker(temp_dir)

            # Simulate multiple detections
            zombie_host = {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "criterion_type": "T1",
                "criterion_alias": "CPU Performance Decline",
                "is_zombie": True,
            }

            # First detection
            tracker.save_current_zombies([zombie_host])

            # Second detection (persisting)
            tracker.save_current_zombies([zombie_host])

            # Remove zombie (killed)
            tracker.save_current_zombies([])

            # Check lifecycle
            lifecycle = tracker.get_zombie_lifecycle("HOST-1")

            assert lifecycle["zombie_id"] == "HOST-1"
            assert lifecycle["total_detections"] == 2
            assert not lifecycle["is_active"]
            assert lifecycle["killed_info"] is not None
            assert lifecycle["first_seen"] is not None
            assert lifecycle["last_seen"] is not None

    def test_cleanup_old_data(self):
        """Test cleanup of old tracking data."""

        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ZombieTracker(temp_dir)

            # Create some old data
            old_zombie = {
                "dynatrace_host_id": "HOST-OLD",
                "hostname": "old-host",
                "criterion_type": "T1",
                "criterion_alias": "CPU Performance Decline",
                "is_zombie": True,
            }

            tracker.save_current_zombies([old_zombie])
            tracker.save_current_zombies([])  # Kill it

            # Cleanup with 0 days (should remove everything)
            tracker.cleanup_old_data(0)

            # Check that data was cleaned
            killed_zombies = tracker.get_killed_zombies(24)
            assert len(killed_zombies) == 0
