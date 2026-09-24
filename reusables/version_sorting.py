"""
Version key comparison for sorting them in referenced GitHub repositories 
"""

# Sort by version numbers when given references dataset paths containing versions.
# This assumes the version number is always in the form of /v.../
# Return a tuple that is sortable
import re

def version_key(path):
    s = str(path)
    match = re.search(r"/v(\d+)_(\d+)(?:_(\d+))?", s)
    if not match:
        raise ValueError(f"No version found in: {s}")

    # Concat the version numbers into a tuple for comparison:
    # v0_110_0 --> (0, 110, 0) > v0_3_0 --> (0, 3, 0)
    return tuple(int(g) if g is not None else 0 for g in match.groups())
