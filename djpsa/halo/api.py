import logging
import requests
from django.conf import settings
from django.core.cache import cache

from djpsa.api.client import APIClient
from djpsa.api.exceptions import APIError
from djpsa.utils import LockNotAcquiredError, redis_lock

logger = logging.getLogger(__name__)


HALO_TOKEN_CACHE_NAME = 'halo_token'
CACHE_EXPIRE_TIME = 3540  # 1 hour less 1 minute so the token expires
# locally before expiring remotely, so we avoid access denied errors.
TOKEN_REQUEST_TIMEOUT = 30
TOKEN_LOCK_LIFETIME = TOKEN_REQUEST_TIMEOUT + 1
TOKEN_LOCK_ACQUIRE_TIMEOUT = 60


class HaloAPICredentials:
    def __init__(self, authorisation_server, client_id, client_secret):
        self.authorisation_server = authorisation_server
        if not self.authorisation_server.endswith('/'):
            self.authorisation_server += '/'
        self.client_id = client_id
        self.client_secret = client_secret


class HaloAPIClient(APIClient):
    endpoint = None

    def __init__(self,
                 conditions=None,
                 credentials=None,
                 resource_server=None,
                 token_locking=True):
        super().__init__(conditions)
        if not credentials:
            credentials = HaloAPICredentials(
                settings.HALO_AUTHORISATION_SERVER,
                settings.HALO_CLIENT_ID,
                settings.HALO_CLIENT_SECRET,
            )

        self.resource_server = resource_server or settings.HALO_RESOURCE_SERVER
        if not self.resource_server.endswith('/'):
            self.resource_server += '/'

        self.token_fetcher = HaloAPITokenFetcher(credentials, token_locking)

    def check_auth(self):
        return bool(self.token_fetcher.get_token(use_cache=False))

    def get_page(self, page=None, batch_size=None, params=None):
        params = params or {}
        if page:
            params['page_no'] = page
        if batch_size:
            params['page_size'] = batch_size
        return self.fetch_resource(params=params)

    def get(self, record_id):
        return self.request('GET', params={'search_id': record_id})

    def create(self, data):
        # Halo API expects a list of records, even if we're only creating one
        return self.request('POST', body=[data])

    def update(self, record_id, data):
        data['id'] = record_id
        return self.request('POST', body=[data])

    def delete(self, record_id):
        return self.request(
            'DELETE',
            endpoint_url=self._format_endpoint(record_id)
        )

    def _format_endpoint(self, record_id=None):

        if record_id:
            return '{}{}/{}'.format(
                self.resource_server, self.endpoint, record_id)

        return '{}{}'.format(self.resource_server, self.endpoint)

    def _format_params(self, params=None):
        params = params or {}
        request_params = {}

        for condition in self.conditions:
            request_params.update(condition)

        request_params.update(params)

        if 'page' in request_params:
            request_params['page_size'] = params.get('batch_size', 100)
            request_params['pageinate'] = True

        return request_params

    def _request(
            self, method, endpoint_url, headers=None, params=None, **kwargs):
        token = self.token_fetcher.get_token()
        token_header = {'Authorization': f'Bearer {token}'}

        # If kwargs contains headers, update it with the token, if not,
        # create it
        if headers:
            headers.update(token_header)
        else:
            headers = token_header

        # Make the actual request
        response = requests.request(
            method,
            endpoint_url,
            headers=headers,
            params=params,
            timeout=self.request_settings['timeout'],
            **kwargs
        )

        # If the token is invalid, refresh it and retry
        if response.status_code == 401:
            token = self.token_fetcher.get_token()
            headers['Authorization'] = f'Bearer {token}'
            response = requests.request(
                method,
                endpoint_url,
                headers=headers,
                params=params,
                **kwargs
            )

        return response


class HaloAPITokenFetcher:
    def __init__(self, credentials, token_locking=True):
        self.credentials = credentials
        self.token_locking = token_locking

    def get_token(self, use_cache=True):
        if use_cache:
            token = self._get_saved_token()
            if token:
                return token

        if self.token_locking:
            try:
                with redis_lock(
                        'halo_token_lock',
                        TOKEN_LOCK_LIFETIME,
                        TOKEN_LOCK_ACQUIRE_TIMEOUT):
                    # Check if a valid token is already available. May
                    # have been fetched by another worker thread while we
                    # were waiting.
                    if use_cache:
                        token = self._get_saved_token()
                        if token:
                            return token

                    # No valid token- get a new one.
                    # We'll save it even if we didn't use the cache, because
                    # it's possible getting a new token invalidates prior
                    # tokens.
                    return self._get_new_token_and_save()
            except LockNotAcquiredError as e:
                logger.error(f"Could not acquire lock: {e}")
        else:
            # Get a new token without locking
            return self._get_new_token_and_save()

    def _get_saved_token(self):
        return cache.get(HALO_TOKEN_CACHE_NAME)

    def _get_new_token_and_save(self):
        logger.debug('Getting new access token')
        token_url = '{}token'.format(self.credentials.authorisation_server)
        try:
            response = requests.post(
                token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.credentials.client_id,
                    'client_secret': self.credentials.client_secret,
                    'scope': 'all',
                },
                timeout=TOKEN_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            token = response.json()['access_token']
        except requests.RequestException as e:
            logger.error(f"Failed to get new token: {e}")
            raise APIError('{}'.format(e))

        cache.set(HALO_TOKEN_CACHE_NAME, token, CACHE_EXPIRE_TIME)
        return token
