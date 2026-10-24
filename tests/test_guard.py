# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""Unit tests for the in-process cooldown, concurrency cap, opt-out store and audit line."""

import asyncio
import json
import logging
import os
import tempfile
import unittest

from yo_mama.guard import GenerationGuard, OptOutStore, Refused, audit


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def run(coro):
    return asyncio.run(coro)


class TestCooldown(unittest.TestCase):
    def test_second_request_inside_window_is_refused(self):
        clock = FakeClock()
        guard = GenerationGuard(cooldown_seconds=10, max_concurrent=5, clock=clock)

        async def scenario():
            async with guard.slot("u1"):
                pass
            with self.assertRaises(Refused):
                async with guard.slot("u1"):
                    self.fail("body must not run while on cooldown")
            clock.now += 10.5
            async with guard.slot("u1"):
                pass

        run(scenario())

    def test_cooldown_is_per_user(self):
        guard = GenerationGuard(cooldown_seconds=10, max_concurrent=5, clock=FakeClock())

        async def scenario():
            async with guard.slot("u1"):
                pass
            async with guard.slot("u2"):
                pass

        run(scenario())

    def test_zero_disables_cooldown(self):
        guard = GenerationGuard(cooldown_seconds=0, max_concurrent=5, clock=FakeClock())

        async def scenario():
            for _ in range(3):
                async with guard.slot("u1"):
                    pass

        run(scenario())

    def test_cooldown_table_is_bounded(self):
        clock = FakeClock()
        guard = GenerationGuard(cooldown_seconds=1, max_concurrent=5, clock=clock)

        async def scenario():
            for i in range(guard.MAX_TRACKED + 50):
                clock.now += 2  # every earlier entry has expired
                async with guard.slot(f"u{i}"):
                    pass

        run(scenario())
        self.assertLessEqual(len(guard._last), guard.MAX_TRACKED)


class TestConcurrency(unittest.TestCase):
    def test_cap_refuses_extra_and_releases_slot(self):
        guard = GenerationGuard(cooldown_seconds=0, max_concurrent=1, clock=FakeClock())

        async def scenario():
            entered = asyncio.Event()
            release = asyncio.Event()

            async def holder():
                async with guard.slot("u1"):
                    entered.set()
                    await release.wait()

            task = asyncio.create_task(holder())
            await entered.wait()
            with self.assertRaises(Refused):
                async with guard.slot("u2"):
                    self.fail("body must not run over the cap")
            release.set()
            await task
            async with guard.slot("u2"):  # slot was released
                pass

        run(scenario())

    def test_slot_released_when_body_raises(self):
        guard = GenerationGuard(cooldown_seconds=0, max_concurrent=1, clock=FakeClock())

        async def scenario():
            with self.assertRaises(RuntimeError):
                async with guard.slot("u1"):
                    raise RuntimeError("boom")
            async with guard.slot("u1"):
                pass

        run(scenario())

    def test_busy_refusal_does_not_start_a_cooldown(self):
        clock = FakeClock()
        guard = GenerationGuard(cooldown_seconds=30, max_concurrent=1, clock=clock)

        async def scenario():
            entered = asyncio.Event()
            release = asyncio.Event()

            async def holder():
                async with guard.slot("u1"):
                    entered.set()
                    await release.wait()

            task = asyncio.create_task(holder())
            await entered.wait()
            with self.assertRaises(Refused):
                async with guard.slot("u2"):
                    pass
            release.set()
            await task
            async with guard.slot("u2"):  # not on cooldown: the refusal was not a run
                pass

        run(scenario())


class TestOptOutStore(unittest.TestCase):
    def test_memory_only_without_path(self):
        store = OptOutStore(None)
        self.assertFalse(store.is_opted_out(5))
        store.add(5)
        self.assertTrue(store.is_opted_out(5))
        self.assertTrue(store.is_opted_out("5"))
        store.remove(5)
        self.assertFalse(store.is_opted_out(5))

    def test_persists_atomically_and_reloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "optout.json")
            OptOutStore(path).add(42)
            self.assertEqual(os.listdir(tmp), ["optout.json"])  # no temp file left
            with open(path) as fh:
                self.assertEqual(json.load(fh)["opted_out"], ["42"])
            self.assertTrue(OptOutStore(path).is_opted_out(42))
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)

    def test_corrupt_file_is_kept_aside_and_store_starts_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "optout.json")
            with open(path, "w") as fh:
                fh.write("{not json")
            store = OptOutStore(path)
            self.assertFalse(store.is_opted_out(1))
            self.assertTrue(os.path.exists(path + ".corrupt"))


class TestAudit(unittest.TestCase):
    def test_line_has_ids_and_level_only(self):
        with self.assertLogs("yo_mama.audit", level=logging.INFO) as cm:
            audit("discord", "joke", invoker="111", target="222", level=7,
                  guild="333", channel="444")
        line = cm.output[0]
        for needle in ("discord", "joke", "invoker=111", "target=222", "level=7",
                       "guild=333", "channel=444"):
            self.assertIn(needle, line)

    def test_missing_target_is_dash(self):
        with self.assertLogs("yo_mama.audit", level=logging.INFO) as cm:
            audit("matrix", "random", invoker="@a:example.org", target=None, level=None)
        self.assertIn("target=-", cm.output[0])
        self.assertIn("level=-", cm.output[0])


if __name__ == "__main__":
    unittest.main()
