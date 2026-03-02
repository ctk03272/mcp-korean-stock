from __future__ import annotations

import time

try:
    from cachetools import TTLCache as _TTLCache
except ImportError:
    class TTLCache(dict):
        def __init__(self, maxsize: int, ttl: int) -> None:
            super().__init__()
            self.maxsize = maxsize
            self.ttl = ttl
            self._expires: dict[object, float] = {}

        def __contains__(self, key: object) -> bool:
            if key not in self._expires:
                return False
            if self._expires[key] < time.time():
                super().pop(key, None)
                self._expires.pop(key, None)
                return False
            return super().__contains__(key)

        def __setitem__(self, key: object, value: object) -> None:
            if len(self._expires) >= self.maxsize:
                oldest = min(self._expires, key=self._expires.get)
                super().pop(oldest, None)
                self._expires.pop(oldest, None)
            super().__setitem__(key, value)
            self._expires[key] = time.time() + self.ttl

        def __getitem__(self, key: object) -> object:
            if key not in self:
                raise KeyError(key)
            return super().__getitem__(key)
else:
    TTLCache = _TTLCache
