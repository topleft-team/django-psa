
import logging

from djpsa.halo import models
from djpsa.halo.records.fieldinfo import api
from djpsa.halo import sync
from djpsa.sync.sync import SyncResults, log_sync_job
from djpsa.sync.udf.utils import caption_to_snake_case
from djpsa.halo.utils import UDF_TYPE_MAP

logger = logging.getLogger(__name__)

UNSUPPORTED_REF_NAME = 'Unsupported custom field type, will not sync'


class FieldInfoSynchronizer(sync.HaloSynchronizer):
    model_class = models.UDFDefinition
    client_class = api.FieldInfoAPI

    @log_sync_job
    def sync(self):
        """
        For each FieldInfo reference, fetch the field definition
        from the Halo API and update_or_create the generic
        UDFDefinition.

        We are unable to determine through the API which custom fields
        are of interest to the user, so they will need to create a reference
        for each field they want to sync.
        """
        results = SyncResults()
        client = self.client_class()
        synced_names = set()

        for ref in models.FieldInfoReference.objects.all():
            try:
                api_data = client.get_by_field_id(ref.field_id)
                name = self._sync_field(ref, api_data, results)
                if name:
                    synced_names.add(name)
            except Exception as e:
                logger.warning(
                    "Failed to sync FieldInfo %s: %s", ref.field_id, e
                )

        # Delete UDFDefinitions that no longer have a matching reference.
        deleted_count, _ = models.UDFDefinition.objects.filter(
            record_type='ticket',
        ).exclude(name__in=synced_names).delete()
        results.deleted_count += deleted_count

        return (results.created_count, results.updated_count,
                results.skipped_count, results.deleted_count)

    def _sync_field(self, ref, api_data, results):
        label = api_data.get('label', '')

        # Update reference name so it shows in the form
        if label and ref.name != label:
            ref.name = label
            ref.save()

        snake_name = caption_to_snake_case(label)
        if not snake_name:
            logger.exception(
                "UDF name stripped became empty string: %s.", label
            )
            return ''

        halo_type = api_data.get('type')

        if halo_type not in UDF_TYPE_MAP:
            logger.info(
                "Skipping unsupported UDF type %s for field %s.",
                halo_type, label
            )
            ref.name = UNSUPPORTED_REF_NAME
            ref.save()
            return ''

        data_type, type_name = UDF_TYPE_MAP[halo_type]

        _, created = models.UDFDefinition.objects.update_or_create(
            record_type='ticket',
            name=snake_name,
            defaults={
                'display': label,
                'udf_type': type_name,
                'data_type': data_type,
                'extra': {},
            },
        )

        if created:
            results.created_count += 1
        else:
            results.updated_count += 1

        return snake_name

    def fetch_sync_by_id(self, field_id):
        """
        Fetch and sync a single FieldInfo by its Halo field ID.
        Creates or updates both the FieldInfoReference and
        UDFDefinition. Raises ValueError if the type is unsupported
        or the label can't be parsed.
        """
        client = self.client_class()
        api_data = client.get_by_field_id(field_id)

        ref, _ = models.FieldInfoReference.objects.get_or_create(
            field_id=field_id,
        )

        label = api_data.get('label', '')
        if label and ref.name != label:
            ref.name = label
            ref.save()

        snake_name = caption_to_snake_case(label)
        if not snake_name:
            raise ValueError(
                f"Could not parse field name from '{label}'."
            )

        halo_type = api_data.get('type')
        if halo_type not in UDF_TYPE_MAP:
            raise ValueError(
                f"Unsupported custom field type for '{label}'."
            )

        data_type, type_name = UDF_TYPE_MAP[halo_type]
        models.UDFDefinition.objects.update_or_create(
            record_type='ticket',
            name=snake_name,
            defaults={
                'display': label,
                'udf_type': type_name,
                'data_type': data_type,
                'extra': {},
            },
        )
        return ref

    def _format_job_condition(self, last_sync_time):
        return None
