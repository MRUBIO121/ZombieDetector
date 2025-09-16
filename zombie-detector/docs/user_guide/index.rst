==========
User Guide
==========

This section provides comprehensive documentation for using Zombie Detector.

.. toctree::
   :maxdepth: 2

   cli
   api
   tracking
   examples
   configuration

Overview
========

Zombie Detector provides multiple interfaces for detecting zombie hosts:

Command Line Interface (CLI)
    Batch processing and automation scripts

REST API
    Web service integration and real-time detection

Tracking System
    Historical analysis and zombie lifecycle management

Detection Criteria
==================

The system uses 5 core criteria to detect zombie hosts:

1. **Recent CPU Decrease**: Sudden drop in CPU usage
2. **Recent Network Traffic Decrease**: Reduction in network activity  
3. **Sustained Low CPU**: Consistently low CPU utilization
4. **Excessively Constant RAM**: Unchanging memory usage patterns
5. **Daily CPU Profile Lost**: Missing expected CPU activity patterns

These criteria are combined to create sophisticated zombie classification patterns from simple single-criterion zombies to complex multi-criterion combinations.

Classification System
=====================

The system generates codes like:

* **0**: No zombie criteria detected
* **1A-1E**: Single criterion zombies
* **2A-2J**: Two criteria combinations  
* **3A-3J**: Three criteria combinations
* **4A-4E**: Four criteria combinations
* **5**: All five criteria active

Each code maps to Spanish creature names like "Mummy", "Vampire", "Wraith", etc., providing intuitive zombie type identification.

States Configuration
====================

Control which zombie types are active:

.. code-block:: json

   {
     "0": 0,     // No zombie - inactive
     "1A": 1,    // Single CPU criterion - active
     "2A": 1,    // CPU + Network - active  
     "3A": 0,    // Three criteria - inactive
     "5": 1      // All criteria - active
   }

This allows fine-tuned control over zombie detection sensitivity and which patterns trigger alerts.