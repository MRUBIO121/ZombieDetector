===============
Developer Guide
===============

This section provides information for developers contributing to Zombie Detector.

.. toctree::
   :maxdepth: 2

Development Overview
===================

Zombie Detector is built with modern Python practices:

- **Python 3.9+** with type hints throughout
- **FastAPI** for REST API development  
- **Pydantic** for data validation
- **Pytest** for comprehensive testing
- **Black** for code formatting
- **MyPy** for static type checking

Architecture
============

**Core Components:**

.. code-block:: text

   zombie-detector/
   ├── zombie_detector/
   │   ├── core/           # Core detection logic
   │   ├── api/            # REST API endpoints
   │   ├── cli/            # Command-line interface
   │   ├── tracking/       # Zombie tracking system
   │   └── config/         # Configuration management
   ├── tests/              # Test suite
   ├── docs/               # Documentation
   └── packaging/          # Deployment packages

**Data Flow:**

1. **Input**: Host data via API or CLI
2. **Classification**: Multi-criteria zombie detection
3. **Tracking**: State persistence and lifecycle management
4. **Output**: Results via API response or Kafka events

Code Style
==========

We use **Black** for code formatting and **flake8** for linting:

.. code-block:: bash

   # Format code
   black zombie_detector/ tests/
   
   # Check style
   flake8 zombie_detector/ tests/
   
   # Run both
   make lint

**Code Standards:**

- Line length: 88 characters (Black default)
- Type hints required for all public functions
- Docstrings for all modules, classes, and functions
- Comprehensive error handling

Type Checking
=============

All code must pass **MyPy** type checking:

.. code-block:: bash

   # Run type checking
   mypy zombie_detector/
   
   # Check specific module
   mypy zombie_detector/core/processor.py

Testing
=======

**Test Categories:**

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Category
     - Location
     - Purpose
   * - Unit Tests
     - ``tests/test_*.py``
     - Test individual functions/classes
   * - Integration Tests
     - ``tests/integration/``
     - Test component interactions
   * - Performance Tests
     - ``tests/test_performance_*.py``
     - Performance benchmarking and bottleneck analysis
   * - API Tests
     - ``tests/api/``
     - REST API endpoint testing

**Running Tests:**

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=zombie_detector --cov-report=html
   
   # Run specific test categories
   pytest tests/test_core.py                           # Unit tests
   pytest tests/integration/                           # Integration tests
   pytest tests/test_performance_focused.py            # Focused performance tests
   pytest tests/test_performance_large_scale.py        # Large scale benchmarks
   
   # Run performance analysis
   python tests/test_performance_focused.py            # Detailed performance analysis

**Performance Testing:**

The performance test suite includes:

- **Focused Performance Tests** (``test_performance_focused.py``):
  - Bottleneck identification (tracking vs Kafka vs memory)
  - Function-level profiling
  - Memory usage analysis
  - Optimization recommendations

- **Large Scale Benchmarks** (``test_performance_large_scale.py``):
  - Scaling analysis (1K to 25K hosts)
  - Concurrency testing
  - Memory efficiency graphing
  - CLI vs API performance comparison

**Test Data Generation:**

.. code-block:: python

   # Generate realistic test data
   from tests.performance_utils import create_realistic_host_data
   
   hosts = create_realistic_host_data(
       count=10000,
       zombie_ratio=0.15,
       include_edge_cases=True
   )

Documentation
=============

Documentation is built with Sphinx:

.. code-block:: bash

   # Build HTML documentation
   cd docs/
   make html

   # Build PDF documentation
   make latexpdf

   # Clean build artifacts
   make clean

**Documentation Standards:**

- All public APIs must be documented
- Include code examples for complex features
- Update documentation with any API changes
- Performance documentation must include benchmarks

Release Process
===============

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Run full test suite (including performance tests)
4. Build documentation
5. Create git tag
6. Build packages (RPM/DEB)
7. Deploy to production

Contributing Workflow
====================

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests (including performance tests if relevant)
5. Update documentation
6. Run the full test suite
7. Submit a pull request

**Performance Impact Assessment:**

For changes that might affect performance:

.. code-block:: bash

   # Run performance baseline before changes
   pytest tests/test_performance_focused.py -v -s > before_results.txt
   
   # Make your changes
   
   # Run performance tests after changes
   pytest tests/test_performance_focused.py -v -s > after_results.txt
   
   # Compare results and document any performance impact
   diff before_results.txt after_results.txt

Code Quality Standards
======================

All contributions must:

- Pass all existing tests
- Include tests for new functionality
- Follow PEP 8 style guidelines (enforced by Black)
- Include type hints for new functions
- Update documentation as needed
- Maintain or improve code coverage
- Include performance tests for performance-critical changes

**Performance Requirements:**

New features must maintain these performance standards:

- Throughput: >500 hosts/second minimum
- Memory: <15KB per host maximum
- Processing time: <10ms per host target
- No memory leaks in long-running processes

**Performance Testing Integration:**

Performance tests are automatically run in CI/CD:

.. code-block:: yaml

   # Example GitLab CI configuration
   performance_test:
     stage: test
     script:
       - pytest tests/test_performance_focused.py --junit-xml=performance.xml
     artifacts:
       reports:
         junit: performance.xml

**Local Development Setup:**

.. code-block:: bash

   # Clone repository
   git clone https://gitlab.com/your-org/zombie-detector.git
   cd zombie-detector
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Run tests to verify setup
   pytest
   
   # Run performance baseline
   python tests/test_performance_focused.py