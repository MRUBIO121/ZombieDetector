# tests/test_procesor_kafka.py
# filepath: zombie-detector/tests/test_procesor_kafka.py
import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from zombie_detector.core.processor import process_host_data, _load_kafka_config


class TestProcessorKafkaIntegration:
    def setUp(self):
        """Set up test data."""
        self.sample_hosts = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": -1,  # Inactive
                "Sustained_Low_CPU_criterion": 1,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": -1,
                "tenant": "tenant1",
                "asset_tag": "CI01234567",
            },
            {
                "dynatrace_host_id": "HOST-2",
                "hostname": "hostname2",
                "Recent_CPU_decrease_criterion": 1,
                "Recent_net_traffic_decrease_criterion": 1,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": -1,  # Inactive
                "Daily_CPU_profile_lost_criterion": -1,
                "tenant": "tenant2",
                "asset_tag": "CI02345678",
            },
        ]

        # Use the real criterion codes from your system
        self.state_map = {
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

    @patch("zombie_detector.core.processor.ZombieKafkaPublisher")
    @patch("zombie_detector.core.processor._load_kafka_config")
    @patch("zombie_detector.core.processor.ZombieTracker")
    def test_process_host_data_with_kafka_enabled(
        self, mock_tracker, mock_kafka_config, mock_publisher
    ):
        """Test processing hosts with Kafka publishing enabled."""
        self.setUp()

        # Mock Kafka config
        mock_kafka_config.return_value = {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "test-zombie",
        }

        # Mock tracker
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.save_current_zombies.return_value = {
            "new_zombies": ["HOST-1"],
            "persisting_zombies": [],
            "killed_zombies": [],
            "stats": {"total_zombies": 1, "new_zombies": 1},
        }

        # Mock publisher
        mock_publisher_instance = Mock()
        mock_publisher.return_value = mock_publisher_instance

        results = process_host_data(
            self.sample_hosts, self.state_map, enable_tracking=True, enable_kafka=True
        )

        # Verify results
        assert len(results) == 2

        # FIXED: Based on your actual classification logic
        # HOST-1: CPU(index 0) + Sustained_Low_CPU(index 2) = "2B" (combination of indices 0,2)
        assert results[0]["criterion_type"] == "2B"
        assert results[0]["is_zombie"]

        # HOST-2: CPU(index 0) + Network(index 1) = "2A" (combination of indices 0,1)
        assert results[1]["criterion_type"] == "2A"
        assert results[1]["is_zombie"]

        # FIXED: Verify Kafka publisher was called with authentication parameters
        mock_publisher.assert_called_once_with(
            bootstrap_servers="localhost:9092",
            topic_prefix="test-zombie",
            security_protocol="PLAINTEXT",
            ssl_config=None,
            sasl_config=None,
        )
        mock_publisher_instance.publish_zombie_detection.assert_called_once()
        mock_publisher_instance.publish_tracking_stats.assert_called_once()
        mock_publisher_instance.publish_zombie_lifecycle_event.assert_called()
        mock_publisher_instance.close.assert_called_once()

    @patch("zombie_detector.core.processor.ZombieKafkaPublisher")
    @patch("zombie_detector.core.processor._load_kafka_config")
    def test_process_host_data_with_kafka_disabled(
        self, mock_kafka_config, mock_publisher
    ):
        """Test processing hosts with Kafka disabled."""
        self.setUp()

        # Mock Kafka config - disabled
        mock_kafka_config.return_value = {"enabled": False}

        results = process_host_data(
            self.sample_hosts,
            self.state_map,
            enable_tracking=False,
            enable_kafka=True,  # Enabled but config says disabled
        )

        # Verify results
        assert len(results) == 2

        # Verify Kafka publisher was not called
        mock_publisher.assert_not_called()

    @patch("zombie_detector.core.processor._load_kafka_config")
    def test_process_host_data_with_kafka_parameter_disabled(self, mock_kafka_config):
        """Test processing hosts with Kafka parameter disabled."""
        self.setUp()

        results = process_host_data(
            self.sample_hosts,
            self.state_map,
            enable_tracking=False,
            enable_kafka=False,  # Explicitly disabled
        )

        # Verify results
        assert len(results) == 2

        # Verify config wasn't even loaded
        mock_kafka_config.assert_not_called()

    @patch("zombie_detector.core.processor.ZombieKafkaPublisher")
    @patch("zombie_detector.core.processor._load_kafka_config")
    @patch("zombie_detector.core.processor.ZombieTracker")
    def test_process_host_data_kafka_exception_handling(
        self, mock_tracker, mock_kafka_config, mock_publisher
    ):
        """Test Kafka exception handling doesn't break processing."""
        self.setUp()

        # Mock Kafka config
        mock_kafka_config.return_value = {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "test-zombie",
        }

        # Mock publisher to raise exception
        mock_publisher.side_effect = Exception("Kafka connection failed")

        # Should not raise exception
        results = process_host_data(
            self.sample_hosts, self.state_map, enable_tracking=False, enable_kafka=True
        )

        # Verify processing continued despite Kafka error
        assert len(results) == 2
        assert results[0]["is_zombie"] == True

    @patch("zombie_detector.core.processor.ZombieKafkaPublisher")
    @patch("zombie_detector.core.processor._load_kafka_config")
    @patch("zombie_detector.core.processor.ZombieTracker")
    def test_process_host_data_no_zombies_no_kafka_calls(
        self, mock_tracker, mock_kafka_config, mock_publisher
    ):
        """Test that Kafka lifecycle events aren't published when no zombies."""
        # Create non-zombie hosts (all criteria = 0)
        non_zombie_hosts = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "Recent_CPU_decrease_criterion": 0,
                "Recent_net_traffic_decrease_criterion": 0,
                "Sustained_Low_CPU_criterion": 0,
                "Excessively_constant_RAM_criterion": 0,
                "Daily_CPU_profile_lost_criterion": 0,
            }
        ]

        # State map with all zombie types enabled
        state_map = {
            "0": 0,  # No zombie - disabled (important!)
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
        }

        # Mock Kafka config
        mock_kafka_config.return_value = {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "test-zombie",
        }

        # Mock publisher
        mock_publisher_instance = Mock()
        mock_publisher.return_value = mock_publisher_instance

        results = process_host_data(
            non_zombie_hosts, state_map, enable_tracking=True, enable_kafka=True
        )

        # Verify no zombies
        assert len([r for r in results if r.get("is_zombie", False)]) == 0

        # FIXED: Verify publisher was called with authentication parameters
        mock_publisher.assert_called_once_with(
            bootstrap_servers="localhost:9092",
            topic_prefix="test-zombie",
            security_protocol="PLAINTEXT",
            ssl_config=None,
            sasl_config=None,
        )

        # Verify basic detection publishing still happens
        mock_publisher_instance.publish_zombie_detection.assert_called_once()

        # Verify no tracking stats or lifecycle events (no zombies to track)
        mock_publisher_instance.publish_tracking_stats.assert_not_called()
        mock_publisher_instance.publish_zombie_lifecycle_event.assert_not_called()
