# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""Helper for calling the synchronous LLM engine from async bot handlers."""

import asyncio
from collections.abc import Callable
from typing import Any


async def run_blocking(func: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """
    Run a blocking call in a worker thread so the event loop stays free.

    The LLM engine sleeps between retries and a local model can take many
    seconds to answer. Called directly from a handler, that stalls the Discord
    gateway heartbeat or the Matrix sync loop for every user at once.
    """
    return await asyncio.to_thread(func, *args, **kwargs)
