#!/usr/bin/env python3
"""Additional Linux arm64 bind/listen prohibition, applied inside srt.

This does not replace srt's namespace, endpoint proxy or Unix socket filter.
The explicit arm64 guest is the only validated architecture for this wrapper.
"""
import ctypes
import errno
import os
from pathlib import Path
import platform
import sys


class Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]


class Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]


def restrict_binding():
    if sys.platform != 'linux' or platform.machine() != 'aarch64':
        raise OSError('review network filter platform unsupported')
    # Linux UAPI: arm64 uses asm-generic bind=200/listen=201. Check the
    # syscall architecture before numbers; incompatible ABIs fail closed.
    rows = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc00000b7), (0x06, 0, 0, 0x80000000),
            (0x20, 0, 0, 0), (0x15, 0, 1, 200), (0x06, 0, 0, 0x50000 | errno.EPERM),
            (0x15, 0, 1, 201), (0x06, 0, 0, 0x50000 | errno.EPERM),
            (0x06, 0, 0, 0x7fff0000)]
    filters = (Filter * len(rows))(*(Filter(*row) for row in rows))
    program = Program(len(rows), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'review network filter unavailable')


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != '--' or not Path(sys.argv[2]).is_absolute():
        raise SystemExit('trusted absolute review executable required')
    try:
        restrict_binding()
    except OSError:
        raise SystemExit('review_network_filter_unavailable') from None
    os.execv(sys.argv[2], sys.argv[2:])
