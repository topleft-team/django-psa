from djpsa.halo.api import HaloAPIClient


class MilestoneAPI(HaloAPIClient):
    # Read-only: the endpoint answers `Allow: GET`. Milestones are written
    # through the project ticket instead — see MilestoneSynchronizer.
    endpoint = 'Milestone'
