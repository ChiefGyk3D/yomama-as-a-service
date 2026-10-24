# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Abuse controls for the Discord and Matrix bots (threat model t4 and t6):
cooldown and concurrency cap, /batch size cap, bots ignored, Matrix auto-join
allowlist, Discord guild-only and allowlists, no mention parsing, per-user
opt-out and an ids-only audit line.
"""

import asyncio
import logging
import os
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from yo_mama.config import Config
from yo_mama.platforms.discord_bot import DiscordBot
from yo_mama.platforms.matrix_bot import MatrixBot


class DictConfig(Config):
    """The real Config parsing, backed by a dict instead of the environment."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def get_secret(self, key, default=None):
        return self.values.get(key, default)


class FakeGenerator:
    def __init__(self, delay=0.0):
        self.calls = []
        self.delay = delay

    def _do(self, name, kwargs):
        self.calls.append((name, kwargs))
        if self.delay:
            time.sleep(self.delay)
        return "Yo mama is so fake, she is a test double."

    def generate_joke(self, **kwargs):
        return self._do("generate_joke", kwargs)

    def random_joke(self):
        return self._do("random_joke", {})

    def generate_batch(self, count=1, **kwargs):
        self._do("generate_batch", dict(kwargs, count=count))
        return ["joke"] * count


def _interaction(user_id=111, guild_id=900, channel_id=800, in_guild=True):
    i = MagicMock()
    i.user.id = user_id
    i.guild = MagicMock(id=guild_id) if in_guild else None
    i.guild_id = guild_id if in_guild else None
    i.channel_id = channel_id
    i.response.defer = AsyncMock()
    i.response.send_message = AsyncMock()
    i.followup.send = AsyncMock()
    return i


def _discord(values=None, delay=0.0):
    cfg = DictConfig(dict({"RATE_LIMIT_COOLDOWN_SECONDS": "0"}, **(values or {})))
    with patch("yo_mama.platforms.discord_bot.YoMamaGenerator") as gen_cls:
        gen_cls.list_flavors.return_value = ["tech"]
        bot = DiscordBot(config=cfg)
    bot.generator = FakeGenerator(delay)
    return bot


def _sent_text(mock_send):
    """All text and embed text sent through a send mock, joined."""
    parts = []
    for call in mock_send.call_args_list:
        if call.args:
            parts.append(str(call.args[0]))
        if call.kwargs.get("content"):
            parts.append(str(call.kwargs["content"]))
        embed = call.kwargs.get("embed")
        if embed is not None:
            parts.append(str(embed.description or ""))
            parts.extend(str(f.value) for f in embed.fields)
    return "\n".join(parts)


class TestConservativeDefaults(unittest.TestCase):
    def test_defaults(self):
        c = DictConfig()
        self.assertEqual(c.rate_limit_cooldown, 10)
        self.assertEqual(c.max_concurrent_generations, 2)
        self.assertEqual(c.batch_max_count, 5)
        self.assertTrue(c.discord_guild_only)
        self.assertEqual(c.discord_allowed_guilds, [])
        self.assertEqual(c.discord_allowed_channels, [])
        self.assertIsNone(c.discord_optout_file)
        self.assertTrue(c.matrix_auto_join)
        self.assertEqual(c.matrix_auto_join_allowlist, [])
        self.assertFalse(c.matrix_auto_join_allow_all)

    def test_bad_values_fall_back_or_clamp(self):
        c = DictConfig({"RATE_LIMIT_COOLDOWN_SECONDS": "-5", "MAX_CONCURRENT_GENERATIONS": "0",
                        "BATCH_MAX_COUNT": "nope"})
        self.assertEqual(c.rate_limit_cooldown, 0)
        self.assertEqual(c.max_concurrent_generations, 1)
        self.assertEqual(c.batch_max_count, 5)


