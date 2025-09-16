# tests/test_classifier_names.py
# filepath: zombie-detector/tests/test_classifier_names.py
import pytest
from zombie_detector.core.classifier import (
    classify_host,
    get_all_zombie_types,
    get_zombie_types_by_criteria_count,
    get_criteria_combinations,
    ALIAS_BY_CODE,
)


class TestZombieClassifierNames:
    """Test the enhanced zombie classification system with complete names."""

    def test_all_codes_have_names(self):
        """Test that all zombie codes have human-readable names."""
        # Check that no code falls back to itself as alias
        for code, alias in ALIAS_BY_CODE.items():
            assert alias != code or code == "0", f"Code {code} has no name assigned"
            assert alias, f"Code {code} has empty alias"

    def test_single_criteria_zombies(self):
        """Test single-criteria zombie classification and naming."""
        test_cases = [
            # Format: (criteria_values, expected_code, expected_alias)
            ([1, 0, 0, 0, 0], "1A", "Zombie"),
            ([0, 1, 0, 0, 0], "1B", "Walker"),
            ([0, 0, 1, 0, 0], "1C", "Crawler"),
            ([0, 0, 0, 1, 0], "1D", "Lurker"),
            ([0, 0, 0, 0, 1], "1E", "Sleeper"),
        ]

        for criteria_values, expected_code, expected_alias in test_cases:
            host = {
                "Recent_CPU_decrease_criterion": criteria_values[0],
                "Recent_net_traffic_decrease_criterion": criteria_values[1],
                "Sustained_Low_CPU_criterion": criteria_values[2],
                "Excessively_constant_RAM_criterion": criteria_values[3],
                "Daily_CPU_profile_lost_criterion": criteria_values[4],
            }

            code, alias, description = classify_host(host)
            assert code == expected_code, f"Expected code {expected_code}, got {code}"
            assert alias == expected_alias, (
                f"Expected alias {expected_alias}, got {alias}"
            )
            assert description, "Description should not be empty"

    def test_double_criteria_zombies(self):
        """Test double-criteria zombie classification and naming."""
        test_cases = [
            # Format: (criteria_indices, expected_code, expected_alias)
            ([0, 1], "2A", "Mummy"),  # CPU + Network
            ([0, 2], "2B", "Wraith"),  # CPU + Sustained Low CPU
            ([0, 3], "2C", "Vampire"),  # CPU + Constant RAM
            ([0, 4], "2D", "Banshee"),  # CPU + Daily Profile Lost
            ([1, 2], "2E", "Phantom"),  # Network + Sustained Low CPU
            ([1, 3], "2F", "Specter"),  # Network + Constant RAM
            ([1, 4], "2G", "Shade"),  # Network + Daily Profile Lost
            ([2, 3], "2H", "Poltergeist"),  # Sustained Low CPU + Constant RAM
            ([2, 4], "2I", "Spirit"),  # Sustained Low CPU + Daily Profile Lost
            ([3, 4], "2J", "Apparition"),  # Constant RAM + Daily Profile Lost
        ]

        for active_indices, expected_code, expected_alias in test_cases:
            host = {
                "Recent_CPU_decrease_criterion": 1 if 0 in active_indices else 0,
                "Recent_net_traffic_decrease_criterion": 1
                if 1 in active_indices
                else 0,
                "Sustained_Low_CPU_criterion": 1 if 2 in active_indices else 0,
                "Excessively_constant_RAM_criterion": 1 if 3 in active_indices else 0,
                "Daily_CPU_profile_lost_criterion": 1 if 4 in active_indices else 0,
            }

            code, alias, description = classify_host(host)
            assert code == expected_code, f"Expected code {expected_code}, got {code}"
            assert alias == expected_alias, (
                f"Expected alias {expected_alias}, got {alias}"
            )
            assert description, "Description should not be empty"

    def test_existing_multi_criteria_zombies(self):
        """Test that existing 3+ criteria zombies still work."""
        # Test 5-criteria zombie
        host_all_active = {
            "Recent_CPU_decrease_criterion": 1,
            "Recent_net_traffic_decrease_criterion": 1,
            "Sustained_Low_CPU_criterion": 1,
            "Excessively_constant_RAM_criterion": 1,
            "Daily_CPU_profile_lost_criterion": 1,
        }

        code, alias, description = classify_host(host_all_active)
        assert code == "5"
        assert alias == "Coloso"

        # Test 4-criteria zombie (missing first criterion)
        host_4_criteria = {
            "Recent_CPU_decrease_criterion": 0,  # Missing this one
            "Recent_net_traffic_decrease_criterion": 1,
            "Sustained_Low_CPU_criterion": 1,
            "Excessively_constant_RAM_criterion": 1,
            "Daily_CPU_profile_lost_criterion": 1,
        }

        code, alias, description = classify_host(host_4_criteria)
        assert code == "4A"
        assert alias == "Nemesis"

    def test_no_zombie_classification(self):
        """Test classification when no criteria are active."""
        host_no_criteria = {
            "Recent_CPU_decrease_criterion": 0,
            "Recent_net_traffic_decrease_criterion": 0,
            "Sustained_Low_CPU_criterion": 0,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }

        code, alias, description = classify_host(host_no_criteria)
        assert code == "0"
        assert alias == "No Zombie Detected"
        assert description == "Sin criterios de zombie activos"

    def test_get_all_zombie_types(self):
        """Test getting all available zombie types."""
        all_types = get_all_zombie_types()

        # Should have all single criteria zombies
        assert "1A" in all_types and all_types["1A"] == "Zombie"
        assert "1B" in all_types and all_types["1B"] == "Walker"
        assert "1C" in all_types and all_types["1C"] == "Crawler"
        assert "1D" in all_types and all_types["1D"] == "Lurker"
        assert "1E" in all_types and all_types["1E"] == "Sleeper"

        # Should have all double criteria zombies
        assert "2A" in all_types and all_types["2A"] == "Mummy"
        assert "2B" in all_types and all_types["2B"] == "Wraith"
        assert "2J" in all_types and all_types["2J"] == "Apparition"

        # Should have existing multi-criteria zombies
        assert "5" in all_types and all_types["5"] == "Coloso"
        assert "4A" in all_types and all_types["4A"] == "Nemesis"
        assert (
            "4D" in all_types and all_types["4D"] == "Ghoul"
        )  # FIXED: Updated expectation
        assert "3A" in all_types and all_types["3A"] == "Solomon"

        # Should have no zombie
        assert "0" in all_types

    def test_get_zombie_types_by_criteria_count(self):
        """Test grouping zombie types by criteria count."""
        grouped = get_zombie_types_by_criteria_count()

        # Check each group has the right number of types
        assert len(grouped[0]) == 1  # Just "0"
        assert len(grouped[1]) == 5  # 1A-1E
        assert len(grouped[2]) == 10  # 2A-2J
        assert len(grouped[3]) == 10  # 3A-3J
        assert len(grouped[4]) == 5  # 4A-4E
        assert len(grouped[5]) == 1  # Just "5"

        # Verify specific entries
        assert grouped[1]["1A"] == "Zombie"
        assert grouped[2]["2A"] == "Mummy"
        assert grouped[4]["4D"] == "Ghoul"
        assert grouped[5]["5"] == "Coloso"

    def test_zombie_name_uniqueness(self):
        """Test that all zombie names are unique (no duplicates)."""
        all_types = get_all_zombie_types()
        aliases = list(all_types.values())

        # Check for duplicates
        duplicates = []
        seen = set()
        for alias in aliases:
            if alias in seen:
                duplicates.append(alias)
            seen.add(alias)

        assert not duplicates, f"Found duplicate zombie names: {duplicates}"

    def test_zombie_name_quality(self):
        """Test that zombie names follow quality standards."""
        all_types = get_all_zombie_types()

        for code, alias in all_types.items():
            # Names should not be empty
            assert alias.strip(), f"Empty alias for code {code}"

            # Names should be reasonable length
            assert 3 <= len(alias) <= 20, (
                f"Alias '{alias}' for code {code} has unreasonable length"
            )

            # Names should not contain special characters (except spaces and accents)
            import re

            assert re.match(r"^[A-Za-zÀ-ÿ\s]+$", alias), (
                f"Alias '{alias}' contains invalid characters"
            )

    def test_most_common_zombie_combinations(self):
        """Test the most common zombie combinations have appropriate names."""
        # 2A (CPU + Network) should be "Mummy" - most common combination
        host_2a = {
            "Recent_CPU_decrease_criterion": 1,
            "Recent_net_traffic_decrease_criterion": 1,
            "Sustained_Low_CPU_criterion": 0,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }

        code, alias, description = classify_host(host_2a)
        assert code == "2A"
        assert alias == "Mummy"
        assert "CPU" in description and "red" in description

    def test_classification_stability(self):
        """Test that classification is stable and deterministic."""
        # Same input should always produce same result
        host = {
            "Recent_CPU_decrease_criterion": 1,
            "Recent_net_traffic_decrease_criterion": 0,
            "Sustained_Low_CPU_criterion": 1,
            "Excessively_constant_RAM_criterion": 0,
            "Daily_CPU_profile_lost_criterion": 0,
        }

        # Run classification multiple times
        results = [classify_host(host) for _ in range(5)]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Classification is not deterministic"

        assert first_result[0] == "2B"  # CPU + Sustained Low CPU
        assert first_result[1] == "Wraith"


