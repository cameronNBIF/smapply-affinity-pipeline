import pandas as pd

def is_blank(val):
    """Returns True if val is None, NaN, or an empty/whitespace string."""
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False