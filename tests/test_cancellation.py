# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0
"""Test cleanup during cancellation."""

import asyncio
import socket

import pytest

import asyncio_either

barrier = asyncio.Barrier(2)
log = []


@asyncio_either.either
async def mul(a: int, b: int) -> int:
    """Multiply two numbers in one way."""
    await barrier.wait()
    await asyncio.sleep(0.1)
    return a * b


@asyncio_either.or_(mul)
async def mul_alt(a: int, b: int) -> int:
    """Multiply two numbers after blocking on stuff."""
    await barrier.wait()
    try:
        log.append('mul_alt waits')
        rsock, wsock = socket.socketpair()
        await asyncio.sleep(100500)
        log.append('mul_alt wakes up')
        return b * a
    except asyncio.exceptions.CancelledError:
        log.append('mul_alt cancelled')
    finally:
        await asyncio.sleep(0)  # still can do asyncio stuff after cancellation
        rsock.close()
        wsock.close()
        log.append('mul_alt exits')
    return 0


@pytest.mark.asyncio()
async def test_smoke() -> None:
    """Smoke-test the basic functionality."""
    assert await mul(2, 3) == 6  # noqa: PLR2004
    assert log == ['mul_alt waits', 'mul_alt cancelled', 'mul_alt exits']
    assert 'mul_alt wakes up' not in log
