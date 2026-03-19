import re


def caption_to_snake_case(caption):
    """
    Convert a UDF caption to a snake_case key.
    Removes special characters, preserves numbers, collapses whitespace.
    e.g. "Hello 3 there?" -> "hello_3_there"
    """
    s = caption.lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    s = re.sub(r'_+', '_', s)
    return s.strip('_')
