import os
import json
import shutil
from datetime import datetime
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError


def init_client(elastic_host, elastic_token_file_path):
    # Read the token from the file
    with open(elastic_token_file_path, 'r') as file:
        token = file.read().strip()

    # Create an Elasticsearch client instance using the service token
    return Elasticsearch(
        hosts=[elastic_host],
        api_key=token
    )


def init_query_config(query_config_directory, query_config_filename):
    file_path = os.path.join(query_config_directory, query_config_filename)
    print(file_path)
    with open(file_path, 'r') as file:
        try:
            return json.load(file)
        except Exception as e:
            print(f"An unexpected error occurred while reading {query_config_filename}: {e}")
        finally:
            if file is not None:
                file.close()


def test_connection(query_config):
    elastic_host, elastic_token_file_path = query_config["Elastic_Host"], query_config["Elastic_Service_Token_File"]
    es = init_client(elastic_host, elastic_token_file_path)
    if es.ping():
        print("Connected to Elasticsearch!")
    else:
        print("Failed to connect to Elasticsearch.")


def upload_data(
        elastic_client,
        input_directory,
        error_directory,
        index_name):

    os.makedirs(error_directory, exist_ok=True)

    if not elastic_client.indices.exists(index_name):
        elastic_client.indices.create(index_name)
        print(f"Index '{index_name}' created.")

    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    data = transform_response(data)
                    elastic_client.index(index_name, data)
                    print(f"Uploaded {filename} to index '{index_name}'.")

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {filename}: {e}")
                    handle_invalid_input(
                        error_directory=error_directory,
                        file_path=file_path,
                        filename=filename)
                    raise
                except NotFoundError as e:
                    print(f"Error uploading {filename}: Index not found. {e}")
                except ConnectionError as e:
                    print(f"Error uploading {filename}: Connection issue. {e}")
                except Exception as e:
                    print(f"An unexpected error occurred with {filename}: {e}")
        else:
            print(f"Skipping {file_path}, as it is not a file.")


def transform_response(data):
    response_timestamps = []

    if not data:
        return {"ResponseTimestamp": None}

    for category in data:
        if isinstance(data[category], list):
            for ele in data[category]:
                ele, response_timestamp = update_response_header(ele)
                if response_timestamp:  # Only add valid timestamps
                    response_timestamps.append(response_timestamp)
        else:
            data[category], response_timestamp = update_response_header(data[category])
            if response_timestamp:
                response_timestamps.append(response_timestamp)

    if response_timestamps:
        first_timestamp = response_timestamps[0]
        is_consistent = all(timestamp == first_timestamp for timestamp in response_timestamps)
        if is_consistent:
            data["ResponseTimestamp"] = first_timestamp
    else:
        data["ResponseTimestamp"] = None

    return data


def update_response_header(node):

    header_timestamp = None
    if node['ResponseMetadata'] \
        and node['ResponseMetadata']['HTTPHeaders'] \
            and node['ResponseMetadata']['HTTPHeaders']['date']:
        timestamp_str = node['ResponseMetadata']['HTTPHeaders']['date']

        header_timestamp = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %Z")
        node['ResponseMetadata']['HTTPHeaders']['date'] = header_timestamp

    return node, header_timestamp


def handle_invalid_input(error_directory, file_path, filename):

    failed_file_path = os.path.join(error_directory, filename)
    shutil.copy(file_path, failed_file_path)
    print(f"Copied failed file to '{failed_file_path}'.")


def download_data(
        elastic_client,
        search_name,
        index_name,
        output_directory,
        search_config_filters):
    query = build_query(search_config_filters)
    # Execute the search query
    response = elastic_client.search(index=index_name, body=query)
    hits = response['hits']['hits']
    print("Got %d Hits:" % response['hits']['total']['value'])

    save_search_result(search_name, hits, output_directory)


def build_query(search_config_filters):
    range_conditions = []
    for filter_config in search_config_filters:
        range_condition = {
            "range": {
                filter_config["date_path"]: {
                    "gte": filter_config["start_date"],
                    "lte": filter_config["end_date"]
                }
            }
        }
        range_conditions.append(range_condition)

    # Define the query to filter by the specified date ranges in OR conditions
    return {
        "query": {
            "bool": {
                "should": range_conditions
            }
        },
        "size": 10
    }


def save_search_result(search_name, hits, output_directory):

    output_directory = output_directory+search_name
    os.makedirs(output_directory, exist_ok=True)

    for hit in hits:
        document_id = hit['_id']
        document_data = hit['_source']

        output_file = \
            os.path.join(output_directory, f"{document_id}.json")\
            .replace(':', '') \
            .replace('-', '')
        with open(output_file, 'w') as json_file:
            json.dump(document_data, json_file, indent=2)

        print(f"Saved document {document_id} to {output_file}")


if __name__ == "__main__":

    query_config = init_query_config(
        query_config_directory="./",
        query_config_filename="query-config.json")

    elastic_client = init_client(
        elastic_host=query_config["elastic_host"],
        elastic_token_file_path=query_config["elastic_service_token_file"])

    if query_config["upload_config"]:
        for upload_config in query_config["upload_config"]:
            if upload_config["is_enabled"]:
                upload_data(
                    elastic_client=elastic_client,
                    input_directory=upload_config["input_directory"],
                    error_directory=upload_config["error_directory"],
                    index_name=upload_config["index_name"])

    if query_config["search_config"]:
        for search_config in query_config["search_config"]:
            if search_config["is_enabled"]:
                download_data(
                    elastic_client=elastic_client,
                    search_name=search_config["name"],
                    index_name=search_config["index_name"],
                    output_directory=search_config["output_directory"],
                    search_config_filters=search_config["filters"])


