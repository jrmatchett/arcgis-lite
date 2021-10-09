import urllib.request
import urllib.parse
import json


def url_get(url, params):
    url = url.strip('/')
    params = {k:v for k,v in params.items() if v is not None}
    params_encoded = urllib.parse.urlencode(params)
    url_params = f"{url}?{params_encoded}"
    with urllib.request.urlopen(url_params) as f:
        response = f.read().decode('utf-8')
    return json.loads(response)


def url_post(url, data):
    url = url.strip('/')
    data = {k:v for k,v in data.items() if v is not None}
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    with urllib.request.urlopen(url, data_encoded) as f:
        response = f.read().decode('utf-8')
    return json.loads(response)
