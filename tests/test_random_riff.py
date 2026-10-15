# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Tests for the drive-by joke gate: who the bot may riff on, and how often.
"""

import unittest

from yo_mama.random_riff import RiffGate, meaningful_words


class _Dice:
    """Deterministic stand-in for random: always returns the same roll."""

    def __init__(self, value):
        self.value = value
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.value


class _Clock:
    """Manually advanced monotonic clock."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _gate(chance=1.0, cooldown=600, roll=0.0, **kwargs):
    clock = _Clock()
    dice = _Dice(roll)
    gate = RiffGate(chance=chance, cooldown=cooldown, rng=dice, clock=clock, **kwargs)
    return gate, dice, clock


HUMAN = {'author_is_bot': False, 'channel_id': 1}


class TestMeaningfulWords(unittest.TestCase):

    def test_plain_sentence(self):
        self.assertEqual(meaningful_words("this link is broken"), ['this', 'link', 'is', 'broken'])

    def test_strips_links_mentions_emoji_and_numbers(self):
        text = "<@123> look https://example.com/x?y=1 <:kekw:456> 42 <#789> lol"
        self.assertEqual(meaningful_words(text), ['look', 'lol'])

    def test_empty(self):
        self.assertEqual(meaningful_words(""), [])
        self.assertEqual(meaningful_words(None), [])


class TestCandidates(unittest.TestCase):
    """The deterministic half: which messages are fair game at all."""

    def test_human_sentence_is_a_candidate(self):
        gate, _, _ = _gate()
        self.assertTrue(gate.is_candidate("this link is broken", **HUMAN))

    def test_bots_are_never_candidates(self):
        gate, _, _ = _gate()
        self.assertFalse(gate.is_candidate("this link is broken", author_is_bot=True, channel_id=1))

    def test_dms_are_never_candidates(self):
        gate, _, _ = _gate()
        self.assertFalse(gate.is_candidate("this link is broken", in_guild=False, **HUMAN))

    def test_commands_are_never_candidates(self):
        gate, _, _ = _gate()
        self.assertFalse(gate.is_candidate("!joke tech 5 5", command_prefix='!', **HUMAN))
        self.assertFalse(gate.is_candidate("$joke tech 5 5", command_prefix='$', **HUMAN))
        self.assertFalse(gate.is_candidate("/joke tech 5 5", **HUMAN))
        # A different prefix means it's just a sentence that happens to start with a symbol
        self.assertTrue(gate.is_candidate("!!! this link is broken", command_prefix='$', **HUMAN))

    def test_too_short_messages_are_skipped(self):
        gate, _, _ = _gate()
        self.assertFalse(gate.is_candidate("lol", **HUMAN))
        self.assertFalse(gate.is_candidate("", **HUMAN))
        self.assertFalse(gate.is_candidate("   ", **HUMAN))
        self.assertFalse(gate.is_candidate("https://example.com", **HUMAN))
        self.assertFalse(gate.is_candidate("<@123> <:kekw:456>", **HUMAN))
        self.assertFalse(gate.is_candidate("ok cool", **HUMAN))
        self.assertTrue(gate.is_candidate("ok cool thanks", **HUMAN))

    def test_min_words_is_configurable(self):
        gate, _, _ = _gate(min_words=1)
        self.assertTrue(gate.is_candidate("lol", **HUMAN))

    def test_channel_allowlist(self):
        gate, _, _ = _gate(allowed_channels=[10, 20])
        self.assertTrue(gate.is_candidate("this link is broken", author_is_bot=False, channel_id=10))
        self.assertFalse(gate.is_candidate("this link is broken", author_is_bot=False, channel_id=30))

    def test_empty_allowlist_means_everywhere(self):
        gate, _, _ = _gate(allowed_channels=[])
        self.assertTrue(gate.is_candidate("this link is broken", author_is_bot=False, channel_id=999))

    def test_chance_zero_disables_everything(self):
        gate, _, _ = _gate(chance=0)
        self.assertFalse(gate.enabled)
        self.assertFalse(gate.is_candidate("this link is broken", **HUMAN))
        self.assertFalse(gate.roll(1))


class TestRolling(unittest.TestCase):
    """The random half: dice and cooldowns."""

    def test_chance_is_clamped(self):
        self.assertEqual(RiffGate(chance=5).chance, 1.0)
        self.assertEqual(RiffGate(chance=-1).chance, 0.0)
        self.assertEqual(RiffGate(chance=0.25).chance, 0.25)

    def test_roll_below_chance_fires(self):
        gate, _, _ = _gate(chance=0.5, roll=0.49)
        self.assertTrue(gate.roll(1))

    def test_roll_at_or_above_chance_does_not_fire(self):
        gate, _, _ = _gate(chance=0.5, roll=0.5)
        self.assertFalse(gate.roll(1))
        gate, _, _ = _gate(chance=0.5, roll=0.99)
        self.assertFalse(gate.roll(1))

    def test_cooldown_silences_the_channel_it_fired_in(self):
        gate, _, clock = _gate(cooldown=600)
        self.assertTrue(gate.roll(1))
        self.assertFalse(gate.roll(1))         # same channel, immediately: quiet
        self.assertTrue(gate.roll(2))          # another channel is unaffected
        clock.now += 599
        self.assertFalse(gate.roll(1))         # still inside the cooldown
        clock.now += 1
        self.assertTrue(gate.roll(1))          # cooldown over

    def test_cooldown_is_checked_before_the_dice(self):
        gate, dice, _ = _gate(cooldown=600)
        gate.roll(1)
        rolls_before = dice.calls
        gate.roll(1)
        self.assertEqual(dice.calls, rolls_before, "a cooled-down channel should not roll")

    def test_failed_roll_does_not_start_cooldown(self):
        gate, dice, _ = _gate(chance=0.5, roll=0.9)
        self.assertFalse(gate.roll(1))
        dice.value = 0.1
        self.assertTrue(gate.roll(1))

    def test_zero_cooldown_allows_back_to_back(self):
        gate, _, _ = _gate(cooldown=0)
        self.assertTrue(gate.roll(1))
        self.assertTrue(gate.roll(1))

    def test_should_riff_combines_both_halves(self):
        gate, _, _ = _gate()
        self.assertFalse(gate.should_riff("this link is broken", author_is_bot=True, channel_id=1))
        self.assertTrue(gate.should_riff("this link is broken", **HUMAN))
        self.assertFalse(gate.should_riff("this link is broken", **HUMAN))  # cooldown

    def test_default_rng_is_real(self):
        """With no injected dice the gate still works, using a real RNG."""
        gate = RiffGate(chance=1.0, cooldown=0)
        self.assertTrue(gate.roll(1))
        gate = RiffGate(chance=0.0)
        self.assertFalse(gate.roll(1))


if __name__ == '__main__':
    unittest.main()
