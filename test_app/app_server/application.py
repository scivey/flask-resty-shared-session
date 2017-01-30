import flask
from flask import redirect, escape, url_for
from app_server.config import session_redis, setup_logging
from werkzeug.contrib.fixers import ProxyFix
from app_server.util import (
    make_id, now_timestamp
)
from app_server.user import User
from app_server.user_session import UserSession
from app_server.errors import LoginError, Unauthorized, NotLoggedIn
from app_server.config import CONFIG

class Status(object):
    NOT_LOGGED_IN = 401
    UNAUTHORIZED = 403


def make_app():
    from flask.ext.resty_shared_session import RestySharedSession
    app = flask.Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.secret_key = 'fishes'
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = session_redis()
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_KEY_PREFIX'] = 'app_session_prefix'
    app.session_cookie_name = CONFIG.SESSION_COOKIE_NAME
    app.session_cookie_salt = 'app_session_salt'

    # these settings are normally a good idea:
    # app.config['SESSION_COOKIE_SECURE'] = True
    # app.config['SESSION_COOKIE_HTTPONLY'] = True

    RestySharedSession(app)
    return app

app = make_app()


@app.route('/app', methods=['GET'])
def home():
    try:
        sess = UserSession.get_current_or_fail()
        return "Logged in as '%s'" % escape(sess.user.email)
    except NotLoggedIn:
        return "You are not logged in!"



LOGIN_FORM = """
    <form method="post">
        <p><input type="text" name="email"/></p>
        <p><input type="text" name="password"/></p>
        <p><input type="submit" value="Login"></p>
    </form>
"""

@app.route('/app/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        email = flask.request.form['email']
        password = flask.request.form['password']
        user = User.attempt_login(email, password)
        flask.current_app.session_interface.regenerate(flask.session)
        flask.session['username'] = email
        flask.session['groups'] = list(user.groups)
        return redirect(url_for('home'))
    return LOGIN_FORM


@app.route('/app/logout', methods=['GET', 'POST'])
def logout():
    flask.current_app.session_interface.destroy(flask.session)
    return redirect(url_for('home'))


@app.route('/app/api/v1/myself', methods=['GET'])
def myself_api():
    sess = UserSession.get_current_or_fail()
    return flask.jsonify({
        'email': sess.user.email
    })



def _make_resource_data(group_id, resource_id):
    return {
        'group_id': group_id,
        'resource_id': resource_id,
        'response_id': make_id(),
        'origin_timestamp': now_timestamp()
    }


@app.route('/app/api/v1/group/<group_id>/cacheable/<resource_id>', methods=['GET'])
def group_cacheable_resource_api(group_id, resource_id):
    sess = UserSession.get_current_or_fail()
    sess.user.verify_group_access(group_id)
    json_data = _make_resource_data(group_id, resource_id)
    response = flask.jsonify(**json_data)
    response.headers['Cache-Control'] = 'max-age=%i' % CONFIG.CACHE_TIMEOUT_SECS
    return response


@app.route('/app/group/<group_id>/cacheable/<resource_id>', methods=['GET'])
def group_cacheable_resource_page(group_id, resource_id):
    sess = UserSession.get_current_or_fail()
    sess.user.verify_group_access(group_id)
    doc = """
        <html>
        <h2>{group_id} CACHEABLE RESOURCE: {resource_id}</h2>
        <div>
            <p>response_id:        {response_id}</p>
            <p>origin_timestamp: {origin_timestamp}</p>
        </div>
        </html>
    """.format(**_make_resource_data(group_id, resource_id))
    response = flask.make_response(doc)
    response.headers['Cache-Control'] = 'max-age=%i' % CONFIG.CACHE_TIMEOUT_SECS
    return response


@app.route('/app/api/v1/group/<group_id>/uncacheable/<resource_id>', methods=['GET'])
def group_uncacheable_resource_api(group_id, resource_id):
    sess = UserSession.get_current_or_fail()
    sess.user.verify_group_access(group_id)
    json_data = _make_resource_data(group_id, resource_id)
    response = flask.jsonify(**json_data)
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/app/group/<group_id>/uncacheable/<page_name>', methods=['GET'])
def group_uncacheable_resource_page(group_id, page_name):
    sess = UserSession.get_current_or_fail()
    sess.user.verify_group_access(group_id)
    doc = """
        <html>
        <h2>{group_id} UNCACHEABLE PAGE: {page_name}</h2>
        <h3>You are: {user}</h3>
        <div>
            <p>render_id:        {render_id}</p>
            <p>render_timestamp: {render_timestamp}</p>
        </div>
        </html>
    """.format(user=sess.user.email,
        group_id=group_id,
        page_name=page_name,
        render_id=make_id(),
        render_timestamp=now_timestamp()
    )
    response = flask.make_response(doc)
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/', methods=['GET'])
def handle_404():
    return flask.jsonify(**{}), 404

@app.errorhandler(LoginError)
def login_error_handler(err):
    response = flask.make_response(LOGIN_FORM)
    response.status_code = Status.UNAUTHORIZED
    return response


@app.errorhandler(NotLoggedIn)
def handle_not_logged_in(err):
    return flask.jsonify(**{
        'error': str(err),
        'error_id': make_id()
    }), Status.NOT_LOGGED_IN

@app.errorhandler(Unauthorized)
def handle_unauthorized(err):
    return flask.jsonify(**{
        'error': str(err),
        'error_id': make_id()
    }), Status.UNAUTHORIZED


if __name__ == '__main__':
    setup_logging()
    app.run(host='0.0.0.0', port=5017, debug=True)
