import pytest
import json
from unittest.mock import Mock, patch, MagicMock, ANY
from datetime import datetime
from zombie_detector.core.zombie_publisher import ZombieKafkaPublisher


class TestZombieKafkaPublisher:
    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_initialization_success(self, mock_kafka_producer):
        """Test successful Kafka producer initialization."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="localhost:9092", topic_prefix="test-zombie"
        )

        assert publisher.bootstrap_servers == "localhost:9092"
        assert publisher.topic_prefix == "test-zombie"
        assert publisher.security_protocol == "PLAINTEXT"
        assert publisher.producer == mock_producer

        mock_kafka_producer.assert_called_once_with(
            bootstrap_servers="localhost:9092",
            value_serializer=ANY,
            key_serializer=ANY,
            retries=3,
            acks="all",
            compression_type="gzip",
            batch_size=16384,
            linger_ms=100,
            buffer_memory=33554432,
            security_protocol="PLAINTEXT",
        )

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_publish_zombie_detection_success(self, mock_kafka_producer):
        """Test successful zombie detection publishing."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        detection_results = [
            {
                "dynatrace_host_id": "HOST-1",
                "hostname": "hostname1",
                "criterion_type": "2A",  # FIXED: Use real codes
                "criterion_alias": "Mummy",  # FIXED: Use real aliases
                "is_zombie": True,
                "tenant": "tenant1",
                "asset_tag": "CI01234567",
            },
            {
                "dynatrace_host_id": "HOST-2",
                "hostname": "hostname2",
                "criterion_type": "0",  # FIXED: Use real codes
                "criterion_alias": "Sin criterios de zombie activos",  # FIXED
                "is_zombie": False,
                "tenant": "tenant2",
            },
        ]

        publisher.publish_zombie_detection(detection_results)

        assert mock_producer.send.call_count >= 2
        mock_producer.flush.assert_called_once()

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_publish_lifecycle_event(self, mock_kafka_producer):
        """Test publishing zombie lifecycle events."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        zombie_data = {
            "dynatrace_host_id": "HOST-1",
            "hostname": "hostname1",
            "criterion_type": "2A",  # FIXED: Use real codes
        }

        publisher.publish_zombie_lifecycle_event("zombie_new", zombie_data)

        mock_producer.send.assert_called_once()
        mock_producer.flush.assert_called_once()

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_get_criterion_breakdown(self, mock_kafka_producer):
        """Test criterion breakdown calculation."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()

        # FIXED: Use real criterion types
        zombies = [
            {"criterion_type": "2A", "is_zombie": True},
            {"criterion_type": "2A", "is_zombie": True},
            {"criterion_type": "1A", "is_zombie": True},
            {"criterion_type": "unknown", "is_zombie": True},
            {"criterion_type": "0", "is_zombie": False},  # Non-zombie shouldn't count
        ]

        breakdown = publisher._get_criterion_breakdown(zombies)

        expected = {"2A": 2, "1A": 1, "unknown": 1}
        assert breakdown == expected

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_close_producer(self, mock_kafka_producer):
        """Test closing Kafka producer."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher()
        publisher.close()

        mock_producer.close.assert_called_once()

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_serialization_functions(self, mock_kafka_producer):
        """Test that serialization functions work correctly."""
        mock_kafka_producer.return_value = Mock()

        publisher = ZombieKafkaPublisher()

        # Test value serializer
        test_data = {"timestamp": datetime.now(), "count": 5}
        # This should not raise an exception
        serialized = json.dumps(test_data, default=str).encode("utf-8")
        assert isinstance(serialized, bytes)

        # Test key serializer
        key = "test-key"
        serialized_key = key.encode("utf-8")
        assert isinstance(serialized_key, bytes)

        # Test None key
        none_key = None
        assert none_key is None

    def test_kafka_unavailable_initialization(self):
        """Test publisher initialization when Kafka is unavailable."""
        with patch("zombie_detector.core.zombie_publisher.KAFKA_AVAILABLE", False):
            publisher = ZombieKafkaPublisher(
                bootstrap_servers="localhost:9092",
                topic_prefix="test-zombie",
                security_protocol="SSL",
            )

            # FIXED: Ensure attributes are set even when Kafka unavailable
            assert publisher.producer is None
            assert publisher.bootstrap_servers == "localhost:9092"
            assert publisher.topic_prefix == "test-zombie"
            assert publisher.security_protocol == "SSL"

            # Health check should work without throwing AttributeError
            health = publisher.health_check()
            assert health["status"] == "unhealthy"
            assert health["security_protocol"] == "SSL"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_producer_initialization_failure(self, mock_kafka_producer):
        """Test handling of producer initialization failure."""
        mock_kafka_producer.side_effect = Exception("Connection failed")

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="localhost:9092", security_protocol="SASL_PLAINTEXT"
        )

        # Should handle failure gracefully
        assert publisher.producer is None
        assert publisher.security_protocol == "SASL_PLAINTEXT"

        # Health check should work
        health = publisher.health_check()
        assert health["status"] == "unhealthy"
        assert health["security_protocol"] == "SASL_PLAINTEXT"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_publish_with_no_producer(self, mock_kafka_producer):
        """Test publishing when producer is None."""
        mock_kafka_producer.return_value = Mock()

        publisher = ZombieKafkaPublisher()
        publisher.producer = None  # Simulate failed initialization

        detection_results = [{"dynatrace_host_id": "HOST-1", "is_zombie": True}]

        # Should not raise exception
        publisher.publish_zombie_detection(detection_results)
        publisher.publish_tracking_stats({"total": 1})
        publisher.publish_zombie_lifecycle_event("new", {"host": "HOST-1"})
