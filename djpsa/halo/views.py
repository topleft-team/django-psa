import json
import logging

from braces import views
from django.views.generic import View
from django.http import HttpResponse

from djpsa.halo.records.ticket.sync import TicketSynchronizer

logger = logging.getLogger(__name__)


class CallBackView(views.CsrfExemptMixin,
                   views.JsonRequestResponseMixin, View):

    CALLBACK_TYPES = {
        'ticket': TicketSynchronizer,
    }

    def post(self, request, *args, **kwargs):
        logger.debug(f"Received callback {request.path} {request.method}")

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error('Error decoding JSON for callback: %s', e)
            return HttpResponse(status=400)

        sync = None

        for record_type, sync_class in self.CALLBACK_TYPES.items():
            # Searches for record type keys in data, i.e. if it's a ticket
            # callback, it will find 'ticket'.
            if record_type in data:
                sync = sync_class()

                sync.update_or_create_instance(data.get(record_type))
                break

        if sync is None:
            # This is normal if we get a callback for a record type we don't
            # care about somehow.
            return HttpResponse(status=404)

        return HttpResponse(status=200)
