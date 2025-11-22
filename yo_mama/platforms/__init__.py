# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""Platform integrations for Yo Mama Bot."""

from .discord_bot import DiscordBot, run_discord_bot
from .matrix_bot import MatrixBot, run_matrix_bot

__all__ = ['DiscordBot', 'MatrixBot', 'run_discord_bot', 'run_matrix_bot']
"""Platform integrations for Yo Mama Bot."""

from .discord_bot import DiscordBot, run_discord_bot
from .matrix_bot import MatrixBot, run_matrix_bot

__all__ = ['DiscordBot', 'MatrixBot', 'run_discord_bot', 'run_matrix_bot']
