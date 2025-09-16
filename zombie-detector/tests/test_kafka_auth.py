# tests/test_kafka_auth.py
# filepath: zombie-detector/tests/test_kafka_auth.py
import pytest
import tempfile
import os
import configparser
from unittest.mock import Mock, patch, MagicMock
from zombie_detector.core.zombie_publisher import ZombieKafkaPublisher
from zombie_detector.core.processor import _load_kafka_config


class TestKafkaAuthentication:
    """Test Kafka authentication and SSL configurations."""

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_plaintext_init(self, mock_kafka_producer):
        """Test publisher initialization with PLAINTEXT security."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="test-zombie",
            security_protocol="PLAINTEXT",
        )

        assert publisher.security_protocol == "PLAINTEXT"
        assert publisher.bootstrap_servers == "localhost:9092"
        assert publisher.topic_prefix == "test-zombie"

        # Verify KafkaProducer called with basic config
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["security_protocol"] == "PLAINTEXT"
        assert call_args["bootstrap_servers"] == "localhost:9092"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_ssl_init(self, mock_kafka_producer):
        """Test publisher initialization with SSL security."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        # Create temporary SSL files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as ca_file:
            ca_file.write("# Mock CA certificate")
            ca_path = ca_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as cert_file:
            cert_file.write("# Mock client certificate")
            cert_path = cert_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as key_file:
            key_file.write("# Mock client key")
            key_path = key_file.name

        try:
            ssl_config = {
                "ssl_cafile": ca_path,
                "ssl_certfile": cert_path,
                "ssl_keyfile": key_path,
                "ssl_check_hostname": True,
                "ssl_ciphers": "ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH",
            }

            publisher = ZombieKafkaPublisher(
                bootstrap_servers="kafka.example.com:9093",
                topic_prefix="test-zombie",
                security_protocol="SSL",
                ssl_config=ssl_config,
            )

            assert publisher.security_protocol == "SSL"

            # Verify SSL configuration passed to KafkaProducer
            mock_kafka_producer.assert_called_once()
            call_args = mock_kafka_producer.call_args[1]
            assert call_args["security_protocol"] == "SSL"
            assert call_args["ssl_cafile"] == ca_path
            assert call_args["ssl_certfile"] == cert_path
            assert call_args["ssl_keyfile"] == key_path
            assert call_args["ssl_check_hostname"] == True
            assert call_args["ssl_ciphers"] == "ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH"

        finally:
            # Cleanup
            os.unlink(ca_path)
            os.unlink(cert_path)
            os.unlink(key_path)

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_sasl_plain_init(self, mock_kafka_producer):
        """Test publisher initialization with SASL PLAIN authentication."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        sasl_config = {
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": "zombie-user",
            "sasl_plain_password": "secure-password",
        }

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9092",
            topic_prefix="test-zombie",
            security_protocol="SASL_PLAINTEXT",
            sasl_config=sasl_config,
        )

        assert publisher.security_protocol == "SASL_PLAINTEXT"

        # Verify SASL configuration passed to KafkaProducer
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["security_protocol"] == "SASL_PLAINTEXT"
        assert call_args["sasl_mechanism"] == "PLAIN"
        assert call_args["sasl_plain_username"] == "zombie-user"
        assert call_args["sasl_plain_password"] == "secure-password"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_sasl_scram_init(self, mock_kafka_producer):
        """Test publisher initialization with SASL SCRAM authentication."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        sasl_config = {
            "sasl_mechanism": "SCRAM-SHA-256",
            "sasl_username": "zombie-user",
            "sasl_password": "secure-password",
        }

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9092",
            topic_prefix="test-zombie",
            security_protocol="SASL_PLAINTEXT",
            sasl_config=sasl_config,
        )

        # Verify SASL SCRAM configuration
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["sasl_mechanism"] == "SCRAM-SHA-256"
        assert call_args["sasl_plain_username"] == "zombie-user"
        assert call_args["sasl_plain_password"] == "secure-password"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_sasl_ssl_combined(self, mock_kafka_producer):
        """Test publisher initialization with combined SASL + SSL."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        # Create temporary SSL files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as ca_file:
            ca_file.write("# Mock CA certificate")
            ca_path = ca_file.name

        try:
            ssl_config = {"ssl_cafile": ca_path, "ssl_check_hostname": True}

            sasl_config = {
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": "zombie-user",
                "sasl_plain_password": "secure-password",
            }

            publisher = ZombieKafkaPublisher(
                bootstrap_servers="kafka.example.com:9093",
                topic_prefix="test-zombie",
                security_protocol="SASL_SSL",
                ssl_config=ssl_config,
                sasl_config=sasl_config,
            )

            assert publisher.security_protocol == "SASL_SSL"

            # Verify both SSL and SASL configuration
            mock_kafka_producer.assert_called_once()
            call_args = mock_kafka_producer.call_args[1]
            assert call_args["security_protocol"] == "SASL_SSL"
            assert call_args["ssl_cafile"] == ca_path
            assert call_args["ssl_check_hostname"] == True
            assert call_args["sasl_mechanism"] == "PLAIN"
            assert call_args["sasl_plain_username"] == "zombie-user"
            assert call_args["sasl_plain_password"] == "secure-password"

        finally:
            os.unlink(ca_path)

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_missing_ssl_files(self, mock_kafka_producer):
        """Test graceful handling of missing SSL certificate files."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        ssl_config = {
            "ssl_cafile": "/nonexistent/ca.pem",
            "ssl_certfile": "/nonexistent/cert.pem",
            "ssl_keyfile": "/nonexistent/key.pem",
        }

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9093",
            topic_prefix="test-zombie",
            security_protocol="SSL",
            ssl_config=ssl_config,
        )

        # Should still initialize but without the missing files
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["security_protocol"] == "SSL"
        # Missing files should not be in the config
        assert "ssl_cafile" not in call_args
        assert "ssl_certfile" not in call_args
        assert "ssl_keyfile" not in call_args

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_sasl_missing_credentials(self, mock_kafka_producer):
        """Test SASL configuration with missing credentials."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        sasl_config = {
            "sasl_mechanism": "PLAIN",
            # Missing username and password
        }

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9092",
            topic_prefix="test-zombie",
            security_protocol="SASL_PLAINTEXT",
            sasl_config=sasl_config,
        )

        # Should still try to initialize
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["sasl_mechanism"] == "PLAIN"
        # Missing credentials should not be in the config
        assert "sasl_plain_username" not in call_args
        assert "sasl_plain_password" not in call_args

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_health_check(self, mock_kafka_producer):
        """Test Kafka publisher health check functionality."""
        mock_producer = Mock()
        mock_producer.bootstrap_connected.return_value = True
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="localhost:9092",
            topic_prefix="test-zombie",
            security_protocol="PLAINTEXT",
        )

        health = publisher.health_check()

        assert health["status"] == "healthy"
        assert health["bootstrap_servers"] == "localhost:9092"
        assert health["security_protocol"] == "PLAINTEXT"
        assert health["connected"] == True

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_kafka_publisher_health_check_failed(self, mock_kafka_producer):
        """Test Kafka publisher health check when connection fails."""
        mock_producer = Mock()
        mock_producer.bootstrap_connected.side_effect = Exception("Connection failed")
        mock_kafka_producer.return_value = mock_producer

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="localhost:9092", topic_prefix="test-zombie"
        )

        health = publisher.health_check()

        assert health["status"] == "unhealthy"
        assert "Connection failed" in health["error"]
        assert health["security_protocol"] == "PLAINTEXT"

    def test_kafka_publisher_no_producer_health_check(self):
        """Test health check when producer initialization failed."""
        with patch("zombie_detector.core.zombie_publisher.KAFKA_AVAILABLE", False):
            publisher = ZombieKafkaPublisher()

            health = publisher.health_check()

            assert health["status"] == "unhealthy"
            assert "Producer not initialized" in health["error"]


class TestKafkaConfigurationLoading:
    """Test loading Kafka configuration from files."""

    def test_load_kafka_config_ssl_configuration(self):
        """Test loading SSL configuration from config file."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
