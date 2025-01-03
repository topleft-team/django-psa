import json

from django.core.management.base import BaseCommand, CommandError

from djpsa.api.exceptions import APIClientError


class BaseListCommand(BaseCommand):
    help = 'List our existing callbacks on ConnectWise.'
    callback_handler = None

    def handle(self, *args, **options):
        handler = self.callback_handler()
        try:
            callbacks = handler.get_callbacks()
        except APIClientError as e:
            raise CommandError(e)

        # Write out the entire response in JSON; it's not that hard to read.
        self.stdout.write(json.dumps(callbacks, indent=2))
