import os

import requests

from djpsa.halo.api import HaloAPIClient

FILE_UMASK = 0o022


class AttachmentAPI(HaloAPIClient):
    endpoint = 'Attachment'

    def get(self, record_id):
        return self.request('GET', params={'ticket_id': record_id})

    def download_from_url(self, url, attachment_id, filename, path):
        """
        Download attachment from CDN URL and save to disk.
        """
        response = requests.get(url)
        response.raise_for_status()

        saved_filename = f'{attachment_id}-{filename}'
        file_path = os.path.join(path, saved_filename)

        previous_umask = os.umask(FILE_UMASK)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        os.umask(previous_umask)

        return saved_filename
