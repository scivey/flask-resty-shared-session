from __future__ import print_function
import unittest
import flask
import traceback
import sys
import json
from flask.ext.resty_shared_session import RestySharedSession
import redislite


def get_response_cookie(response, name):
    cookie_header = response.headers.get('Set-Cookie')
    if not cookie_header or (name not in cookie_header):
        return None
    start = cookie_header.index(name) + len(name) + 1
    end = cookie_header.index(';', start)
    return cookie_header[start:end]


class FlaskSessionTestCase(unittest.TestCase):
    
    def test_null_session(self):
        app = flask.Flask(__name__)
        RestySharedSession(app)
        def expect_exception(f, *args, **kwargs):
            try:
                f(*args, **kwargs)
            except RuntimeError as e:
                self.assertTrue(e.args and 'session is unavailable' in e.args[0])
            else:
                self.assertTrue(False, 'expected exception')
        with app.test_request_context():
            self.assertTrue(flask.session.get('missing_key') is None)
            expect_exception(flask.session.__setitem__, 'foo', 42)
            expect_exception(flask.session.pop, 'foo')

    def test_redis_session_1(self):
        app = flask.Flask(__name__)
        redis_conn = redislite.Redis('/tmp/session_redis.db')
        app.secret_key = 'secret key'
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_conn
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_PERMANENT'] = False

        RestySharedSession(app)
        @app.route('/set', methods=['POST'])
        def set():
            flask.session['value'] = flask.request.form['value']
            return 'value set'
        @app.route('/get')
        def get():
            return flask.session['value']
        @app.route('/delete', methods=['POST'])
        def delete():
            del flask.session['value']
            return 'value deleted'

        @app.errorhandler(500)
        def on_err(err):
            print("ERR: %r" % err)
            traceback.print_exception(*sys.exc_info())
            return "ERROR: %r" % err

        c = app.test_client()
        self.assertEqual(c.post('/set', data={'value': '42'}).data, b'value set')
        self.assertEqual(c.get('/get').data, b'42')
        c.post('/delete')
        

    def test_redis_session_2(self):
        app = flask.Flask(__name__)
        redis_conn = redislite.Redis('/tmp/session_redis.db')
        app.secret_key = 'secret key'
        app.session_cookie_name = 'session_cookie'
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_conn
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_KEY_PREFIX'] = 'redis_app_2'

        RestySharedSession(app)
        @app.route('/set-groups', methods=['POST'])
        def set_groups():
            body = json.loads(flask.request.data)
            flask.session['groups'] = body['groups']
            return flask.jsonify(status='ok')

        @app.route('/get-groups')
        def get_groups():
            return flask.jsonify(groups=list(flask.session.get('groups', [])))

        @app.route('/delete-groups', methods=['POST'])
        def delete_groups():
            if 'groups' in flask.session:
                del flask.session['groups']
            return flask.jsonify(status='deleted')

        @app.errorhandler(500)
        def on_err(err):
            print("ERR: %r" % err)
            traceback.print_exception(*sys.exc_info())
            return "ERROR: %r" % err

        c = app.test_client()
        response = c.post('/set-groups',
            data=json.dumps({'groups': ['one', 'two']}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual({'status': 'ok'}, json.loads(response.data))
        cookie = get_response_cookie(response, 'session_cookie')
        session_id = cookie[:cookie.index('.')]
        session_sig = cookie[cookie.index('.')+1:]
        stored_sig = redis_conn.get('redis_app_2:signature:' + session_id)
        self.assertEqual(session_sig, stored_sig)

        stored_groups = redis_conn.smembers('redis_app_2:groups:' + session_id)
        self.assertEqual(set(['one', 'two']), stored_groups)

        stored_data = redis_conn.get('redis_app_2:data:' + session_id)
        self.assertTrue(stored_data is not None)

        response = c.get('/get-groups')
        self.assertEqual({'groups': ['one', 'two']}, json.loads(response.data))

        response = c.post('/delete-groups')
        self.assertEqual({'status': 'deleted'}, json.loads(response.data))
