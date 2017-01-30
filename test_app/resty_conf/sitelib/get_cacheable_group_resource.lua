-- this would normally be imported as "resty.shared_session"
local shared_session = require "local_resty.shared_session"

local redis = require "resty.redis"


local function fail_500(err)
    ngx.log(ngx.ERR, err)
    ngx.status = 500
    ngx.say("500!")
    return ngx.exit(500)
end

local function fail_auth(status, err)
    ngx.log(ngx.ERR, err)
    ngx.status = status
    ngx.say("forbidden!")
    return ngx.exit(status)
end


local function get_session_redis()
    local redis_conn = redis:new()
    redis_conn:set_timeout(1000)

    local ok, err = redis_conn:connect("127.0.0.1", 6379)
    if not ok then
        return nil, err
    end

    local session_db_num = "12"
    local ok, err = redis_conn:select(session_db_num)
    if not ok then
        return nil, err
    end

    return redis_conn
end

local redis_conn, err = get_session_redis()
if not redis_conn then
    return fail_500(err)
end


local cookie_name = "app_session_cookie"
local key_prefix = "app_session_prefix"

local session, err = shared_session:new(redis_conn, cookie_name, key_prefix)
if not session then
    -- this means there's no session cookie.
    -- we should probably pass through to the app to allow login
    return fail_auth(401, err)
end

local ok, err = session:verify_signature()
if not ok then
    return fail_auth(403, err)
end

local ok, err = session:is_group_member(ngx.var.group_id)
if ok then
    return ngx.exec("@internal_cacheable_group_resource")
else
    return fail_auth(403, err)
end


