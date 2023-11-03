# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""asyncio-either.

When you have two coroutines to do the same thing, make use of both.
"""

from asyncio_either._either import either

__all__ = ['either']
