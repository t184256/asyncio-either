# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Main module of asyncio_either."""

import asyncio
import contextlib
import os
import typing

_P = typing.ParamSpec('_P')
_T = typing.TypeVar('_T')
_Coroutine = typing.Coroutine[typing.Any, typing.Any, _T]
_Corofunc = typing.Callable[_P, _Coroutine[_T]]


@typing.overload
def either(
    *,
    wait_for_all: bool | None = None,
) -> typing.Callable[[_Corofunc[_P, _T]], _Corofunc[_P, _T]]: ...  # overload


@typing.overload
def either(
    corofunc1: _Corofunc[_P, _T],
    *corofuncs_rest: _Corofunc[_P, _T],
    wait_for_all: bool | None = None,
) -> _Corofunc[_P, _T]: ...  # overload


def either(
    corofunc1: _Corofunc[_P, _T] | None = None,
    *corofuncs_rest: _Corofunc[_P, _T],
    wait_for_all: bool | None = None,
) -> (
    typing.Callable[[_Corofunc[_P, _T]], _Corofunc[_P, _T]] | _Corofunc[_P, _T]
):
    """Augment a coroutine so that alternatives can be specified.

    ```
    @asyncio_either.either
    async def coro() -> int:
        return 1

    @asyncio_either.or_(coro)
    async def coro_alternative() -> int:
        return 2

    await coro()  # either 1 or 2, whichever one completes first
    ```

    or

    ```
    coro = asyncio_either(coro, alternative)
    ```

    With `wait_for_all=False`,
    it does nothing to verify that the values are in agreement.
    With `wait_for_all=True`, it asserts they match.
    With `wait_for_all=None`,
    it looks whether `ASYNCIO_EITHER_WAIT_FOR_BOTH=1`.
    """
    if corofunc1 is None:
        return _either_single(wait_for_all=wait_for_all)
    corofuncs = (corofunc1, *corofuncs_rest)
    return _either_multi(*corofuncs, wait_for_all=wait_for_all)


def _either_single(
    wait_for_all: bool | None = None,  # noqa: FBT001
) -> typing.Callable[[_Corofunc[_P, _T]], _Corofunc[_P, _T]]:
    def decorator(coro: _Corofunc[_P, _T]) -> _Corofunc[_P, _T]:
        return _either_multi(coro, wait_for_all=wait_for_all)

    return decorator


def _either_multi(
    *corofuncs: _Corofunc[_P, _T],
    wait_for_all: bool | None = None,
) -> _Corofunc[_P, _T]:
    _alternatives = list(corofuncs)

    def or_(corofunc: _Corofunc[_P, _T]) -> None:
        _alternatives.append(corofunc)

    if wait_for_all is None:
        wait_for_all = os.getenv('ASYNCIO_EITHER_WAIT_FOR_BOTH', '0') == '1'

    if wait_for_all:

        async def _wait_for_all(*a: _P.args, **kwa: _P.kwargs) -> _T:
            tasks: list[asyncio.Task[_T]]
            tasks = [
                asyncio.create_task(c(*a, **kwa), name=c.__name__)
                for c in _alternatives
            ]
            first, *rest = await asyncio.gather(*tasks)
            assert all(first == r for r in rest)  # noqa: S101
            return first

        _wait_for_all.or_ = or_  # type: ignore[attr-defined]
        return _wait_for_all

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
        for task in unfinished:
            with contextlib.suppress(asyncio.CancelledError):
                await task
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
