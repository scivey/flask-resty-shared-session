import uuid
from datetime import datetime
import flask

def make_id():
    return str(uuid.uuid4())

def now_timestamp():
    return datetime.utcnow().isoformat()

def cacheable_headers(**kwargs):
    from app_server.config import CACHEABLE_TIMEOUT_SECS
    headers = dict(kwargs)
    headers.update({
        'Cache-Control': 'max-age=%i' % CACHEABLE_TIMEOUT_SECS
    })
    return headers

def uncacheable_headers(**kwargs):
    headers = dict(kwargs)
    headers.update({
        'Cache-Control': 'no-cache'
    })
    return headers


def json_response(data, status, extra_headers=None):
    res = flask.jsonify(**data)
    res.status_code = status
    for k, v in (extra_headers or {}).items():
        res.headers[k] = v
    return res
