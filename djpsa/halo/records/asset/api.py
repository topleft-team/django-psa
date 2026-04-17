from djpsa.halo.api import HaloAPIClient


class AssetAPI(HaloAPIClient):
    endpoint = 'Asset'

    def get(self, record_id, include_details=False):
        params = {}
        if include_details:
            params['includedetails'] = 'true'

        return self.request(
            'GET',
            endpoint_url=self._format_endpoint(record_id),
            params=params,
        )
