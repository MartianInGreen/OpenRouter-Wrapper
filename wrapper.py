from flask import Flask, request, Response, jsonify
import requests, json
from urllib.parse import urljoin

app = Flask(__name__)

# Base URL of the OpenRouter API
OPENROUTER_API_BASE = "https://openrouter.ai/api/"

# Open Router API endpoint for models.json
with open('models.json', 'r') as f:
    CUSTOM_MODELS_RESPONSE = json.load(f)

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    # Check if the request is to /api/v1/models
    if path == "v1/models":
        return jsonify(CUSTOM_MODELS_RESPONSE)

    # Construct the full URL to the OpenRouter API
    url = urljoin(OPENROUTER_API_BASE, path)

    # Forward the query parameters
    params = request.args

    # Forward the headers, excluding Host to avoid issues
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    # Forward the data (for POST, PUT, PATCH requests)
    data = request.get_data()
    print(str(data))

    try:
        # Make the request to the OpenRouter API with the same method
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=120  # Adjust timeout as needed
        )

        response = Response(resp.content, resp.status_code, headers)
        return response

    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., network errors)
        return jsonify({
            "error": "Failed to connect to OpenRouter API",
            "message": str(e)
        }), 502

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "OpenRouter API Wrapper is running.",
        "documentation": "Provide your API requests to /api/<path> endpoints."
    })