class TestDiscordSlashControls(unittest.TestCase):
    def test_cooldown_blocks_second_joke_and_skips_generation(self):
        bot = _discord({"RATE_LIMIT_COOLDOWN_SECONDS": "60"})
        joke = bot.bot.tree.get_command("joke")

        async def scenario():
            first, second = _interaction(), _interaction()
            await joke.callback(first)
            await joke.callback(second)
            return first, second

        _, second = asyncio.run(scenario())
        self.assertEqual(len(bot.generator.calls), 1)
        self.assertIn("Slow down", _sent_text(second.followup.send))

    def test_concurrency_cap_refuses_extra_generation(self):
        bot = _discord({"MAX_CONCURRENT_GENERATIONS": "1"}, delay=0.3)
        joke = bot.bot.tree.get_command("joke")

        async def scenario():
            a, b = _interaction(user_id=1), _interaction(user_id=2)
            await asyncio.gather(joke.callback(a), joke.callback(b))
            return a, b

        a, b = asyncio.run(scenario())
        self.assertEqual(len(bot.generator.calls), 1)
        self.assertIn("busy", (_sent_text(a.followup.send) + _sent_text(b.followup.send)).lower())

    def test_batch_default_cap_is_five(self):
        bot = _discord()
        batch = bot.bot.tree.get_command("batch")
        over, ok = _interaction(), _interaction()

        async def scenario():
            await batch.callback(over, count=6)
            await batch.callback(ok, count=5)

        asyncio.run(scenario())
        self.assertEqual([c[1]["count"] for c in bot.generator.calls], [5])
        self.assertIn("between 1 and 5", _sent_text(over.followup.send))

    def test_batch_cap_is_configurable_and_hard_limited_to_ten(self):
        bot = _discord({"BATCH_MAX_COUNT": "50"})
        batch = bot.bot.tree.get_command("batch")
        over = _interaction()
        asyncio.run(batch.callback(over, count=11))
        self.assertEqual(bot.generator.calls, [])
        self.assertIn("between 1 and 10", _sent_text(over.followup.send))

    def test_guild_only_blocks_dm_by_default(self):
        bot = _discord()
        dm = _interaction(in_guild=False)
        allowed = asyncio.run(bot.bot.tree.interaction_check(dm))
        self.assertFalse(allowed)
        dm.response.send_message.assert_awaited()

    def test_guild_only_can_be_turned_off(self):
        bot = _discord({"DISCORD_GUILD_ONLY": "false"})
        self.assertTrue(asyncio.run(bot.bot.tree.interaction_check(_interaction(in_guild=False))))

    def test_guild_and_channel_allowlists(self):
        bot = _discord({"DISCORD_ALLOWED_GUILDS": "900, 901", "DISCORD_ALLOWED_CHANNELS": "800"})
        check = bot.bot.tree.interaction_check
        self.assertTrue(asyncio.run(check(_interaction(guild_id=900, channel_id=800))))
        self.assertFalse(asyncio.run(check(_interaction(guild_id=999, channel_id=800))))
        self.assertFalse(asyncio.run(check(_interaction(guild_id=900, channel_id=777))))

    def test_empty_allowlists_allow_any_guild(self):
        bot = _discord()
        self.assertTrue(asyncio.run(bot.bot.tree.interaction_check(_interaction(guild_id=12345))))

    def test_opted_out_user_is_not_targeted(self):
        bot = _discord()
        bot.optout.add(222)
        target = MagicMock(id=222, display_name="Target", mention="<@222>")
        i = _interaction()
        asyncio.run(bot.bot.tree.get_command("joke").callback(i, user=target))
        self.assertEqual(bot.generator.calls, [])
        self.assertIn("opted out", _sent_text(i.followup.send).lower())

    def test_opted_out_user_is_not_targeted_by_thegame(self):
        bot = _discord()
        bot.optout.add(222)
        target = MagicMock(id=222, display_name="Target", mention="<@222>")
        i = _interaction()
        asyncio.run(bot.bot.tree.get_command("joke").callback(i, flavor="thegame", user=target))
        self.assertEqual(bot.generator.calls, [])

    def test_optout_and_optin_commands(self):
        bot = _discord()
        out, back = _interaction(user_id=333), _interaction(user_id=333)
        asyncio.run(bot.bot.tree.get_command("optout").callback(out))
        self.assertTrue(bot.optout.is_opted_out(333))
        out.response.send_message.assert_awaited()
        self.assertTrue(out.response.send_message.call_args.kwargs.get("ephemeral"))
        asyncio.run(bot.bot.tree.get_command("optin").callback(back))
        self.assertFalse(bot.optout.is_opted_out(333))

    def test_optout_is_reachable_in_a_dm_even_when_guild_only(self):
        bot = _discord()
        dm = _interaction(in_guild=False)
        dm.command = MagicMock()
        dm.command.name = "optout"
        self.assertTrue(asyncio.run(bot.bot.tree.interaction_check(dm)))

    def test_optout_persists_to_configured_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "optout.json")
            bot = _discord({"DISCORD_OPTOUT_FILE": path})
            asyncio.run(bot.bot.tree.get_command("optout").callback(_interaction(user_id=77)))
            again = _discord({"DISCORD_OPTOUT_FILE": path})
            self.assertTrue(again.optout.is_opted_out(77))

    def test_audit_line_has_ids_only(self):
        bot = _discord()
        target = MagicMock(id=222, display_name="SECRETNAME", mention="<@222>")
        with self.assertLogs("yo_mama.audit", level=logging.INFO) as cm:
            asyncio.run(bot.bot.tree.get_command("joke").callback(
                _interaction(user_id=111), meanness=9, user=target, target="FREETEXTSECRET"))
        line = cm.output[0]
        for needle in ("invoker=111", "target=222", "level=9", "guild=900", "channel=800"):
            self.assertIn(needle, line)
        for forbidden in ("SECRETNAME", "FREETEXTSECRET", "Yo mama"):
            self.assertNotIn(forbidden, line)

    def test_no_audit_or_generation_for_refused_requests(self):
        bot = _discord({"RATE_LIMIT_COOLDOWN_SECONDS": "60"})
        joke = bot.bot.tree.get_command("joke")
        asyncio.run(joke.callback(_interaction()))
        with self.assertLogs("yo_mama.audit", level=logging.INFO) as cm:
            logging.getLogger("yo_mama.audit").info("sentinel")
            asyncio.run(joke.callback(_interaction()))
        self.assertEqual(len(cm.output), 1)  # only the sentinel

    def test_sends_never_parse_mentions(self):
        bot = _discord()
        i = _interaction()
        target = MagicMock(id=222, display_name="T", mention="<@222>")
        asyncio.run(bot.bot.tree.get_command("joke").callback(i, user=target))
        am = i.followup.send.call_args.kwargs.get("allowed_mentions")
        self.assertIsNotNone(am)
        self.assertFalse(am.everyone)
        self.assertFalse(am.users)
        self.assertFalse(am.roles)
        self.assertFalse(am.replied_user)

    def test_client_default_allowed_mentions_is_none(self):
        am = _discord().bot.allowed_mentions
        self.assertIsNotNone(am)
        self.assertEqual((am.everyone, am.users, am.roles, am.replied_user),
                         (False, False, False, False))


