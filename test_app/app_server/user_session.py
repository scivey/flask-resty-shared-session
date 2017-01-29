import flask
from itsdangerous import want_bytes

from app_server.user import User
from app_server.errors import NotLoggedIn

class UserSession(object):
    def __init__(self, user, flask_session=None, app=None):
        assert isinstance(user, User)
        flask_session = flask_session or flask.session
        app = app or flask.current_app
        self._flask_session = flask_session
        self._user = user
        self._app = app

    @property
    def user(self):
        return self._user

    @property
    def data(self):
        return self._flask_session

    @property
    def sid(self):
        return want_bytes(self._flask_session.sid)

    @classmethod
    def get_current_or_fail(cls):
        email = flask.session.get('username', None)
        if email is None:
            raise NotLoggedIn()
        user = User.by_email(email)
        assert user is not None
        return cls(user=user)
