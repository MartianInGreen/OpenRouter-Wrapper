import gzip
from flask import Flask, request, Response, jsonify, stream_with_context
import requests
import json
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
        enable_streaing = json.loads(data)["stream"]
        print("Enable Streaming: " + str(enable_streaing))
    except Exception as e:
        print("Error: " + str(e))
        enable_streaing = False

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
            stream=True,  # Enable streaming
            timeout=120  # Adjust timeout as needed
        )

        # Check if the response should be streamed
        if enable_streaing == True:
            # Create a streaming response
            def generate():
                for chunk in resp.iter_content(chunk_size=4096):
                    yield chunk

            return Response(stream_with_context(generate()), 
                            status=resp.status_code, 
                            headers=dict(resp.headers))
        else:
            # For non-streaming responses, handle potential gzip encoding
            content = resp.content
            if 'gzip' in resp.headers.get('Content-Encoding', '').lower():
                content = gzip.decompress(content)

            # Remove the Content-Encoding header to prevent double decoding
            headers = dict(resp.headers)
            headers.pop('Content-Encoding', None)

            return Response(content, resp.status_code, headers)

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
