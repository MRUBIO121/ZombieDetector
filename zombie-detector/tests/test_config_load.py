import pytest
import tempfile
import os
import configparser
from unittest.mock import patch
from zombie_detector.core.processor import _load_kafka_config


class TestKafkaConfig:
    """Test Kafka configuration loading functionality."""

    def test_load_kafka_config_file_not_exists(self):
        """Test loading config when file doesn't exist."""
        with patch("zombie_detector.core.processor.os.path.exists", return_value=False):
            config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "zombie-detector",
            "security_protocol": "PLAINTEXT",
        }
        assert config == expected

    def test_load_kafka_config_valid_file(self):
        """Test loading valid Kafka configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
topic_prefix = test-zombies
compression_type = gzip
retries = 5
acks = all
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

            expected = {
                "enabled": True,
                "bootstrap_servers": "kafka.example.com:9092",
                "topic_prefix": "test-zombies",
                "security_protocol": "PLAINTEXT",
                "compression_type": "gzip",
                "retries": 5,
                "acks": "all",
                "batch_size": 16384,
                "linger_ms": 100,
                "buffer_memory": 33554432,
            }
            assert config == expected

        finally:
            os.unlink(config_path)

    def test_load_kafka_config_no_kafka_section(self):
        """Test loading config when kafka section is missing."""
        config_content = """
[api]
host = 0.0.0.0
port = 8000
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {"enabled": False}
        assert config == expected

    def test_load_kafka_config_disabled(self):
        """Test loading config with Kafka disabled."""
        config_content = """
[kafka]
enabled = false
bootstrap_servers = localhost:9092
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": False,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "zombie-detector",
            "security_protocol": "PLAINTEXT",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
        }
        assert config == expected

    def test_load_kafka_config_exception_handling(self):
        """Test exception handling during config loading."""
        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser.read",
                side_effect=Exception("File error"),
            ):
                config = _load_kafka_config()

        expected = {"enabled": False}
        assert config == expected

    def test_load_kafka_config_with_ssl_and_sasl(self):
        """Test loading config with SSL and SASL authentication."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SASL_SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_check_hostname = true
sasl_mechanism = PLAIN
sasl_plain_username = zombie-user
sasl_plain_password = secure-password
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "kafka.example.com:9093",
            "topic_prefix": "zombie-detector",
            "security_protocol": "SASL_SSL",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
            "ssl_config": {
                "ssl_cafile": "/etc/ssl/ca.pem",
                "ssl_check_hostname": True,
            },
            "sasl_config": {
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": "zombie-user",
                "sasl_plain_password": "secure-password",
            },
        }
        assert config == expected

    def test_load_kafka_config_ssl_only(self):
        """Test loading config with SSL authentication only."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_certfile = /etc/ssl/client.pem
ssl_keyfile = /etc/ssl/client-key.pem
ssl_check_hostname = false
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "kafka.example.com:9093",
            "topic_prefix": "zombie-detector",
            "security_protocol": "SSL",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
            "ssl_config": {
                "ssl_cafile": "/etc/ssl/ca.pem",
                "ssl_certfile": "/etc/ssl/client.pem",
                "ssl_keyfile": "/etc/ssl/client-key.pem",
                "ssl_check_hostname": False,
            },
        }
        assert config == expected

    def test_load_kafka_config_sasl_only(self):
        """Test loading config with SASL authentication only."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = SCRAM-SHA-256
sasl_username = zombie-service
sasl_password = super-secure-password
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "kafka.example.com:9092",
            "topic_prefix": "zombie-detector",
            "security_protocol": "SASL_PLAINTEXT",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
            "sasl_config": {
                "sasl_mechanism": "SCRAM-SHA-256",
                "sasl_username": "zombie-service",
                "sasl_password": "super-secure-password",
            },
        }
        assert config == expected

    def test_load_kafka_config_partial_ssl_config(self):
        """Test loading config with partial SSL configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SSL
ssl_cafile = /etc/ssl/ca.pem
# Missing ssl_certfile and ssl_keyfile
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "kafka.example.com:9093",
            "topic_prefix": "zombie-detector",
            "security_protocol": "SSL",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
            "ssl_config": {
                "ssl_cafile": "/etc/ssl/ca.pem",
            },
        }
        assert config == expected

    def test_load_kafka_config_partial_sasl_config(self):
        """Test loading config with partial SASL configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = PLAIN
# Missing username and password
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected = {
            "enabled": True,
            "bootstrap_servers": "kafka.example.com:9092",
            "topic_prefix": "zombie-detector",
            "security_protocol": "SASL_PLAINTEXT",
            "compression_type": "gzip",
            "retries": 3,
            "acks": "all",
            "batch_size": 16384,
            "linger_ms": 100,
            "buffer_memory": 33554432,
            "sasl_config": {
                "sasl_mechanism": "PLAIN",
            },
        }
        assert config == expected

    def test_load_kafka_config_boolean_conversion(self):
        """Test boolean value conversion in configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SSL
ssl_check_hostname = false
ssl_ciphers = HIGH:!aNULL:!MD5
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        # Verify boolean conversion
        assert config["enabled"] is True
        assert config["ssl_config"]["ssl_check_hostname"] is False
        # FIXED: Removed ssl_verify_mode check as it's not supported
        assert config["ssl_config"]["ssl_ciphers"] == "HIGH:!aNULL:!MD5"

        # Verify other default fields are present
        assert "compression_type" in config
        assert "retries" in config
        assert "batch_size" in config

    def test_load_kafka_config_integer_conversion(self):
        """Test integer value conversion in configuration."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
