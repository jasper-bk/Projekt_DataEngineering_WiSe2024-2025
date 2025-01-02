# Project DataEngineering WiSe2024-2025 Documentation

## Overview
This repository contains all resources necessary for deploying a Helm chart and building multiple microservices using `podman-compose`. The project integrates Kafka, PostgreSQL, and custom services to create a comprehensive system. Below, you will find details about the repository structure, deployment instructions, and available service endpoints.

---

## Repository Structure

```
.
├── helm-chart-deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── charts
│   │   └── custom-helm-chart
│   │       ├── README.md
│   │       ├── values.yaml
│   │       ├── Chart.yaml
│   │       └── templates
│   │           ├── pvc.yaml
│   │           ├── custom-conf-configmap.yaml
│   │           ├── cronjob.yaml
│   │           ├── application-conf-secret.yaml
│   │           ├── custom-conf-secret.yaml
│   │           ├── global-conf-secret.yaml
│   │           ├── deployment.yaml
│   │           ├── statefulset.yaml
│   │           └── service.yaml
├── custom_microservices_build
│   ├── compose.yml
│   ├── automatic_order_microservice
│   │   ├── Containerfile
│   │   ├── requirements.txt
│   │   └── src
│   │       └── main.py
│   ├── aggregation_reporting_microservice
│   │   ├── Containerfile
│   │   ├── requirements.txt
│   │   └── src
│   │       └── main.py
│   └── [other_microservices]...
├── .gitignore
└── README.md
```

### Key Files
- **`helm-chart-deployment/values.yaml`**: Configuration for Helm deployment.
- **`helm-chart-deployment/charts`**: Contains Helm chart dependencies (Kafka, PostgreSQL, AKHQ, and custom charts).
- **`custom_microservices_build/compose.yml`**: Podman Compose file for building and theoretically also running the microservices. Running functionality is not used because it will run in K8S cluster.
- **Microservice Directories**: Each microservice includes:
  - `Containerfile`: For building the service container.
  - `requirements.txt`: Python dependencies for the service.
  - `src/main.py`: The main application logic.

---

## Deployment Instructions

### Prerequisites
- Helm installed
- Kubernetes cluster (e.g., K3S for local deployment)
- Podman and `podman-compose` installed (only for building of services. For deployment its not required)

### Deploying with Helm
From the repository root, run the following commands:

1. Update Helm dependencies:
    ```bash
    helm dependency update helm-chart-deployment/
    ```

2. Install the Helm chart:
    ```bash
    helm install my-release helm-chart-deployment/
    ```

3. Retrieve deployed service endpoints:
    ```bash
    kubectl get svc | grep LoadBalancer
    ```

### Service endpoints on local Development with K3S
For local deployments on a single-node K3S cluster:

- Kafka Monitoring: [http://localhost:8080/](http://localhost:8080/)
- Database: `jdbc:postgresql://localhost:5432/postgres`
- Kafka Broker: `localhost:9094`

### Building Microservices with Podman

1. Navigate to `custom_microservices_build/`.
2. Use `podman-compose` to build and run the microservices:
    ```bash
    podman-compose -f custom_microservices_build/compose.yml build
    ```

## Notes
- For custom configurations, modify the `values.yaml` file in `helm-chart-deployment` or the `compose.yml` file in `custom_microservices_build`.
- The Helm chart release name (`my-release`) from the installation command needs to align with the configured hostnames in the `values.yaml` file. In case of using another release name, also search and replace the `my-release` with your newly chosen release name