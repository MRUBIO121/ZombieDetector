# Zombie Detector

> **🔗 For complete documentation, visit: [Zombie Detector Documentation](docs/_build/html/index.html)**

A sophisticated system for detecting and tracking "zombie" hosts in infrastructure environments using multi-criteria analysis and basic tracking.

## 🚀 Quick Start

### Installation

```bash
git clone <repo>
cd zombie-detector
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Basic Usage

```bash
# CLI Detection
zombie-detector detect example.json --summary

# REST API Server
zombie-detector-api
# Visit: http://localhost:8000/docs
```

### Example

```bash
# Analyze your data
zombie-detector detect data.json --summary --verbose

# Expected output:
# Total hosts: 10
# Zombie hosts: 8 (80%)
# Classification breakdown:
# • 2A (Ghoul): 4 hosts
# • 1A (Wraith): 2 hosts
# • 2B (Revenant): 2 hosts
```

## 🎯 Key Features

- **🔍 Multi-Criteria Detection**: 5 advanced zombie detection algorithms
- **📊 Real-time Tracking**: Lifecycle monitoring and historical analysis
- **🚀 FastAPI REST API**: Modern async API with auto-documentation
- **📈 Kafka Integration**: Enterprise messaging with SSL/SASL auth support
- **🔧 Flexible Configuration**: Extensive customization options

## 📋 Detection Criteria

The system uses 5 core criteria combined into sophisticated patterns:

1. **Recent CPU Decrease** - Sudden performance drops
2. **Recent Network Traffic Decrease** - Reduced network activity  
3. **Sustained Low CPU** - Consistently low utilization
4. **Excessively Constant RAM** - Unchanging memory patterns
5. **Daily CPU Profile Lost** - Missing expected activity

**Classification System**: Generates codes like `2A` (Ghoul), `1A` (Wraith), `3C` (Lich) based on active criteria combinations.

## 📖 Documentation Structure

| Document | Description |
|----------|-------------|
| [📚 **Full Documentation**](docs/_build/html/index.html) | Complete user guide and API reference |
| [⚡ **Quick Start**](docs/_build/html/quickstart.html) | Get running in 5 minutes |
| [🔧 **API Reference**](docs/_build/html/api/index.html) | REST API documentation |
| [🔨 **Developer Guide**](docs/_build/html/developer/index.html) | Contributing and development setup |
| [⚙️ **Configuration**](docs/_build/html/configuration.html) | Advanced configuration options |

## 🌐 API Endpoints

When running the API server (`zombie-detector-api`):

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **Health Check**: <http://localhost:8000/api/v1/health>

### Core Endpoints

```bash
POST /api/v1/zombie-detection    # Detect zombies
GET  /api/v1/zombies/stats       # Tracking statistics  
GET  /api/v1/zombies/killed      # Recently resolved zombies
GET  /api/v1/zombies/{id}/lifecycle  # Zombie history
```

## 🏗️ Architecture

```
zombie_detector/
├── api/                    # FastAPI REST API
├── core/                   # Detection algorithms
│   ├── classifier.py       # Zombie classification
│   ├── processor.py        # Data processing
│   ├── zombie_tracker.py   # Lifecycle tracking
│   └── zombie_publisher.py # Kafka integration
├── config/                 # Configuration
└── utils/                  # Utilities
```

## 🚀 Production Deployment

### Quick Deploy

```bash
# RPM/DEB Installation
sudo rpm -ivh zombie-detector-*.rpm
sudo systemctl enable zombie-detector
sudo systemctl start zombie-detector

# Docker (coming soon)
docker run -p 8000:8000 zombie-detector:latest
```

### Configuration

```ini
# /etc/zombie-detector/zombie-detector.ini
[api]
host = 0.0.0.0
port = 8000

[kafka]
enabled = true
bootstrap_servers = kafka.example.com:9093
security_protocol = SASL_SSL
```

## 🧪 Development

```bash
# Development setup
git clone <repo>
cd zombie-detector
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Build docs
cd docs && make html
```

## 📊 Example Results

```json
{
  "total_hosts": 10,
  "zombie_hosts": 8,
  "summary": {
    "2A": {"count": 4, "alias": "Mummy"},
    "1A": {"count": 2, "alias": "Wraith"},
    "2B": {"count": 2, "alias": "Revenant"}
  }
}
```

## 📞 Support

- **📧 Email**: [dayron.fernandez@naudit.es](mailto:dayron.fernandez@naudit.es)
- **📖 Documentation**: [Full Documentation](docs/_build/html/index.html)
- **💬 API Help**: Visit `/docs` when API is running

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## ⚡ TL;DR

```bash
# Install and run on a venv
pip install -e .
zombie-detector detect your-data.json --summary

# Or use API
zombie-detector-api
curl -X POST http://localhost:8000/api/v1/zombie-detection \
  -H "Content-Type: application/json" \
  -d @your-data.json

# Example request (make sure your-data.json uses correct field names):
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
    ],
    "states": {
      "0": 0,
      "1A": 1,
      "1B": 1,
      "1C": 1,
      "1D": 1,
      "1E": 1
    },
    "options": {
      "include_summary": true,
      "zombies_only": false
    }
  }'

# Note:
# - For more details and examples, see [API Reference](localhost:8000/docs) when the service is running.
```

**➡️ [Read the Full Documentation](docs/_build/html/index.html) for detailed usage, configuration, and examples.**