retries = 10
batch_size = 32768
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        # Verify integer conversion
        assert config["retries"] == 10
        assert config["batch_size"] == 32768
        assert isinstance(config["retries"], int)
        assert isinstance(config["batch_size"], int)

        # Verify other default fields are present with correct types
        assert isinstance(config["linger_ms"], int)
        assert isinstance(config["buffer_memory"], int)

    def test_load_kafka_config_custom_performance_settings(self):
        """Test loading config with custom performance settings."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
compression_type = snappy
retries = 10
acks = 1
batch_size = 32768
linger_ms = 50
buffer_memory = 67108864
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        # Verify custom values override defaults
        assert config["compression_type"] == "snappy"
        assert config["retries"] == 10
        assert config["acks"] == "1"
        assert config["batch_size"] == 32768
        assert config["linger_ms"] == 50
        assert config["buffer_memory"] == 67108864

    def test_load_kafka_config_with_all_ssl_options(self):
        """Test loading config with comprehensive SSL options."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_certfile = /etc/ssl/client.pem
ssl_keyfile = /etc/ssl/client-key.pem
ssl_password = cert-password
ssl_crlfile = /etc/ssl/revoked.pem
ssl_ciphers = HIGH:!aNULL:!MD5
ssl_check_hostname = true
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
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
            "ssl_password": "cert-password",
            "ssl_crlfile": "/etc/ssl/revoked.pem",
            "ssl_ciphers": "HIGH:!aNULL:!MD5",
            "ssl_check_hostname": True,
        }

        assert config["security_protocol"] == "SSL"
        assert config["ssl_config"] == expected_ssl_config

    def test_load_kafka_config_with_oauth_sasl(self):
        """Test loading config with OAuth SASL authentication."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = OAUTHBEARER
sasl_oauth_token_provider = custom_token_provider
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        expected_sasl_config = {
            "sasl_mechanism": "OAUTHBEARER",
            "sasl_oauth_token_provider": "custom_token_provider",
        }

        assert config["security_protocol"] == "SASL_PLAINTEXT"
        assert config["sasl_config"] == expected_sasl_config

    def test_load_kafka_config_supported_ssl_fields_only(self):
        """Test that only supported SSL fields are included in config."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SSL
ssl_cafile = /etc/ssl/ca.pem
ssl_certfile = /etc/ssl/client.pem
ssl_keyfile = /etc/ssl/client-key.pem
ssl_password = cert-password
ssl_crlfile = /etc/ssl/revoked.pem
ssl_ciphers = HIGH:!aNULL:!MD5
ssl_check_hostname = true
# These fields are not supported by the current implementation
ssl_verify_mode = CERT_REQUIRED
ssl_protocol = TLSv1_2
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        # Verify only supported SSL fields are present
        supported_ssl_fields = {
            "ssl_cafile",
            "ssl_certfile",
            "ssl_keyfile",
            "ssl_password",
            "ssl_crlfile",
            "ssl_ciphers",
            "ssl_check_hostname",
        }

        ssl_config = config.get("ssl_config", {})
        for field in ssl_config.keys():
            assert field in supported_ssl_fields, (
                f"Unsupported SSL field found: {field}"
            )

        # Verify unsupported fields are not included
        assert "ssl_verify_mode" not in ssl_config
        assert "ssl_protocol" not in ssl_config

    def test_load_kafka_config_supported_sasl_fields_only(self):
        """Test that only supported SASL fields are included in config."""
        config_content = """
[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9092
security_protocol = SASL_PLAINTEXT
sasl_mechanism = SCRAM-SHA-256
sasl_username = zombie-service
sasl_password = super-secure-password
sasl_plain_username = plain-user
sasl_plain_password = plain-password
sasl_kerberos_service_name = kafka
sasl_kerberos_domain_name = corp.com
sasl_oauth_token_provider = custom_provider
# These fields might not be supported
sasl_oauth_scope = read:write
sasl_oauth_client_id = my-client
"""

        with patch("zombie_detector.core.processor.os.path.exists", return_value=True):
            mock_config = configparser.ConfigParser()
            mock_config.read_string(config_content)

            with patch(
                "zombie_detector.core.processor.configparser.ConfigParser",
                return_value=mock_config,
            ):
                config = _load_kafka_config()

        # Verify SASL fields based on what the processor actually supports
        supported_sasl_fields = {
            "sasl_mechanism",
            "sasl_username",
            "sasl_password",
            "sasl_plain_username",
            "sasl_plain_password",
            "sasl_kerberos_service_name",
            "sasl_kerberos_domain_name",
            "sasl_oauth_token_provider",
        }

        sasl_config = config.get("sasl_config", {})
        for field in sasl_config.keys():
            assert field in supported_sasl_fields, (
                f"Unsupported SASL field found: {field}"
            )