topic_prefix = prod-zombie
security_protocol = SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_certfile = /etc/ssl/client.pem
ssl_keyfile = /etc/ssl/client-key.pem
ssl_check_hostname = true
ssl_ciphers = HIGH:!aNULL:!MD5
compression_type = snappy
retries = 5
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch(
                "zombie_detector.core.processor.os.path.exists", return_value=True
            ):
                with patch(
                    "zombie_detector.core.processor.configparser.ConfigParser.read"
                ) as mock_read:
                    mock_config = configparser.ConfigParser()
                    mock_config.read_string(config_content)

                    with patch(
                        "zombie_detector.core.processor.configparser.ConfigParser",
                        return_value=mock_config,
                    ):
                        config = _load_kafka_config()

            expected_ssl_config = {
                "ssl_cafile": "/etc/ssl/ca.pem",
                "ssl_certfile": "/etc/ssl/client.pem",
                "ssl_keyfile": "/etc/ssl/client-key.pem",
                "ssl_check_hostname": True,
                "ssl_ciphers": "HIGH:!aNULL:!MD5",
            }

            assert config["enabled"] == True
            assert config["security_protocol"] == "SSL"
            assert config["ssl_config"] == expected_ssl_config
            assert config["compression_type"] == "snappy"
            assert config["retries"] == 5

        finally:
            os.unlink(config_path)

    def test_load_kafka_config_sasl_configuration(self):
        """Test loading SASL configuration from config file."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = SCRAM-SHA-256
sasl_username = zombie-service
sasl_password = super-secure-password
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch(
                "zombie_detector.core.processor.os.path.exists", return_value=True
            ):
                with patch(
                    "zombie_detector.core.processor.configparser.ConfigParser.read"
                ) as mock_read:
                    mock_config = configparser.ConfigParser()
                    mock_config.read_string(config_content)

                    with patch(
                        "zombie_detector.core.processor.configparser.ConfigParser",
                        return_value=mock_config,
                    ):
                        config = _load_kafka_config()

            expected_sasl_config = {
                "sasl_mechanism": "SCRAM-SHA-256",
                "sasl_username": "zombie-service",
                "sasl_password": "super-secure-password",
            }

            assert config["enabled"] == True
            assert config["security_protocol"] == "SASL_PLAINTEXT"
            assert config["sasl_config"] == expected_sasl_config

        finally:
            os.unlink(config_path)

    def test_load_kafka_config_combined_ssl_sasl(self):
        """Test loading combined SSL and SASL configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SASL_SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_check_hostname = false
