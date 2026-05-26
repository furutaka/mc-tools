"""Minimal numeric formatting helpers used by the FLUKA readers."""

from __future__ import annotations


def format(number, length=16, useExp=False):
    """Return a compact string representation of *number*."""

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

