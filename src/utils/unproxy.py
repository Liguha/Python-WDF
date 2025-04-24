from weakref import ProxyType
from typing import Any

__all__ = ["unproxy"]

def unproxy(proxy: ProxyType) -> Any:
    '''Get original reference from proxy.
    Note that it does not work with class proxies.'''
    return proxy.__repr__.__self__