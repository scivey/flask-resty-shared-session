-- this would normally be imported as "resty.shared_session"
local shared_session = require "local_resty.shared_session"

local redis = require "resty.redis"
local red = redis:new()
red:set_timeout(1000)

local ok, err = red:connect("127.0.0.1", 6379)
if not ok then
    ngx.log(ngx.ERR, err)
    return ngx.exit(500)
end

local ok, err = red:select("12")
if not ok then
    ngx.log(ngx.ERR, err)
    return ngx.exit(500)
end


local cookie_name = "app_session_cookie"
local key_prefix = "app_session_prefix"

local session, err = shared_session:new(red, cookie_name, key_prefix)
if not session then
    ngx.log(ngx.ERR, err)
    ngx.say("bad!")
    return ngx.exit(500)
end

local ok, err = session:verify_signature()
if not ok then
    ngx.log(ngx.ERR, err)
    return ngx.exit(403)
end

local ok, err = session:is_group_member(ngx.var.group_id)
if not ok then
    ngx.log(ngx.ERR, err)
    ngx.say("unauthorized for this group!")
    return ngx.exit(403)
end

return ngx.exec("@internal_cacheable_group_page")

