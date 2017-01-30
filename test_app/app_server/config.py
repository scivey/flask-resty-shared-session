import redis
import logging.config

class Configurator(object):
    CACHE_PROXY_URL = 'http://localhost:8089'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_SESSION_DB = 12
    SESSION_COOKIE_NAME = 'app_session_cookie'
    CACHE_TIMEOUT_SECS = 3

CONFIG = Configurator()

def session_redis():
    return redis.StrictRedis(
        host=CONFIG.REDIS_HOST,
        port=CONFIG.REDIS_PORT,
        db=CONFIG.REDIS_SESSION_DB
    )


def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {},
        'formatters': {
            'noisy': {
                'format': '%(name)s %(levelname)s %(process)d %(thread)d - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'noisy'
            }
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            }
        }
    })
