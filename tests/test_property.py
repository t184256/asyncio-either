# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test asyncio_either with awaitable properties."""

import asyncio
import typing

import awaitable_property
import pytest

import asyncio_either

event = asyncio.Event()


class Example:
    async def _p_main(self) -> tuple[int, typing.Self]:
        await event.wait()
        return 1, self

    async def _p_alt(self) -> tuple[int, typing.Self]:
        return 2, self

    p = awaitable_property.awaitable_property(
        asyncio_either.either(_p_main, _p_alt),
    )


@pytest.mark.asyncio()
async def test_property() -> None:
    """Smoke-test awaitable properties."""
    ex = Example()
    assert await ex.p == (2, ex)
