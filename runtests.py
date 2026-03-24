#!/usr/bin/env python
import sys
import environ
import subprocess

from django.conf import settings
from django.core.management import call_command
from django.test.utils import get_runner
import django
import tempfile

DEBUG = True
tmp_media = tempfile.TemporaryDirectory()
env = environ.Env()


def djpsa_configuration():
    return {
        'timeout': 30.0,
        'max_attempts': 3,
        'keep_completed_hours': 24,
        'batch_query_size': 400,
    }


settings.configure(
    DEBUG=True,
    ALLOWED_HOSTS=('testserver',),
    INSTALLED_APPS=(  # Including django.contrib apps prevents warnings during
        # tests.
        'djpsa.sync.apps.SyncConfig',
        'djpsa.halo.apps.HaloConfig',
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.sessions',
    ),
    DATABASES={
        # TODO need to figure out something for multiple PSA support
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'djpsa-test.sqlite',
        },
    },
    # Member avatar tests like to save files to disk,
    # so here's a temporary place for them.
    MEDIA_ROOT=tmp_media.name,
    USE_TZ=True,  # Prevent 'ValueError: SQLite backend does not support
    # timezone-aware datetimes when USE_TZ is False.'
    # ROOT_URLCONF='djconnectwise.tests.urls',
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    },
    HALO_API="https://test.halopsa.com/",
    HALO_CLIENT_ID="fake_client_id",
    HALO_CLIENT_SECRET="fake_client_secret",
    DJPSA_CONF_CALLABLE=djpsa_configuration,
    HALO_AUTHORISATION_SERVER="https://example.com/",
    HALO_RESOURCE_SERVER="https://example.com/",
    REDIS={
        'host': env('REDIS_HOST', default=str('127.0.0.1')),
        'port': env('REDIS_PORT', default=6379),
        'password': env('REDIS_PASSWORD', default=str('')),
        'db': env('REDIS_DB', default=0),
    },
)


def _setup():
    """Configure Django stuff for tests."""
    django.setup()
    # Set up the test DB, if necessary.
    # Note that the test DB is not deleted before or after a test,
    # which speeds up subsequent tests because migrations
    # don't need to be run. But if you run into any funny errors,
    # you may want to remove the DB file and start fresh.
    # The DB file is stored in settings.DATABASES['default']['NAME'].
    call_command('migrate')
    # Clear out the test DB
    call_command('flush', '--noinput')


def exit_on_failure(command, message=None):
    if command:
        sys.exit(command)


def flake8_main():
    print('Running: flake8')
    _call = ['flake8'] + ['.']
    command = subprocess.call(_call)

    print("Failed: flake8 failed." if command else "Success. flake8 passed.")
    return command


def suite():
    """
    Set up and return a test suite. This is used in `python setup.py test`.
    """
    _setup()
    runner_cls = get_runner(settings)
    return runner_cls().build_suite(test_labels=None)


if __name__ == '__main__':
    _setup()
    exit_on_failure(flake8_main())
    call_command('test')
    # To run specific tests, try something such as:
    # call_command('test', 'djconnectwise.tests.test_api')  # noqa: E501
