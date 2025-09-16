========
API Usage
========

This section covers how to use the Zombie Detector REST API effectively.

Getting Started
===============

Start the API Server
--------------------

.. code-block:: bash

   # Development mode
   uvicorn zombie_detector.api.rest:app --host 0.0.0.0 --port 8000 --reload

   # Production mode (systemd service)
   sudo systemctl start zombie-detector

Basic API Calls
===============

Health Check
------------

.. code-block:: bash

   curl http://localhost:8000/api/v1/health

Expected response:

.. code-block:: json

   {
     "status": "healthy",
     "service": "zombie-detector",
     "version": "0.1.1"
   }

Zombie Detection
----------------

.. code-block:: bash

   curl -X POST http://localhost:8000/api/v1/zombie-detection \
     -H "Content-Type: application/json" \
     -d '{
       "hosts": [
         {
           "dynatrace_host_id": "HOST-1",
           "hostname": "hostname1",
           "Recent_CPU_decrease_criterion": 1,
           "Recent_net_traffic_decrease_criterion": 1,
           "Sustained_Low_CPU_criterion": 0,
           "Excessively_constant_RAM_criterion": 0,
           "Daily_CPU_profile_lost_criterion": 0
         }
       ],
       "options": {
         "include_summary": true
       }
     }'

API Authentication
==================

Currently, no authentication is required. Future versions may include:

- API Key authentication
- OAuth2 integration
- JWT tokens

Rate Limiting
=============

No rate limiting is currently implemented. For production:

- Use a reverse proxy (nginx/Apache) with rate limiting
- Consider API gateway solutions
- Monitor usage patterns

Error Handling
==============

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (validation errors)
- **404**: Not Found
- **500**: Internal Server Error

Example error response:

.. code-block:: json

   {
     "detail": {
       "error": "Invalid host data",
       "invalid_host_indices": [0, 2],
       "required_fields": ["dynatrace_host_id", "hostname"]
     }
   }

Best Practices
==============

Batch Processing
----------------

- Send multiple hosts in a single request
- Use reasonable batch sizes (100-1000 hosts)
- Handle partial failures gracefully

Configuration Management
-------------------------

- Use consistent states configuration
- Version your configuration changes
- Test configuration changes in development

Monitoring and Logging
-----------------------

- Monitor API response times
- Set up health check alerts
- Log all API interactions for debugging