class TestDiscordTextControls(unittest.TestCase):
    def _ctx(self, author_bot=False, guild_id=900, channel_id=800, in_guild=True):
        ctx = MagicMock()
        ctx.author.bot = author_bot
        ctx.author.id = 111
        ctx.guild = MagicMock(id=guild_id) if in_guild else None
        ctx.channel.id = channel_id
        ctx.send = AsyncMock()
        return ctx

    def test_other_bots_are_ignored(self):
        bot = _discord()
        self.assertFalse(asyncio.run(bot.bot.can_run(self._ctx(author_bot=True))))
        self.assertTrue(asyncio.run(bot.bot.can_run(self._ctx())))

    def test_guild_only_and_allowlist_apply_to_text_commands(self):
        bot = _discord({"DISCORD_ALLOWED_GUILDS": "900"})
        self.assertFalse(asyncio.run(bot.bot.can_run(self._ctx(in_guild=False))))
        self.assertFalse(asyncio.run(bot.bot.can_run(self._ctx(guild_id=1))))
        self.assertTrue(asyncio.run(bot.bot.can_run(self._ctx(guild_id=900))))

    def test_text_cooldown_and_no_mention_parsing(self):
        bot = _discord({"RATE_LIMIT_COOLDOWN_SECONDS": "60"})
        random_cmd = bot.bot.get_command("random")
        first, second = self._ctx(), self._ctx()
        asyncio.run(random_cmd.callback(first))
        asyncio.run(random_cmd.callback(second))
        self.assertEqual(len(bot.generator.calls), 1)
        self.assertIn("Slow down", _sent_text(second.send))
        self.assertIsInstance(first.send.call_args.kwargs.get("allowed_mentions"),
                              discord.AllowedMentions)


def _matrix(values=None):
    base = {"MATRIX_USER_ID": "@bot:example.org", "MATRIX_ACCESS_TOKEN": "x",
            "RATE_LIMIT_COOLDOWN_SECONDS": "0"}
    cfg = DictConfig(dict(base, **(values or {})))
    with patch("yo_mama.platforms.matrix_bot.YoMamaGenerator"):
        bot = MatrixBot(config=cfg)
    bot.generator = FakeGenerator()
    bot.client = MagicMock()
    bot.client.join = AsyncMock()
    bot.client.room_send = AsyncMock()
    return bot


def _msg(body, sender="@alice:example.org", content=None):
    event = MagicMock()
    event.sender = sender
    event.body = body
    event.source = {"content": content if content is not None else {"msgtype": "m.text", "body": body}}
    return event


def _room():
    room = MagicMock()
    room.room_id = "!room:example.org"
    return room


def _invite(sender):
    event = MagicMock()
    event.sender = sender
    return event


