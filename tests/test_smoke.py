# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test main module of asyncio_either."""

import asyncio

import pytest

import asyncio_either


@asyncio_either.either
async def mul(a: int, b: int) -> int:
    """Multiply two numbers in one way."""
    await asyncio.sleep(0.1)
    return a * b


@asyncio_either.or_(mul)
async def mul_alt(a: int, b: int) -> int:
    """Multiply two numbers in another way."""
    await asyncio.sleep(0.2)
    return b * a


@pytest.mark.asyncio()
async def test_smoke() -> None:
    """Smoke-test the basic functionality."""
    assert await mul(2, 3) == 6  # noqa: PLR2004
