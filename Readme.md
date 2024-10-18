# Elasticsearch and Kibana Setup with Docker Compose

This repository provides a setup for **Elasticsearch** and **Kibana** using Docker Compose. It includes the generation of a **service account token** for Kibana, ensuring secure communication between the two services.

## Prerequisites

Make sure you have the following installed on your machine:
- Docker
- Docker Compose

## Services Overview

- **Elasticsearch**: Version `8.15.3`, configured as a single-node setup with memory limits set to 2GB.
- **Kibana**: Version `8.15.3`, using a service account token to authenticate with Elasticsearch.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure the Setup

- **Service Token Generation**: This setup generates a service account token for Kibana using Elasticsearch's built-in tool, and the token is stored in a shared volume between the Elasticsearch and Kibana containers.

### 3. Start the Docker Containers

Run the following command to build and start the services:

```bash
docker-compose up --build -d
```

### 4. Verify the Setup

#### Check Elasticsearch Health

Once the services are running, you can check the health of your Elasticsearch cluster by accessing:

```
http://localhost:9200/_cluster/health?pretty
```

#### Check Kibana

Kibana should be available at:

```
http://localhost:5601
```

### 5. Verify the Generated Token

If needed, you can verify that the service account token for Kibana was generated correctly:

```bash
docker exec -it elasticsearch bash
cat /tmp/kibana-service-token.txt
```

The token will be used by Kibana to authenticate with Elasticsearch.

## Docker Compose Configuration

### `docker-compose.yml`

This is the main configuration file that defines the Elasticsearch and Kibana services:


## Service Account Token Generation

### `elasticsearch-init.sh`

This script waits for Elasticsearch to fully start and generates a service account token for Kibana.


## Stopping and Cleaning Up

To stop the services, run:

```bash
docker-compose down
```

This will stop the running containers and remove them. To remove persistent data, also include the `-v` flag to remove volumes:

```bash
docker-compose down -v
```
