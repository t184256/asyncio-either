# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Main module of asyncio_either."""

import asyncio
import typing

_P = typing.ParamSpec('_P')
_T = typing.TypeVar('_T')
_Coroutine = typing.Coroutine[typing.Any, typing.Any, _T]
_Corofunc = typing.Callable[_P, _Coroutine[_T]]


def either(*corofuncs: _Corofunc[_P, _T]) -> _Corofunc[_P, _T]:
    """Augment a coroutine so that alternatives can be specified.

    ```
    @asyncio_either.either
    async def coro() -> int:
        return 1

    @asyncio_either.or_(coro)
    async def alternative() -> int:
        return 2

    await coro()  # either 1 or 2, whichever one completes first
    ```

    Does nothing to verify that the values are in agreement.
    """
    _alternatives = list(corofuncs)

    def or_(corofunc: _Corofunc[_P, _T]) -> None:
        _alternatives.append(corofunc)

    async def _return_first(*a: _P.args, **kwa: _P.kwargs) -> _T:
        tasks: list[asyncio.Task[_T]]
        tasks = [
            asyncio.create_task(c(*a, **kwa), name=c.__name__)
            for c in _alternatives
        ]
        finished, unfinished = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )
        res = finished.pop().result()
        for task in unfinished:
            task.cancel()
        return res

    _return_first.or_ = or_  # type: ignore[attr-defined]
    return _return_first


def or_(
    corofunc: _Corofunc[_P, _T],
) -> typing.Callable[[_Corofunc[_P, _T]], _Corofunc[_P, _T]]:
    while hasattr(corofunc, '__wrapped__') and not hasattr(corofunc, 'or_'):
        corofunc = corofunc.__wrapped__
    assert hasattr(corofunc, 'or_')  # noqa: S101

    def decorator(corofunc_alt: _Corofunc[_P, _T]) -> _Corofunc[_P, _T]:
        corofunc.or_(corofunc_alt)
        return corofunc_alt

    return decorator


__all__ = ['either', 'or_']
