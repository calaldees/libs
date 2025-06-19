import asyncio
import dataclasses
import datetime
import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Awaitable, ParamSpec, TypeVar, overload

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@dataclasses.dataclass(frozen=True)
class CachePath:
    path: Path = Path("__cache")
    ttl: datetime.timedelta = datetime.timedelta(minutes=10)

    def __post_init__(self):
        self.path.mkdir(exist_ok=True)


T = TypeVar("T")
P = ParamSpec("P")


def cache_filesystem(
    test: str,
    cache_path: CachePath = CachePath(),
) -> Callable:
    @overload
    def _typed_decorator(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...
    @overload
    def _typed_decorator(fn: Callable[P, T]) -> Callable[P, T]: ...
    def _typed_decorator(fn: Callable[P, T]) -> Callable:
        log.info(f"decorator - function level setup {test=}")

        if asyncio.iscoroutinefunction(fn):

            async def async_decorated(*args: P.args, **kwargs: P.kwargs) -> T:
                logging.info(f"Async {fn.__name__} was called")
                return await fn(*args, **kwargs)

            return functools.wraps(fn)(async_decorated)
        else:

            def sync_decorated(*args: P.args, **kwargs: P.kwargs) -> T:
                logging.info(f"Sync {fn.__name__} was called")
                return fn(*args, **kwargs)

            return functools.wraps(fn)(sync_decorated)

    return _typed_decorator


@cache_filesystem("hello async")
async def add_async(x: float, y: float) -> float:
    """add two number (async)"""
    return x + y


@cache_filesystem("hello sync")
def add_sync(x: float, y: float) -> float:
    """add two number (sync)"""
    return x + y


async def main():
    value = await add_async(1, 2)
    print(value)


if __name__ == "__main__":
    log.info("main")
    asyncio.run(main())
    value = add_sync(1, 2)
    print(value)

    value = add_sync(3, 4)
    breakpoint()


# References/Notes -------------------------------------------------------------

# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
# https://discuss.python.org/t/decorator-to-facilitate-sync-and-async-calls-to-one-function/78986
# https://stackoverflow.com/a/71132186/3356840
"""
from typing import Awaitable, Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def decorator(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    async def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
        return await fn(*args, **kwargs)

    return decorated
"""

# def cache_filesystem(
#     test: str,
#     cache_path: CachePath = CachePath(),
# ) -> Callable:
#     log.info('setup decorator - module level')
#     def _typed_decorator[T,**P](fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
#         @functools.wraps(fn)
#         async def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
#             logging.info(f'{fn.__name__} was called')
#             return await fn(*args, **kwargs)
#         return decorated
#     return _typed_decorator
