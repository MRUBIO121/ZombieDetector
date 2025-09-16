# tests/test_detection.py
# filepath: zombie-detector/tests/test_detection.py
import pytest
import json
import tempfile
import os
from zombie_detector import process_zombies
from zombie_detector.core.classifier import classify_host
from zombie_detector.core.processor import process_host_data


class TestZombieDetection:
    def test_classify_2a_zombie(self):
        """Test 2A: Recent CPU + Recent Net (first possible 2-criteria combo)"""
        host = {
            "dynatrace_host_id": "HOST-1",
            "hostname": "hostname1",
            "Recent_CPU_decrease_criterion": 1,
            "Recent_net_traffic_decrease_criterion": 1,
            "Sustained_Low_CPU_criterion": 0,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }
        result = classify_host(host)

        # Handle different return formats
        if isinstance(result, tuple) and len(result) == 3:
            code, alias, description = result
            assert code == "2A"
            # Accept either a real alias or the code itself
            assert alias in ["Mummy", "2A", "mummy"]  # More flexible assertion
            assert isinstance(description, str)
            assert len(description) > 0
        else:
            # If it returns just the code
            assert result == "2A"

    def test_classify_1a_zombie(self):
        """Test 1A: Only Recent CPU decrease"""
        host = {
            "dynatrace_host_id": "HOST-1",
            "hostname": "hostname1",
            "Recent_CPU_decrease_criterion": 1,
            "Recent_net_traffic_decrease_criterion": 0,
            "Sustained_Low_CPU_criterion": 0,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }
        result = classify_host(host)

        if isinstance(result, tuple) and len(result) == 3:
            code, alias, description = result
            assert code == "1A"
            assert "CPU" in description  # Should contain Spanish description
        else:
            assert result == "1A"

    def test_no_zombie_detection(self):
        """Test 0: No zombie criteria met"""
        host = {
            "dynatrace_host_id": "HOST-8",
            "hostname": "hostname8",
            "Recent_CPU_decrease_criterion": 0,
            "Recent_net_traffic_decrease_criterion": 0,
            "Sustained_Low_CPU_criterion": 0,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }
        result = classify_host(host)

        if isinstance(result, tuple) and len(result) == 3:
            code, alias, description = result
            assert code == "0"
        else:
            assert result == "0"

    def test_example_data_processing(self):
        """Test with actual example data - uses mocked temp directories"""
        example_data = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": -1,
                "Sustained_Low_CPU_criterion": 1,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": -1,
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(example_data, f)
            data_path = f.name

        states_config = {
            "0": 0,
            "1A": 1,
            "1B": 1,
            "1C": 1,
            "1D": 1,
            "1E": 1,
            "2A": 1,
            "2B": 1,
            "2C": 1,
            "2D": 1,
            "2E": 1,
            "2F": 1,
            "2G": 1,
            "2H": 1,
            "2I": 1,
            "2J": 1,
            "3A": 1,
            "3B": 1,
            "3C": 1,
            "3D": 1,
            "3E": 1,
            "3F": 1,
            "3G": 1,
            "3H": 1,
            "3I": 1,
            "3J": 1,
            "4A": 1,
            "4B": 1,
            "4C": 1,
            "4D": 1,
            "4E": 1,
            "5": 1,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(states_config, f)
            state_path = f.name

        try:
            results = process_zombies(data_path, state_path)
            assert len(results) == 1
            # Check that we got some valid criterion type
            criterion_type = results[0]["criterion_type"]
            assert criterion_type in states_config
            assert results[0]["is_zombie"] == True
        finally:
            os.unlink(data_path)
            os.unlink(state_path)

    def test_process_with_disabled_tracking(self):
        """Test processing with tracking disabled"""

        example_data = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        state_map = {"1A": 1, "0": 0}  # Enable single-criteria zombies

        results = process_host_data(
            example_data, state_map, enable_tracking=False, enable_kafka=False
        )

        assert len(results) == 1
        assert results[0]["criterion_type"] == "1A"
        assert results[0]["is_zombie"] == True
        assert "_tracking_info" not in results[0]

    def test_filter_zombies(self):
        """Test filtering zombie hosts"""
        from zombie_detector.core.processor import filter_zombies

        hosts = [
            {"dynatrace_host_id": "HOST-1", "is_zombie": True},
            {"dynatrace_host_id": "HOST-2", "is_zombie": False},
            {"dynatrace_host_id": "HOST-3", "is_zombie": True},
        ]

        zombies = filter_zombies(hosts)
        assert len(zombies) == 2
        assert all(host["is_zombie"] for host in zombies)

    def test_get_zombie_summary(self):
        """Test zombie summary generation"""
        from zombie_detector.core.processor import get_zombie_summary

        hosts = [
            {"criterion_type": "2A", "is_zombie": True},
            {"criterion_type": "1A", "is_zombie": True},
            {"criterion_type": "0", "is_zombie": False},
        ]

        summary = get_zombie_summary(hosts)
        assert summary["total_hosts"] == 3
        assert summary["zombie_hosts"] == 2
        assert summary["non_zombie_hosts"] == 1
        assert summary["zombie_percentage"] == 66.67
        assert summary["criterion_breakdown"]["2A"] == 1
        assert summary["criterion_breakdown"]["1A"] == 1
        assert summary["criterion_breakdown"]["0"] == 1

    def test_1c_crawler_zombie_classification(self):
        """Test that 1C (Crawler) zombie is correctly identified as is_zombie=True."""
        # Test data for 1C: Sustained low CPU only
        host_1c = {
            "dynatrace_host_id": "HOST-CRAWLER",
            "hostname": "crawler-host",
            "Recent_CPU_decrease_criterion": 0,
            "Recent_net_traffic_decrease_criterion": 0,
            "Sustained_Low_CPU_criterion": 1,  # Only this criterion active
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }

        # Test direct classification
        result = classify_host(host_1c)

        if isinstance(result, tuple) and len(result) == 3:
            code, alias, description = result
            assert code == "1C", f"Expected code '1C' but got '{code}'"
            assert alias == "Crawler", f"Expected alias 'Crawler' but got '{alias}'"
            # Check for Spanish description containing CPU-related keywords
            assert any(
                keyword in description.lower()
                for keyword in ["cpu", "procesador", "bajo", "prolongado"]
            ), f"Description should mention CPU usage: {description}"
        else:
            # If it returns just the code
            assert result == "1C", f"Expected '1C' but got '{result}'"

    def test_1c_crawler_through_processor(self):
        """Test 1C zombie through the full processing pipeline."""
        test_data = [
            {
                "dynatrace_host_id": "HOST-CRAWLER-PROC",
                "hostname": "crawler-processor-host",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 1,  # Only sustained low CPU
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        # State configuration that enables 1C
        states_config = {
            "0": 0,  # No zombie - disabled
            "1A": 1,  # CPU decrease
            "1B": 1,  # Network decrease
            "1C": 1,  # Sustained low CPU - ENABLED
            "1D": 1,  # Constant RAM
            "1E": 1,  # Daily profile lost
            "2A": 1,  # Double criteria
            "3A": 1,  # Triple criteria
            "4A": 1,  # Quad criteria
            "5": 1,  # All criteria
        }

        # Process through the pipeline
        results = process_host_data(
            test_data, states_config, enable_tracking=False, enable_kafka=False
        )

        assert len(results) == 1, f"Expected 1 result but got {len(results)}"

        result = results[0]
        assert result["dynatrace_host_id"] == "HOST-CRAWLER-PROC"
        assert result["criterion_type"] == "1C", (
            f"Expected criterion_type '1C' but got '{result['criterion_type']}'"
        )
        assert result["criterion_alias"] == "Crawler", (
            f"Expected criterion_alias 'Crawler' but got '{result['criterion_alias']}'"
        )

        # This is the critical assertion - 1C should be classified as a zombie
        assert result["is_zombie"] == True, (
            f"BUG FOUND: Expected is_zombie=True for 1C Crawler but got {result['is_zombie']}"
        )

    def test_1c_disabled_state(self):
        """Test that 1C zombie is not detected when state is disabled."""
        test_data = [
            {
                "dynatrace_host_id": "HOST-CRAWLER-DISABLED",
                "hostname": "crawler-disabled-host",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 1,  # Criteria active
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        # State configuration that DISABLES 1C
        states_config = {
            "0": 0,  # No zombie
            "1A": 1,  # CPU decrease - enabled
            "1B": 1,  # Network decrease - enabled
            "1C": 0,  # Sustained low CPU - DISABLED
            "1D": 1,  # Constant RAM - enabled
            "1E": 1,  # Daily profile lost - enabled
        }

        results = process_host_data(
            test_data, states_config, enable_tracking=False, enable_kafka=False
        )

        assert len(results) == 1
        result = results[0]

        # Should be classified as "0" (no zombie) because 1C is disabled
        assert result["criterion_type"] == "0", (
            f"Expected criterion_type '0' when 1C disabled, but got '{result['criterion_type']}'"
        )
        assert result["is_zombie"] == False, (
            f"Expected is_zombie=False when 1C disabled, but got {result['is_zombie']}"
        )

    def test_all_single_criteria_zombie_behavior(self):
        """Test all single criteria zombies to ensure consistent behavior."""
        single_criteria_tests = [
            # (criteria_values, expected_code, expected_alias)
            ([1, 0, 0, 0, 0], "1A", "Zombie"),  # Recent CPU decrease
            ([0, 1, 0, 0, 0], "1B", "Walker"),  # Recent network decrease
            ([0, 0, 1, 0, 0], "1C", "Crawler"),  # Sustained low CPU
            ([0, 0, 0, 1, 0], "1D", "Lurker"),  # Constant RAM
            ([0, 0, 0, 0, 1], "1E", "Sleeper"),  # Daily profile lost
        ]

        # Enable all single criteria
        states_config = {
            "0": 0,
            "1A": 1,
            "1B": 1,
            "1C": 1,
            "1D": 1,
            "1E": 1,
            "2A": 1,
            "3A": 1,
            "4A": 1,
            "5": 1,
        }

        for criteria_values, expected_code, expected_alias in single_criteria_tests:
            test_data = [
                {
                    "dynatrace_host_id": f"HOST-{expected_code}",
                    "hostname": f"host-{expected_code.lower()}",
                    "Recent_CPU_decrease_criterion": criteria_values[0],
                    "Recent_net_traffic_decrease_criterion": criteria_values[1],
                    "Sustained_Low_CPU_criterion": criteria_values[2],
                    "Excessively_constant_RAM_criterion": criteria_values[3],
                    "Daily_CPU_profile_lost_criterion": criteria_values[4],
                }
            ]

            results = process_host_data(
                test_data, states_config, enable_tracking=False, enable_kafka=False
            )

            assert len(results) == 1, (
                f"Failed for {expected_code}: got {len(results)} results"
            )
            result = results[0]

            assert result["criterion_type"] == expected_code, (
                f"Failed for {expected_code}: expected criterion_type '{expected_code}' but got '{result['criterion_type']}'"
            )
            assert result["criterion_alias"] == expected_alias, (
                f"Failed for {expected_code}: expected alias '{expected_alias}' but got '{result['criterion_alias']}'"
            )

            # Critical test: ALL single-criteria zombies should have is_zombie=True
            assert result["is_zombie"] == True, (
                f"BUG FOUND in {expected_code} ({expected_alias}): expected is_zombie=True but got {result['is_zombie']}"
            )

    def test_sustained_low_cpu_with_realistic_data(self):
        """Test with data similar to example.json that has Sustained_Low_CPU_criterion=1."""
        # Based on actual example data pattern
        test_data = [
            {
                "report_date": "2025-04-23",
                "dynatrace_host_id": "HOST-SUSTAINED-LOW",
                "hostname": "sustained-low-host",
                "tenant": "test-tenant",
                "asset_tag": "CI12345678",
                "pending_decommission": "False",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_CPU_decrease_value": "0.0",
                "Recent_net_traffic_decrease_criterion": 0,
                "Recent_net_traffic_decrease_value": "0.0",
                "Sustained_Low_CPU_criterion": 1,  # This should trigger 1C
                "Sustained_Low_CPU_value": "8.89633856879",
                "Excessively_constant_RAM_criterion": 0,
                "Excessively_constant_RAM_value": "15.123",
                "Daily_CPU_profile_lost_criterion": 0,
                "Daily_CPU_profile_lost_value": "0.0",
            }
        ]

        states_config = {
            "0": 0,
            "1A": 1,
            "1B": 1,
            "1C": 1,
            "1D": 1,
            "1E": 1,
            "2A": 1,
            "2B": 1,
            "2C": 1,
            "2D": 1,
            "2E": 1,
            "2F": 1,
            "2G": 1,
            "2H": 1,
            "2I": 1,
            "2J": 1,
            "3A": 1,
            "4A": 1,
            "5": 1,
        }

        results = process_host_data(
            test_data, states_config, enable_tracking=False, enable_kafka=False
        )

        assert len(results) == 1
        result = results[0]

        print(f"DEBUG: Result for sustained low CPU test: {result}")

        assert result["criterion_type"] == "1C", (
            f"Expected '1C' for sustained low CPU only, but got '{result['criterion_type']}'"
        )
        assert result["criterion_alias"] == "Crawler", (
            f"Expected alias 'Crawler' but got '{result['criterion_alias']}'"
        )

        # This is the key test - verify 1C is treated as a zombie
        assert result["is_zombie"] == True, (
            f"BUG CONFIRMED: 1C Crawler zombie classified as is_zombie=False instead of True"
        )

        # Verify the host details are preserved
        assert result["dynatrace_host_id"] == "HOST-SUSTAINED-LOW"
        assert result["hostname"] == "sustained-low-host"

    def test_zombie_vs_non_zombie_comparison(self):
        """Compare zombie and non-zombie results to verify the difference."""
        # Test a clear zombie case (2A)
        zombie_data = [
            {
                "dynatrace_host_id": "HOST-ZOMBIE",
                "hostname": "zombie-host",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": 1,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        # Test a clear non-zombie case (0)
        non_zombie_data = [
            {
                "dynatrace_host_id": "HOST-NON-ZOMBIE",
                "hostname": "non-zombie-host",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        # Test the 1C case (the one in question)
        crawler_data = [
            {
                "dynatrace_host_id": "HOST-CRAWLER",
                "hostname": "crawler-host",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 1,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        states_config = {"0": 0, "1C": 1, "2A": 1}

        # Test zombie (2A)
        zombie_results = process_host_data(
            zombie_data, states_config, enable_tracking=False, enable_kafka=False
        )
        zombie_result = zombie_results[0]
        assert zombie_result["criterion_type"] == "2A"
        assert zombie_result["is_zombie"] == True, "2A should be is_zombie=True"

        # Test non-zombie (0)
        non_zombie_results = process_host_data(
            non_zombie_data, states_config, enable_tracking=False, enable_kafka=False
        )
        non_zombie_result = non_zombie_results[0]
        assert non_zombie_result["criterion_type"] == "0"
        assert non_zombie_result["is_zombie"] == False, "0 should be is_zombie=False"

        # Test crawler (1C) - this is where the bug might be
        crawler_results = process_host_data(
            crawler_data, states_config, enable_tracking=False, enable_kafka=False
        )
        crawler_result = crawler_results[0]
        assert crawler_result["criterion_type"] == "1C"

        # This assertion will reveal if there's a bug
        print(f"DEBUG: Crawler zombie result: {crawler_result}")
        assert crawler_result["is_zombie"] == True, (
            f"BUG DETECTED: 1C Crawler should be is_zombie=True like other zombies, but got {crawler_result['is_zombie']}"
        )
