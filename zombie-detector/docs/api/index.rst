=============
API Reference
=============

This section provides detailed API documentation for Zombie Detector.

.. toctree::
   :maxdepth: 2

   rest
   models
   core

REST API Overview
=================

The Zombie Detector REST API provides endpoints for:

* **Host Analysis**: Detect zombies in host data
* **Health Monitoring**: Check service status
* **Configuration**: Manage detection states and criteria
* **Tracking**: Monitor zombie lifecycles and history
* **Statistics**: Generate reports and summaries

Base URL
--------

When running locally: ``http://localhost:8000``

Authentication
--------------

Currently, the API does not require authentication. Future versions may include API key or OAuth2 support.

Response Format
---------------

All API responses follow this format:

.. code-block:: json

   {
     "status": "success|error",
     "results": [...],
     "summary": {...},
     "message": "Optional message"
   }

Error Handling
--------------

HTTP status codes used:

* **200**: Success
* **400**: Bad Request (invalid input)
* **404**: Not Found
* **422**: Validation Error
* **500**: Internal Server Error

Interactive Documentation
==========================

The API provides automatic interactive documentation:

* **Swagger UI**: ``/docs`` - Interactive API explorer
* **ReDoc**: ``/redoc`` - Alternative documentation view
* **OpenAPI Schema**: ``/openapi.json`` - Machine-readable schema

Rate Limiting
=============

Currently no rate limiting is implemented. For production deployments, consider adding rate limiting at the reverse proxy level.

API Versioning
==============

All endpoints are versioned with ``/api/v1/`` prefix. Future versions will maintain backward compatibility where possible.