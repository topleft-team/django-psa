from djpsa.halo import models
from djpsa.halo.records import api
from djpsa.halo import sync


class StatusSynchronizer(sync.HaloSynchronizer):
    model_class = models.StatusTracker
    client_class = api.StatusAPI

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.colour = json_data.get('colour')
