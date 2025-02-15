from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from djpsa.api.exceptions import APIClientError


class Command(BaseCommand):
    help = 'Ensure callbacks are registered.'

    def handle(self, *args, **options):
        handler = settings.PROVIDER.callback_handler()
        try:
            handler.ensure_registered()
        except APIClientError as e:
            raise CommandError(e)
