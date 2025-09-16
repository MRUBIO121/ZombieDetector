=============
Configuration
=============

This section covers all configuration options for Zombie Detector.

Configuration Files
===================

Main Configuration
------------------

The main configuration file is located at ``/etc/zombie-detector/zombie-detector.ini``:

.. code-block:: ini

   # /etc/zombie-detector/zombie-detector.ini
   
   [api]
   host = 0.0.0.0
   port = 8000
   workers = 1
   log_level = info

   [detection]
   # Default criterion states (0=inactive, 1=active)
   default_states_2a = 1  # Ghoul (CPU + Network)
   default_states_1a = 1  # Single CPU criterion

   [kafka]
   enabled = true
   bootstrap_servers = localhost:9092
   topic_prefix = zombie-detector
   compression_type = gzip
   retries = 3
   acks = all
   batch_size = 16384
   linger_ms = 100
   buffer_memory = 33554432
   security_protocol = PLAINTEXT

   [tracking]
   max_history_entries = 1000
   cleanup_days = 30
   enable_lifecycle_events = true

   [logging]
   log_file = /var/log/zombie-detector/zombie-detector.log
   log_level = INFO
   log_format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
   max_file_size = 10MB
   backup_count = 5

Configuration Sections
======================

API Section
-----------

The ``[api]`` section controls the REST API server behavior.

.. list-table:: API Configuration Options
   :header-rows: 1
   :widths: 25 15 60

   * - Option
     - Default
     - Description
   * - ``host``
     - ``0.0.0.0``
     - Server bind address. Use ``0.0.0.0`` for all interfaces, ``127.0.0.1`` for localhost only
   * - ``port``
     - ``8000``
     - TCP port number for the API server (1024-65535)
   * - ``workers``
     - ``1``
     - Number of worker processes. Recommended: number of CPU cores
   * - ``log_level``
     - ``info``
     - API server log level. Options: ``debug``, ``info``, ``warning``, ``error``

**Example configurations:**

.. code-block:: ini

   # Development configuration
   [api]
   host = 127.0.0.1
   port = 8000
   workers = 1
   log_level = debug

   # Production configuration
   [api]
   host = 0.0.0.0
   port = 8080
   workers = 4
   log_level = info

Detection Section
----------------

The ``[detection]`` section configures zombie detection criteria defaults.

.. list-table:: Detection Configuration Options
   :header-rows: 1
   :widths: 30 15 55

   * - Option
     - Default
     - Description
   * - ``default_states_1a``
     - ``1``
     - Single CPU criterion detection (0=inactive, 1=active)
   * - ``default_states_2a``
     - ``1``
     - Ghoul pattern: CPU + Network decline (0=inactive, 1=active)
   * - ``default_states_*``
     - varies
     - Default state for any zombie detection pattern

**Available Detection Patterns:**

- **1A-1E**: Single criteria patterns
- **2A-2J**: Dual criteria patterns (most common)
- **3A-3J**: Triple criteria patterns
- **4A-4E**: Quad criteria patterns
- **5**: All criteria pattern (rare)

.. code-block:: ini

   # Enable only specific patterns
   [detection]
   default_states_1a = 1  # Recent CPU decrease
   default_states_1b = 0  # Network traffic decrease (disabled)
   default_states_2a = 1  # Ghoul pattern (CPU + Network)
   default_states_2b = 1  # CPU decline + Sustained low CPU
   default_states_3a = 0  # Triple criteria (disabled)

Kafka Section
------------

The ``[kafka]`` section configures Apache Kafka integration for event streaming.

Basic Configuration
^^^^^^^^^^^^^^^^^^

.. list-table:: Basic Kafka Options
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Description
   * - ``enabled``
     - ``true``
     - Enable/disable Kafka integration (true/false)
   * - ``bootstrap_servers``
     - ``localhost:9092``
     - Comma-separated list of Kafka broker addresses
   * - ``topic_prefix``
     - ``zombie-detector``
     - Prefix for all Kafka topics created by the system

