============
Installation
============

System Requirements
===================

* **Python 3.8+**: Core runtime environment
* **systemd**: For service management (Linux systems only)
* **curl**: For API testing and health checks (optional)

Installation Methods
====================

From Source
-----------

.. code-block:: bash

   git clone https://repo1.naudit.es/santander-cantabria/zombie-detector.git
   cd zombie-detector
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .

From Package (RPM/DEB)
----------------------

RPM-based systems (RHEL, CentOS, Fedora):

.. code-block:: bash

   sudo rpm -ivh zombie-detector-0.1.0-1.noarch.rpm

DEB-based systems (Ubuntu, Debian):

.. code-block:: bash

   sudo dpkg -i zombie-detector_0.1.0_all.deb

Development Installation
------------------------

For development and testing:

.. code-block:: bash

   git clone https://repo1.naudit.es/santander-cantabria/zombie-detector.git
   cd zombie-detector
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"

Post-Installation Setup
=======================

After installation, configure the system:

1. **Configuration Files**: Edit ``/etc/zombie-detector/zombie-detector.ini``
2. **States Configuration**: Customize ``/etc/zombie-detector/states.json``
3. **Service Setup**: Enable the systemd service (package installations only)

.. code-block:: bash

   # Start the service
   sudo systemctl start zombie-detector

   # Enable auto-start on boot
   sudo systemctl enable zombie-detector

   # Check service status
   sudo systemctl status zombie-detector

Verification
============

Verify your installation:

.. code-block:: bash

   # Check CLI
   zombie-detector --help

   # Check API (if service is running)
   curl http://localhost:8000/api/v1/health

   # Test with example data
   zombie-detector detect example.json --summary