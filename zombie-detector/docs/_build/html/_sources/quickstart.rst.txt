==========
Quickstart
==========

This guide will get you up and running with Zombie Detector in 5 minutes.

1. Installation
===============

.. code-block:: bash

   # Install from source
   git clone https://repo1.naudit.es/santander-cantabria/zombie-detector.git
   cd zombie-detector
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .

2. Basic CLI Usage
==================

Start with the command-line interface:

.. code-block:: bash

   # Analyze hosts from JSON file
   zombie-detector detect example.json

   # Include summary statistics
   zombie-detector detect example.json --summary

   # Show only zombie hosts
   zombie-detector detect example.json --zombies-only

3. Start the API Server
=======================

.. code-block:: bash

   # Start the API server
   uvicorn zombie_detector.api.rest:app --host 0.0.0.0 --port 8000

   # Or using the systemd service (package installations)
   sudo systemctl start zombie-detector

4. Test the API
===============

.. code-block:: bash

   # Health check
   curl http://localhost:8000/api/v1/health

   # Get default states
   curl http://localhost:8000/api/v1/states

   # Detect zombies (with example data)
   curl -X POST http://localhost:8000/api/v1/zombie-detection \
     -H "Content-Type: application/json" \
     -d @example.json

5. View Documentation
=====================

Access the interactive API documentation:

* **Swagger UI**: http://localhost:8000/docs
* **ReDoc**: http://localhost:8000/redoc

Example Data Format
===================

Your input JSON should contain host data like this:

.. code-block:: json

   [
     {
       "dynatrace_host_id": "HOST-1",
       "hostname": "hostname1",
       "Recent_CPU_decrease_criterion": 1,
       "Recent_net_traffic_decrease_criterion": 1,
       "Sustained_Low_CPU_criterion": 0,
       "Excessively_constant_RAM_criterion": 0,
       "Daily_CPU_profile_lost_criterion": 0
     }
   ]

Next Steps
==========

* Read the :doc:`user_guide/index` for detailed usage
* Explore the :doc:`api/index` for API reference
* See :doc:`user_guide/examples` for more examples
* Check :doc:`configuration` for customization options