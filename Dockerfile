# Use the official Elasticsearch image
FROM docker.elastic.co/elasticsearch/elasticsearch:8.15.3

# Copy the initialization script into the /usr/share/elasticsearch/config/ directory
COPY elasticsearch-init.sh /usr/share/elasticsearch/config/elasticsearch-init.sh

# Start Elasticsearch and run the initialization script
CMD ["/bin/bash", "-c", "/usr/share/elasticsearch/bin/elasticsearch & sleep 20 && /usr/share/elasticsearch/config/elasticsearch-init.sh && wait"]
