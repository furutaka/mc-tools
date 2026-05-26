#!/usr/bin/env python3
"""Helpers for reading and writing Fortran-style unformatted records."""

from __future__ import annotations

import struct
from typing import BinaryIO


def skip_record(handle: BinaryIO) -> int:
    """Skip the next record in *handle* and return its payload size."""

    size_bytes = handle.read(4)
    if not size_bytes:
        return 0
    (size,) = struct.unpack("=i", size_bytes)
    handle.seek(size, 1)
    end_bytes = handle.read(4)
    if size_bytes != end_bytes:
        raise IOError("Skipping Fortran record")
    return size


def read_record(handle: BinaryIO) -> bytes | None:
    """Read and return the payload of the next Fortran record."""

    size_bytes = handle.read(4)
    if not size_bytes:
        return None
    (size,) = struct.unpack("=i", size_bytes)
    payload = handle.read(size)
    end_bytes = handle.read(4)
    if size_bytes != end_bytes:
        raise IOError("Reading Fortran record")
    return payload


def write_record(handle: BinaryIO, payload: bytes) -> int:
    """Write *payload* as a Fortran record and return the final write result."""

    handle.write(struct.pack("=i", len(payload)))
    handle.write(payload)
    return handle.write(struct.pack("=i", len(payload)))

