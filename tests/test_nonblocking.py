# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
The LLM engine is synchronous (it sleeps between retries), so a bot handler
that calls the generator directly freezes the Discord gateway and the Matrix
sync loop for every user. These tests prove the handlers keep the event loop
free while a generation is in flight.
"""

import ast
import asyncio
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tests.test_abuse_controls import DictConfig
from yo_mama.guard import GenerationGuard
from yo_mama.platforms.discord_bot import DiscordBot
from yo_mama.platforms.matrix_bot import MatrixBot

SLOW = 0.4  # seconds a fake generation blocks, like a retrying LLM call


class SlowGenerator:
    """Stands in for YoMamaGenerator; every call blocks the calling thread."""

    def _block(self):
        time.sleep(SLOW)
        return "Yo mama so slow, the test had to wait."

    def generate_joke(self, **kwargs):
        return self._block()

    def random_joke(self):
        return self._block()

    def generate_batch(self, count=1, **kwargs):
        return [self._block() for _ in range(count)]


async def _ticks_while(coro):
    """Run coro and count how often a 10 ms ticker ran meanwhile."""
    ticks = 0
    stop = False

    async def ticker():
        nonlocal ticks
        while not stop:
            await asyncio.sleep(0.01)
            ticks += 1

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0)  # let the ticker start
    try:
        await coro
    finally:
        stop = True
        await task
    return ticks


def _matrix_bot():
    bot = MatrixBot.__new__(MatrixBot)
    bot.generator = SlowGenerator()
    bot.config = DictConfig()
    bot.guard = GenerationGuard(cooldown_seconds=0, max_concurrent=2)
    bot._send_message = AsyncMock()
    return bot


def _discord_bot():
    with patch("yo_mama.platforms.discord_bot.YoMamaGenerator") as gen_cls:
        gen_cls.list_flavors.return_value = ["tech"]
        bot = DiscordBot(config=DictConfig({"RATE_LIMIT_COOLDOWN_SECONDS": "0"}))
    bot.generator = SlowGenerator()
    return bot


def _interaction():
    interaction = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


class TestMatrixHandlersDoNotBlockLoop(unittest.TestCase):
    MIN_TICKS = 15  # a 0.4 s generation leaves ~40 ticks when the loop is free

    def _check(self, make_coro):
        ticks = asyncio.run(_ticks_while(make_coro(_matrix_bot())))
        self.assertGreaterEqual(ticks, self.MIN_TICKS)

    def test_joke(self):
        self._check(lambda b: b._cmd_joke(MagicMock(), ["tech", "5", "5"]))

    def test_random(self):
        self._check(lambda b: b._cmd_random(MagicMock()))

    def test_thegame(self):
        self._check(lambda b: b._cmd_thegame(MagicMock(), []))

    def test_batch(self):
        self._check(lambda b: b._cmd_batch(MagicMock(), ["1"]))


class TestDiscordHandlersDoNotBlockLoop(unittest.TestCase):
    MIN_TICKS = 15

    def _check(self, name, *args, **kwargs):
        bot = _discord_bot()
        command = bot.bot.tree.get_command(name)
        self.assertIsNotNone(command)
        ticks = asyncio.run(_ticks_while(command.callback(_interaction(), *args, **kwargs)))
        self.assertGreaterEqual(ticks, self.MIN_TICKS)

    def test_slash_joke(self):
        self._check("joke")

    def test_slash_random(self):
        self._check("random")

    def test_slash_batch(self):
        self._check("batch", count=1)


def _direct_generator_calls(source):
    """Lines where self.generator.<method>(...) is called outside run_blocking(...)."""
    tree = ast.parse(source)
    inside = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "run_blocking"):
            for arg in node.args:
                inside.update(id(n) for n in ast.walk(arg))
    bad = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "generator"
                and id(node.func) not in inside):
            bad.append(node.lineno)
    return bad


class TestNoDirectGeneratorCalls(unittest.TestCase):
    """Guard: collect loosely, assert strictly, prove the guard bites."""

    def test_guard_bites(self):
        direct = "async def f(self):\n    return self.generator.generate_joke()\n"
        wrapped = "async def f(self):\n    return await run_blocking(self.generator.generate_joke)\n"
        self.assertEqual(_direct_generator_calls(direct), [2])
        self.assertEqual(_direct_generator_calls(wrapped), [])

    def test_platform_modules(self):
        root = Path(__file__).resolve().parent.parent / "yo_mama" / "platforms"
        files = sorted(root.glob("*_bot.py"))
        self.assertEqual({f.name for f in files}, {"discord_bot.py", "matrix_bot.py"})
        for path in files:
            source = path.read_text()
            self.assertIn("self.generator", source)  # something was collected
            self.assertEqual(_direct_generator_calls(source), [], path.name)


if __name__ == "__main__":
    unittest.main()