class TestMatrixControls(unittest.TestCase):
    def test_auto_join_default_joins_nobody(self):
        bot = _matrix()
        asyncio.run(bot._handle_invite(_room(), _invite("@mallory:evil.example")))
        bot.client.join.assert_not_awaited()

    def test_allowlist_matches_user_id_and_server_name(self):
        bot = _matrix({"MATRIX_AUTO_JOIN_ALLOWLIST": "@alice:example.org, friends.example"})
        for sender, joined in (("@alice:example.org", True), ("@bob:friends.example", True),
                               ("@bob:example.org", False), ("@mallory:evil.example", False),
                               ("@x:notfriends.example", False)):
            bot.client.join.reset_mock()
            asyncio.run(bot._handle_invite(_room(), _invite(sender)))
            self.assertEqual(bot.client.join.await_count == 1, joined, sender)

    def test_allow_all_setting_keeps_old_behavior(self):
        bot = _matrix({"MATRIX_AUTO_JOIN_ALLOW_ALL": "true"})
        asyncio.run(bot._handle_invite(_room(), _invite("@mallory:evil.example")))
        bot.client.join.assert_awaited_once()

    def test_auto_join_false_never_joins_even_if_allowlisted(self):
        bot = _matrix({"MATRIX_AUTO_JOIN": "false", "MATRIX_AUTO_JOIN_ALLOWLIST": "example.org"})
        asyncio.run(bot._handle_invite(_room(), _invite("@alice:example.org")))
        bot.client.join.assert_not_awaited()

    def test_batch_cap_default_five(self):
        bot = _matrix()
        asyncio.run(bot._handle_message(_room(), _msg("!batch 6")))
        self.assertEqual(bot.generator.calls, [])
        sent = _sent_text_matrix(bot)
        self.assertIn("between 1 and 5", sent)
        asyncio.run(bot._handle_message(_room(), _msg("!batch 5")))
        self.assertEqual([c[1]["count"] for c in bot.generator.calls], [5])

    def test_cooldown_per_sender(self):
        bot = _matrix({"RATE_LIMIT_COOLDOWN_SECONDS": "60"})
        asyncio.run(bot._handle_message(_room(), _msg("!random")))
        asyncio.run(bot._handle_message(_room(), _msg("!random")))
        self.assertEqual(len(bot.generator.calls), 1)
        self.assertIn("Slow down", _sent_text_matrix(bot))
        asyncio.run(bot._handle_message(_room(), _msg("!random", sender="@carol:example.org")))
        self.assertEqual(len(bot.generator.calls), 2)

    def test_concurrency_cap(self):
        bot = _matrix({"MAX_CONCURRENT_GENERATIONS": "1"})
        bot.generator = FakeGenerator(delay=0.3)

        async def scenario():
            await asyncio.gather(
                bot._handle_message(_room(), _msg("!random", sender="@a:example.org")),
                bot._handle_message(_room(), _msg("!random", sender="@b:example.org")))

        asyncio.run(scenario())
        self.assertEqual(len(bot.generator.calls), 1)
        self.assertIn("busy", _sent_text_matrix(bot).lower())

    def test_configured_ignore_senders(self):
        bot = _matrix({"MATRIX_IGNORE_SENDERS": "@otherbot:example.org"})
        asyncio.run(bot._handle_message(_room(), _msg("!random", sender="@otherbot:example.org")))
        self.assertEqual(bot.generator.calls, [])
        asyncio.run(bot._handle_message(_room(), _msg("!random")))
        self.assertEqual(len(bot.generator.calls), 1)

    def test_messages_from_other_yomama_instances_are_ignored(self):
        bot = _matrix()
        marked = {"msgtype": "m.text", "body": "!random", "dev.yomama.bot": True}
        asyncio.run(bot._handle_message(_room(), _msg("!random", content=marked)))
        self.assertEqual(bot.generator.calls, [])

    def test_own_sends_carry_the_bot_marker(self):
        bot = _matrix()
        asyncio.run(bot._send_message(_room(), "hello"))
        content = bot.client.room_send.call_args.kwargs["content"]
        self.assertTrue(content.get("dev.yomama.bot"))

    def test_audit_line_has_ids_only(self):
        bot = _matrix()
        with self.assertLogs("yo_mama.audit", level=logging.INFO) as cm:
            asyncio.run(bot._handle_message(_room(), _msg("!joke SECRETFLAVOR 9 3")))
        line = cm.output[0]
        for needle in ("matrix", "joke", "invoker=@alice:example.org", "level=9",
                       "channel=!room:example.org"):
            self.assertIn(needle, line)
        self.assertNotIn("SECRETFLAVOR", line)


def _sent_text_matrix(bot):
    return "\n".join(str(c.kwargs["content"]["body"]) for c in bot.client.room_send.call_args_list)


if __name__ == "__main__":
    unittest.main()
