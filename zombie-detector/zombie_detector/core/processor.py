import json
import configparser
import os
from typing import List, Dict, Any, Optional
from .zombie_tracker import ZombieTracker
from .zombie_publisher import ZombieKafkaPublisher
import logging

logger = logging.getLogger(__name__)


def _load_kafka_config() -> Dict[str, Any]:
    """Load enhanced Kafka configuration with authentication and SSL support."""
    config_path = "/etc/zombie-detector/zombie-detector.ini"
    if not os.path.exists(config_path):
        logger.info("Config file not found, using defaults")
        return {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic_prefix": "zombie-detector",
            "security_protocol": "PLAINTEXT",
        }

    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        if "kafka" not in config:
            logger.warning("No kafka section in config, disabling Kafka")
            return {"enabled": False}

        kafka_config = config["kafka"]

        # Basic configuration
        result = {
            "enabled": kafka_config.getboolean("enabled", True),
            "bootstrap_servers": kafka_config.get(
                "bootstrap_servers", "localhost:9092"
            ),
            "topic_prefix": kafka_config.get("topic_prefix", "zombie-detector"),
            "security_protocol": kafka_config.get("security_protocol", "PLAINTEXT"),
            "compression_type": kafka_config.get("compression_type", "gzip"),
            "retries": kafka_config.getint("retries", 3),
            "acks": kafka_config.get("acks", "all"),
            "batch_size": kafka_config.getint("batch_size", 16384),
            "linger_ms": kafka_config.getint("linger_ms", 100),
            "buffer_memory": kafka_config.getint("buffer_memory", 33554432),
        }

        # SSL configuration
        ssl_config = {}
        ssl_fields = [
            "ssl_cafile",
            "ssl_certfile",
            "ssl_keyfile",
            "ssl_password",
            "ssl_crlfile",
            "ssl_ciphers",
        ]

        for field in ssl_fields:
            value = kafka_config.get(field, "").strip()
            if value:
                ssl_config[field] = value

        if "ssl_check_hostname" in kafka_config:
            ssl_config["ssl_check_hostname"] = kafka_config.getboolean(
                "ssl_check_hostname", True
            )

        if ssl_config:
            result["ssl_config"] = ssl_config

        # SASL configuration
        sasl_config = {}
        sasl_mechanism = kafka_config.get("sasl_mechanism", "").strip()

        if sasl_mechanism:
            sasl_config["sasl_mechanism"] = sasl_mechanism

            # Common SASL fields
            sasl_fields = [
                "sasl_username",
                "sasl_password",
                "sasl_plain_username",
                "sasl_plain_password",
                "sasl_kerberos_service_name",
                "sasl_kerberos_domain_name",
                "sasl_oauth_token_provider",
            ]

            for field in sasl_fields:
                value = kafka_config.get(field, "").strip()
                if value:
                    sasl_config[field] = value

        if sasl_config:
            result["sasl_config"] = sasl_config

        logger.info(
            f"Loaded Kafka config with security protocol: {result['security_protocol']}"
        )
        return result

    except Exception as e:
        logger.warning(f"Failed to load Kafka config: {e}")
        return {"enabled": False}


