from .errors import UserNotFound, BadPassword, LoginError, Unauthorized

_STATIC_USERS = (
    ('joe@gmail.com', 'jj612', ('one', 'three')),
    ('sam@gmail.com', 'itssam', ('two',)),
    ('maria@gmail.com', 'solvinproblems', tuple())
)

_STATIC_USERS = {u[0]: u for u in _STATIC_USERS}

class User(object):
    def __init__(self, email, password, groups=None):
        self.email = email
        self.password = password
        self.groups = set(list(groups or []))

    @classmethod
    def by_email(cls, email):
        user_data = _STATIC_USERS.get(email)
        if user_data is None:
            raise UserNotFound(email)
        assert user_data[0] == email
        return cls(email=user_data[0], password=user_data[1], groups=user_data[2])

    def check_password(self, pw):
        if pw != self.password:
            raise BadPassword()

    @classmethod
    def attempt_login(cls, email, password):
        try:
            user = cls.by_email(email)
            user.check_password(password)
            return user
        except (UserNotFound, BadPassword):
            raise LoginError(email)

    def is_group_member(self, group):
        return group in self.groups

    def verify_group_access(self, group):
        if not self.is_group_member(group):
            raise Unauthorized("Not a member of group '%s'" % group)
