import time
import redis
import logging
import requests
from contextlib import contextmanager

from django.conf import settings

logger = logging.getLogger(__name__)

ONE_HOUR = 3600
TOKEN_TIMEOUT = 30


redis_client = redis.StrictRedis(
        host=settings.REDIS['host'],
        port=settings.REDIS['port'],
        password=settings.REDIS['password'],
    )


@contextmanager
def redis_lock(lock_name, timeout=TOKEN_TIMEOUT+1):
    # If its timing out on the request, then the 1-second buffer
    # should be enough to let the request finish, and it can
    # release the lock itself
    lock = redis_client.lock(lock_name, timeout=timeout)
    acquired = lock.acquire(blocking=True)
    try:
        yield acquired
    finally:
        if acquired:
            lock.release()


def get_saved_token():
    token_data = redis_client.hgetall('halo_token')
    if not token_data:
        return None

    token = token_data.get(b'token')
    expiry = token_data.get(b'expiry')

    # Check if the token has expired
    if expiry and float(expiry) > time.time():
        return token.decode('utf-8')

    # Token expired, remove it
    rm_token()
    return None


def save_token(token):
    logger.debug('Saving token to Redis')
    # Subtract some time for buffer, say 60 seconds
    expiry_time = time.time() + ONE_HOUR - 60
    redis_client.hset('halo_token',
                      mapping={'token': token, 'expiry': expiry_time})


def rm_token():
    redis_client.delete('halo_token')


def get_token():
    with redis_lock('halo_token_lock'):
        # Check if a valid token is already available, may
        # have been fetched by another worker thread while we
        # were waiting
        token = get_saved_token()
        if token:
            return token

        # No valid token, get a new one
        token = get_new_access_token()
        save_token(token)
        return token


def get_new_access_token():
    logger.debug('Getting new access token')
    token_url = '{}auth/token'.format(settings.HALO_API)
    response = requests.post(
        token_url,
        data={
            'grant_type': 'client_credentials',
            'client_id': settings.HALO_CLIENT_ID,
            'client_secret': settings.HALO_CLIENT_SECRET,
            'scope': 'all',
        },
        timeout=TOKEN_TIMEOUT,
    )
    response.raise_for_status()
    token = response.json()['access_token']

    return token
