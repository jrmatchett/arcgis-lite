import json
import urllib.request
import urllib.parse


def get(url, params):
    url = url.strip('/')
    params = {k: string_valu(v) for k,v in params.items() if v}
    params_encoded = urllib.parse.urlencode(params)
    url_params = f"{url}?{params_encoded}"
    with urllib.request.urlopen(url_params) as f:
        response = f.read().decode('utf-8')
    return check_json(response)


def post(url, data):
    url = url.strip('/')
    data = {k: string_valu(v) for k,v in data.items() if v}
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    with urllib.request.urlopen(url, data_encoded) as f:
        response = f.read().decode('utf-8')
    return check_json(response)


def string_valu(x):
    return x if isinstance(x, str) else json.dumps(x, separators=(',', ':'))


def check_json(s):
    try:
        r = json.loads(s)
    except json.decoder.JSONDecodeError:
        r = None
    return r if isinstance(r, dict) or isinstance(r, list) else s
