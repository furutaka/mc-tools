"""Minimal numeric formatting helpers used by the FLUKA readers."""

from __future__ import annotations


def format(number, length=16, useExp=False):
    """Return a compact string representation of *number*.

    The legacy FLUKA reader only uses this helper to avoid tiny floating-point
    artifacts in USRBIN bin edges.  The implementation keeps the old behavior
    close enough for that use case without pulling in the historical utility
    module.
    """

    if isinstance(number, (float, int)):
        if number == 0:
            number = 0
        return repr(number).upper()

    num = str(number).strip().upper().replace("D", "E")
    try:
        float(num)
    except ValueError:
        return number
    return num

