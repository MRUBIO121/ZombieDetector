import pytest
import tempfile
import os
from unittest.mock import patch, Mock


@pytest.fixture(autouse=True)
def mock_zombie_tracker(request):
    """Mock ZombieTracker to use temp directories, but skip for tracking tests."""
    # Skip mocking for tracking tests
    if "test_tracking" in request.node.name or "TestZombieTracking" in str(
        request.node.cls
    ):
        yield None
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        with (
            patch(
                "zombie_detector.core.zombie_tracker.ZombieTracker.__init__",
                lambda self, data_dir=None: None,
            ),
            patch(
                "zombie_detector.core.zombie_tracker.ZombieTracker.save_current_zombies"
            ) as mock_save,
        ):
            # Set up the mock return value
            mock_save.return_value = {
                "new_zombies": [],
                "persisting_zombies": [],
                "killed_zombies": [],
                "stats": {
                    "total_zombies": 0,
                    "new_zombies": 0,
                    "persisting_zombies": 0,
                    "killed_zombies": 0,
                },
            }

            yield temp_dir


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for zombie tracking data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_zombie_data():
    """Sample zombie data for testing."""
    return [
        {
            "dynatrace_host_id": "HOST-1",
            "hostname": "hostname1",
            "criterion_type": "T1",
            "criterion_alias": "CPU Performance Decline",
            "is_zombie": True,
            "tenant": "tenant1",
            "asset_tag": "CI01234567",
        }
    ]
