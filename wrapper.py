import gzip
from flask import Flask, request, Response, jsonify, stream_with_context
import requests
import json
import time, uuid
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
        loaded_data = json.loads(data)
    except:
        loaded_data = {}

    try: 
        enable_streaing = loaded_data["stream"]
        print("Enable Streaming: " + str(enable_streaing))
    except Exception as e:
        print("Error: " + str(e))
        enable_streaing = False

    try: 
        msgs = loaded_data["messages"]
        if loaded_data["model"] == "openai/gpt-4o-mini":
            for msg in msgs: 
                print(msg)
                if msg["role"]:
                    if msg["content"].startswith("Available Tools:"):
                        # Get unix timestamp
                        timestamp = time.time()
                        id = str(uuid.uuid4().hex)[20:]

                        CUSTOM_REPONSE={
                            "id":f"gen-{timestamp}-la2CIxFcZy062cUrVpyw",
                            "provider":"OpenAI",
                            "model":"openai/gpt-4o-mini",
                            "object":"chat.completion",
                            "created": timestamp,
                            "choices":[
                                {
                                    "logprobs":None,
                                    "finish_reason":"stop",
                                    "index":0,
                                    "message":{
                                        "role":"assistant",
                                        "content":"```json\\n{}\\n```",
                                        "refusal":""
                                    }
                                }
                            ],
                            "system_fingerprint":"fp_f85bea6784",
                            "usage":{
                                "prompt_tokens":490,
                                "completion_tokens":5,
                                "total_tokens":495
                            }
                        }
                        resp = Response(json.dumps(CUSTOM_REPONSE), content_type='application/json')
                        resp.headers['Content-Type'] = 'application/json'
                        return resp
    except Exception as e:
        print("Error: " + str(e))
        pass

    try:
        if loaded_data["model"] == "gemini-1-5-pro":
            loaded_data["model"] == "google/gemini-pro-1.5"
        elif loaded_data["model"] == "claude-3-5-sonnet":
            loaded_data["model"] == "anthropic/claude-3.5-sonnet"
        elif loaded_data["model"] == "llama-3-1-405b":
            loaded_data["model"] == "meta-llama/llama-3.1-405b-instruct"

        print("Model is: " + loaded_data["model"])
        data = json.dumps(loaded_data).endcode('utf-8')
    except Exception as e:
        print("Error: " + str(e))
        pass

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

            print("----------- End of request -----------")

            return Response(stream_with_context(generate()), 
                            status=resp.status_code, 
                            headers=dict(resp.headers))
        else:
            # For non-streaming responses, handle potential gzip encoding
            content = resp.content
            if 'gzip' in resp.headers.get('Content-Encoding', '').lower():
                try:
                    content = gzip.decompress(content)
                except gzip.BadGzipFile:
                    # Content is not actually gzipped, use it as-is
                    pass

            # Remove the Content-Encoding header to prevent double decoding
            headers = dict(resp.headers)
            headers.pop('Content-Encoding', None)

            print(content)
            print("----------- End of request -----------")

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