Producer Configuration
^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Kafka Producer Options
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Description
   * - ``compression_type``
     - ``gzip``
     - Message compression. Options: ``none``, ``gzip``, ``snappy``, ``lz4``, ``zstd``
   * - ``retries``
     - ``3``
     - Number of retry attempts for failed sends
   * - ``acks``
     - ``all``
     - Acknowledgment level. Options: ``0``, ``1``, ``all``
   * - ``batch_size``
     - ``16384``
     - Batch size in bytes for producer batching
   * - ``linger_ms``
     - ``100``
     - Time to wait for additional messages before sending batch
   * - ``buffer_memory``
     - ``33554432``
     - Total memory available for producer buffering (32MB)

Security Configuration
^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Kafka Security Options
   :header-rows: 1
   :widths: 30 20 50

   * - Option
     - Default
     - Description
   * - ``security_protocol``
     - ``PLAINTEXT``
     - Security protocol. Options: ``PLAINTEXT``, ``SSL``, ``SASL_PLAINTEXT``, ``SASL_SSL``

**SSL Configuration** (when ``security_protocol`` = ``SSL`` or ``SASL_SSL``):

.. list-table:: SSL Options
   :header-rows: 1
   :widths: 30 50

   * - Option
     - Description
   * - ``ssl_check_hostname``
     - Verify SSL certificate hostname (true/false)
   * - ``ssl_cafile``
     - Path to CA certificate file
   * - ``ssl_certfile``
     - Path to client certificate file
   * - ``ssl_keyfile``
     - Path to client private key file
   * - ``ssl_password``
     - Password for encrypted private key (optional)
   * - ``ssl_crlfile``
     - Path to certificate revocation list file (optional)
   * - ``ssl_ciphers``
     - Allowed SSL cipher suites

**SASL Configuration** (when ``security_protocol`` = ``SASL_PLAINTEXT`` or ``SASL_SSL``):

.. list-table:: SASL Options
   :header-rows: 1
   :widths: 30 20 50

   * - Option
     - Default
     - Description
   * - ``sasl_mechanism``
     - ``PLAIN``
     - SASL mechanism. Options: ``PLAIN``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``, ``GSSAPI``, ``OAUTHBEARER``
   * - ``sasl_username``
     - ``zombie-detector``
     - SASL username for authentication
   * - ``sasl_password``
     - ``your-secure-password``
     - SASL password for authentication

**SASL PLAIN/SCRAM Configuration:**

.. list-table:: SASL PLAIN/SCRAM Options
   :header-rows: 1
   :widths: 30 50

   * - Option
     - Description
   * - ``sasl_plain_username``
     - Username for PLAIN authentication
   * - ``sasl_plain_password``
     - Password for PLAIN authentication

**SASL GSSAPI (Kerberos) Configuration:**

.. list-table:: SASL GSSAPI Options
   :header-rows: 1
   :widths: 30 50

   * - Option
     - Description
   * - ``sasl_kerberos_service_name``
     - Kerberos service name (usually ``kafka``)
   * - ``sasl_kerberos_domain_name``
     - Kerberos domain name

**SASL OAuth Configuration:**

.. list-table:: SASL OAuth Options
   :header-rows: 1
   :widths: 30 50

   * - Option
     - Description
   * - ``sasl_oauth_token_provider``
     - Custom OAuth token provider implementation

**Example Kafka Configurations:**

.. code-block:: ini

   # Simple PLAINTEXT configuration
   [kafka]
   enabled = true
   bootstrap_servers = kafka1:9092,kafka2:9092,kafka3:9092
   topic_prefix = prod-zombie-detector
   compression_type = gzip
   retries = 5
   acks = all

   # SSL configuration
   [kafka]
   enabled = true
   bootstrap_servers = kafka1:9093,kafka2:9093,kafka3:9093
   security_protocol = SSL
   ssl_check_hostname = true
   ssl_cafile = /etc/zombie-detector/ssl/ca-cert.pem
   ssl_certfile = /etc/zombie-detector/ssl/client-cert.pem
   ssl_keyfile = /etc/zombie-detector/ssl/client-key.pem

   # SASL_SSL with SCRAM-SHA-256
   [kafka]
   enabled = true
   bootstrap_servers = kafka1:9094,kafka2:9094,kafka3:9094
   security_protocol = SASL_SSL
   sasl_mechanism = SCRAM-SHA-256
   sasl_username = zombie-detector-prod
   sasl_password = ${KAFKA_PASSWORD}
   ssl_cafile = /etc/ssl/certs/ca-certificates.crt

