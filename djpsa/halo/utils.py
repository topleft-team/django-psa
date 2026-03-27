import logging

from djpsa.sync.udf.utils import caption_to_snake_case

logger = logging.getLogger(__name__)

# Maps Halo UDF type IDs to (data_type, display_name).
# Types come in from Halo API as integers. The types are system
# defined, so they will not change.
UDF_TYPE_MAP = {
    0: ('string', 'Text Field'),
    1: ('string', 'Memo Field'),
    2: ('string', 'Single Selection'),
    3: ('string', 'Multiple Selection'),
    4: ('datetime', 'Date'),
    5: ('time', 'Time'),
    6: ('boolean', 'Checkbox'),
    10: ('string', 'Rich Text'),
}


def parse_udf(custom_fields):
    """Convert Halo customfields list to standardized udf_data format."""
    result = {}
    for field in custom_fields:
        label = field.get('label', '')
        snake_name = caption_to_snake_case(label)
        if not snake_name:
            # I should hope this would never happen, but log it if
            # it does so we can handle it.
            logger.exception(
                "UDF name stripped became empty string: %s.", label
            )
            continue

        halo_type = field.get('type')
        if halo_type not in UDF_TYPE_MAP:
            continue

        data_type, type_name = UDF_TYPE_MAP[halo_type]
        value = field.get('value')
        display_value = field.get('display', value)

        result[snake_name] = {
            'id': field.get('id'),
            'udf_type': type_name,
            'data_type': data_type,
            'name': label,
            'value': value,
            'display_value': display_value,
            'extra': {},
        }
    return result
