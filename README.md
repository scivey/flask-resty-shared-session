## flask-resty-shared-session

This is an adapted version of the [flask-session](https://github.com/fengsp/flask-session) Python package with a corresponding Lua rock for [OpenResty](https://openresty.org/en/).

This package allows you to share certain session information between a Flask application and nginx servers connected to the same Redis database.  It handles cookie signature verification, and can retrieve the username and a set of generic "groups" associated with the current session.

(c) 2017 Scott Ivey

See licensing at the end of this file (mixture of BSD and MIT)

### purpose

**flask-resty-shared-session**'s main goal is to enable nginx-side caching of resources that are otherwise uncacheable due to complicated permissions on the application side.  In particular, it's targeted toward "multitenant" applications with the following properties:
* Users belong to one or more "groups", "namespaces", "workspaces", etc.
* Users can only access resources for groups which they are a member of.
* Most groups consist of multiple users.
* The application has some relatively expensive backend calls scoped at the group level, e.g. analytics or various kinds of reporting on group-level resources.  Caching the results of these calls across all group members would improve performance.
* Because the nginx servers running in front of the application have no visibility into group membership, they are unable to determine which users have access to a given group resource.  This prevents any meaningful caching within nginx: all requests need to be satisfied by the application itself.

### installation
For the Python package:
```bash
pip install flask-resty-shared-session
```

For the Lua rock:
```bash
luarocks intall resty-shared-session
```

### example

There is a full example application [here](/test_app), which also serves as an integration test of the Python and Lua packages working together.  The entire directory is relevant, but [this is the main Flask server](test_app/app_server/application.py) and [this is the main nginx configuration](/test_app/resty_conf/nginx.conf).

### usage and API: flask-side

#### enabling in a Flask application

```python
def make_app():
    app = flask.Flask(__name__)
    app.secret_key = 'some-cookie-secret-key'
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_KEY_PREFIX'] = 'app_session_prefix'
    app.session_cookie_name = 'session'
    app.session_cookie_salt = 'app_session_salt'

    # in production, these settings are also a good idea:
    # app.config['SESSION_COOKIE_SECURE'] = True
    # app.config['SESSION_COOKIE_HTTPONLY'] = True

    from flask.ext.resty_shared_session import RestySharedSession
    RestySharedSession(app)
    return app
```

#### user login, logout and group assocation
Login and logout follows the same basic process as `flask-session`, which is also similar to how flask's builtin `Session` works.
The main difference is that the `"groups"` session key is treated specially: it should be set to a list of user groups which are relevant to access-control.

```python

LOGIN_FORM = """
    <form method="post">
        <p><input type="text" name="email"/></p>
        <p><input type="text" name="password"/></p>
        <p><input type="submit" value="Login"></p>
    </form>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        email = flask.request.form['email']
        password = flask.request.form['password']

        # validate the user's password here

        flask.current_app.session_interface.regenerate(flask.session)
        flask.session['username'] = email

        # these groups ids will be made available to nginx for access-control decisions
        flask.session['groups'] = ['group-one', 'group-two']
        return redirect(url_for('home'))
    else:
        return LOGIN_FORM

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    flask.current_app.session_interface.destroy(flask.session)
    return redirect(url_for('home'))

```

#### other
Aside from the above sections, the interface is identical to that in `flask-session`.


### usage and API: nginx-side

#### full example
```lua
local redis = require "resty.redis"
local shared_session = require "resty.shared_session"

local redis_conn = redis:new()
redis_conn:set_timeout(1000)

-- handle redis connection failure here
local ok, err = redis_conn.connect("127.0.0.1", 6379)

-- corresponds to `app.session_cookie_name` in the Flask application
local cookie_name = "app_session_cookie"

-- corresponds to `app.config["SESSION_KEY_PREFIX"]` in the Flask application
local key_prefix = "app_session_prefix"

local session, err = shared_session:new(redis_conn, cookie_name, key_prefix)
if not session then
    -- this mean's there's no active session.
    -- you would probably want to pass this through to an application endpoint
    -- for some kind of redirect.  Here, we just return an error.
    return ngx.exit(401)
end

local ok, err = session:verify_signature()
if not ok then
    -- the cookie signature doesn't match what the Flask application says it should be.
    -- this means someone is doing something bad.
    return ngx.exit(403)
end

local ok, err = session:is_group_member("some-group")
if ok then
    -- the session is allowed access to this resource.
    -- you would pass to an internal route here.
else
    return ngx.exit(403)
end

```

#### Lua API methods

##### `shared_session:new(redis_conn, cookie_name, key_prefix)`
Constructs a new shared session.  Its arguments are:
* `redis_conn`: an active connection from the `resty.redis` module.  You should have already selected the correct database on this connection: e.g. if the Flask application is using redis db #12, you should call `redis_conn:select(12)` before constructing the session object.
* `cookie_name`: the name of the session cookie.  This is often just `session`, and corresponds to the `app.session_cookie_name` attribute in the Flask application.
* `key_prefix`: the prefix used for redis-related session keys, corresponding to the `app.config["SESSION_KEY_PREFIX"]` setting.


##### `shared_session:verify_signature()`
Instance method.
* If the cookie's signature is valid, returns `true`.
* If the signature is invalid, returns `nil` and an error.

##### `shared_session:is_group_member(group_id)`
Instance method.
* If the current session is a member of the given group, returns true.
* Otherwise, returns `nil` and an error.


### approaches to nginx caching
The examples above show the basic session APIs, but gloss over how you would use this to cache API responses.  The [example application](/test_app) is useful here.

More generally, there are two basic approaches you could use.

#### using nginx's disk-backed cache
In this approach, you use an internal endpoint configured to use nginx's standard `ngx_http_proxy` module.  Access control decisions are made by a lua endpoint, which rejects invalid requests and passes the rest on to the internal endpoint.

```
http {
    proxy_cache_path /var/lib/something/some_cache levels=1:2 keys_zone=some_cache:10m inactive=10m max_size=1g;
    server {
        listen 80;
    }
    location @internal_cacheable_resource {
        proxy_cache group_cache;
        proxy_ignore_client_abort on;
        proxy_ignore_headers Set-Cookie;
        proxy_cache_min_uses 1;
        proxy_cache_valid 200 1d;
        proxy_cache_key "$host$request_uri";
        default_type application/json;
        proxy_pass http://upstream-hostname;
        more_clear_headers Set-Cookie;
    }
    location ~ ^/api/(?<group_name>.*)/something$ {
        content_by_lua_block {
            local group_name = ngx.var.group_name -- capture above

            -- ...
            -- instantiate a session and check permission -- see above
            -- ..

            local ok, err = session_instance.is_group_member(group_name)
            if ok then
                return ngx.exec("@internal_cacheable_resource")
            else
                return ngx.exit(403)
            end
        }
    }
}
```

#### using memcached or redis
In this approach, you use the same access control logic as the example above.  You then use [lua-resty-memcached](https://github.com/openresty/lua-resty-memcached) or [lua-resty-redis](https://github.com/openresty/lua-resty-redis) for the actual caching.  See their docs for examples.


### architectural requirements

**flask-resty-shared-session** requires a running Redis server.  It does not require an OpenResty installation, but without OpenResty it has no real advantage over the existing flask-session package.

### licensing
I generally use the MIT license for everything, but this is a combination of BSD and MIT.

The `flask_resty_shared_session` python package is largely derived from the existing [flask-session](https://github.com/fengsp/flask-session) package, which is BSD licensed.  Accordingly, everything under [/flask_resty_shared_session](/flask_resty_shared_session) (including the tests) is BSD licensed.

Everything else in this repo is MIT-licensed.

In practice, the BSD and MIT licenses are similar and are both commercial-friendly.  The distinction probably won't make a difference for you, but I'm not a lawyer.

 