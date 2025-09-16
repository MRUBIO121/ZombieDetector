import pytest
import time
from unittest.mock import Mock, patch
from zombie_detector.core.zombie_publisher import ZombieKafkaPublisher
from zombie_detector.core.processor import process_host_data


class TestKafkaPerformance:
    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_large_dataset_processing(self, mock_kafka_producer):
        """Test processing large datasets with Kafka."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "dynatrace_host_id": f"HOST-{i}",
                    "hostname": f"hostname{i}",
                    "criterion_type": "2A",  # FIXED: Use real code instead of "T1"
                    "criterion_alias": "Mummy",  # FIXED: Use real alias
                    "is_zombie": i % 2 == 0,  # Half are zombies
                    "tenant": f"tenant{i}",
                }
            )

        start_time = time.time()
        publisher.publish_zombie_detection(large_dataset)
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max

        # Verify calls were made
        assert mock_producer.send.call_count > 0
        mock_producer.flush.assert_called_once()

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_timeout_handling(self, mock_kafka_producer):
        """Test handling of Kafka timeouts."""
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Timeout")
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        detection_results = [{"dynatrace_host_id": "HOST-1", "is_zombie": True}]

        # Should not raise exception
        publisher.publish_zombie_detection(detection_results)

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_network_failure_resilience(self, mock_kafka_producer):
        """Test resilience to network failures."""
        from kafka.errors import KafkaError

        mock_producer = Mock()
        mock_producer.send.side_effect = KafkaError("Network error")
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        detection_results = [{"dynatrace_host_id": "HOST-1", "is_zombie": True}]

        # Should handle Kafka errors gracefully
        publisher.publish_zombie_detection(detection_results)

    @patch("zombie_detector.core.processor._load_kafka_config")
    def test_processing_performance_with_kafka_disabled(self, mock_kafka_config):
        """Test that disabling Kafka doesn't impact performance significantly."""
        mock_kafka_config.return_value = {"enabled": False}

        # Large dataset
        hosts = []
        for i in range(1000):
            hosts.append(
                {
                    "dynatrace_host_id": f"HOST-{i}",
                    "hostname": f"hostname{i}",
                    "Recent_CPU_decrease_criterion": 1,
                    "Recent_net_traffic_decrease_criterion": -1,
                    "Sustained_Low_CPU_criterion": 1,
                    "Excessively_constant_RAM_criterion": 0,
                    "Daily_CPU_profile_lost_criterion": -1,
                }
            )

        # FIXED: Use real codes instead of old "T1", "T2" codes
        state_map = {
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

        start_time = time.time()
        results = process_host_data(hosts, state_map, enable_kafka=True)
        end_time = time.time()

        # Should complete quickly without Kafka overhead
        assert end_time - start_time < 2.0  # 2 seconds max
        assert len(results) == 1000
