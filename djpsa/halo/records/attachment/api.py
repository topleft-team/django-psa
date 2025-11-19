from djpsa.halo.api import HaloAPIClient


class AttachmentAPI(HaloAPIClient):
    endpoint = 'Attachment'

    def get(self, record_id):
        return self.request('GET', params={'ticket_id': record_id})
