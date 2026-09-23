"""Atomic credentials: owner-only POSIX files, per-user DPAPI on Windows."""
import base64
import json
import os
import tempfile
from pathlib import Path


def protect(data, decrypt=False):
    import ctypes
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise OSError('Windows could not unlock this connection for the current user. Reconnect with your own account.')
    local_free = ctypes.WinDLL('kernel32').LocalFree
    local_free.argtypes = [ctypes.c_void_p]; local_free.restype = ctypes.c_void_p
    try: return ctypes.string_at(result.data, result.size)
    finally: local_free(result.data)


def read_json(path, allow_plain=False):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if value.get('margen_dpapi') == 1:
        if os.name != 'nt': raise ValueError('This Windows connection is bound to its user. Connect your own account on this device.')
        value = json.loads(protect(base64.b64decode(value['data'], validate=True), decrypt=True))
    elif os.name == 'nt' and not allow_plain:
        raise ValueError('Reconnect with margen connect to protect this Windows credential. Never copy another person\'s configuration.')
    return value


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')
    if os.name == 'nt':
        raw = json.dumps({'margen_dpapi':1, 'data':base64.b64encode(protect(raw)).decode('ascii')}).encode('utf-8')
    fd, name = tempfile.mkstemp(prefix='.margen-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out: out.write(raw)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)
