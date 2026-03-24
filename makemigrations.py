#!/usr/bin/env python
import django
import argparse

from django.conf import settings
from django.core.management import call_command

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=(
        'djpsa.sync',
        'djpsa.halo',
    ),
)


def makemigrations(merge):
    django.setup()
    if merge:
        call_command('makemigrations', '--merge')
    else:
        call_command('makemigrations')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run makemigrations with optional --merge.')
    parser.add_argument(
        '--merge', action='store_true', help='Include the --merge option')
    args = parser.parse_args()
    makemigrations(args.merge)
