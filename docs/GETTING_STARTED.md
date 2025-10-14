# Getting Started with UCIP

This guide will help you set up and run the Urban Carbon Intelligence Platform locally.

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Node.js 18+ (for dashboard)
- PostgreSQL with PostGIS
- Redis
- MinIO

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/UCIP.git
cd UCIP
```

### 2. Setup Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Setup Environment Variables

```bash
cp env.example .env
# Edit .env with your configuration
```

### 4. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with PostGIS (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- MLflow (port 5000)
- Prometheus (port 9090)
- Grafana (port 3001)

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Or create tables manually
python -c "from features.store.postgis_store import PostGISStore; PostGISStore().create_tables()"
```

### 6. Start the API Server

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 7. Start the Dashboard (Optional)

```bash
cd dashboard
npm install
npm run dev
```

Dashboard will be available at http://localhost:3000

## Verify Installation

### Test API

```bash
curl http://localhost:8000/health
```

### Test Database Connection

```bash
python -c "from features.store.postgis_store import PostGISStore; store = PostGISStore(); print('Connected!')"
```

### Test Redis

```bash
python -c "from features.store.redis_store import RedisFeatureStore; store = RedisFeatureStore(); print('Connected!')"
```

### Test MinIO

```bash
python -c "from features.store.minio_store import MinIOStore; store = MinIOStore(); print('Connected!')"
```

## Running Examples

### Ingest Satellite Data

```bash
python ingestion/satellite/sentinel_ingest.py
```

### Run Building Segmentation

```bash
python models/cv/building_segmentation.py
```

### Generate Emissions Forecast

```bash
python models/time_series/emissions_forecast.py
```

### Parse Policy Document

```bash
python models/nlp/policy_parser.py
```

### Detect Hotspots

```bash
python fusion/hotspot_detector.py
```

### Chat with AI Assistant

```bash
python chatbot/assistant.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

## Accessing Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **MLflow**: http://localhost:5000
- **MinIO Console**: http://localhost:9001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Default Credentials

- **MinIO**: minioadmin / minioadmin
- **Grafana**: admin / admin
- **PostgreSQL**: ucip / ucip_dev_password

## Troubleshooting

### Docker Services Won't Start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql -h localhost -U ucip -d ucip
```

### Redis Connection Error

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping
```

## Next Steps

- Read the [Architecture Guide](architecture.md)
- Explore the [API Reference](api.md)
- Review [Model Documentation](models.md)
- Check out [Deployment Guide](deployment.md)

## Getting Help

- GitHub Issues: https://github.com/yourusername/UCIP/issues
- Documentation: https://ucip.readthedocs.io
- Email: your.email@psu.edu

