# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Abuse controls shared by the Discord and Matrix bots.

Everything here is in-process and dependency free: a per-user cooldown, a
global cap on concurrent generations, a per-user opt-out store and an ids-only
audit line. State lives in this process; a restart clears the cooldowns and
the in-flight count (the opt-out list persists only when a file is configured).
"""

import contextlib
import json
import logging
import os
import tempfile
import time
from collections.abc import AsyncIterator, Callable

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("yo_mama.audit")


class Refused(Exception):
    """A request was turned away; the message is safe to show to the user."""


class GenerationGuard:
    """Per-user cooldown plus a global cap on generations running at once."""

    MAX_TRACKED = 1024  # cap on remembered users; expired entries are dropped first

    def __init__(
        self,
        cooldown_seconds: float = 10,
        max_concurrent: int = 2,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.cooldown = max(0.0, float(cooldown_seconds))
        self.max_concurrent = max(1, int(max_concurrent))
        self._clock = clock
        self._last: dict[str, float] = {}
        self._running = 0

    def _prune(self, now: float) -> None:
        if len(self._last) < self.MAX_TRACKED:
            return
        self._last = {k: t for k, t in self._last.items() if now - t < self.cooldown}
        if len(self._last) >= self.MAX_TRACKED:  # still full of live cooldowns: drop the oldest
            for key, _ in sorted(self._last.items(), key=lambda kv: kv[1])[: len(self._last) - self.MAX_TRACKED + 1]:
                del self._last[key]

    @contextlib.asynccontextmanager
    async def slot(self, key: str) -> AsyncIterator[None]:
        """Admit one generation for ``key`` or raise Refused. Released on exit."""
        now = self._clock()
        if self._running >= self.max_concurrent:
            raise Refused("The roast machine is busy right now. Try again in a moment.")
        last = self._last.get(key)
        if self.cooldown and last is not None and now - last < self.cooldown:
            wait = int(self.cooldown - (now - last)) + 1
            raise Refused(f"Slow down. Try again in {wait}s.")
        if self.cooldown:
            self._prune(now)
            self._last[key] = now
        self._running += 1
        try:
            yield
        finally:
            self._running -= 1


class OptOutStore:
    """Ids of users who asked not to be targeted. Memory only unless a path is given."""

    def __init__(self, path: str | None = None):
        self.path = path or None
        self._ids: set[str] = set()
        if self.path:
            self._load()

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
            self._ids = {str(i) for i in data["opted_out"]}
        except FileNotFoundError:
            return
        except (ValueError, KeyError, TypeError, OSError) as exc:
            logger.error("Opt-out file %s is unreadable (%s); moved aside, starting empty",
                         self.path, type(exc).__name__)
            with contextlib.suppress(OSError):
                os.replace(self.path, self.path + ".corrupt")

    def _save(self) -> None:
        if not self.path:
            return
        directory = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".optout-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"opted_out": sorted(self._ids)}, fh)
                fh.flush()
                os.fsync(fh.fileno())
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def is_opted_out(self, user_id) -> bool:
        return str(user_id) in self._ids

    def add(self, user_id) -> None:
        self._ids.add(str(user_id))
        self._save()

    def remove(self, user_id) -> None:
        self._ids.discard(str(user_id))
        self._save()


def audit(platform: str, command: str, *, invoker, target=None, level=None,
          guild=None, channel=None) -> None:
    """Log who ran what. Ids and the meanness level only: never message text or tokens."""
    def show(value):
        return "-" if value is None else str(value)

    audit_logger.info(
        "audit platform=%s command=%s invoker=%s target=%s level=%s guild=%s channel=%s",
        platform, command, show(invoker), show(target), show(level), show(guild), show(channel))
