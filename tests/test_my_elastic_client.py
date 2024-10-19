import pytest
import json
import os
from my_elastic_client import (
    init_client,
    init_query_config,
    upload_data,
    handle_invalid_input,
    transform_response,
    update_response_header,
)


def test_init_client(tmp_path):
    # Create a temporary token file
    token_file = tmp_path / "token.txt"
    token_file.write_text("your_api_key")

    elastic_host = "http://localhost:9200"
    client = init_client(elastic_host, str(token_file))

    assert client is not None


def test_init_query_config(tmp_path):
    # Create a temporary JSON configuration file
    config_file = tmp_path / "fake_config.json"
    config_file.write_text('{"key": "value"}')

    query_config = init_query_config(str(tmp_path), "fake_config.json")

    assert query_config == {"key": "value"}


# Test for handle_invalid_input
def test_handle_invalid_input(tmp_path):
    error_dir = tmp_path / "error_dir"
    error_dir.mkdir()

    source_file = tmp_path / "file.json"
    source_file.write_text('{"some": "data"}')

    handle_invalid_input(str(error_dir), str(source_file), "file.json")

    assert (error_dir / "file.json").exists()  # Check that the file was copied to the error directory


# Test for transform_response
def test_transform_response():
    input_data = {
        "category": {
            "ResponseMetadata": {
                "HTTPHeaders": {
                    "date": "Fri, 19 Oct 2024 12:00:00 GMT"
                }
            }
        }
    }
    transformed_data = transform_response(input_data)

    assert "ResponseTimestamp" in transformed_data


def test_transform_response_empty():
    input_data = {}
    transformed_data = transform_response(input_data)

    assert "ResponseTimestamp" in transformed_data


# Test for update_response_header
def test_update_response_header():
    node = {
        "ResponseMetadata": {
            "HTTPHeaders": {
                "date": "Fri, 19 Oct 2024 12:00:00 GMT"
            }
        }
    }
    updated_node, timestamp = update_response_header(node)

    assert timestamp is not None


def test_update_response_header_missing_date():
    node = {
        "ResponseMetadata": {
            "HTTPHeaders": {}
        }
    }
    updated_node, timestamp = update_response_header(node)

    assert timestamp is None


if __name__ == "__main__":
    pytest.main()
