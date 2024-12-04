import logging

from typing import List, Any
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.conf import settings

from djpsa.sync.models import SyncJob

logger = logging.getLogger(__name__)

CREATED = 1
UPDATED = 2
SKIPPED = 3


def get_synchronizer(model_class, **kwargs):
    sync_class = settings.PROVIDER.sync_factory(model_class)
    return sync_class(**kwargs)


def log_sync_job(f):
    def wrapper(*args, **kwargs):
        sync_instance = args[0]
        created_count = updated_count = deleted_count = skipped_count = 0
        sync_job = SyncJob()
        sync_job.start_time = timezone.now()
        sync_job.entity_name = sync_instance.get_model_name()
        sync_job.synchronizer_class = \
            sync_instance.__class__.__name__

        if sync_instance.full:
            sync_job.sync_type = 'full'
        else:
            sync_job.sync_type = 'partial'

        sync_job.save()

        try:
            created_count, updated_count, skipped_count, deleted_count = \
                f(*args, **kwargs)
            sync_job.success = True
        except Exception as e:
            sync_job.message = str(e.args[0])
            sync_job.success = False
            raise
        finally:
            sync_job.end_time = timezone.now()
            sync_job.added = created_count
            sync_job.updated = updated_count
            sync_job.skipped = skipped_count
            sync_job.deleted = deleted_count
            sync_job.save()

        return created_count, updated_count, skipped_count, deleted_count

    return wrapper


class InvalidObjectException(Exception):
    """
    If for any reason an object can't be created (for example, it references
    an unknown foreign object, or is missing a required field), raise this
    so that the synchronizer can catch it and continue with other records.
    """
    pass


class SyncResults:
    """Track results of a sync job."""

    def __init__(self):
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.deleted_count = 0
        self.synced_ids = set()


