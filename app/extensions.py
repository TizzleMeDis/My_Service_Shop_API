from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
 
ma = Marshmallow()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["400 per day", "100 per hour", "10 per minute"]
)
cache = Cache(config={
    "DEBUG": True,
    'CACHE_TYPE': 'SimpleCache',
    "CACHE_DEFAULT_TIMEOUT": 30
})