Tracking Section
---------------

The ``[tracking]`` section configures zombie lifecycle tracking and history management.

.. list-table:: Tracking Configuration Options
   :header-rows: 1
   :widths: 30 20 50

   * - Option
     - Default
     - Description
   * - ``max_history_entries``
     - ``1000``
     - Maximum number of historical entries to retain per zombie
   * - ``cleanup_days``
     - ``30``
     - Number of days to retain zombie history before cleanup
   * - ``enable_lifecycle_events``
     - ``true``
     - Enable tracking of zombie lifecycle events (birth/death)

**Tracking Behavior:**

- **History Management**: Automatically cleans up old entries based on ``cleanup_days``
- **Memory Management**: Limits in-memory history to ``max_history_entries``
- **Lifecycle Events**: Tracks when zombies appear and disappear when ``enable_lifecycle_events`` is true

.. code-block:: ini

   # High-volume environment
   [tracking]
   max_history_entries = 5000
   cleanup_days = 7
   enable_lifecycle_events = true

   # Low-resource environment
   [tracking]
   max_history_entries = 500
   cleanup_days = 60
   enable_lifecycle_events = false

Logging Section
--------------

The ``[logging]`` section configures application logging behavior.

.. list-table:: Logging Configuration Options
   :header-rows: 1
   :widths: 25 20 55

   * - Option
     - Default
     - Description
   * - ``log_file``
     - ``/var/log/zombie-detector/zombie-detector.log``
     - Path to the main log file
   * - ``log_level``
     - ``INFO``
     - Logging level. Options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``
   * - ``log_format``
     - ``%(asctime)s - %(name)s - %(levelname)s - %(message)s``
     - Python logging format string
   * - ``max_file_size``
     - ``10MB``
     - Maximum size before log rotation (supports KB, MB, GB)
   * - ``backup_count``
     - ``5``
     - Number of rotated log files to keep

**Log Levels:**

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

**Log Rotation:**

When the log file reaches ``max_file_size``, it's rotated and compressed. Old log files are named with a suffix (e.g., ``.1``, ``.2``) and removed when exceeding ``backup_count``.

.. code-block:: ini

   # Development logging
   [logging]
   log_file = /tmp/zombie-detector.log
   log_level = DEBUG
   log_format = %(asctime)s [%(levelname)s] %(name)s: %(message)s
   max_file_size = 50MB
   backup_count = 3

   # Production logging
   [logging]
   log_file = /var/log/zombie-detector/zombie-detector.log
   log_level = INFO
   log_format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
   max_file_size = 100MB
   backup_count = 10

States Configuration
-------------------

Zombie state definitions are configured in ``/etc/zombie-detector/states.json``:

.. code-block:: json

   {
     "0": 0,
     "1A": 1, "1B": 1, "1C": 1, "1D": 1, "1E": 1,
     "2A": 1, "2B": 1, "2C": 1, "2D": 1, "2E": 1,
     "2F": 1, "2G": 1, "2H": 1, "2I": 1, "2J": 1,
     "3A": 1, "3B": 1, "3C": 1, "3D": 1, "3E": 1,
     "3F": 1, "3G": 1, "3H": 1, "3I": 1, "3J": 1,
     "4A": 1, "4B": 1, "4C": 1, "4D": 1, "4E": 1,
     "5": 1
   }

Environment Variables
====================

Service Configuration
--------------------

Environment variables can override configuration file settings.

.. envvar:: ZOMBIE_DETECTOR_HOST

   Service bind address
   
   :Default: ``0.0.0.0``

.. envvar:: ZOMBIE_DETECTOR_PORT

   Service port number
   
   :Default: ``8000``

.. envvar:: ZOMBIE_DETECTOR_LOG_LEVEL

   Logging level
   
   :Default: ``INFO``
   :Options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``

.. envvar:: ZOMBIE_DETECTOR_WORKERS

   Number of worker processes
   
   :Default: ``1``

Data Processing
--------------

.. envvar:: ZOMBIE_DETECTOR_BATCH_SIZE

   Processing batch size
   
   :Default: ``1000``

