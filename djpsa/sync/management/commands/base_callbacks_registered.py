from django.core.management.base import BaseCommand, CommandError

from djpsa.api.exceptions import APIClientError


class BaseRegisterCommand(BaseCommand):
    help = 'Ensure callbacks are registered on ConnectWise.'
    callback_handler = None

    def handle(self, *args, **options):
        handler = self.callback_handler()
        try:
            handler.ensure_registered()
        except APIClientError as e:
            raise CommandError(e)
