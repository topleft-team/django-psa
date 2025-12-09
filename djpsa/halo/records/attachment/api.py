import base64
import os

import requests

from djpsa.halo.api import HaloAPIClient

FILE_UMASK = 0o022


class AttachmentAPI(HaloAPIClient):
    endpoint = 'Attachment'

    def get(self, record_id):
        return self.request('GET', params={'ticket_id': record_id})

    def upload(self, ticket_id, filename, content_type, file_content):
        """
        Upload an attachment to a ticket.

        Args:
            ticket_id: The ticket ID to attach to
            filename: The filename
            content_type: The MIME type (e.g. 'text/plain', 'image/png')
            file_content: The file content as bytes

        Returns:
            The API response
        """
        base64_content = base64.b64encode(file_content).decode('utf-8')
        data_uri = f'data:{content_type};base64,{base64_content}'

        return self.request('POST', body=[{
            'ticket_id': ticket_id,
            'filename': filename,
            'data_base64': data_uri,
        }])

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