sasl_mechanism = PLAIN
sasl_plain_username = zombie-user
sasl_plain_password = password123
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch(
                "zombie_detector.core.processor.os.path.exists", return_value=True
            ):
                with patch(
                    "zombie_detector.core.processor.configparser.ConfigParser.read"
                ) as mock_read:
                    mock_config = configparser.ConfigParser()
                    mock_config.read_string(config_content)

                    with patch(
                        "zombie_detector.core.processor.configparser.ConfigParser",
                        return_value=mock_config,
                    ):
                        config = _load_kafka_config()

            expected_ssl_config = {
                "ssl_cafile": "/etc/ssl/ca.pem",
                "ssl_check_hostname": False,
            }

            expected_sasl_config = {
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": "zombie-user",
                "sasl_plain_password": "password123",
            }

            assert config["security_protocol"] == "SASL_SSL"
            assert config["ssl_config"] == expected_ssl_config
            assert config["sasl_config"] == expected_sasl_config

        finally:
            os.unlink(config_path)

    def test_load_kafka_config_kerberos_configuration(self):
        """Test loading Kerberos (GSSAPI) configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.corp.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = GSSAPI
sasl_kerberos_service_name = kafka
sasl_kerberos_domain_name = corp.com
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch(
                "zombie_detector.core.processor.os.path.exists", return_value=True
            ):
                with patch(
                    "zombie_detector.core.processor.configparser.ConfigParser.read"
                ) as mock_read:
                    mock_config = configparser.ConfigParser()
                    mock_config.read_string(config_content)

                    with patch(
                        "zombie_detector.core.processor.configparser.ConfigParser",
                        return_value=mock_config,
                    ):
                        config = _load_kafka_config()

            expected_sasl_config = {
                "sasl_mechanism": "GSSAPI",
                "sasl_kerberos_service_name": "kafka",
                "sasl_kerberos_domain_name": "corp.com",
            }

            assert config["security_protocol"] == "SASL_PLAINTEXT"
            assert config["sasl_config"] == expected_sasl_config

        finally:
            os.unlink(config_path)

    def test_load_kafka_config_minimal_ssl(self):
        """Test loading minimal SSL configuration."""
        config_content = """