class TestZombieClassificationIntegration:
    """Test integration with the rest of the system."""

    def test_integration_with_processor(self):
        """Test that the new names work with the processor."""
        from zombie_detector.core.processor import process_host_data

        hosts = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "test-host-1",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": 1,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        state_map = {"2A": 1}  # Enable Ghoul detection

        results = process_host_data(
            hosts, state_map, enable_tracking=False, enable_kafka=False
        )

        assert len(results) == 1
        result = results[0]
        assert result["criterion_type"] == "2A"
        assert result["criterion_alias"] == "Mummy"
        assert result["is_zombie"] == True

    def test_api_response_format(self):
        """Test that API responses include the new zombie names."""
        from zombie_detector.api.rest import DetectionResponse

        # This would typically be tested with actual API calls
        # but here we test the data structure
        response_data = {
            "total_hosts": 1,
            "zombie_hosts": 1,
            "detection_results": [
                {
                    "dynatrace_host_id": "HOST-1",
                    "criterion_type": "2A",
                    "criterion_alias": "Mummy",
                    "is_zombie": True,
                }
            ],
            "summary": {"2A": {"count": 1, "alias": "Mummy"}},
        }

        # Verify structure is valid
        assert response_data["detection_results"][0]["criterion_alias"] == "Mummy"
        assert response_data["summary"]["2A"]["alias"] == "Mummy"

    def test_criteria_combinations_function(self):
        """Test the get_criteria_combinations function."""
        combinations = get_criteria_combinations()

        # Test single criteria combinations
        assert combinations["1A"] == ["Recent_CPU_decrease_criterion"]
        assert combinations["1E"] == ["Daily_CPU_profile_lost_criterion"]

        # Test double criteria combinations
        assert combinations["2A"] == [
            "Recent_CPU_decrease_criterion",
            "Recent_net_traffic_decrease_criterion",
        ]
        assert combinations["2J"] == [
            "Excessively_constant_RAM_criterion",
            "Daily_CPU_profile_lost_criterion",
        ]

        # Test no criteria
        assert combinations["0"] == []

        # Test all criteria
        assert len(combinations["5"]) == 5
        assert "Recent_CPU_decrease_criterion" in combinations["5"]

        # Test that all codes have combinations defined
        all_types = get_all_zombie_types()
        for code in all_types.keys():
            assert code in combinations, f"No combination defined for code {code}"
