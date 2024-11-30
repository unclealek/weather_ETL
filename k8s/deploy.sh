#!/bin/bash

# Function to check if a pod is ready
wait_for_pod() {
    echo "Waiting for $1 pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=$1 --timeout=300s
}

# Create namespace
kubectl create namespace weather-etl

# Switch to the namespace
kubectl config set-context --current --namespace=weather-etl

# Apply ConfigMaps
echo "Applying ConfigMaps..."
kubectl apply -f configmap.yaml
kubectl apply -f dags-configmap.yaml

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f redis.yaml
wait_for_pod "redis"

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f postgres.yaml
wait_for_pod "postgres"

# Deploy Airflow components
echo "Deploying Airflow components..."
kubectl apply -f airflow.yaml
wait_for_pod "airflow-webserver"
wait_for_pod "airflow-scheduler"

# Get the Airflow webserver URL
echo "Getting Airflow webserver URL..."
minikube service airflow-webserver --url -n weather-etl

echo "Deployment complete! Use the URL above to access Airflow webserver"
