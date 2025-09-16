===============
Zombie Tracking
===============

The Zombie Detector includes comprehensive tracking capabilities to monitor zombie lifecycles over time.

Overview
========

The tracking system provides:

- **Lifecycle Management**: Track when zombies first appear and when they're resolved
- **Historical Analysis**: View zombie trends and patterns
- **Resolution Detection**: Automatically detect when zombies are "killed"
- **Statistics and Reporting**: Generate detailed reports on zombie populations

How Tracking Works
==================

Detection Flow
--------------

1. **First Detection**: When a host meets zombie criteria, it's recorded as a new zombie
2. **Persistence Tracking**: Subsequent detections update the "last seen" timestamp
3. **Kill Detection**: When a zombie no longer appears, it's marked as "killed"
4. **Historical Storage**: All activity is stored for analysis

Data Files
----------

The system maintains three tracking files:

``/var/lib/zombie-detector/current_zombies.json``
  Current active zombies and statistics

``/var/lib/zombie-detector/zombie_history.json``
  Historical detection records

``/var/lib/zombie-detector/killed_zombies.json``
  Record of resolved zombies

Using the Tracking System
==========================

CLI Commands
------------

Check killed zombies:

.. code-block:: bash

   # Last 24 hours
   zombie-detector killed

   # Custom time period
   zombie-detector killed --since-hours 48

   # Save to file
   zombie-detector killed --output killed_report.json

Check specific zombie:

.. code-block:: bash

   # Basic status
   zombie-detector check HOST-1

   # Full lifecycle
   zombie-detector check HOST-1 --lifecycle

Clean up old data:

.. code-block:: bash

   # Keep last 30 days
   zombie-detector cleanup --days 30

API Endpoints
-------------

**Get killed zombies:**

.. code-block:: bash

   curl "http://localhost:8000/api/v1/zombies/killed?since_hours=24"

**Check zombie lifecycle:**

.. code-block:: bash

   curl http://localhost:8000/api/v1/zombies/HOST-1/lifecycle

**Get tracking statistics:**

.. code-block:: bash

   curl http://localhost:8000/api/v1/zombies/tracking-stats

Data Structures
===============

Current Zombies
---------------

.. code-block:: json

   {
     "timestamp": "2025-01-30T10:00:00",
     "zombies": [
       {
         "dynatrace_host_id": "HOST-1",
         "hostname": "hostname1",
         "criterion_type": "2A",
         "criterion_alias": "Mummy",
         "is_zombie": true
       }
     ],
     "zombie_ids": ["HOST-1"],
     "stats": {
       "total_zombies": 1,
       "new_zombies": 0,
       "persisting_zombies": 1,
       "killed_zombies": 0
     }
   }

Zombie History
--------------

.. code-block:: json

   {
     "history": [
       {
         "timestamp": "2025-01-30T10:00:00",
         "zombie_count": 1,
         "zombies": [
           {
             "dynatrace_host_id": "HOST-1",
             "criterion_type": "2A",
             "is_zombie": true
           }
         ]
       }
     ]
   }

Killed Zombies
--------------

.. code-block:: json

   {
     "killed_zombies": [
       {
         "dynatrace_host_id": "HOST-2",
         "hostname": "hostname2",
         "criterion_type": "1A",
         "killed_at": "2025-01-30T11:00:00",
         "last_detection": {
           "criterion_type": "1A",
           "is_zombie": true
         }
       }
     ]
   }

Configuration
=============

Tracking can be configured in ``/etc/zombie-detector/zombie-detector.ini``:

.. code-block:: ini

   [tracking]
   max_history_entries = 1000
   cleanup_days = 30
   enable_lifecycle_events = true

Best Practices
==============

Data Management
---------------

- Regular cleanup of old tracking data
- Monitor disk usage in ``/var/lib/zombie-detector/``
- Backup tracking data before major changes

Analysis Workflow
-----------------

1. Run regular zombie detection
2. Monitor tracking statistics
3. Investigate persistent zombies
4. Verify resolution of killed zombies
5. Generate periodic reports

Troubleshooting
===============

Common Issues
-------------

**Tracking files not updating**
  - Check permissions on ``/var/lib/zombie-detector/``
  - Verify service user can write to directory

**High disk usage**
  - Run cleanup more frequently
  - Reduce ``max_history_entries`` setting

**Missing killed zombies**
  - Ensure consistent detection runs
  - Check that zombie resolution is actually occurring