[kafka]
enabled = true
security_protocol = SSL
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch(
                "zombie_detector.core.processor.os.path.exists", return_value=True
            ):
                with patch(
                    "zombie_detector.core.processor.configparser.ConfigParser.read"
                ) as mock_read:
                    mock_config = configparser.ConfigParser()
                    mock_config.read_string(config_content)

                    with patch(
                        "zombie_detector.core.processor.configparser.ConfigParser",
                        return_value=mock_config,
                    ):
                        config = _load_kafka_config()

            assert config["security_protocol"] == "SSL"
            # Should not have ssl_config since no SSL options were specified
            assert "ssl_config" not in config

        finally:
            os.unlink(config_path)


class TestKafkaAuthenticationIntegration:
    """Test integration of authentication with message publishing."""

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_publish_with_ssl_authentication(self, mock_kafka_producer):
        """Test publishing messages with SSL authentication."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        # Create temporary SSL files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as ca_file:
            ca_file.write("# Mock CA certificate")
            ca_path = ca_file.name

        try:
            ssl_config = {"ssl_cafile": ca_path, "ssl_check_hostname": True}

            publisher = ZombieKafkaPublisher(
                bootstrap_servers="kafka.example.com:9093",
                topic_prefix="secure-zombie",
                security_protocol="SSL",
                ssl_config=ssl_config,
            )

            # Test publishing detection results
            detection_results = [
                {
                    "dynatrace_host_id": "HOST-1",
                    "hostname": "hostname1",
                    "criterion_type": "2A",
                    "is_zombie": True,
                    "tenant": "tenant1",
                }
            ]

            publisher.publish_zombie_detection(detection_results)

            # Verify producer was configured with SSL
            mock_kafka_producer.assert_called_once()
            call_args = mock_kafka_producer.call_args[1]
            assert call_args["security_protocol"] == "SSL"
            assert call_args["ssl_cafile"] == ca_path

            # Verify messages were sent
            assert mock_producer.send.call_count >= 1
            mock_producer.flush.assert_called()

        finally:
            os.unlink(ca_path)

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_publish_with_sasl_authentication(self, mock_kafka_producer):
        """Test publishing messages with SASL authentication."""
        mock_producer = Mock()
        mock_kafka_producer.return_value = mock_producer

        sasl_config = {
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": "zombie-user",
            "sasl_plain_password": "secure-password",
        }

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9092",
            topic_prefix="secure-zombie",
            security_protocol="SASL_PLAINTEXT",
            sasl_config=sasl_config,
        )

        # Test publishing tracking stats
        tracking_stats = {"total_zombies": 5, "new_zombies": 2, "killed_zombies": 1}

        publisher.publish_tracking_stats(tracking_stats)

        # Verify producer was configured with SASL
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args[1]
        assert call_args["security_protocol"] == "SASL_PLAINTEXT"
        assert call_args["sasl_mechanism"] == "PLAIN"
        assert call_args["sasl_plain_username"] == "zombie-user"
        assert call_args["sasl_plain_password"] == "secure-password"

        # Verify message was sent with security metadata
        mock_producer.send.assert_called_once()
        send_args = mock_producer.send.call_args
        message_value = send_args[1]["value"]
        assert message_value["metadata"]["security_protocol"] == "SASL_PLAINTEXT"

    @patch("zombie_detector.core.zombie_publisher.KafkaProducer")
    def test_authentication_failure_handling(self, mock_kafka_producer):
        """Test handling of authentication failures."""
        from kafka.errors import KafkaError

        # Mock authentication failure
        mock_kafka_producer.side_effect = KafkaError("Authentication failed")

        publisher = ZombieKafkaPublisher(
            bootstrap_servers="kafka.example.com:9092",
            topic_prefix="secure-zombie",
            security_protocol="SASL_PLAINTEXT",
            sasl_config={
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": "wrong-user",
                "sasl_plain_password": "wrong-password",
            },
        )

        # Publisher should handle the failure gracefully
        assert publisher.producer is None

        # Health check should report the failure
        health = publisher.health_check()
        assert health["status"] == "unhealthy"
        assert "Producer not initialized" in health["error"]
