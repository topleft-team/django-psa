from typing import Any, List

from djpsa.halo.records.asset.api import AssetAPI


class AssetSynchronizer:
    client_class = AssetAPI

    def __init__(self,
                 full: bool = False,
                 conditions: List = None,
                 *args: Any,
                 **kwargs: Any):
        self.client = self.client_class(conditions or [])

    def fetch_by_id(self, asset_id, include_details=True):
        return self.client.get(
            record_id=asset_id,
            include_details=include_details,
        )

    def fetch_assets(
            self,
            client_id=None,
            username=None,
            search=None,
            page=1,
            page_size=50
    ):
        params = {
            'pageinate': True,
            'page_no': page,
            'page_size': page_size,
            'includechildren': True,
        }
        if client_id:
            params['client_id'] = client_id
        if username:
            params['username'] = username
        if search:
            params['search'] = search

        response = self.client.fetch_resource(params=params)
        return response.get('assets', [])
