import logging

from djpsa.platform.udf.utils import caption_to_snake_case

logger = logging.getLogger(__name__)

# Types come in from Halo API as integers, so we will convert them
# for QOL for developers. The types are system defined, so
# they will not change.
UDF_TYPE_NAME_MAP = {
    0: 'Text Field',
    1: 'Memo Field',
    2: 'Single Selection',
    3: 'Multiple Selection',
    4: 'Date',
    5: 'Time',
    6: 'Checkbox',
    10: 'Rich Text',
}

DATA_TYPE_MAP = {
    0: 'string',      # Text Field
    1: 'string',      # Memo Field
    2: 'string',      # Single Selection
    3: 'string',      # Multiple Selection
    4: 'datetime',    # Date
    5: 'time',        # Time
    6: 'boolean',     # Checkbox
    10: 'string',     # Rich Text
}


def parse_udf(custom_fields):
    """Convert Halo customfields list to standardized udf_data format."""
    result = {}
    for field in custom_fields:
        label = field.get('label', '')
        snake_name = caption_to_snake_case(label)
        if not snake_name:
            # I should hope this would never happen, but ping it to
            # sentry if it does so we can handle it.
            logger.exception(
                "UDF name stripped became empty string: %s.", label
            )
            continue

        halo_type = field.get('type')
        if halo_type not in DATA_TYPE_MAP:
            continue

        value = field.get('value')
        display_value = field.get('display', value)

        result[snake_name] = {
            'id': field.get('id'),
            'udf_type': UDF_TYPE_NAME_MAP.get(halo_type, str(halo_type)),
            'data_type': DATA_TYPE_MAP.get(halo_type, 'string'),
            'name': label,
            'value': value,
            'display_value': display_value,
            'extra': {},
        }
    return result
