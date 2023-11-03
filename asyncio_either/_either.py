# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Main module of asyncio_either."""

import asyncio
import typing

_P = typing.ParamSpec('_P')
_T = typing.TypeVar('_T')
_Coroutine = typing.Coroutine[typing.Any, typing.Any, _T]
_Corofunc = typing.Callable[_P, _Coroutine[_T]]


class CorofuncWithAlternatives(typing.Generic[_P, _T]):
    _alternatives: list[_Corofunc[_P, _T]]

    def __init__(self, corofunc: _Corofunc[_P, _T]) -> None:
        self._alternatives = [corofunc]

    def __call__(self, *a: _P.args, **kwa: _P.kwargs) -> _Coroutine[_T]:
        tasks: list[asyncio.Task[_T]]
        tasks = [
            asyncio.create_task(c(*a, **kwa), name=c.__name__)
            for c in self._alternatives
        ]

        async def return_first() -> _T:
            finished, unfinished = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            res = finished.pop().result()
            for task in unfinished:
                task.cancel()
            return res

        return return_first()

    def or_(self, corofunc: _Corofunc[_P, _T]) -> None:
        self._alternatives.append(corofunc)


def either(corofunc: _Corofunc[_P, _T]) -> CorofuncWithAlternatives[_P, _T]:
    """Augment a coroutine so that alternatives can be specified.

    ```
    @asyncio_either
    async def coro() -> int:
        return 1

    @coro.or_
    async def alternative() -> int:
        return 2

    await coro()  # either 1 or 2, whichever one completes first
    ```

    Does nothing to verify that the values are in agreement.
    """
    return CorofuncWithAlternatives(corofunc)


__all__ = ['either']
