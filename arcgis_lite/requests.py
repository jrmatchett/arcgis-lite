import urllib.request
import urllib.parse
import json


def get(url, params):
    url = url.strip('/')
    params = {k: _string_value(v) for k,v in params.items()}
    params_encoded = urllib.parse.urlencode(params)
    url_params = f"{url}?{params_encoded}"
    with urllib.request.urlopen(url_params) as f:
        response = f.read().decode('utf-8')
    return _check_json(response)


def post(url, data):
    url = url.strip('/')
    data = {k: _string_value(v) for k,v in data.items()}
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    with urllib.request.urlopen(url, data_encoded) as f:
        response = f.read().decode('utf-8')
    return _check_json(response)


def _string_value(x):
    if x is None:
        return ''
    elif isinstance(x, bool):
        return str(x).lower()
    else:
        return str(x)


def _check_json(s):
    try:
        r = json.loads(s)
    except json.decoder.JSONDecodeError:
        r = None
    return r if isinstance(r, dict) or isinstance(r, list) else s
