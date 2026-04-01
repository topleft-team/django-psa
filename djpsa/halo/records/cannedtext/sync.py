from djpsa.halo import models
from djpsa.halo.records import api
from djpsa.halo import sync


class CannedTextSynchronizer(sync.HaloSynchronizer):
    model_class = models.CannedTextTracker
    client_class = api.CannedTextAPI

    related_meta = {
        'team_id': (models.Team, 'team'),
        'agent_id': (models.Agent, 'agent'),
    }

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.name = json_data.get('name') or ''
        instance.text = json_data.get('text') or ''
        self.set_relations(instance, json_data)
