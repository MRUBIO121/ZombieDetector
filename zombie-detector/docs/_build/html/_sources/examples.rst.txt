========
Examples
========

This section provides practical examples of using Zombie Detector.

Basic Examples
==============

CLI Usage
---------

Simple detection:

.. code-block:: bash

   # Basic zombie detection
   zombie-detector detect example.json

   # With summary and verbose output
   zombie-detector detect example.json --summary --verbose

   # Only show zombies
   zombie-detector detect example.json --zombies-only

API Usage
---------

Basic detection request:

.. code-block:: bash

   curl -X POST http://localhost:8000/api/v1/zombie-detection \
     -H "Content-Type: application/json" \
     -d '{
       "hosts": [
         {
           "dynatrace_host_id": "HOST-1",
           "hostname": "hostname1",
           "Recent_CPU_decrease_criterion": 1,
           "Recent_net_traffic_decrease_criterion": 0,
           "Sustained_Low_CPU_criterion": 0,
           "Excessively_constant_RAM_criterion": 0,
           "Daily_CPU_profile_lost_criterion": 0
         }
       ]
     }'

Real-World Scenarios
====================

Daily Monitoring
----------------

Automated daily zombie detection:

.. code-block:: bash

   #!/bin/bash
   # daily_zombie_check.sh
   
   DATE=$(date +%Y%m%d)
   REPORT_DIR="/reports/daily"
   
   mkdir -p "$REPORT_DIR"
   
   # Run detection with full reporting
   zombie-detector detect /data/daily_hosts.json \
     --summary \
     --verbose \
     --output "$REPORT_DIR/zombies_$DATE.json"
   
   # Check for killed zombies
   zombie-detector killed \
     --since-hours 24 \
     --output "$REPORT_DIR/killed_$DATE.json"
   
   # Generate summary
   echo "Daily Zombie Report - $DATE" > "$REPORT_DIR/summary_$DATE.txt"
   echo "=========================" >> "$REPORT_DIR/summary_$DATE.txt"
   
   # Extract summary info
   jq '.summary' "$REPORT_DIR/zombies_$DATE.json" >> "$REPORT_DIR/summary_$DATE.txt"

Emergency Investigation
-----------------------

Quick zombie investigation:

.. code-block:: bash

   # Emergency zombie check
   zombie-detector detect emergency_hosts.json \
     --zombies-only \
     --verbose \
     --no-kafka

   # Check specific problematic host
   zombie-detector check HOST-PROBLEM-01 --lifecycle

   # Get recent resolution data
   zombie-detector killed --since-hours 4

Python Integration
==================

Using the API with Python:

.. code-block:: python

   import requests
   import json
   
   def check_zombies(hosts_data):
       """Check for zombies using the API."""
       response = requests.post(
           'http://localhost:8000/api/v1/zombie-detection',
           json={
               'hosts': hosts_data,
               'options': {
                   'include_summary': True,
                   'zombies_only': False
               }
           }
       )
       return response.json()
   
   def get_tracking_stats():
       """Get current tracking statistics."""
       response = requests.get(
           'http://localhost:8000/api/v1/zombies/tracking-stats'
       )
       return response.json()
   
   # Example usage
   with open('hosts.json') as f:
       hosts = json.load(f)
   
   results = check_zombies(hosts)
   print(f"Found {results['summary']['zombie_hosts']} zombies")
   
   stats = get_tracking_stats()
   print(f"New zombies: {len(stats['new_zombies'])}")

Configuration Examples
======================

States Configuration
--------------------

Enable only specific zombie types:

.. code-block:: json

   {
     "0": 0,
     "1A": 1,
     "1B": 0,
     "1C": 1,
     "2A": 1,
     "2B": 0,
     "3A": 0,
     "5": 1
   }

Service Configuration
---------------------

Production systemd environment:

