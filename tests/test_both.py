# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test fetching both alternatives."""

import asyncio

import pytest

import asyncio_either

log = []


@asyncio_either.either(wait_for_all=True)
async def same(x: int) -> int:
    """Async identity function."""
    log.append('same')
    await asyncio.sleep(0)
    return x


@asyncio_either.or_(same)
async def same2(x: int) -> int:
    """Also an async identity function."""
    log.append('same2')
    await asyncio.sleep(0)
    return x


@asyncio_either.either(wait_for_all=True)
async def different(x: int) -> int:
    """Add 1."""
    log.append('different')
    await asyncio.sleep(0)
    return x + 1


@asyncio_either.or_(different)
async def different2(x: int) -> int:
    """Add 2."""
    log.append('different2')
    await asyncio.sleep(0)
    return x + 2


@pytest.mark.asyncio()
async def test_same() -> None:
    """Test that returning same results works ok with wait_for_all."""
    log.clear()
    assert await same(0) == 0
    assert set(log) == {'same', 'same2'}
    log.clear()


@pytest.mark.asyncio()
async def test_different() -> None:
    """Test that returning different results breaks with wait_for_all."""
    log.clear()
    with pytest.raises(AssertionError):
        await different(0)
    assert set(log) == {'different', 'different2'}
    log.clear()
