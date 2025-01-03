from django.core.management.base import BaseCommand, CommandError

from djpsa.api.exceptions import APIClientError


class BaseDeleteCommand(BaseCommand):
    help = 'Ensure callbacks are deleted on ConnectWise.'
    callback_handler = None

    def handle(self, *args, **options):
        handler = self.callback_handler()
        try:
            handler.ensure_deleted()
        except APIClientError as e:
            raise CommandError(e)
