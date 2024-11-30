# Weather ETL Pipeline

A robust weather monitoring system that collects data from Open-Meteo API based on temperature changes in Kuopio, Finland. The system is orchestrated using Apache Airflow and can be deployed both locally using Astro CLI or on Kubernetes.

## Project Overview

- **Location Monitored**: Kuopio, Finland (Lat: 62.8966, Long: 27.6786)
- **Data Source**: Open-Meteo Weather API
- **Trigger Condition**: Temperature change ≥ -10.0°C (detects significant cold fronts)
- **Monitored Parameters**:
  - Temperature
  - Wind Speed
  - Wind Direction
  - Weather Code
  - Timestamp

## Temperature Monitoring Details
The system is configured to detect significant temperature drops, particularly useful for:
- Cold front detection
- Severe weather warnings
- Winter weather monitoring
- Frost protection alerts

The current threshold of -10.0°C is specifically chosen to:
- Capture major temperature drops
- Monitor severe winter conditions
- Track significant weather pattern changes
- Provide early warning for extreme cold events

## Architecture

The project supports two deployment modes:

### 1. Local Development (Astro CLI)
- Uses Docker Compose under the hood
- Managed through `astro` commands
- Configuration in `airflow_settings.yaml`
- Easy local development and testing

### 2. Kubernetes Deployment
Located in the `k8s/` directory:
- `configmap.yaml`: Environment variables and Airflow configuration
- `airflow.yaml`: Airflow webserver and scheduler deployments
- `postgres.yaml`: PostgreSQL database deployment with persistent storage
- `redis.yaml`: Redis for Celery executor
- `dags-configmap.yaml`: DAG configurations
- `deploy.sh`: Deployment automation script

## Prerequisites

### Local Development
1. Astro CLI
2. Docker
3. Python 3.x

### Kubernetes Deployment
1. Kubernetes cluster (minikube for local testing)
2. kubectl
3. Docker

## Setup Instructions

### Local Development
```bash
# Initialize project
astro dev init

# Start the project
astro dev start

# Access Airflow UI
open http://localhost:8080
```

### Kubernetes Deployment
```bash
# Navigate to k8s directory
cd k8s

# Make deploy script executable
chmod +x deploy.sh

# Deploy to Kubernetes
./deploy.sh
```

## Project Structure
```
.
├── dags/
│   └── etlweather.py       # Main DAG file
├── k8s/                    # Kubernetes manifests
│   ├── airflow.yaml
│   ├── configmap.yaml
│   ├── dags-configmap.yaml
│   ├── deploy.sh
│   ├── postgres.yaml
│   └── redis.yaml
├── airflow_settings.yaml   # Local development settings
├── Dockerfile             # Custom Airflow image
└── README.md
```

## DAG Configuration
- Schedule: Hourly checks
- Poke Interval: Every 5 minutes
- Timeout: 1 hour
- Catchup: Disabled

## Environment Variables
- `LATITUDE`: 62.8966
- `LONGITUDE`: 27.6786
- `TEMP_THRESHOLD`: -10.0
- `API_CONN_ID`: 'open_meteo_api'
- `POSTGRES_CONN_ID`: 'postgres_default'

## Database Schema
- Automatic table creation
- Stores weather parameters with timestamps
- Tracks historical weather changes

## Deployment Configuration

### Setting Up Kubernetes Secrets
Before deploying, you need to:

1. Copy the template files:
```bash
cp k8s/configmap.template.yaml k8s/configmap.yaml
```

2. Set your environment variables in configmap.yaml:
- POSTGRES_PASSWORD
- AIRFLOW_SECRET_KEY

3. Never commit the actual configmap.yaml file with real credentials

### Environment Variables
Create a `.env` file in the k8s directory with:
```bash
POSTGRES_PASSWORD=your_secure_password
AIRFLOW_SECRET_KEY=your_secret_key
```

The deploy.sh script will use these variables to populate your configuration.

## Deployment Notes

### Local (Astro)
- Uses local Docker containers
- Easy development and testing
- Configuration through `airflow_settings.yaml`

### Kubernetes
- Scalable production deployment
- Persistent storage for PostgreSQL
- Celery executor with Redis
- LoadBalancer service for web UI access

## Monitoring and Maintenance

### Local
```bash
# View logs
astro dev logs

# Stop the project
astro dev stop
```

### Kubernetes
```bash
# View pod status
kubectl get pods -n weather-etl

# View logs
kubectl logs -n weather-etl deployment/airflow-webserver
```

## Security Considerations
- Sensitive data managed through Kubernetes secrets
- API credentials handled securely
- Database credentials managed through environment variables

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Create a pull request

## License
[MIT License](LICENSE)
