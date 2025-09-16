# zombie_detector/core/zombie_publisher.py
# filepath: zombie-detector/zombie_detector/core/zombie_publisher.py
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import os

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError, KafkaTimeoutError

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception
    KafkaTimeoutError = Exception

logger = logging.getLogger(__name__)


class ZombieKafkaPublisher:
    """Enhanced Kafka publisher with authentication and SSL support."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic_prefix: str = "zombie-detector",
        security_protocol: str = "PLAINTEXT",
        ssl_config: Optional[Dict[str, Any]] = None,
        sasl_config: Optional[Dict[str, Any]] = None,
        **kafka_config,
    ):
        """
        Initialize Kafka publisher with authentication support.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic_prefix: Topic prefix for all topics
            security_protocol: Security protocol (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL)
            ssl_config: SSL configuration dictionary
            sasl_config: SASL configuration dictionary
            **kafka_config: Additional Kafka configuration
        """
        # FIXED: Always set these attributes, even when Kafka is unavailable
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.security_protocol = security_protocol
        self.ssl_config = ssl_config or {}
        self.sasl_config = sasl_config or {}

        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available, publisher will be disabled")
            self.producer = None
            return

        # Build Kafka configuration
        producer_config = {
            "bootstrap_servers": bootstrap_servers,
            "value_serializer": self._value_serializer,
            "key_serializer": self._key_serializer,
            "retries": kafka_config.get("retries", 3),
            "acks": kafka_config.get("acks", "all"),
            "compression_type": kafka_config.get("compression_type", "gzip"),
            "batch_size": kafka_config.get("batch_size", 16384),
            "linger_ms": kafka_config.get("linger_ms", 100),
            "buffer_memory": kafka_config.get("buffer_memory", 33554432),
            "security_protocol": security_protocol,
        }

        # Add SSL configuration
        if security_protocol in ["SSL", "SASL_SSL"]:
            producer_config.update(self._build_ssl_config())

        # Add SASL configuration
        if security_protocol in ["SASL_PLAINTEXT", "SASL_SSL"]:
            producer_config.update(self._build_sasl_config())

        # Add any additional configuration
        producer_config.update(kafka_config)

        try:
            self.producer = KafkaProducer(**producer_config)
            logger.info(
                f"Kafka producer initialized with security protocol: {security_protocol}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None

    def _build_ssl_config(self) -> Dict[str, Any]:
        """Build SSL configuration from ssl_config."""
        ssl_config = {}

        if "ssl_cafile" in self.ssl_config and self.ssl_config["ssl_cafile"]:
            if os.path.exists(self.ssl_config["ssl_cafile"]):
                ssl_config["ssl_cafile"] = self.ssl_config["ssl_cafile"]
            else:
                logger.warning(
                    f"SSL CA file not found: {self.ssl_config['ssl_cafile']}"
                )

        if "ssl_certfile" in self.ssl_config and self.ssl_config["ssl_certfile"]:
            if os.path.exists(self.ssl_config["ssl_certfile"]):
                ssl_config["ssl_certfile"] = self.ssl_config["ssl_certfile"]
            else:
                logger.warning(
                    f"SSL cert file not found: {self.ssl_config['ssl_certfile']}"
                )

        if "ssl_keyfile" in self.ssl_config and self.ssl_config["ssl_keyfile"]:
            if os.path.exists(self.ssl_config["ssl_keyfile"]):
                ssl_config["ssl_keyfile"] = self.ssl_config["ssl_keyfile"]
            else:
                logger.warning(
                    f"SSL key file not found: {self.ssl_config['ssl_keyfile']}"
                )

        # Optional SSL settings
        if "ssl_password" in self.ssl_config and self.ssl_config["ssl_password"]:
            ssl_config["ssl_password"] = self.ssl_config["ssl_password"]

        if "ssl_check_hostname" in self.ssl_config:
            ssl_config["ssl_check_hostname"] = self.ssl_config["ssl_check_hostname"]

        if "ssl_crlfile" in self.ssl_config and self.ssl_config["ssl_crlfile"]:
            if os.path.exists(self.ssl_config["ssl_crlfile"]):
                ssl_config["ssl_crlfile"] = self.ssl_config["ssl_crlfile"]

        if "ssl_ciphers" in self.ssl_config:
            ssl_config["ssl_ciphers"] = self.ssl_config["ssl_ciphers"]

        logger.debug(f"SSL config built: {list(ssl_config.keys())}")
        return ssl_config

    def _build_sasl_config(self) -> Dict[str, Any]:
        """Build SASL configuration from sasl_config."""
        sasl_config = {}

        mechanism = self.sasl_config.get("sasl_mechanism", "PLAIN")
        sasl_config["sasl_mechanism"] = mechanism

        if mechanism in ["PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512"]:
            username = self.sasl_config.get("sasl_username") or self.sasl_config.get(
                "sasl_plain_username"
            )
            password = self.sasl_config.get("sasl_password") or self.sasl_config.get(
                "sasl_plain_password"
            )

            if username and password:
                sasl_config["sasl_plain_username"] = username
                sasl_config["sasl_plain_password"] = password
            else:
                logger.error(f"SASL {mechanism} requires username and password")

        elif mechanism == "GSSAPI":
            if "sasl_kerberos_service_name" in self.sasl_config:
                sasl_config["sasl_kerberos_service_name"] = self.sasl_config[
                    "sasl_kerberos_service_name"
                ]
            if "sasl_kerberos_domain_name" in self.sasl_config:
                sasl_config["sasl_kerberos_domain_name"] = self.sasl_config[
                    "sasl_kerberos_domain_name"
                ]

        elif mechanism == "OAUTHBEARER":
            if "sasl_oauth_token_provider" in self.sasl_config:
                sasl_config["sasl_oauth_token_provider"] = self.sasl_config[
                    "sasl_oauth_token_provider"
                ]

        logger.debug(f"SASL config built for mechanism: {mechanism}")
        return sasl_config

    @staticmethod
    def _value_serializer(value: Union[Dict, List, str]) -> bytes:
        """Serialize value to JSON bytes."""
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str).encode("utf-8")
        return str(value).encode("utf-8")

    @staticmethod
    def _key_serializer(key: Optional[str]) -> Optional[bytes]:
        """Serialize key to bytes."""
        return key.encode("utf-8") if key else None

    def publish_zombie_detection(self, detection_results: List[Dict]) -> None:
        """Publish zombie detection results."""
        if not self.producer:
            logger.warning(
                "Kafka producer not available, skipping detection publishing"
            )
            return

        try:
            topic = f"{self.topic_prefix}-detections"

            # Publish summary message
            summary_data = {
                "timestamp": datetime.now().isoformat(),
                "total_hosts": len(detection_results),
                "zombie_hosts": len(
                    [r for r in detection_results if r.get("is_zombie", False)]
                ),
                "criterion_breakdown": self._get_criterion_breakdown(detection_results),
                "metadata": {
                    "service": "zombie-detector",
                    "version": "0.1.1",
                    "security_protocol": self.security_protocol,
                },
            }

            self.producer.send(topic, key="detection-summary", value=summary_data)

            # Publish individual results
            for result in detection_results:
                key = f"host-{result.get('dynatrace_host_id', 'unknown')}"
                self.producer.send(topic, key=key, value=result)

            self.producer.flush()
            logger.debug(
                f"Published {len(detection_results)} detection results to {topic}"
            )

        except KafkaTimeoutError:
            logger.error("Kafka timeout while publishing detection results")
        except KafkaError as e:
            logger.error(f"Kafka error while publishing detection results: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while publishing detection results: {e}")

    def publish_tracking_stats(self, tracking_stats: Dict) -> None:
        """Publish zombie tracking statistics."""
        if not self.producer:
            logger.warning(
                "Kafka producer not available, skipping tracking stats publishing"
            )
            return

        try:
            topic = f"{self.topic_prefix}-tracking"

            enhanced_stats = {
                **tracking_stats,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "service": "zombie-detector",
                    "security_protocol": self.security_protocol,
                },
            }

            self.producer.send(topic, key="tracking-stats", value=enhanced_stats)
            self.producer.flush()
            logger.debug(f"Published tracking stats to {topic}")

        except Exception as e:
            logger.error(f"Error while publishing tracking stats: {e}")

    def publish_zombie_lifecycle_event(
        self, event_type: str, zombie_data: Dict
    ) -> None:
        """Publish zombie lifecycle events."""
        if not self.producer:
            logger.warning(
                "Kafka producer not available, skipping lifecycle event publishing"
            )
            return

        try:
            topic = f"{self.topic_prefix}-lifecycle"

            event_data = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "zombie": zombie_data,
                "metadata": {
                    "service": "zombie-detector",
                    "security_protocol": self.security_protocol,
                },
            }

            key = f"lifecycle-{zombie_data.get('dynatrace_host_id', 'unknown')}"
            self.producer.send(topic, key=key, value=event_data)
            self.producer.flush()
            logger.debug(f"Published lifecycle event {event_type} to {topic}")

        except Exception as e:
            logger.error(f"Error while publishing lifecycle event: {e}")

    def _get_criterion_breakdown(self, detection_results: List[Dict]) -> Dict[str, int]:
        """Get breakdown of detection results by criterion type."""
        breakdown = {}
        for result in detection_results:
            if result.get("is_zombie", False):
                criterion = result.get("criterion_type", "unknown")
                breakdown[criterion] = breakdown.get(criterion, 0) + 1
        return breakdown

    def close(self) -> None:
        """Close the Kafka producer."""
        if self.producer:
            try:
                self.producer.close()
                logger.debug("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Kafka connection."""
        if not self.producer:
            return {
                "status": "unhealthy",
                "error": "Producer not initialized",
                "security_protocol": self.security_protocol,
            }

        try:
            # Try to get metadata (this tests connectivity)
            metadata = self.producer.bootstrap_connected()
            return {
                "status": "healthy" if metadata else "degraded",
                "bootstrap_servers": self.bootstrap_servers,
                "security_protocol": self.security_protocol,
                "connected": metadata,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "security_protocol": self.security_protocol,
            }
