from elasticsearch import Elasticsearch

# Path to the token file on your local machine
token_file_path = './local_tokens/kibana-service-token.txt'

# Read the token from the file
with open(token_file_path, 'r') as file:
    token = file.read().strip()

# Create an Elasticsearch client instance using the service token
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    api_key=token
)

# Check if the connection is successful
if es.ping():
    print("Connected to Elasticsearch!")
else:
    print("Failed to connect to Elasticsearch.")

doc = {
    'author': 'John Doe',
    'text': 'Elasticsearch is awesome!',
    'timestamp': '2024-10-18T12:00:00'
}
# res = es.index(index='test-index', id=1, document=doc)
# print(res['result'])

res = es.search(index='test-index', body={'query': {'match': {'author': 'John'}}})
print("Got %d Hits:" % res['hits']['total']['value'])
for hit in res['hits']['hits']:
    print(hit['_source'])
