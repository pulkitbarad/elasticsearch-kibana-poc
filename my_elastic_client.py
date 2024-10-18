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


def init_query_config(query_config_directory,query_config_filename):
    file_path = os.path.join(query_config_directory, query_config_filename)
    with open(file_path, 'r') as file:
        try:
            # Load JSON data from the file
            return json.load(file)
        except Exception as e:
            print(f"An unexpected error occurred while reading {query_config_filename}: {e}")
        finally:
            if file is not None:
                file.close()  # Ensure the file is closed


def test_connection(query_config):
    elastic_host, elastic_token_file_path = query_config["Elastic_Host"], query_config["Elastic_Service_Token_File"]
    es = init_client(elastic_host, elastic_token_file_path)
    # Check if the connection is successful
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

    if not elastic_client.indices.exists(index=index_name):
        elastic_client.indices.create(index=index_name)
        print(f"Index '{index_name}' created.")

    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        with open(file_path, 'r') as file:
            try:
                # Load JSON data from the file
                data = json.load(file)
                for category in data:
                    if isinstance(data[category], list):
                        for ele in data[category]:
                            ele = update_response_header(ele)
                    else:
                        data[category] = update_response_header(data[category])

                # Upload the JSON document to Elasticsearch
                elastic_client.index(index=index_name, body=data)
                print(f"Uploaded {filename} to index '{index_name}'.")

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
                failed_file_path = os.path.join(error_directory, filename)
                shutil.copy(file_path, failed_file_path)
                print(f"Copied failed file to '{failed_file_path}'.")
            except NotFoundError as e:
                print(f"Error uploading {filename}: Index not found. {e}")
            except ConnectionError as e:
                print(f"Error uploading {filename}: Connection issue. {e}")
            except Exception as e:
                print(f"An unexpected error occurred with {filename}: {e}")


def update_response_header(node):

    if node['ResponseMetadata'] \
        and node['ResponseMetadata']['HTTPHeaders'] \
            and node['ResponseMetadata']['HTTPHeaders']['date']:
        timestamp_str = node['ResponseMetadata']['HTTPHeaders']['date']

        node['ResponseMetadata']['HTTPHeaders']['date'] = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %Z")

    return node


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

    # Save each document to a separate JSON file
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

    # Ensure the output directory exists
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
