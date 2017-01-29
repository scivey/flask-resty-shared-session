package = "resty-shared-session"
version = "0.1.0-1"

source = {
  url = "git://github.com/scivey/flask_resty_shared_session.git",
  tag = "v0.1.0-1",
}

description = {
  summary = "Redis-based sessions shared between flask and openresty",
  homepage = "https://github.com/scivey/flask_resty_shared_session.git",
  license = "MIT",
}

dependencies = {
  "lua >= 5.1",  -- lua-nginx-module needed
  "lua-resty-cookie >= 0.1.0-1",
}

build = {
    type = "builtin",
    modules = {
        ["resty.shared_session"] = "lib/resty/shared_session.lua"
    }
}