.. code-block:: bash

   # /etc/default/zombie-detector
   ZOMBIE_DETECTOR_HOST=0.0.0.0
   ZOMBIE_DETECTOR_PORT=8000
   ZOMBIE_DETECTOR_WORKERS=4
   ZOMBIE_DETECTOR_LOG_LEVEL=INFO

Monitoring Examples
===================

Health Check Script
-------------------

.. code-block:: bash

   #!/bin/bash
   # health_check.sh
   
   HEALTH_URL="http://localhost:8000/api/v1/health"
   
   if curl -f -s "$HEALTH_URL" > /dev/null; then
       echo "OK: Zombie Detector API is healthy"
       exit 0
   else
       echo "CRITICAL: Zombie Detector API is down"
       exit 2
   fi

Performance Monitoring
----------------------

.. code-block:: python

   import time
   import requests
   
   def measure_detection_time(hosts_file):
       """Measure zombie detection performance."""
       with open(hosts_file) as f:
           hosts = json.load(f)
       
       start_time = time.time()
       
       response = requests.post(
           'http://localhost:8000/api/v1/zombie-detection',
           json={'hosts': hosts}
       )
       
       end_time = time.time()
       duration = end_time - start_time
       
       print(f"Processed {len(hosts)} hosts in {duration:.2f} seconds")
       print(f"Rate: {len(hosts)/duration:.1f} hosts/second")
       
       return response.json()

Troubleshooting Examples
========================

Debug High Memory Usage
-----------------------

.. code-block:: bash

   # Check tracking file sizes
   ls -lh /var/lib/zombie-detector/
   
   # Monitor process memory
   ps aux | grep zombie-detector
   
   # Clean up if needed
   zombie-detector cleanup --days 7

Debug API Issues
----------------

.. code-block:: bash

   # Check API logs
   sudo journalctl -u zombie-detector -f
   
   # Test with curl
   curl -v http://localhost:8000/api/v1/health
   
   # Check port availability
   netstat -tlnp | grep :8000

Automation Scripts
==================

Weekly Report Generation
------------------------

.. code-block:: bash

   #!/bin/bash
   # weekly_report.sh
   
   WEEK=$(date +%Y-W%V)
   REPORT_DIR="/reports/weekly"
   
   mkdir -p "$REPORT_DIR"
   
   # Generate weekly killed zombies report
   zombie-detector killed --since-hours 168 \
     --output "$REPORT_DIR/killed_week_$WEEK.json"
   
   # Generate summary statistics
   cat > "$REPORT_DIR/summary_$WEEK.md" << EOF
   # Weekly Zombie Report - $WEEK
   
   ## Summary
   - Report Period: $(date -d '7 days ago' +%Y-%m-%d) to $(date +%Y-%m-%d)
   - Generated: $(date)
   
   ## Killed Zombies
   EOF
   
   # Add killed zombie count
   KILLED_COUNT=$(jq '.killed_zombies_count' "$REPORT_DIR/killed_week_$WEEK.json")
   echo "- Total Resolved: $KILLED_COUNT zombies" >> "$REPORT_DIR/summary_$WEEK.md"

Batch Processing
----------------

.. code-block:: python

   import json
   import glob
   import requests
   from pathlib import Path
   
   def process_host_files(pattern):
       """Process multiple host files."""
       files = glob.glob(pattern)
       results = {}
       
       for file_path in files:
           print(f"Processing {file_path}...")
           
           with open(file_path) as f:
               hosts = json.load(f)
           
           response = requests.post(
               'http://localhost:8000/api/v1/zombie-detection',
               json={'hosts': hosts, 'options': {'include_summary': True}}
           )
           
           results[file_path] = response.json()
           
           # Log summary
           summary = results[file_path]['summary']
           print(f"  {summary['zombie_hosts']}/{summary['total_hosts']} zombies")
       
       return results
   
   if __name__ == "__main__":
       results = process_host_files("/data/hosts_*.json")
       
       with open("batch_results.json", "w") as f:
           json.dump(results, f, indent=2)