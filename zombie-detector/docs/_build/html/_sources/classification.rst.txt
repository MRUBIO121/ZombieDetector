===================
Zombie Classification
===================

Complete Zombie Type Reference
==============================

Single Criteria Zombies (1A-1E)
--------------------------------

These are basic zombies detected by a single criterion:

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Code
     - Name
     - Criteria Description
   * - **1A**
     - **Zombie**
     - Recent CPU decrease detected
   * - **1B**
     - **Walker**
     - Recent network traffic decrease detected
   * - **1C**
     - **Crawler**
     - Sustained low CPU usage detected
   * - **1D**
     - **Lurker**
     - Excessively constant RAM usage detected
   * - **1E**
     - **Sleeper**
     - Daily CPU profile pattern lost

Double Criteria Zombies (2A-2J)
--------------------------------

These are intermediate zombies with two active criteria:

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Code
     - Name
     - Criteria Combination
   * - **2A**
     - **Mummy**
     - CPU decrease + Network traffic decrease
   * - **2B**
     - **Wraith**
     - CPU decrease + Sustained low CPU
   * - **2C**
     - **Vampire**
     - CPU decrease + Constant RAM
   * - **2D**
     - **Banshee**
     - CPU decrease + Daily profile lost
   * - **2E**
     - **Phantom**
     - Network decrease + Sustained low CPU
   * - **2F**
     - **Specter**
     - Network decrease + Constant RAM
   * - **2G**
     - **Shade**
     - Network decrease + Daily profile lost
   * - **2H**
     - **Poltergeist**
     - Sustained low CPU + Constant RAM
   * - **2I**
     - **Spirit**
     - Sustained low CPU + Daily profile lost
   * - **2J**
     - **Apparition**
     - Constant RAM + Daily profile lost

Triple Criteria Zombies (3A-3J)
--------------------------------

Advanced zombies with three active criteria:

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Code
     - Name
     - Description
   * - **3A**
     - **Solomon**
     - CPU + Network + Sustained low CPU
   * - **3B**
     - **Bud**
     - CPU + Network + Constant RAM
   * - **3C**
     - **Tarman**
     - CPU + Network + Daily profile lost
   * - **3D**
     - **Ben**
     - CPU + Sustained low CPU + Constant RAM
   * - **3E**
     - **Fido**
     - CPU + Sustained low CPU + Daily profile lost
   * - **3F**
     - **Bloater**
     - CPU + Constant RAM + Daily profile lost
   * - **3G**
     - **Shambler**
     - Network + Sustained low CPU + Constant RAM
   * - **3H**
     - **Stalker**
     - Network + Sustained low CPU + Daily profile lost
   * - **3I**
     - **Zeus**
     - Network + Constant RAM + Daily profile lost
   * - **3J**
     - **Wights**
     - Sustained low CPU + Constant RAM + Daily profile lost

Quad Criteria Zombies (4A-4E)
------------------------------

High-threat zombies with four active criteria:

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Code
     - Name
     - Missing Criterion
   * - **4A**
     - **Nemesis**
     - Missing: Recent CPU decrease
   * - **4B**
     - **Clicker**
     - Missing: Recent network traffic decrease
   * - **4C**
     - **Revenant**
     - Missing: Sustained low CPU
   * - **4D**
     - **Ghoul**
     - Missing: Excessively constant RAM
   * - **4E**
     - **Gael**
     - Missing: Daily CPU profile lost

Ultimate Zombie (5)
-------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 65

   * - Code
     - Name
     - Description
   * - **5**
     - **Coloso**
     - All five criteria active - maximum threat level

Classification Logic
====================

The zombie classification system works as follows:

1. **Detect Active Criteria**: Count how many of the 5 base criteria are active (value = 1)
2. **Generate Code**: Based on the specific combination of active criteria
3. **Assign Name**: Each code maps to a unique creature name
4. **Create Description**: Generate Spanish description of active criteria

Code Generation Rules
---------------------

* **0 criteria**: Code "0" - Sin criterios de zombie activos
* **1 criterion**: Codes "1A" to "1E" - Single criterion index
* **2 criteria**: Codes "2A" to "2J" - Combination of two criteria indices
* **3 criteria**: Codes "3A" to "3J" - Combination of three criteria indices  
* **4 criteria**: Codes "4A" to "4E" - Missing criterion index
* **5 criteria**: Code "5" - All criteria active

Usage in Detection
==================

When processing host data:

.. code-block:: python

   from zombie_detector.core.classifier import classify_host
   
   host_data = {
       "Recent_CPU_decrease_criterion": 1,
       "Recent_net_traffic_decrease_criterion": 1,
       "Sustained_Low_CPU_criterion": 0,
       "Excessively_constant_RAM_criterion": 0,
       "Daily_CPU_profile_lost_criterion": 0,
   }
   
   code, alias, description = classify_host(host_data)
   # Returns: ("2A", "Mummy", "Detectada una bajada repentina en el uso de CPU, Detectada una caída brusca en el tráfico de red reciente")

API Integration
===============

The classification system integrates seamlessly with the REST API:

.. code-block:: json

   {
     "detection_results": [
       {
         "dynatrace_host_id": "HOST-1",
         "criterion_type": "2A",
         "criterion_alias": "Mummy",
         "criterion_description": "Detectada una bajada repentina en el uso de CPU, Detectada una caída brusca en el tráfico de red reciente",
         "is_zombie": true
       }
     ],
     "summary": {
       "2A": {"count": 4, "alias": "Mummy"},
       "1A": {"count": 2, "alias": "Zombie"},
       "2B": {"count": 2, "alias": "Wraith"}
     }
   }