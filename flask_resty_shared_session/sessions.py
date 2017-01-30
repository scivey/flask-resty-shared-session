# -*- coding: utf-8 -*-

# adapted from flask-session; see https://github.com/fengsp/flask-session
# original code is (c) 2014 by Shipeng Feng,
# released under BSD license.

# adaptations (c) 2017 by Scott Ivey, also under BSD license.

import sys
from uuid import uuid4
import json
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin
from werkzeug.datastructures import CallbackDict
from itsdangerous import Signer, BadSignature, want_bytes


PY2 = sys.version_info[0] == 2
if not PY2:
    text_type = str
else:
    text_type = unicode


def total_seconds(td):
    return td.days * 60 * 60 * 24 + td.seconds


class ServerSideSession(CallbackDict, SessionMixin):
    """Baseclass for server-side based sessions."""

    def __init__(self, initial=None, sid=None, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        if permanent:
            self.permanent = permanent
        self.modified = False


class RedisSession(ServerSideSession):
    pass



class SessionInterface(FlaskSessionInterface):

    def _generate_sid(self):
        return str(uuid4())

    def _get_signer(self, app):
        if not app.secret_key:
            return None
        salt = getattr(app, 'session_cookie_salt', 'flask-resty-session')
        return Signer(app.secret_key, salt=salt,
                      key_derivation='hmac')


class NullSessionInterface(SessionInterface):
    """Used to open a :class:`flask.sessions.NullSession` instance.
    """

    def open_session(self, app, request):
        return None


class RedisSessionInterface(SessionInterface):
    """Uses the Redis key-value store as a session backend.

    .. versionadded:: 0.2
        The `use_signer` parameter was added.

    :param redis: A ``redis.Redis`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    """

    serializer = json
    session_class = RedisSession

    def __init__(self, redis, key_prefix, use_signer=True, permanent=True):
        if redis is None:
            from redis import Redis
            redis = Redis()
        self.redis = redis
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=self.permanent)
        if self.use_signer:
            signer = self._get_signer(app)
            if signer is None:
                return None
            try:
                sid_as_bytes = signer.unsign(sid)
                sid = sid_as_bytes.decode()
            except BadSignature:
                sid = self._generate_sid()
                return self.session_class(sid=sid, permanent=self.permanent)

        if not PY2 and not isinstance(sid, text_type):
            sid = sid.decode('utf-8', 'strict')
        value = self.redis.get(self._get_redis_data_key(sid))
        if value is not None:
            try:
                data = self.serializer.loads(value)
                return self.session_class(data, sid=sid)
            except:
                return self.session_class(sid=sid, permanent=self.permanent)
        return self.session_class(sid=sid, permanent=self.permanent)

    def _get_redis_data_key(self, session_id):
        return '%s:data:%s' % (self.key_prefix, session_id)

    def _get_redis_groups_key(self, session_id):
        return '%s:groups:%s' % (self.key_prefix, session_id)

    def _get_redis_signature_key(self, session_id):
        return '%s:signature:%s' % (self.key_prefix, session_id)

    def _get_session_keys(self, session_id):
        return [
            self._get_redis_data_key(session_id),
            self._get_redis_groups_key(session_id),
            self._get_redis_signature_key(session_id)
        ]

    def regenerate(self, session):
        if session.sid:
            self.redis.delete(*self._get_session_keys(session.sid))
        session.sid = self._generate_sid()
        session.modified = True

    def destroy(self, session):
        if session.sid:
            self.redis.delete(*self._get_session_keys(session.sid))
        session.sid = None

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if not session.sid:
            response.delete_cookie(app.session_cookie_name,
                                   domain=domain, path=path)
            return

        # Modification case.  There are upsides and downsides to
        # emitting a set-cookie header each request.  The behavior
        # is controlled by the :meth:`should_set_cookie` method
        # which performs a quick check to figure out if the cookie
        # should be set or not.  This is controlled by the
        # SESSION_REFRESH_EACH_REQUEST config flag as well as
        # the permanent flag on the session itself.
        # if not self.should_set_cookie(app, session):
        #    return

        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        serialized_session = self.serializer.dumps(dict(session))

        if self.use_signer:
            session_cookie_val = self._get_signer(app).sign(want_bytes(session.sid))
            session_signature = session_cookie_val[session_cookie_val.index('.')+1:]
        else:
            session_cookie_val = session.sid
            session_signature = ''

        session_data_key = self._get_redis_data_key(session.sid)
        session_groups_key = self._get_redis_groups_key(session.sid)
        session_sig_key = self._get_redis_signature_key(session.sid)
        ttl = total_seconds(app.permanent_session_lifetime)

        pipeline = self.redis.pipeline()
        pipeline.setex(name=session_data_key,
            value=serialized_session,
            time=ttl
        )
        pipeline.setex(name=session_sig_key,
            value=session_signature,
            time=ttl
        )
        pipeline.delete(session_groups_key)
        group_ids = session.get('groups', None)
        if group_ids:
            group_ids = list(set(group_ids))
            pipeline.sadd(session_groups_key, *group_ids)
            pipeline.expire(session_groups_key, time=ttl)
        pipeline.execute()
        response.set_cookie(app.session_cookie_name, session_cookie_val,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure)

