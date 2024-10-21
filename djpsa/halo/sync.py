import logging

from django.utils import timezone
from dateutil.parser import parse
from djpsa.sync.sync import Synchronizer

# README #
#
# "response_key"
#    The Halo API is very inconsistent, the response_key field is used to
#     specify the key in the response that contains the data we want to unpack.
#
#     Where when the response is just a list with no key, the response_key is
#     omitted from the class. ResponseKeyMixin should be applied to any class
#     that requires the response_key field.
#
# "lookup_key"
#    Some records need to be tracked by a different field than id for the
#     primary key. For example, the priority model uses priorityid as the
#     primary key, so the lookup_key is set to 'priorityid'. This is because
#     in the Halo API the 'id' seems to be a large alphanumeric string, and
#     isn't used on the ticket model.

logger = logging.getLogger(__name__)


def empty_date_parser(date_time):
    # Halo API returns a date of 1/1/1900 or earlier as an empty date.
    # This will set the model fields as None if it is an impossible date.
    # Set to 1980 in case they also do 1950 or something and I haven't seen it.
    if date_time:
        date_time = timezone.make_aware(parse(date_time), timezone.utc)
        return date_time if date_time.year > 1980 else None


class ResponseKeyMixin:
    response_key = None

    def _unpack_records(self, response):
        records = response[self.response_key]
        return records


class HaloSynchronizer(Synchronizer):

    def _format_job_condition(self, last_sync_time):
        return {
            self.last_updated_field: last_sync_time
        }


class HaloChildFetchRecordsMixin:
    parent_model_class = None
    parent_field = None

    def fetch_records(self, results, params=None):
        params = params or {}

        batch = 1
        for object_id in self.parent_object_ids:
            logger.info(
                'Fetching {} records, batch {}'.format(
                    self.get_model_name(), batch)
            )
            params.update(self.format_parent_params(object_id))
            response = self.client.fetch_resource(params=params)
            records = self._unpack_records(response)
            self.persist_page(records, results)
            batch += 1

        return results

    @property
    def parent_object_ids(self):
        object_ids = self.parent_model_class.objects.all() \
            .values_list('id', flat=True)

        return object_ids

    def format_parent_params(self, object_id):
        return {
            self.parent_field: object_id
        }
