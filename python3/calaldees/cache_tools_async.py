import asyncio
from functools import lru_cache, wraps
from typing import Any, Awaitable, Callable, Generator, TypeVar

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


# -------


def async_cached_property[T, **P](fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    CACHED_VALUE_VARIABLE_NAME = '_' + fn.__name__
    ASYNC_LOCK_VARIABLE_NAME = CACHED_VALUE_VARIABLE_NAME + '_lock'

    @wraps(fn)
    async def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
        self = args[0]
        if not hasattr(self, ASYNC_LOCK_VARIABLE_NAME):
            setattr(self, ASYNC_LOCK_VARIABLE_NAME, asyncio.Lock())
        async with getattr(self, ASYNC_LOCK_VARIABLE_NAME):
            if not hasattr(self, CACHED_VALUE_VARIABLE_NAME):
                value = await fn(*args, **kwargs)
                setattr(self, CACHED_VALUE_VARIABLE_NAME, value)
            return getattr(self, CACHED_VALUE_VARIABLE_NAME)

    return decorated
