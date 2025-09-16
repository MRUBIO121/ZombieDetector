========
REST API
========

Detailed documentation for all REST API endpoints.

.. automodule:: zombie_detector.api.rest
   :members:
   :undoc-members:
   :show-inheritance:

Core Endpoints
==============

Health Check
------------

.. http:get:: /api/v1/health

   Check if the service is running and healthy.

   **Example Request:**

   .. code-block:: bash

      curl -X GET http://localhost:8000/api/v1/health

   **Example Response:**

   .. code-block:: json

      {
        "status": "healthy",
        "service": "zombie-detector",
        "version": "0.1.1"
      }

Zombie Detection
----------------

.. http:post:: /api/v1/zombie-detection

   Analyze hosts and detect zombies based on performance criteria.

   **Request Body:**

   .. code-block:: json

      {
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
        "states": {
          "2A": 1,
          "1A": 1
        },
        "options": {
          "zombies_only": false,
          "include_summary": true
        }
      }

   **Response:**

   .. code-block:: json

      {
        "status": "success",
        "results": [
          {
            "dynatrace_host_id": "HOST-1",
            "hostname": "hostname1",
            "criterion_type": "2A",
            "criterion_alias": "Mummy",
            "criterion_description": "CPU and Network decline detected",
            "is_zombie": true
          }
        ],
        "summary": {
          "total_hosts": 1,
          "zombie_hosts": 1,
          "zombie_percentage": 100.0
        }
      }

Configuration Endpoints
=======================

Default States
--------------

.. http:get:: /api/v1/states

   Get the default criterion states configuration.

   **Response:**

   .. code-block:: json

      {
        "states": {
          "0": 0,
          "1A": 1,
          "1B": 1,
          "2A": 1,
          "5": 1
        }
      }

Criteria Information
--------------------

.. http:get:: /api/v1/criteria

   Get information about all zombie detection criteria.

   **Response:**

   .. code-block:: json

      {
        "criteria": {
          "2A": {
            "alias": "Mummy",
            "description": "Recent CPU and network traffic decrease detected"
          },
          "1A": {
            "alias": "Espectro",
            "description": "Recent CPU decrease detected"
          }
        }
      }

Tracking Endpoints
==================

Killed Zombies
---------------

.. http:get:: /api/v1/zombies/killed

   Get zombies that were resolved in a time period.

   **Query Parameters:**

   * ``since_hours`` (int): Hours to look back (default: 24, max: 168)

   **Example:**

   .. code-block:: bash

      curl "http://localhost:8000/api/v1/zombies/killed?since_hours=48"

Zombie Lifecycle
-----------------

.. http:get:: /api/v1/zombies/{zombie_id}/lifecycle

   Get complete lifecycle information for a specific zombie.

   **Path Parameters:**

   * ``zombie_id`` (str): Dynatrace host ID

   **Example:**

   .. code-block:: bash

      curl http://localhost:8000/api/v1/zombies/HOST-1/lifecycle

Tracking Statistics
-------------------

.. http:get:: /api/v1/zombies/tracking-stats

   Get current zombie tracking statistics.

   **Response:**

   .. code-block:: json

      {
        "new_zombies": ["HOST-1", "HOST-2"],
        "persisting_zombies": ["HOST-3"],
        "killed_zombies": ["HOST-4"],
        "stats": {
          "total_zombies": 3,
          "new_zombies": 2,
          "persisting_zombies": 1,
          "killed_zombies": 1
        }
      }

Utility Endpoints
=================

Cleanup Data
------------

.. http:post:: /api/v1/zombies/cleanup

   Clean up old zombie tracking data.

   **Query Parameters:**

   * ``days_to_keep`` (int): Days of data to keep (default: 30, max: 365)

   **Example:**

   .. code-block:: bash

      curl -X POST "http://localhost:8000/api/v1/zombies/cleanup?days_to_keep=7"