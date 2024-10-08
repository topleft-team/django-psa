#!/usr/bin/env python
import django

from django.conf import settings
from django.core.management import call_command

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=(
        'djpsa.sync',
        'djpsa.halo',
    ),
    REDIS={
        'host': '',
        'port': '',
        'password': '',
        'db': '',
    },
)


def makemigrations():
    django.setup()
    # If a migration ever says to run makemigrations --merge, run this:
    # call_command('makemigrations', 'sync', '--merge')
    # (And consider adding --merge to this script.)
    call_command('makemigrations')


if __name__ == '__main__':
    makemigrations()
