import json
import logging
import hmac
import hashlib
import base64

from braces import views
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings

from djpsa.halo.records.ticket.sync import TicketSynchronizer

logger = logging.getLogger(__name__)


class CallBackView(views.CsrfExemptMixin,
                   views.JsonRequestResponseMixin, View):

    CALLBACK_TYPES = {
        'ticket': TicketSynchronizer,
    }

    def post(self, request, *args, **kwargs):
        logger.debug(f"Received callback {request.path} {request.method}")

        received_token = request.headers['Token']

        computed_hash = hmac.new(
            settings.CALLBACK_SECRET.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).digest()
        computed_token = base64.b64encode(computed_hash).decode()

        if not hmac.compare_digest(computed_token, received_token):
            logger.error('Invalid token received')
            return HttpResponse(status=401)

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

                instance, _ = sync.update_or_create_instance(data.get(record_type))

                # Sync related records, actions, appointments, etc.
                sync.sync_related(instance)
                break

        if sync is None:
            # This is normal if we get a callback for a record type we don't
            # care about somehow.
            return HttpResponse(status=400)

        return HttpResponse(status=200)
