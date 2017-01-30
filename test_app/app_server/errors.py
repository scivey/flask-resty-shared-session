
class AuthError(RuntimeError):
    pass

class LoginError(AuthError):
    pass

class BadPassword(LoginError):
    pass

class UserNotFound(LoginError):
    pass

class Unauthorized(AuthError):
    pass

class NotLoggedIn(AuthError):
    pass
