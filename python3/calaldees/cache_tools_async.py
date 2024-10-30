import asyncio
from functools import lru_cache, wraps
from typing import Any, Awaitable, TypeVar, Generator

# python/cpython: [Add an async variant of lru_cache for coroutines. #90780](https://github.com/python/cpython/issues/90780)


T = TypeVar('T')


class CachedAwaitable(Awaitable[T]):
    def __init__(self, awaitable: Awaitable[T]) -> None:
        self.awaitable = awaitable
        self.result: asyncio.Future[T] | None = None

    def __await__(self) -> Generator[Any, None, T]:
        if self.result is None:
            fut = asyncio.get_event_loop().create_future()
            self.result = fut
            result = yield from self.awaitable.__await__()
            fut.set_result(result)
        if not self.result.done():
            yield from self.result
        return self.result.result()


def reawaitable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return CachedAwaitable(func(*args, **kwargs))

    return wrapper


def async_lru_cache(maxsize=128, typed=False):
    if callable(maxsize) and isinstance(typed, bool):
        user_function, maxsize = maxsize, 128
        return lru_cache(maxsize, typed)(reawaitable(user_function))

    def decorating_function(user_function):
        return lru_cache(maxsize, typed)(reawaitable(user_function))

    return decorating_function
