from djpsa.halo.api import HaloAPIClient


class FieldInfoAPI(HaloAPIClient):
    endpoint = 'FieldInfo'

    def get_by_field_id(self, field_id):
        """Fetch a single FieldInfo by its ID."""
        endpoint_url = self._format_endpoint(record_id=field_id)
        return self.fetch_resource(endpoint_url=endpoint_url)
