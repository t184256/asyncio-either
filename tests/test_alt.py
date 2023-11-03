# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test main module of asyncio_either."""

import asyncio

import pytest

import asyncio_either

barrier = asyncio.Barrier(3)
event1 = asyncio.Event()
event2 = asyncio.Event()
event3 = asyncio.Event()

log = []


@asyncio_either.either
async def c() -> int:
    """Return 1."""
    log.append('>1')
    await barrier.wait()
    await event1.wait()
    log.append('<1')
    return 1


@c.or_
async def c2() -> int:
    """Return 2."""
    log.append('>2')
    await barrier.wait()
    await event2.wait()
    log.append('<2')
    return 2


@c.or_
async def c3() -> int:
    """Return 3."""
    log.append('>3')
    await barrier.wait()
    await event3.wait()
    log.append('<3')
    return 3


@pytest.mark.asyncio()
async def test_alts() -> None:
    """Test that different versions do run when others are held up."""
    event1.set()
    assert await c() == 1
    assert log == ['>1', '>2', '>3', '<1']
    log.clear()
    event1.clear()

    event2.set()
    assert await c() == 2  # noqa: PLR2004
    assert log == ['>1', '>2', '>3', '<2']
    log.clear()
    event2.clear()

    event3.set()
    assert await c() == 3  # noqa: PLR2004
    assert log == ['>1', '>2', '>3', '<3']
    log.clear()
    event3.clear()

    event1.set()
    event3.set()
    assert await c() in {1, 3}
    assert tuple(log) in {
        ('>1', '>2', '>3', '<1'),
        ('>1', '>2', '>3', '<3'),
        ('>1', '>2', '>3', '<1', '<3'),
        ('>1', '>2', '>3', '<3', '<1'),
    }
    log.clear()
    event3.clear()
