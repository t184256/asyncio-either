# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test adding alternatives to methods."""

import asyncio
import typing

import pytest

import asyncio_either


class Example:
    @asyncio_either.either
    async def m(self) -> tuple[int, typing.Self]:
        await asyncio.Event().wait()
        return (1, self)

    @asyncio_either.or_(m)
    async def m_alt(self) -> tuple[int, typing.Self]:
        return (2, self)

    # > Changed in version 3.11:
    # > Class methods can no longer wrap other descriptors such as property().

    @classmethod
    @asyncio_either.either()
    async def cm(cls) -> tuple[int, type[typing.Self]]:
        await asyncio.Event().wait()
        return 1, cls

    @classmethod
    @asyncio_either.or_(cm)
    async def cm_alt(cls) -> tuple[int, type[typing.Self]]:
        return 2, cls

    @staticmethod
    @asyncio_either.either
    async def sm() -> int:
        await asyncio.Event().wait()
        return 1

    @staticmethod
    @asyncio_either.or_(sm)
    async def sm_alt2() -> int:
        await asyncio.Event().wait()
        return 2

    @staticmethod
    @asyncio_either.or_(sm)
    async def sm_alt3() -> int:
        return 3


@pytest.mark.asyncio()
async def test_method() -> None:
    """Smoke-test a regular method with alternatives."""
    ex = Example()
    assert await ex.m() == (2, ex)


@pytest.mark.asyncio()
async def test_classmethod() -> None:
    """Smoke-test a classmethod with alternatives."""
    assert await Example().cm() == (2, Example)


@pytest.mark.asyncio()
async def test_staticmethod() -> None:
    """Smoke-test a staticmethod with alternatives."""
    assert await Example().sm() == 3  # noqa: PLR2004