.. envvar:: ZOMBIE_DETECTOR_MAX_CONCURRENT_JOBS

   Maximum concurrent processing jobs
   
   :Default: ``10``

.. envvar:: ZOMBIE_DETECTOR_ENABLE_TRACKING

   Enable zombie tracking
   
   :Default: ``true``

**Location**: ``/etc/default/zombie-detector``

.. code-block:: bash

   # API Server Configuration
   ZOMBIE_DETECTOR_HOST=0.0.0.0
   ZOMBIE_DETECTOR_PORT=8000
   ZOMBIE_DETECTOR_WORKERS=1

   # Data Directories
   ZOMBIE_DETECTOR_CONFIG_DIR=/etc/zombie-detector
   ZOMBIE_DETECTOR_DATA_DIR=/var/lib/zombie-detector

   # Logging
   ZOMBIE_DETECTOR_LOG_LEVEL=INFO
   ZOMBIE_DETECTOR_LOG_FILE=/var/log/zombie-detector/zombie-detector.log

Configuration Priority
======================

Settings are applied in order of precedence (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

Detection Criteria Configuration
================================

The system supports multiple zombie detection patterns:

Single Criteria (1A-1E)
-----------------------

- **1A**: Recent CPU decrease only
- **1B**: Recent network traffic decrease only
- **1C**: Sustained low CPU only
- **1D**: Excessively constant RAM only
- **1E**: Daily CPU profile lost only

Double Criteria (2A-2J)
-----------------------

- **2A**: CPU + Network decline (Ghoul pattern)
- **2B**: CPU decline + Sustained low CPU
- **2C**: CPU decline + Constant RAM
- **2D**: CPU decline + Lost CPU profile
- **2E**: Network + Sustained low CPU
- **2F**: Network + Constant RAM
- **2G**: Network + Lost CPU profile
- **2H**: Sustained low CPU + Constant RAM
- **2I**: Sustained low CPU + Lost CPU profile
- **2J**: Constant RAM + Lost CPU profile


**Common Validation Errors:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Error
     - Solution
   * - ``Invalid port number``
     - Use port between 1024-65535
   * - ``Kafka connection failed``
     - Check bootstrap_servers and credentials
   * - ``Memory limit too low``
     - Increase memory_limit_mb to at least 512MB
   * - ``Invalid log level``
     - Use DEBUG, INFO, WARNING, or ERROR

Test your configuration:

.. code-block:: bash

   # Test states configuration
   zombie-detector detect example.json --state-path /etc/zombie-detector/states.json

   # Validate API configuration
   curl http://localhost:8000/api/v1/health

   # Check logs for configuration issues
   sudo journalctl -u zombie-detector | grep -i error

Environment-Specific Configurations Examples
===================================

Development Configuration
-------------------------

.. code-block:: ini

   [api]
   host = 127.0.0.1
   port = 8000
   workers = 1
   log_level = debug

   [kafka]
   enabled = false
   
   [tracking]
   max_history_entries = 100
   cleanup_days = 1
   
   [logging]
   log_file = /tmp/zombie-detector.log
   log_level = DEBUG
   max_file_size = 10MB

Production Configuration
-----------------------

.. code-block:: ini

   [api]
   host = 0.0.0.0
   port = 8000
   workers = 8
   log_level = info

   [kafka]
   enabled = true
   bootstrap_servers = kafka1:9092,kafka2:9092,kafka3:9092
   security_protocol = SASL_SSL
   sasl_mechanism = SCRAM-SHA-256
   
   [tracking]
   max_history_entries = 5000
   cleanup_days = 30
   
   [logging]
   log_file = /var/log/zombie-detector/zombie-detector.log
   log_level = INFO
   max_file_size = 100MB
   backup_count = 30

Configuration Templates
======================

Use the provided templates for quick setup:

.. code-block:: bash

   # Copy template configurations
   cp /usr/share/zombie-detector/config-templates/production.ini /etc/zombie-detector/zombie-detector.ini
   cp /usr/share/zombie-detector/config-templates/states-default.json /etc/zombie-detector/states.json
   
   # Generate configuration from environment
   zombie-detector generate-config --environment production > zombie-detector.ini