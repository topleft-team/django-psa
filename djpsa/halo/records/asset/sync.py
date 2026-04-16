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
