# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Decides when the bot butts into a conversation uninvited.

Every so often the Discord bot takes a random human message ("this link is
broken") and fires back a Yo Mama joke built from it ("Yo mama so broken,
even this link works better than her"). This module holds the gate that
decides *when*: a dice roll, a per-channel cooldown so one unlucky channel
doesn't get roasted twice in a row, an optional channel allowlist, and a few
rules about which messages are fair game (humans only, actual sentences,
not commands).

It is plain Python with no Discord dependency so the rules are easy to unit
test; the Discord layer just translates a message into the arguments.
"""

import random
import re
import time
from collections.abc import Callable, Iterable

#: Default probability that any one eligible message gets a reply (2%).
DEFAULT_CHANCE = 0.02
#: Default per-channel quiet period between unsolicited replies, in seconds.
DEFAULT_COOLDOWN = 600
#: Messages with fewer real words than this are not worth riffing on.
DEFAULT_MIN_WORDS = 3

# Tokens that carry no joke material: links, user/role/channel mentions,
# custom emoji, and bare numbers.
_NOISE = re.compile(
    r'https?://\S+'            # URLs
    r'|<a?:\w+:\d+>'           # custom emoji <:name:id> / <a:name:id>
    r'|<[@#&!]+\d+>'           # mentions <@id>, <@!id>, <@&id>, <#id>
    r'|\b\d+\b'                # bare numbers
)
_WORD = re.compile(r"[^\W\d_]{2,}")


def meaningful_words(content: str) -> list[str]:
    """Words in a message that a joke could actually hang on."""
    return _WORD.findall(_NOISE.sub(' ', content or ''))


class RiffGate:
    """
    Gate for unsolicited "turn what you said into a Yo Mama joke" replies.

    Args:
        chance: Probability (0.0-1.0) that an eligible message gets a reply.
            0 disables the feature entirely. Values outside the range are
            clamped.
        cooldown: Seconds a channel stays quiet after the bot riffs there.
        allowed_channels: Channel IDs the bot may riff in. Empty/None means
            every channel it can see.
        min_words: Minimum number of real words a message needs.
        rng: Random source with a ``random()`` method (injectable for tests).
        clock: Monotonic time source (injectable for tests).
    """

    def __init__(
        self,
        chance: float = DEFAULT_CHANCE,
        cooldown: int = DEFAULT_COOLDOWN,
        allowed_channels: Iterable[int] | None = None,
        min_words: int = DEFAULT_MIN_WORDS,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.chance = max(0.0, min(1.0, float(chance)))
        self.cooldown = max(0, int(cooldown))
        self.allowed_channels = {int(c) for c in (allowed_channels or ())}
        self.min_words = max(1, int(min_words))
        self._rng = rng or random.SystemRandom()
        self._clock = clock
        self._last_fired: dict[int, float] = {}

    @property
    def enabled(self) -> bool:
        """False when the chance is zero, i.e. the feature is switched off."""
        return self.chance > 0

    def is_candidate(
        self,
        content: str,
        *,
        author_is_bot: bool,
        channel_id: int,
        in_guild: bool = True,
        command_prefix: str | None = None,
    ) -> bool:
        """
        Whether a message is the kind of thing the bot may riff on at all.

        This is the deterministic half of the decision: no dice, no cooldown.
        Bots, webhooks, and system messages never qualify (that's what
        ``author_is_bot`` must cover), nor do DMs, commands, or messages that
        are just a link, an emoji, or a "lol".
        """
        if not self.enabled or author_is_bot or not in_guild:
            return False
        if self.allowed_channels and channel_id not in self.allowed_channels:
            return False

        text = (content or '').strip()
        if not text:
            return False
        if command_prefix and text.startswith(command_prefix):
            return False
        if text.startswith('/'):  # someone typing a slash command by hand
            return False

        return len(meaningful_words(text)) >= self.min_words

    def roll(self, channel_id: int) -> bool:
        """
        Roll the dice for a channel, honouring its cooldown.

        Returns True when the bot should riff now; the channel's cooldown
        starts at that moment. The cooldown is checked *before* the roll so a
        quiet channel doesn't burn its luck.
        """
        if not self.enabled:
            return False

        now = self._clock()
        last = self._last_fired.get(channel_id)
        if last is not None and now - last < self.cooldown:
            return False

        if self._rng.random() >= self.chance:
            return False

        self._last_fired[channel_id] = now
        return True

    def should_riff(
        self,
        content: str,
        *,
        author_is_bot: bool,
        channel_id: int,
        in_guild: bool = True,
        command_prefix: str | None = None,
    ) -> bool:
        """``is_candidate`` followed by ``roll``, for callers who want one call."""
        return self.is_candidate(
            content,
            author_is_bot=author_is_bot,
            channel_id=channel_id,
            in_guild=in_guild,
            command_prefix=command_prefix,
        ) and self.roll(channel_id)
