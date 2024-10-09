from djpsa.halo.records import models
from djpsa.halo.records import api
from djpsa.halo.sync import ResponseKeyMixin
from djpsa.sync.sync import Synchronizer


class ClientSynchronizer(ResponseKeyMixin, Synchronizer):
    response_key = 'clients'
    model_class = models.ClientTracker
    client_class = api.ClientAPI

    related_meta = {
        'main_site_id': (models.Site, 'site'),
    }

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'includeactive': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.inactive = json_data.get('inactive')
        instance.phone_number = json_data.get('main_phonenumber')

        self.set_relations(instance, json_data)
