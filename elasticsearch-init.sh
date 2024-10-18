#!/bin/bash
set -e

# Wait for Elasticsearch to be fully started by checking its health endpoint
echo "Waiting for Elasticsearch to be ready..."
until curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"\|"status":"yellow"'; do
    echo "Elasticsearch is still starting..."
    sleep 10
done

# Generate the Kibana service account token
echo "Generating service account token for Kibana..."
if TOKEN=$(/usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/kibana default); then
    # Extract and save the token
    TOKEN_VALUE=$(echo "$TOKEN" | grep -oP '(?<=SERVICE_TOKEN elastic/kibana/default = ).*')
    echo $TOKEN_VALUE > /usr/share/elasticsearch/tmp/kibana-service-token.txt  # Store in /tmp
    echo "Service account token generated and stored at /usr/share/elasticsearch/tmp/kibana-service-token.txt."
else
    echo "Failed to generate service account token" >&2
fi