class Synchronizer:
    lookup_key = 'id'
    model_class = None
    client_class = None
    last_updated_field = None
    bulk_prune = True

    def __init__(self,
                 full: bool = False,
                 conditions: List = None,
                 *args: Any,
                 **kwargs: Any):

        self.sync_settings = {
            'batch_size': 100,
        }
        if hasattr(settings, 'DJPSA_CONFIG'):
            self.request_settings.update(
                settings.DJPSA_CONFIG().get('sync', {}))

        conditions = conditions or []
        self.client = self.client_class(conditions)
        self.partial_sync_support = True
        self.batch_size = self.sync_settings['batch_size']
        self.full = full

    def get_sync_job_qset(self):
        return SyncJob.objects.filter(
            entity_name=self.get_model_name()
        )

    def get_model_name(self):
        return self.model_class.__bases__[0].__name__

    def _get_last_sync_job_time(self, sync_job_qset):
        if sync_job_qset.count() > 1 and self.last_updated_field \
                and not self.full and self.partial_sync_support:
            return self._format_job_condition(
                sync_job_qset.last().start_time.strftime(
                    '%Y-%m-%dT%H:%M:%S.%fZ'))
        return None

    @log_sync_job
    def sync(self):
        sync_job_qset = self.get_sync_job_qset().filter(success=True)

        last_sync_job_condition = self._get_last_sync_job_time(sync_job_qset)
        if last_sync_job_condition:
            self.client.add_condition(last_sync_job_condition)

        results = SyncResults()
        results = self.fetch_records(results)

        if self.full:
            # Set of IDs of all records prior to sync,
            # to find stale records for deletion.
            initial_ids = self._instance_ids()

            results.deleted_count = self.prune_stale_records(
                initial_ids, results.synced_ids
            )

        return results.created_count, results.updated_count, \
            results.skipped_count, results.deleted_count

    def _instance_ids(self):
        ids = self.model_class.objects.all().order_by('id') \
            .values_list('id', flat=True)
        return set(ids)

    def fetch_records(self, results, params=None):
        """
        For all pages of results, save each page of results to the DB.
        """
        page = 1
        while True:
            logger.info(
                'Fetching {} records, batch {}'.format(
                    self.get_model_name(), page)
            )
            response = self.client.get_page(
                page=page, batch_size=self.batch_size, params=params)
            records = self._unpack_records(response)
            self.persist_page(records, results)
            page += 1
            if len(records) < self.batch_size:
                # This page wasn't full, so there's no more records after
                # this page.
                break
        return results

    def persist_page(self, records, results):
        """Persist one page of records to DB."""
        for record in records:
            try:
                with transaction.atomic():
                    instance, result = self.update_or_create_instance(record)
                if result == CREATED:
                    results.created_count += 1
                elif result == UPDATED:
                    results.updated_count += 1
                else:
                    results.skipped_count += 1
            except (IntegrityError, InvalidObjectException) as e:
                logger.warning('{}'.format(e))

            results.synced_ids.add(record[self.lookup_key])

        return results

    def set_relations(self, instance, json_data):
        """
        Set the foreign key relations on the instance as
        defined in the related_meta dictionary.
        """
        for json_field, value in self.related_meta.items():
            model_class, field_name = value
            self._assign_relation(
                instance,
                json_data,
                json_field,
                model_class,
                field_name
            )

    def _assign_field_data(self, instance, api_instance):
        """
        Assign the field data from the API instance to the model instance,
        overriding this method in the subclass to handle the specific fields.
        """
        raise NotImplementedError

    def _format_job_condition(self, last_sync_time):
        raise NotImplementedError

    def _unpack_records(self, response):
        """
        Unpack the records from the response and return them as a list.
        """
        # Override this method to unpack the records from the response, as
        # the structure of the response varies between different PSAs and
        # even between different endpoints in the same PSA.
        return response

    @staticmethod
    def _assign_null_relation(instance, model_field):
        """
        Set the FK to null, but handle issues like the FK being non-null.

        This can happen because ConnectWise gives us records that point to
        non-existent records- such as activities whose assignTo fields point
        to deleted members.
        """
        try:
            setattr(instance, model_field, None)
        except ValueError:
            # The model_field may have been non-null.
            raise InvalidObjectException(
                "Unable to set field {} on {} to null, as it's required.".
                format(model_field, instance)
            )

    def _assign_relation(self, instance, json_data,
                         json_field, model_class, model_field):
        """
        Look up the given foreign relation, and set it to the given
        field on the instance.
        """
        relation_id = json_data.get(json_field)
        if relation_id is None:
            self._assign_null_relation(instance, model_field)
            return

        uid = relation_id

        try:
            related_instance = model_class.objects.get(pk=uid)
            setattr(instance, model_field, related_instance)
        except model_class.DoesNotExist:
            logger.warning(
                'Failed to find {} {} for {} {}.'.format(
                    json_field,
                    uid,
                    type(instance),
                    instance.id
                )
            )
            self._assign_null_relation(instance, model_field)

    def update_or_create_instance(self, api_instance):
        """
        Creates and returns an instance if it does not already exist.
        """
        result = None
        try:
            instance_pk = api_instance[self.lookup_key]
            instance = self.model_class.objects.get(pk=instance_pk)
        except self.model_class.DoesNotExist:
            instance = self.model_class()
            result = CREATED

        try:
            self._assign_field_data(instance, api_instance)

            if result == CREATED:
                instance.save()
            elif self._is_instance_changed(instance):
                instance.save()
                result = UPDATED
            else:
                result = SKIPPED
        except AttributeError as e:
            msg = "AttributeError while attempting to sync object {}." \
                  " Error: {}".format(self.model_class, e)
            logger.error(msg)
            raise InvalidObjectException(msg)
        except IntegrityError as e:
            msg = "IntegrityError while attempting to create {}." \
                  " Error: {}".format(self.model_class, e)
            logger.error(msg)
            raise InvalidObjectException(msg)

        if result == CREATED:
            result_log = 'Created'
        elif result == UPDATED:
            result_log = 'Updated'
        else:
            result_log = 'Skipped'

        logger.info('{}: {} {}'.format(
            result_log,
            self.get_model_name(),
            instance
        ))

        return instance, result

    def prune_stale_records(self, initial_ids, synced_ids):
        """
        Delete records that existed when sync started but were
        not seen as we iterated through all records from REST API.

        If bulk_prune is set to False, delete records one by one to
        prevent errors.
        """
        stale_ids = initial_ids - synced_ids
        deleted_count = 0
        if stale_ids:
            delete_qset = self.get_delete_qset(stale_ids)
            deleted_count = delete_qset.count()

            logger.info(
                'Removing {} stale records for model: {}'.format(
                    len(stale_ids), self.get_model_name(),
                )
            )

            # If bulk_prune is set to True, delete records in bulk
            if self.bulk_prune:
                try:
                    delete_qset.delete()
                except IntegrityError as e:
                    logger.exception(
                        'IntegrityError while attempting to delete {} '
                        'records. Error: {}'.format(
                            self.get_model_name(), e)
                    )
            else:
                for instance in delete_qset:
                    try:
                        instance.delete()
                    except IntegrityError as e:
                        logger.exception(
                            'IntegrityError while attempting to delete {} '
                            'records. Error: {}'.format(
                                self.get_model_name(), e)
                        )

        return deleted_count

    def get_delete_qset(self, stale_ids):
        return self.model_class.objects.filter(pk__in=stale_ids)

    def _is_instance_changed(self, instance):
        return instance.tracker.changed()