def process_host_data(
    host_data: List[Dict[str, Any]],
    states_config: Dict[str, int],
    enable_tracking: bool = True,
    enable_kafka: bool = True,
    data_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Process a list of hosts and enrich them with zombie classification data.
    """
    from .classifier import classify_host

    enriched_hosts = []

    for host in host_data:
        # Step 1: Get the raw classification
        classification = classify_host(host)
        if isinstance(classification, tuple):
            criterion_type, criterion_alias, description = classification
        else:
            criterion_type = classification
            criterion_alias = "Unknown"
            description = ""
        # Get state for this criterion code
        criterion_state = states_config.get(criterion_type, 1)
        if criterion_state == 0:
            # If the detected zombie type is DISABLED, override to "0"
            criterion_type = "0"
            criterion_alias = "No Zombie Detected"
            description = "Sin criterios de zombie activos"
            is_zombie = False
        else:
            # If enabled, keep the classification
            is_zombie = criterion_type != "0"

        # Enrich host data
        enriched_host = host.copy()
        enriched_host.update(
            {
                "dynatrace_host_id": host.get("dynatrace_host_id"),
                "hostname": host.get("hostname"),
                "criterion_type": criterion_type,
                "criterion_alias": criterion_alias,
                "criterion_description": description,
                "criterion_state": criterion_state,
                "is_zombie": is_zombie,
            }
        )

        enriched_hosts.append(enriched_host)

    # Track zombies if enabled
    tracking_info = None
    if enable_tracking:
        zombies_only = [host for host in enriched_hosts if host.get("is_zombie", False)]
        if zombies_only:
            if data_dir:
                tracker = ZombieTracker(data_dir=data_dir)
            else:
                tracker = ZombieTracker()
            tracking_info = tracker.save_current_zombies(zombies_only)

    # Publish to Kafka if enabled
    if enable_kafka:
        try:
            kafka_config = _load_kafka_config()
            if kafka_config.get("enabled", False):
                # Extract configuration components
                bootstrap_servers = kafka_config.get(
                    "bootstrap_servers", "localhost:9092"
                )
                topic_prefix = kafka_config.get("topic_prefix", "zombie-detector")
                security_protocol = kafka_config.get("security_protocol", "PLAINTEXT")
                ssl_config = kafka_config.get("ssl_config")
                sasl_config = kafka_config.get("sasl_config")

                # Create publisher with authentication
                kafka_publisher = ZombieKafkaPublisher(
                    bootstrap_servers=bootstrap_servers,
                    topic_prefix=topic_prefix,
                    security_protocol=security_protocol,
                    ssl_config=ssl_config,
                    sasl_config=sasl_config,
                    **{
                        k: v
                        for k, v in kafka_config.items()
                        if k
                        not in [
                            "enabled",
                            "bootstrap_servers",
                            "topic_prefix",
                            "security_protocol",
                            "ssl_config",
                            "sasl_config",
                        ]
                    },
                )

                kafka_publisher.publish_zombie_detection(enriched_hosts)

                if tracking_info:
                    kafka_publisher.publish_tracking_stats(tracking_info)

                    for zombie_id in tracking_info.get("new_zombies", []):
                        zombie_data = next(
                            (
                                h
                                for h in enriched_hosts
                                if h["dynatrace_host_id"] == zombie_id
                            ),
                            None,
                        )
                        if zombie_data:
                            kafka_publisher.publish_zombie_lifecycle_event(
                                "zombie_new", zombie_data
                            )

                    for zombie_id in tracking_info.get("killed_zombies", []):
                        kafka_publisher.publish_zombie_lifecycle_event(
                            "zombie_killed", {"dynatrace_host_id": zombie_id}
                        )

                kafka_publisher.close()

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to publish to Kafka: {e}")

    if tracking_info and enriched_hosts:
        enriched_hosts[0]["_tracking_info"] = tracking_info

    return enriched_hosts


def filter_zombies(hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter hosts to return only those classified as zombies."""
    return [host for host in hosts if host.get("is_zombie", False)]


def get_zombie_summary(hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary of zombie classification results."""
    total_hosts = len(hosts)
    zombie_hosts = len([h for h in hosts if h.get("is_zombie", False)])

    criterion_counts = {}
    for host in hosts:
        criterion_type = host.get("criterion_type", "0")
        criterion_counts[criterion_type] = criterion_counts.get(criterion_type, 0) + 1

    return {
        "total_hosts": total_hosts,
        "zombie_hosts": zombie_hosts,
        "non_zombie_hosts": total_hosts - zombie_hosts,
        "zombie_percentage": round((zombie_hosts / total_hosts) * 100, 2)
        if total_hosts > 0
        else 0,
        "criterion_breakdown": criterion_counts,
    }


def get_killed_zombies_summary(
    since_hours: int = 24, data_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Get summary of killed zombies."""
    if data_dir:
        tracker = ZombieTracker(data_dir=data_dir)
    else:
        tracker = ZombieTracker()

    killed_zombies = tracker.get_killed_zombies(since_hours)

    criterion_counts = {}
    for zombie in killed_zombies:
        criterion_type = zombie.get("criterion_type", "unknown")
        criterion_counts[criterion_type] = criterion_counts.get(criterion_type, 0) + 1

    return {
        "killed_zombies_count": len(killed_zombies),
        "since_hours": since_hours,
        "killed_zombies": killed_zombies,
        "criterion_breakdown": criterion_counts,
    }
