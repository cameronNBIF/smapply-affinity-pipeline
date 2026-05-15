import pandas as pd

def is_blank(val):
    """Returns True if val is None, any float (NaN or otherwise), or an empty/whitespace string."""
    if val is None:
        return True
    if isinstance(val, float):  # Catches NaN, 0.0, and any other float landing in a name field
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False